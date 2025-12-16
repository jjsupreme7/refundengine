#!/usr/bin/env python3
"""
Re-ingest All Documents with Chunk Overlap

This script:
1. Gets all documents from knowledge_documents
2. Deletes existing chunks for each document
3. Re-chunks with 50-word overlap (new chunking settings)
4. Re-generates embeddings
5. Stores new chunks

Usage:
    python scripts/reingest_with_overlap.py --dry-run    # Preview only
    python scripts/reingest_with_overlap.py              # Full re-ingest
    python scripts/reingest_with_overlap.py --limit 10   # Test with 10 docs
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import pdfplumber
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client
from core.chunking import chunk_legal_document
from core.chunking_with_pages import chunk_document_with_pages

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()


def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """Extract full text from PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                text_parts.append(text)
            return "\n\n".join(text_parts), total_pages
    except Exception as e:
        print(f"  Error extracting PDF: {e}")
        return "", 0


def extract_text_from_html(html_path: str) -> str:
    """Extract text from HTML file."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"  Error extracting HTML: {e}")
        return ""


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text chunk."""
    try:
        # Truncate to 8000 chars for embedding model
        truncated = text[:8000] if len(text) > 8000 else text
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=truncated
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  Error generating embedding: {e}")
        return None


def reingest_document(doc: dict, dry_run: bool = False) -> tuple[int, int]:
    """
    Re-ingest a single document with new chunking.

    Returns: (chunks_deleted, chunks_created)
    """
    doc_id = doc["id"]
    source_file = doc.get("source_file", "")
    doc_type = doc.get("document_type", "tax_law")

    # Determine chunk table
    chunk_table = "tax_law_chunks" if doc_type == "tax_law" else "vendor_background_chunks"

    # Step 1: Delete existing chunks
    existing = supabase.table(chunk_table).select("id").eq("document_id", doc_id).execute()
    chunks_deleted = len(existing.data) if existing.data else 0

    if not dry_run and chunks_deleted > 0:
        supabase.table(chunk_table).delete().eq("document_id", doc_id).execute()

    # Step 2: Extract text from source file
    if not source_file or not os.path.exists(source_file):
        return chunks_deleted, 0

    is_html = source_file.lower().endswith(".html")
    is_pdf = source_file.lower().endswith(".pdf")

    if is_html:
        full_text = extract_text_from_html(source_file)
        total_pages = 1
    elif is_pdf:
        full_text, total_pages = extract_text_from_pdf(source_file)
    else:
        return chunks_deleted, 0

    if not full_text.strip():
        return chunks_deleted, 0

    # Step 3: Re-chunk with overlap (overlap_words=50 is the new default)
    if is_pdf:
        chunks, _ = chunk_document_with_pages(
            source_file,
            target_words=800,
            max_words=1500,
            min_words=150,
            overlap_words=50
        )
    else:
        chunks = chunk_legal_document(
            full_text,
            target_words=800,
            max_words=1500,
            min_words=150,
            overlap_words=50
        )

    if dry_run:
        return chunks_deleted, len(chunks)

    # Step 4: Generate embeddings and store chunks
    chunks_created = 0
    for chunk in chunks:
        embedding = generate_embedding(chunk["chunk_text"])
        if not embedding:
            continue

        chunk_data = {
            "document_id": doc_id,
            "chunk_number": chunk["chunk_index"] + 1,
            "chunk_text": chunk["chunk_text"],
            "embedding": embedding,
            "citation": doc.get("citation", ""),
            "law_category": doc.get("law_category", "general"),
            "section_title": chunk.get("section_id", ""),
            "chunk_role": chunk.get("chunk_role", "rule"),
        }

        try:
            supabase.table(chunk_table).insert(chunk_data).execute()
            chunks_created += 1
        except Exception as e:
            print(f"    Error inserting chunk: {e}")

    # Step 5: Update total_chunks count
    supabase.table("knowledge_documents").update(
        {"total_chunks": chunks_created}
    ).eq("id", doc_id).execute()

    return chunks_deleted, chunks_created


def main():
    parser = argparse.ArgumentParser(description="Re-ingest documents with chunk overlap")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--limit", type=int, help="Limit number of documents to process")
    parser.add_argument("--doc-type", choices=["tax_law", "vendor_background"],
                        default="tax_law", help="Document type to re-ingest")
    args = parser.parse_args()

    print("=" * 70)
    print("Re-ingest Documents with 50-Word Chunk Overlap")
    print("=" * 70)

    if args.dry_run:
        print("\nDRY RUN MODE - No changes will be made\n")

    # Get all documents
    query = supabase.table("knowledge_documents").select("*").eq("document_type", args.doc_type)
    if args.limit:
        query = query.limit(args.limit)

    result = query.execute()
    documents = result.data if result.data else []

    print(f"Found {len(documents)} {args.doc_type} documents to re-ingest\n")

    if not documents:
        print("No documents found. Exiting.")
        return

    # Confirm before proceeding (unless dry run)
    if not args.dry_run:
        response = input("This will DELETE existing chunks and regenerate them. Continue? [y/N]: ")
        if response.strip().lower() != "y":
            print("Cancelled.")
            return

    # Process documents
    total_deleted = 0
    total_created = 0
    processed = 0
    failed = 0

    for doc in tqdm(documents, desc="Re-ingesting"):
        try:
            deleted, created = reingest_document(doc, dry_run=args.dry_run)
            total_deleted += deleted
            total_created += created
            processed += 1
        except Exception as e:
            print(f"\n  Error processing {doc.get('title', 'unknown')}: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"  Documents processed: {processed}")
    print(f"  Documents failed:    {failed}")
    print(f"  Chunks deleted:      {total_deleted}")
    print(f"  Chunks created:      {total_created}")

    if args.dry_run:
        print("\n  (DRY RUN - No actual changes were made)")


if __name__ == "__main__":
    main()
