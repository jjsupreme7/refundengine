#!/usr/bin/env python3
"""
Clean Database Script
Clears old data from Supabase to start fresh
"""

import os
import sys
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed, using system environment variables")

# Import centralized Supabase client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.database import get_supabase_client

supabase = get_supabase_client()


def clean_table(table_name):
    """Delete all records from a table"""
    try:
        # Get count first
        result = supabase.table(table_name).select("id", count="exact").execute()
        count = result.count if hasattr(result, "count") else 0

        if count == 0:
            print(f"  ✓ {table_name}: Already empty")
            return

        # Delete all records
        supabase.table(table_name).delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()
        print(f"  ✓ {table_name}: Deleted {count} records")
    except Exception as e:
        print(f"  ✗ {table_name}: {e}")


def main():
    print("\n" + "=" * 80)
    print("CLEANING SUPABASE DATABASE")
    print("=" * 80)
    print("\nThis will delete ALL data from the following tables:")
    print("  - legal_documents, legal_chunks (old schema)")
    print(
        "  - knowledge_documents, tax_law_chunks, vendor_background_chunks (new schema)"
    )
    print("  - analysis_results, analysis_reviews (analysis data)")
    print("  - vendor_products, vendor_product_patterns (learning data)")
    print("  - audit_trail (audit logs)")

    response = input("\nAre you sure you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Aborted.")
        return

    print("\nCleaning tables...\n")

    # Old schema tables (if they exist)
    clean_table("legal_chunks")
    clean_table("legal_documents")
    clean_table("legal_rules")

    # New schema tables
    clean_table("tax_law_chunks")
    clean_table("vendor_background_chunks")
    clean_table("knowledge_documents")

    # Analysis tables
    clean_table("analysis_reviews")
    clean_table("analysis_results")

    # Learning tables
    clean_table("vendor_product_patterns")
    clean_table("vendor_products")

    # Audit
    clean_table("audit_trail")

    print("\n" + "=" * 80)
    print("✓ Database cleaned successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
