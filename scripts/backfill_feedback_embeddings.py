#!/usr/bin/env python3
"""
One-time script to backfill embeddings for existing corrections.
Run after applying the migration: database/migrations/add_feedback_embedding.sql
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from core.database import get_supabase_client

def main():
    client = OpenAI()
    supabase = get_supabase_client()

    # Fetch corrections without embeddings
    print("Fetching corrections without embeddings...")
    result = supabase.table("user_feedback") \
        .select("id, query") \
        .eq("feedback_type", "correction") \
        .is_("query_embedding", "null") \
        .execute()

    if not result.data:
        print("No corrections to backfill.")
        return

    print(f"Found {len(result.data)} corrections to backfill")

    updated = 0
    for row in result.data:
        if not row.get("query"):
            continue

        try:
            # Generate embedding
            response = client.embeddings.create(
                input=row["query"][:8000],
                model="text-embedding-3-small"
            )

            # Update record
            supabase.table("user_feedback") \
                .update({"query_embedding": response.data[0].embedding}) \
                .eq("id", row["id"]) \
                .execute()

            updated += 1
            print(f"  Updated {row['id'][:8]}...")

        except Exception as e:
            print(f"  Error updating {row['id']}: {e}")

    print(f"\nBackfill complete! Updated {updated} corrections.")

if __name__ == "__main__":
    main()
