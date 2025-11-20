#!/usr/bin/env python3
"""
Populate missing file_url values for WTD documents

This script converts source_file paths to Supabase storage URLs for WTD documents
that are missing their file_url values.
"""

from core.database import get_supabase_client
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


load_dotenv()


def main():
    """Populate file_url for WTD documents"""

    supabase = get_supabase_client()

    # Get all WTD documents missing file_url
    print("🔍 Finding WTD documents without file_url...")
    missing = (
        supabase.table("knowledge_documents")
        .select("id, citation, source_file")
        .ilike("citation", "Det.%")
        .is_("file_url", "null")
        .execute()
    )

    print(f"Found {len(missing.data)} WTD documents missing file_url\n")

    if not missing.data:
        print("✅ All WTD documents already have file_url!")
        return

    # Get the Supabase URL from env
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        print("❌ Error: SUPABASE_URL not found in environment")
        return

    # Process each document
    updated_count = 0
    error_count = 0

    for doc in missing.data:
        doc_id = doc["id"]
        citation = doc.get("citation", "N/A")
        source_file = doc.get("source_file", "")

        if not source_file:
            print(f"⚠️  Skipping {citation} - no source_file")
            error_count += 1
            continue

        # Convert source_file path to Supabase storage URL
        # Example: knowledge_base/wa_tax_law/tax_decisions/2022/41WTD282.pdf
        # Becomes:
        # https://PROJECT.supabase.co/storage/v1/object/public/knowledge-base/wa_tax_law/tax_decisions/2022/41WTD282.pdf

        # Remove leading slashes and 'knowledge_base/' prefix if it doesn't have it
        clean_path = source_file.lstrip("/")
        if not clean_path.startswith("knowledge_base/"):
            clean_path = "knowledge_base/" + clean_path.replace(
                "knowledge_base", ""
            ).lstrip("/")

        # Remove the 'knowledge_base/' prefix for the storage path
        storage_path = clean_path.replace("knowledge_base/", "")

        # Build the full URL
        file_url = (
            f"{supabase_url}/storage/v1/object/public/knowledge-base/{storage_path}"
        )

        # Update the document
        try:
            result = (
                supabase.table("knowledge_documents")
                .update({"file_url": file_url})
                .eq("id", doc_id)
                .execute()
            )

            print(f"✅ Updated: {citation}")
            print(f"   URL: {file_url}")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error updating {citation}: {e}")
            error_count += 1

    print(f"\n{'=' * 80}")
    print(f"✅ Successfully updated {updated_count} documents")
    if error_count > 0:
        print(f"⚠️  {error_count} documents had errors")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
