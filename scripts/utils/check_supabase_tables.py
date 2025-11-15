#!/usr/bin/env python3
"""Check what tables exist in Supabase - both current and deprecated"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# Import centralized Supabase client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.database import get_supabase_client
supabase = get_supabase_client()

def check_table(table_name):
    """Check if a table exists and return row count"""
    try:
        result = supabase.table(table_name).select("*", count="exact").limit(0).execute()
        count = result.count if hasattr(result, "count") else "?"
        return True, count
    except Exception as e:
        return False, 0

print("\n" + "=" * 80)
print("SUPABASE TABLES CHECK")
print("=" * 80 + "\n")

# Current schema tables (should exist and have data)
print("📊 CURRENT SCHEMA (Active - Use These)")
print("-" * 80)
current_tables = [
    ("knowledge_documents", "Master document registry"),
    ("tax_law_chunks", "Tax law chunks with embeddings"),
    ("vendor_background_chunks", "Vendor document chunks"),
]

for table, description in current_tables:
    exists, count = check_table(table)
    status = "✅" if exists and count > 0 else "⚠️ " if exists else "❌"
    rows_text = f"{count:,} rows" if exists else "N/A"
    print(f"{status} {table:30} {rows_text:>15}  | {description}")

# Old schema tables (deprecated, may still exist during transition)
print("\n🗃️  OLD SCHEMA (Deprecated - Archived)")
print("-" * 80)
old_tables = [
    ("legal_documents", "Old document table (replaced by knowledge_documents)"),
    ("document_chunks", "Old chunks table (replaced by tax_law_chunks)"),
    ("legal_rules", "Old rules table (if it exists)"),
]

for table, description in old_tables:
    exists, count = check_table(table)
    if exists:
        status = "⚠️  DEPRECATED" if count > 0 else "📦 EMPTY"
        rows_text = f"{count:,} rows" if count > 0 else "0 rows"
        print(f"{status} {table:30} {rows_text:>15}  | {description}")
    else:
        print(f"✅ REMOVED    {table:30} {'N/A':>15}  | {description}")

# Other tables (client data, vendor learning, etc.)
print("\n📂 OTHER TABLES (Special Purpose)")
print("-" * 80)
other_tables = [
    ("client_documents", "Client invoice/PO documents"),
    ("vendor_products", "Vendor learning - product catalog"),
    ("vendor_product_patterns", "Vendor learning - pattern matching"),
    ("analysis_results", "Refund analysis results"),
    ("analysis_reviews", "Human review corrections"),
]

for table, description in other_tables:
    exists, count = check_table(table)
    if exists:
        status = "✅"
        rows_text = f"{count:,} rows" if count else "0 rows"
        print(f"{status} {table:30} {rows_text:>15}  | {description}")

print("\n" + "=" * 80)
print("\n💡 TIP: Current schema tables should have data.")
print("   Old schema tables should be empty (data migrated to new schema).")
print("   See database/README.md for schema documentation.\n")
