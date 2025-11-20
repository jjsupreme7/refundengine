#!/usr/bin/env python3
"""
Simple Large Document Ingestion
For documents too large for AI metadata extraction

Usage:
    python core/ingest_large_document.py \
      --file "knowledge_base/states/washington/legal_documents/20_Retail_Sales_and_Use_Tax.pd" \
      --type tax_law \
      --title "Retail Sales and Use Tax" \
      --citation "Chapter 20" \
      --category "general"
"""

from core.database import get_supabase_client
from core.chunking_with_pages import chunk_document_with_pages, format_section_with_page
from core.chunking import chunk_legal_document, get_chunking_stats
import argparse
import os
import sys
from pathlib import Path
from typing import List

import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Import canonical chunking
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import centralized Supabase client

supabase = get_supabase_client()


def extract_full_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """Extract all text from PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            text = ""

            print(f"Extracting text from {total_pages} pages...")
            for i, page in enumerate(tqdm(pdf.pages, desc="Pages"), 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            return text, total_pages
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return "", 0


def generate_embedding(text: str) -> List[float]:
    """Generate OpenAI embedding for text"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small", input=text[:8000]  # Limit to 8k chars
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None


def ingest_large_document(
    pdf_path: str,
    document_type: str,
    title: str,
    citation: str = None,
    law_category: str = "general",
    vendor_name: str = None,
    vendor_category: str = None,
):
    """
    Ingest a large document with manual metadata (no AI extraction)

    Args:
        pdf_path: Path to PDF file
        document_type: 'tax_law' or 'vendor'
        title: Document title
        citation: For tax law (e.g., "WAC 458-20-15502")
        law_category: For tax law (e.g., "exemption", "rate", "general")
        vendor_name: For vendor docs
        vendor_category: For vendor docs
    """

    print("=" * 80)
    print("LARGE DOCUMENT INGESTION")
    print("=" * 80)
    print(f"File: {pdf_path}")
    print(f"Type: {document_type}")
    print(f"Title: {title}")
    print("=" * 80)

    # Step 1: Extract full text
    print("\n[1/5] Extracting text from PDF...")
    full_text, total_pages = extract_full_text_from_pdf(pdf_path)

    if not full_text:
        print("❌ Could not extract text from PDF")
        return False

    print(f"✅ Extracted {len(full_text):,} characters from {total_pages} pages")

    # Step 2: Store document in Supabase
    print("\n[2/5] Storing document in Supabase...")

    doc_data = {
        "document_type": document_type,
        "title": title,
        "source_file": pdf_path,
        "processing_status": "processing",
    }

    # Add type-specific metadata
    if document_type == "tax_law":
        doc_data.update({"citation": citation or title, "law_category": law_category})
    else:  # vendor
        doc_data.update(
            {
                "vendor_name": vendor_name or "Unknown",
                "vendor_category": vendor_category or "general",
            }
        )

    try:
        result = supabase.table("knowledge_documents").insert(doc_data).execute()
        document_id = result.data[0]["id"]
        print(f"✅ Document stored (ID: {document_id})")
    except Exception as e:
        print(f"❌ Failed to store document: {e}")
        return False

    # Step 3: Smart chunk text using canonical chunking WITH PAGE NUMBERS
    print("\n[3/5] Chunking text intelligently (with page number tracking)...")
    chunks, total_pages_processed = chunk_document_with_pages(
        pdf_path, target_words=800, max_words=1500, min_words=150
    )

    stats = get_chunking_stats(chunks)
    print(f"✅ Created {len(chunks)} chunks from {total_pages_processed} pages")
    print(
        f"   Average: {stats['avg_words']:.0f} words, Range: {
            stats['min_words']}-{stats['max_words']} words"
    )

    # Update total_chunks
    supabase.table("knowledge_documents").update({"total_chunks": len(chunks)}).eq(
        "id", document_id
    ).execute()

    # Step 4: Generate embeddings and store chunks
    print("\n[4/5] Generating embeddings and storing chunks...")

    chunk_table = (
        "tax_law_chunks" if document_type == "tax_law" else "vendor_background_chunks"
    )
    successful_chunks = 0

    for chunk in tqdm(chunks, desc="Processing chunks"):
        try:
            embedding = generate_embedding(chunk["chunk_text"])

            if embedding:
                chunk_data = {
                    "document_id": document_id,
                    "chunk_number": chunk["chunk_index"] + 1,  # 1-indexed
                    "chunk_text": chunk["chunk_text"],
                    "embedding": embedding,
                }

                # Add type-specific fields
                if document_type == "tax_law":
                    # Combine section_id with page_reference for section_title
                    section_id = chunk.get("section_id", "")
                    page_ref = chunk.get("page_reference", "")
                    combined_section_title = format_section_with_page(
                        section_id, page_ref
                    )

                    chunk_data.update(
                        {
                            "citation": citation or title,
                            "law_category": law_category,
                            "section_title": combined_section_title,  # Now includes page numbers!
                        }
                    )
                else:  # vendor
                    chunk_data.update(
                        {
                            "vendor_name": vendor_name or "Unknown",
                            "vendor_category": vendor_category or "general",
                            "document_category": "general",
                        }
                    )

                supabase.table(chunk_table).insert(chunk_data).execute()
                successful_chunks += 1

        except Exception as e:
            print(f"\n⚠️  Failed to process chunk {chunk['chunk_index']}: {e}")
            continue

    print(f"\n✅ Stored {successful_chunks}/{len(chunks)} chunks with embeddings")

    # Step 5: Mark as completed
    print("\n[5/5] Finalizing...")
    supabase.table("knowledge_documents").update({"processing_status": "completed"}).eq(
        "id", document_id
    ).execute()

    print("\n" + "=" * 80)
    print("✅ LARGE DOCUMENT INGESTION COMPLETE!")
    print("=" * 80)
    print(f"Document ID: {document_id}")
    print(f"Total Chunks: {successful_chunks}")
    print("=" * 80)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Ingest large documents with manual metadata"
    )
    parser.add_argument("--file", required=True, help="Path to PDF file")
    parser.add_argument(
        "--type", required=True, choices=["tax_law", "vendor"], help="Document type"
    )
    parser.add_argument("--title", required=True, help="Document title")

    # Tax law options
    parser.add_argument(
        "--citation", help="Citation (for tax law, e.g., 'WAC 458-20-15502')"
    )
    parser.add_argument(
        "--category",
        default="general",
        help="Law category (exemption, rate, definition, general)",
    )

    # Vendor options
    parser.add_argument("--vendor-name", help="Vendor name (for vendor docs)")
    parser.add_argument(
        "--vendor-category", help="Vendor category (manufacturer, distributor, etc.)"
    )

    args = parser.parse_args()

    # Validate
    if args.type == "tax_law" and not args.citation:
        print("⚠️  Warning: No citation provided, using title as citation")
        args.citation = args.title

    if args.type == "vendor" and not args.vendor_name:
        print("❌ Error: --vendor-name required for vendor documents")
        return

    # Check file exists
    if not Path(args.file).exists():
        print(f"❌ Error: File not found: {args.file}")
        return

    # Ingest
    success = ingest_large_document(
        pdf_path=args.file,
        document_type=args.type,
        title=args.title,
        citation=args.citation,
        law_category=args.category,
        vendor_name=args.vendor_name,
        vendor_category=args.vendor_category,
    )

    if success:
        print("\n✅ Success! Document ingested with consistent chunking.")
    else:
        print("\n❌ Failed to ingest document.")


if __name__ == "__main__":
    main()
