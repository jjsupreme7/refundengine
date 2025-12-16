#!/usr/bin/env python3
"""
Backfill chunk_role for existing tax_law_chunks.

This script updates the chunk_role field for all existing chunks
without regenerating embeddings (saving API costs).

Usage:
    python scripts/backfill_chunk_roles.py --dry-run    # Preview only
    python scripts/backfill_chunk_roles.py              # Run backfill
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client
from core.chunking import classify_chunk_role
from tqdm import tqdm


def backfill_chunk_roles(dry_run: bool = False, batch_size: int = 100):
    """Backfill chunk_role for all existing chunks."""
    supabase = get_supabase_client()

    # Get total count
    count_result = supabase.table("tax_law_chunks").select("id", count="exact").execute()
    total_chunks = count_result.count
    print(f"Total chunks to process: {total_chunks}")

    if dry_run:
        # Just sample a few to show what would happen
        sample = supabase.table("tax_law_chunks").select("id, chunk_text").limit(10).execute()
        print("\nDRY RUN - Sample classifications:")
        for chunk in sample.data:
            role = classify_chunk_role(chunk["chunk_text"])
            preview = chunk["chunk_text"][:60].replace("\n", " ")
            print(f"  {role:12} | {preview}...")
        return

    # Process in batches
    stats = {"definition": 0, "rule": 0, "example": 0, "exception": 0, "procedure": 0}
    offset = 0

    with tqdm(total=total_chunks, desc="Backfilling chunk_role") as pbar:
        while offset < total_chunks:
            # Fetch batch
            batch = (
                supabase.table("tax_law_chunks")
                .select("id, chunk_text")
                .range(offset, offset + batch_size - 1)
                .execute()
            )

            if not batch.data:
                break

            # Classify and update each chunk
            for chunk in batch.data:
                role = classify_chunk_role(chunk["chunk_text"])
                stats[role] += 1

                # Update the chunk
                supabase.table("tax_law_chunks").update({"chunk_role": role}).eq(
                    "id", chunk["id"]
                ).execute()

            pbar.update(len(batch.data))
            offset += batch_size

    # Print stats
    print("\n" + "=" * 50)
    print("Backfill Complete!")
    print("=" * 50)
    print(f"Total chunks updated: {sum(stats.values())}")
    print("\nRole distribution:")
    for role, count in sorted(stats.items(), key=lambda x: -x[1]):
        pct = count / sum(stats.values()) * 100
        print(f"  {role:12}: {count:5} ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Backfill chunk_role for existing chunks")
    parser.add_argument("--dry-run", action="store_true", help="Preview without updating")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    args = parser.parse_args()

    backfill_chunk_roles(dry_run=args.dry_run, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
