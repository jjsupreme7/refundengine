#!/usr/bin/env python3
"""
Set Default Effective Dates for Documents

This script assigns effective dates to documents that don't have them:
- ESSB 5814 documents: 2025-10-01 (already set)
- All other documents (WACs, RCWs, ETAs): Default to 2024-01-01 (pre-ESSB 5814)

This allows the Old Law vs New Law comparison to work properly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client


def set_default_effective_dates():
    """Set default effective dates for documents without them"""

    supabase = get_supabase_client()

    print("=" * 80)
    print("Setting Default Effective Dates")
    print("=" * 80)
    print()

    # Get documents without effective_date
    print("Step 1: Finding documents without effective_date...")
    result = (
        supabase.table("knowledge_documents")
        .select("id, citation, title, effective_date")
        .is_("effective_date", "null")
        .execute()
    )

    if not result.data:
        print("✅ All documents already have effective_date set!")
        return

    print(f"Found {len(result.data)} documents without effective_date")
    print()

    # Categorize documents
    essb_docs = []
    old_law_docs = []

    for doc in result.data:
        citation = doc.get("citation", "")
        title = doc.get("title", "")

        # Check if this is an ESSB 5814 document
        if (
            "ESSB 5814" in citation
            or "ESSB 5814" in title
            or "essb 5814" in citation.lower()
            or "essb 5814" in title.lower()
        ):
            essb_docs.append(doc)
        else:
            old_law_docs.append(doc)

    print(f"Categorized documents:")
    print(f"  - ESSB 5814 documents (will set to 2025-10-01): {len(essb_docs)}")
    print(f"  - Old law documents (will set to 2024-01-01): {len(old_law_docs)}")
    print()

    # Confirm with user
    response = input("Proceed with setting effective dates? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Cancelled.")
        return

    print()
    print("Step 2: Updating documents...")

    # Update ESSB 5814 documents
    if essb_docs:
        print(f"\nSetting {len(essb_docs)} ESSB 5814 documents to 2025-10-01...")
        for i, doc in enumerate(essb_docs, 1):
            supabase.table("knowledge_documents").update(
                {"effective_date": "2025-10-01"}
            ).eq("id", doc["id"]).execute()

            if i % 10 == 0 or i == len(essb_docs):
                print(f"  Updated {i}/{len(essb_docs)}...")

    # Update old law documents
    if old_law_docs:
        print(f"\nSetting {len(old_law_docs)} old law documents to 2024-01-01...")

        # Batch update for efficiency
        batch_size = 100
        for i in range(0, len(old_law_docs), batch_size):
            batch = old_law_docs[i : i + batch_size]
            batch_ids = [doc["id"] for doc in batch]

            # Update batch
            supabase.table("knowledge_documents").update(
                {"effective_date": "2024-01-01"}
            ).in_("id", batch_ids).execute()

            print(
                f"  Updated {min(i+batch_size, len(old_law_docs))}/{len(old_law_docs)}..."
            )

    print()
    print("=" * 80)
    print("✅ Effective dates set successfully!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - ESSB 5814 documents: {len(essb_docs)} → 2025-10-01")
    print(f"  - Old law documents: {len(old_law_docs)} → 2024-01-01")
    print()
    print("Now the Old Law vs New Law comparison will work properly!")
    print()

    # Verify
    print("Step 3: Verification...")
    total = supabase.table("knowledge_documents").select("id", count="exact").execute()
    with_date = (
        supabase.table("knowledge_documents")
        .select("id", count="exact")
        .not_.is_("effective_date", "null")
        .execute()
    )
    without_date = (
        supabase.table("knowledge_documents")
        .select("id", count="exact")
        .is_("effective_date", "null")
        .execute()
    )

    print(f"  Total documents: {total.count}")
    print(f"  With effective_date: {with_date.count}")
    print(f"  Without effective_date: {without_date.count}")

    if without_date.count == 0:
        print("\n✅ Perfect! All documents now have effective_date set.")
    else:
        print(
            f"\n⚠️  Warning: {without_date.count} documents still don't have effective_date"
        )


if __name__ == "__main__":
    set_default_effective_dates()
