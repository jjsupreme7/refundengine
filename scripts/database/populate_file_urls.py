#!/usr/bin/env python3
"""
Database Migration: Populate file_url for Existing Documents

This script backfills the file_url field in the knowledge_documents table
for all existing documents. It generates appropriate URLs based on:
- WAC/RCW citations → Official WA Legislature URLs
- PDF files → Local serving endpoints

Usage:
    python scripts/populate_file_urls.py
    python scripts/populate_file_urls.py --dry-run  # Preview changes without updating
"""

from core.document_urls import generate_document_url
from core.database import get_supabase_client
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Initialize Supabase client (centralized)
supabase = get_supabase_client()


def fetch_all_documents() -> List[Dict]:
    """
    Fetch all documents from knowledge_documents table
    """
    print("📥 Fetching all documents from database...")

    try:
        result = (
            supabase.table("knowledge_documents")
            .select("id, document_type, citation, source_file, file_url, title")
            .execute()
        )

        print(f"✅ Found {len(result.data)} documents in database")
        return result.data

    except Exception as e:
        print(f"❌ Error fetching documents: {e}")
        return []


def generate_urls_for_documents(documents: List[Dict]) -> List[Dict]:
    """
    Generate file URLs for all documents

    Returns list of updates: [{"id": uuid, "file_url": url, "title": title}, ...]
    """
    updates = []
    skipped_count = 0
    already_have_url = 0

    print("\n🔗 Generating URLs for documents...")

    for doc in tqdm(documents, desc="Processing documents"):
        doc_id = doc["id"]
        document_type = doc["document_type"]
        citation = doc.get("citation")
        source_file = doc.get("source_file")
        existing_url = doc.get("file_url")
        title = doc.get("title", "Unknown")

        # Skip if already has a URL
        if existing_url:
            already_have_url += 1
            continue

        # Generate URL
        file_url = generate_document_url(citation, source_file, document_type)

        if file_url:
            updates.append(
                {
                    "id": doc_id,
                    "file_url": file_url,
                    "title": title,
                    "citation": citation,
                    "source_file": source_file,
                }
            )
        else:
            skipped_count += 1
            print(f"\n⚠️  Could not generate URL for: {title}")
            print(f"   Citation: {citation}, Source: {source_file}")

    print("\n📊 URL Generation Summary:")
    print(f"   ✅ URLs generated: {len(updates)}")
    print(f"   ⏭️  Already have URL: {already_have_url}")
    print(f"   ⚠️  Skipped (no valid citation/file): {skipped_count}")

    return updates


def preview_updates(updates: List[Dict], limit: int = 10):
    """
    Preview the first few URL updates
    """
    print(f"\n🔍 Preview of URL updates (showing first {min(limit, len(updates))}):")
    print("=" * 100)

    for i, update in enumerate(updates[:limit]):
        print(f"\n{i + 1}. {update['title'][:60]}")
        print(f"   Citation: {update.get('citation', 'N/A')}")
        print(f"   Source: {update.get('source_file', 'N/A')[:80]}")
        print(f"   → New URL: {update['file_url']}")

    if len(updates) > limit:
        print(f"\n   ... and {len(updates) - limit} more")

    print("=" * 100)


def apply_updates(updates: List[Dict], dry_run: bool = False):
    """
    Apply the URL updates to the database
    """
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made to database")
        preview_updates(updates)
        return

    if not updates:
        print(
            "\n✅ No updates needed - all documents already have URLs or cannot generate URLs"
        )
        return

    # Show preview and ask for confirmation
    preview_updates(updates)

    print(f"\n⚠️  Ready to update {len(updates)} documents in the database")
    response = input("Continue? [y/N]: ").strip().lower()

    if response != "y":
        print("❌ Update cancelled")
        return

    # Apply updates
    print("\n💾 Updating database...")
    successful = 0
    failed = 0

    for update in tqdm(updates, desc="Updating documents"):
        try:
            supabase.table("knowledge_documents").update(
                {"file_url": update["file_url"]}
            ).eq("id", update["id"]).execute()

            successful += 1

        except Exception as e:
            print(f"\n❌ Failed to update {update['title']}: {e}")
            failed += 1

    print(f"\n{'=' * 70}")
    print("📊 UPDATE SUMMARY")
    print(f"{'=' * 70}")
    print(f"✅ Successfully updated: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"{'=' * 70}\n")


def main():
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(
        description="Populate file_url field for existing documents"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating database",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📄 Knowledge Base URL Population Migration")
    print("=" * 70)

    # Fetch all documents
    documents = fetch_all_documents()

    if not documents:
        print("❌ No documents found or error fetching documents")
        return

    # Generate URLs
    updates = generate_urls_for_documents(documents)

    # Apply updates
    apply_updates(updates, dry_run=args.dry_run)

    print("✅ Migration complete!")


if __name__ == "__main__":
    main()
