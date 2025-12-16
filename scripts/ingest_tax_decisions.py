#!/usr/bin/env python3
"""
Batch Ingest Tax Decisions (WTD PDF files)

Ingests PDF documents from knowledge_base/wa_tax_law/tax_decisions/

Usage:
    python scripts/ingest_tax_decisions.py --dry-run    # Preview only
    python scripts/ingest_tax_decisions.py              # Full ingestion
    python scripts/ingest_tax_decisions.py --limit 10   # Test with 10 files
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

# Base path
TAX_DECISIONS_PATH = Path("/Users/jacoballen/Desktop/refund-engine/knowledge_base/wa_tax_law/tax_decisions")


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


def extract_citation_from_filename(filename: str) -> tuple[str, str]:
    """
    Extract citation and year from WTD filename.

    Examples:
        42WTD058.pdf -> ("42 WTD 058", "2023")
        39WTD204.pdf -> ("39 WTD 204", "2020")
    """
    base = Path(filename).stem

    # Match pattern: NNWTDNNN
    match = re.match(r"(\d+)WTD(\d+)", base, re.IGNORECASE)
    if match:
        volume = match.group(1)
        decision = match.group(2)
        citation = f"{volume} WTD {decision}"

        # Approximate year from volume (WTD started around 1983, ~1 per year)
        try:
            year = 1981 + int(volume)
        except:
            year = 2020
        return citation, str(year)

    return base, "unknown"


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text chunk."""
    try:
        truncated = text[:8000] if len(text) > 8000 else text
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=truncated
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  Error generating embedding: {e}")
        return None


def determine_category(text: str) -> str:
    """Determine category based on content."""
    text_lower = text.lower()

    if "exempt" in text_lower or "exemption" in text_lower:
        return "exemption"
    elif "refund" in text_lower or "credit" in text_lower:
        return "refund"
    elif "rate" in text_lower and "percent" in text_lower:
        return "rate"
    elif "definition" in text_lower or "defined" in text_lower:
        return "definition"
    else:
        return "general"


def get_existing_documents() -> set:
    """Get set of existing document citations and source_files."""
    all_docs = []
    offset = 0
    batch_size = 1000

    while True:
        result = supabase.table("knowledge_documents").select("citation, source_file").range(offset, offset + batch_size - 1).execute()
        if not result.data:
            break
        all_docs.extend(result.data)
        if len(result.data) < batch_size:
            break
        offset += batch_size

    existing = set()
    for doc in all_docs:
        if doc.get("citation"):
            existing.add(doc["citation"])
        if doc.get("source_file"):
            existing.add(doc["source_file"])

    return existing


def get_missing_files(existing: set) -> List[Dict]:
    """Get list of PDF files not in database."""
    missing = []

    for year_folder in TAX_DECISIONS_PATH.iterdir():
        if not year_folder.is_dir():
            continue

        year = year_folder.name

        for pdf_file in year_folder.glob("*.pdf"):
            citation, _ = extract_citation_from_filename(pdf_file.name)
            relative_path = f"knowledge_base/wa_tax_law/tax_decisions/{year}/{pdf_file.name}"

            # Skip if already in database by citation or path
            if citation in existing or relative_path in existing:
                continue

            missing.append({
                "path": str(pdf_file),
                "filename": pdf_file.name,
                "year": year,
                "citation": citation,
                "relative_path": relative_path,
            })

    return missing


def ingest_document(file_info: Dict, dry_run: bool = False) -> bool:
    """Ingest a single tax decision document."""
    pdf_path = file_info["path"]
    citation = file_info["citation"]
    relative_path = file_info["relative_path"]
    year = file_info["year"]

    # Extract text
    text, total_pages = extract_text_from_pdf(pdf_path)
    if not text or len(text) < 100:
        print(f"  Skipping {citation} - insufficient text")
        return False

    # Determine category
    category = determine_category(text)

    # Generate title from first line or citation
    title = f"Det. No. XX-XXXX, {citation} ({year})"

    # Try to extract actual title from text
    lines = text.split("\n")[:10]
    for line in lines:
        if "Det." in line and "WTD" in line:
            title = line.strip()[:255]
            break

    if dry_run:
        print(f"  Would ingest: {citation}")
        print(f"    Title: {title[:60]}")
        print(f"    Year: {year}")
        print(f"    Pages: {total_pages}")
        return True

    # Chunk with overlap
    chunks = chunk_legal_document(text, max_words=1500, overlap_words=50)
    if not chunks:
        print(f"  No chunks for {citation}")
        return False

    # Create document record
    doc_data = {
        "document_type": "tax_law",
        "title": title[:255],
        "source_file": relative_path,
        "citation": citation,
        "law_category": category,
        "total_chunks": len(chunks),
        "processing_status": "completed",
        "tax_types": ["sales tax", "use tax"],
    }

    try:
        doc_result = supabase.table("knowledge_documents").insert(doc_data).execute()
        doc_id = doc_result.data[0]["id"]

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
                "source_type": "wtd",
            }

            supabase.table("tax_law_chunks").insert(chunk_data).execute()

        return True
    except Exception as e:
        print(f"  Error ingesting {citation}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Ingest tax decision (WTD) documents")
    parser.add_argument("--dry-run", action="store_true", help="Preview without ingesting")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    args = parser.parse_args()

    print("=" * 70)
    print("BATCH INGEST TAX DECISIONS (WTD)")
    print("=" * 70)

    # Get existing documents
    print("\nChecking existing documents...")
    existing = get_existing_documents()
    print(f"Found {len(existing)} existing references")

    # Get missing files
    print("\nScanning for missing tax decisions...")
    missing = get_missing_files(existing)
    print(f"Found {len(missing)} files not in database")

    if args.limit:
        missing = missing[:args.limit]
        print(f"Processing first {args.limit} files")

    if not missing:
        print("\n✅ All tax decisions already ingested!")
        return

    # Group by year
    by_year = {}
    for f in missing:
        year = f["year"]
        by_year[year] = by_year.get(year, 0) + 1

    print("\nMissing by year:")
    for year in sorted(by_year.keys()):
        print(f"  {year}: {by_year[year]}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")

    # Process files
    print("\n📥 Ingesting documents...")
    success = 0
    failed = 0

    for file_info in tqdm(missing, desc="Ingesting"):
        if ingest_document(file_info, dry_run=args.dry_run):
            success += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully ingested: {success}")
    print(f"❌ Failed: {failed}")

    if not args.dry_run:
        docs = supabase.table("knowledge_documents").select("id", count="exact").execute()
        chunks = supabase.table("tax_law_chunks").select("id", count="exact").execute()
        print(f"\n📈 Database now has:")
        print(f"   Documents: {docs.count}")
        print(f"   Chunks: {chunks.count}")


if __name__ == "__main__":
    main()
