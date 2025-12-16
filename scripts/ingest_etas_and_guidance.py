#!/usr/bin/env python3
"""
Batch Ingest ETAs, Tax Guides, and Other DOR Guidance Documents

Ingests PDF documents from:
- knowledge_base/states/washington/ETAs/
- knowledge_base/states/washington/other_guidance/
- knowledge_base/states/washington/essb_5814_oct_2025/

Usage:
    python scripts/ingest_etas_and_guidance.py --dry-run    # Preview only
    python scripts/ingest_etas_and_guidance.py              # Full ingestion
    python scripts/ingest_etas_and_guidance.py --folder ETAs --limit 10  # Test specific folder
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client
from core.chunking import chunk_legal_document

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()

# Base path for Washington state documents
WA_DOCS_PATH = Path("/Users/jacoballen/Desktop/refund-engine/knowledge_base/states/washington")

# Folder configurations
# Note: document_type must be "tax_law" due to database constraint
FOLDERS = {
    "ETAs": {
        "path": WA_DOCS_PATH / "ETAs",
        "doc_type": "tax_law",  # Database constraint requires tax_law
        "citation_prefix": "ETA",
        "url_template": "https://dor.wa.gov/sites/default/files/2022-02/eta{num}.pdf",
    },
    "other_guidance": {
        "path": WA_DOCS_PATH / "other_guidance",
        "doc_type": "tax_law",  # Database constraint requires tax_law
        "citation_prefix": None,  # Extract from filename
        "url_template": None,
    },
    "essb_5814": {
        "path": WA_DOCS_PATH / "essb_5814_oct_2025",
        "doc_type": "tax_law",  # Database constraint requires tax_law
        "citation_prefix": "ESSB 5814",
        "url_template": None,
    },
    "legal_documents": {
        "path": WA_DOCS_PATH / "legal_documents",
        "doc_type": "tax_law",
        "citation_prefix": None,
        "url_template": None,
    },
}


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


def extract_citation_from_filename(filename: str, folder_config: dict) -> str:
    """Extract citation from filename based on folder type."""
    base = Path(filename).stem

    if folder_config["citation_prefix"] == "ETA":
        # ETA files: 3004.pdf -> ETA 3004
        match = re.search(r"(\d+)", base)
        if match:
            return f"ETA {match.group(1)}"
        return f"ETA {base}"

    elif folder_config["citation_prefix"] == "ESSB 5814":
        # ESSB files: use descriptive title
        return f"ESSB 5814 - {base.replace('_', ' ')}"

    else:
        # Other guidance: use filename as title
        return base.replace("_", " ").replace("-", " ")


def generate_url(filename: str, folder_config: dict) -> Optional[str]:
    """Generate URL for document if template available."""
    if folder_config["url_template"]:
        match = re.search(r"(\d+)", filename)
        if match:
            return folder_config["url_template"].format(num=match.group(1))
    return None


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


def determine_category(text: str, filename: str) -> str:
    """Determine document category based on content."""
    text_lower = text.lower()
    filename_lower = filename.lower()

    if "exempt" in text_lower or "exemption" in filename_lower:
        return "exemption"
    elif "rate" in text_lower and ("percent" in text_lower or "levy" in text_lower):
        return "rate"
    elif "digital" in filename_lower or "software" in filename_lower:
        return "digital_products"
    elif "advertising" in filename_lower or "services" in filename_lower:
        return "services"
    elif "essb" in filename_lower or "5814" in filename_lower:
        return "legislation"
    elif "refund" in text_lower or "credit" in text_lower:
        return "refund"
    else:
        return "general"


def get_existing_documents() -> set:
    """Get set of existing document source files to avoid duplicates."""
    result = supabase.table("knowledge_documents").select("source_file, title").execute()
    existing = set()
    for doc in result.data:
        if doc.get("source_file"):
            existing.add(doc["source_file"])
        if doc.get("title"):
            # Also track by title to catch duplicates
            existing.add(doc["title"].lower()[:50])
    return existing


def ingest_document(pdf_path: Path, folder_name: str, folder_config: dict, existing: set, dry_run: bool = False) -> bool:
    """Ingest a single PDF document."""
    filename = pdf_path.name
    relative_path = f"knowledge_base/states/washington/{folder_name}/{filename}"

    # Check if already exists
    if relative_path in existing:
        return False  # Skip, already ingested

    # Extract text
    text, total_pages = extract_text_from_pdf(str(pdf_path))
    if not text or len(text) < 100:
        print(f"  Skipping {filename} - insufficient text")
        return False

    # Generate metadata
    citation = extract_citation_from_filename(filename, folder_config)
    url = generate_url(filename, folder_config)
    category = determine_category(text, filename)
    title = citation if citation else Path(filename).stem.replace("_", " ")

    # Check for duplicate by title
    if title.lower()[:50] in existing:
        return False  # Skip duplicate

    if dry_run:
        print(f"  Would ingest: {citation}")
        print(f"    Title: {title[:60]}")
        print(f"    Pages: {total_pages}")
        print(f"    Category: {category}")
        return True

    # Chunk the document with 50-word overlap
    chunks = chunk_legal_document(text, max_words=1500, overlap_words=50)
    if not chunks:
        print(f"  No chunks generated for {filename}")
        return False

    # Create document record
    doc_data = {
        "document_type": folder_config["doc_type"],
        "title": title[:255],
        "source_file": relative_path,
        "citation": citation,
        "law_category": category,
        "file_url": url,
        "total_chunks": len(chunks),
        "processing_status": "completed",
        "tax_types": ["sales tax", "use tax"],
    }

    try:
        # Insert document
        doc_result = supabase.table("knowledge_documents").insert(doc_data).execute()
        doc_id = doc_result.data[0]["id"]

        # Insert chunks with embeddings
        for i, chunk in enumerate(chunks):
            chunk_text = chunk["chunk_text"]
            chunk_role = chunk.get("chunk_role", "rule")
            embedding = generate_embedding(chunk_text)

            chunk_data = {
                "document_id": doc_id,
                "chunk_text": chunk_text,
                "chunk_number": i + 1,
                "citation": citation,
                "law_category": category,
                "chunk_role": chunk_role,
                "embedding": embedding,
                "source_type": folder_config["doc_type"],
            }

            supabase.table("tax_law_chunks").insert(chunk_data).execute()

        return True
    except Exception as e:
        print(f"  Error ingesting {filename}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Ingest ETAs and guidance documents")
    parser.add_argument("--dry-run", action="store_true", help="Preview without ingesting")
    parser.add_argument("--folder", choices=list(FOLDERS.keys()), help="Specific folder to process")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    args = parser.parse_args()

    print("=" * 70)
    print("BATCH INGEST ETAs AND GUIDANCE DOCUMENTS")
    print("=" * 70)

    # Get existing documents
    print("\nChecking existing documents...")
    existing = get_existing_documents()
    print(f"Found {len(existing)} existing document references")

    # Determine which folders to process
    folders_to_process = [args.folder] if args.folder else list(FOLDERS.keys())

    total_success = 0
    total_skipped = 0
    total_failed = 0

    for folder_name in folders_to_process:
        config = FOLDERS[folder_name]
        folder_path = config["path"]

        if not folder_path.exists():
            print(f"\nSkipping {folder_name} - folder not found")
            continue

        # Get PDF files
        pdf_files = list(folder_path.glob("*.pdf"))
        if args.limit:
            pdf_files = pdf_files[:args.limit]

        print(f"\n{'=' * 70}")
        print(f"Processing: {folder_name} ({len(pdf_files)} PDFs)")
        print("=" * 70)

        if args.dry_run:
            print("DRY RUN - No changes will be made\n")

        success = 0
        skipped = 0
        failed = 0

        for pdf_path in tqdm(pdf_files, desc=f"Ingesting {folder_name}"):
            result = ingest_document(pdf_path, folder_name, config, existing, args.dry_run)
            if result:
                success += 1
            elif result is False:
                skipped += 1
            else:
                failed += 1

        print(f"\n{folder_name} Results:")
        print(f"  Ingested: {success}")
        print(f"  Skipped (already exists): {skipped}")
        print(f"  Failed: {failed}")

        total_success += success
        total_skipped += skipped
        total_failed += failed

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total ingested: {total_success}")
    print(f"Total skipped: {total_skipped}")
    print(f"Total failed: {total_failed}")

    if not args.dry_run:
        # Verify counts
        docs = supabase.table("knowledge_documents").select("id", count="exact").execute()
        chunks = supabase.table("tax_law_chunks").select("id", count="exact").execute()
        print(f"\nDatabase now has:")
        print(f"  Documents: {docs.count}")
        print(f"  Chunks: {chunks.count}")


if __name__ == "__main__":
    main()
