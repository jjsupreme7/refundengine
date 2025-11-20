#!/usr/bin/env python3
"""
Add Page Numbers to Existing Chunks

Updates existing tax_law_chunks with page number information
without re-ingesting or regenerating embeddings.
"""

from core.database import get_supabase_client
from core.chunking_with_pages import (
    extract_text_with_page_mapping,
    find_chunk_page_numbers,
    format_section_with_page,
)
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

# Import centralized Supabase client

supabase = get_supabase_client()


def add_page_numbers():
    """Add page numbers to all existing chunks"""

    print("=" * 80)
    print("📄 ADDING PAGE NUMBERS TO EXISTING CHUNKS")
    print("=" * 80)

    # Get all documents
    print("\n[1/3] Fetching documents...")
    docs_result = supabase.table("knowledge_documents").select("*").execute()
    documents = docs_result.data

    print(f"✅ Found {len(documents)} documents\n")

    total_updated = 0

    for doc in documents:
        doc_id = doc["id"]
        title = doc["title"]
        source_file = doc["source_file"]

        print(f"\n{'=' * 70}")
        print(f"Processing: {title}")
        print(f"File: {source_file}")
        print(f"{'=' * 70}")

        # Check if file exists
        if not Path(source_file).exists():
            print(f"⚠️  File not found: {source_file}")
            print("   Skipping this document")
            continue

        # Extract text with page mapping
        print("📄 Extracting text with page mapping...")
        try:
            full_text, page_map, total_pages = extract_text_with_page_mapping(
                source_file
            )
            print(f"✅ Extracted {total_pages} pages")
        except Exception as e:
            print(f"❌ Error extracting PDF: {e}")
            continue

        # Get all chunks for this document
        print("📥 Fetching chunks for this document...")
        chunks_result = (
            supabase.table("tax_law_chunks")
            .select("*")
            .eq("document_id", doc_id)
            .order("chunk_number")
            .execute()
        )
        chunks = chunks_result.data

        print(f"✅ Found {len(chunks)} chunks")

        # Update each chunk with page numbers
        print("📝 Adding page numbers to chunks...")
        updated_count = 0

        for chunk in chunks:
            chunk_id = chunk["id"]
            chunk_text = chunk["chunk_text"]
            section_id = chunk.get("section_title", "")

            # Find page numbers for this chunk
            page_nums = find_chunk_page_numbers(chunk_text, full_text, page_map)

            # Format page reference
            if page_nums:
                if len(page_nums) == 1:
                    page_ref = f"Page {page_nums[0]}"
                elif len(page_nums) > 1:
                    page_ref = f"Pages {page_nums[0]}-{page_nums[-1]}"
                else:
                    page_ref = ""
            else:
                page_ref = ""

            # Combine section_id and page_ref
            new_section_title = format_section_with_page(section_id, page_ref)

            # Update chunk
            try:
                supabase.table("tax_law_chunks").update(
                    {"section_title": new_section_title}
                ).eq("id", chunk_id).execute()

                updated_count += 1

                if updated_count % 10 == 0:
                    print(
                        f"  Updated {updated_count}/{len(chunks)} chunks...", end="\r"
                    )

            except Exception as e:
                print(f"\n⚠️  Error updating chunk {chunk['chunk_number']}: {e}")

        print(f"\n✅ Updated {updated_count}/{len(chunks)} chunks with page numbers")
        total_updated += updated_count

    print("\n" + "=" * 80)
    print("✅ PAGE NUMBER UPDATE COMPLETE")
    print("=" * 80)
    print(f"Total chunks updated: {total_updated}")
    print("=" * 80)


def verify_page_numbers():
    """Verify that page numbers were added correctly"""

    print("\n" + "=" * 80)
    print("🔍 VERIFYING PAGE NUMBERS")
    print("=" * 80)

    # Sample a few chunks
    chunks = (
        supabase.table("tax_law_chunks")
        .select("citation, chunk_number, section_title")
        .limit(5)
        .execute()
    )

    print("\nSample chunks:")
    for chunk in chunks.data:
        print(f"  • {chunk['citation']} - Chunk {chunk['chunk_number']}")
        print(f"    Section: {chunk['section_title']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(description="Add page numbers to existing chunks")
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify, do not update"
    )

    args = parser.parse_args()

    if args.verify_only:
        verify_page_numbers()
    else:
        add_page_numbers()
        verify_page_numbers()
