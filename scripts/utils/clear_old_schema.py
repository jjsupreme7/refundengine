#!/usr/bin/env python3
"""
Clear OLD/DEPRECATED schema tables

⚠️  WARNING: This script clears data from DEPRECATED tables only!
- legal_documents (old table, replaced by knowledge_documents)
- document_chunks (old table, replaced by tax_law_chunks)

The current schema uses:
- knowledge_documents
- tax_law_chunks
- vendor_background_chunks

This script is useful for:
1. Cleaning up residual data in old tables during migration
2. Verifying old tables are empty before dropping them
3. Testing migration scenarios

See: database/archive/old_schema/README.md for more information
"""

from core.database import get_supabase_client
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

supabase = get_supabase_client()


def check_and_clear_table(table_name, description):
    """Check table and optionally clear it"""
    try:
        result = (
            supabase.table(table_name).select("id", count="exact").limit(0).execute()
        )
        count = result.count

        status = "⚠️  HAS DATA" if count > 0 else "✅ EMPTY"
        print(f"\n{status} {table_name}: {count:,} rows")
        print(f"       ({description})")

        return count
    except Exception as e:
        print(f"\n❌ {table_name}: Table does not exist or error")
        print(f"       Error: {e}")
        return None


print("\n" + "=" * 80)
print("🗃️  OLD SCHEMA DATA CHECK")
print("=" * 80)
print("\nThis script checks DEPRECATED tables from the old schema.")
print("Current active schema uses: knowledge_documents, tax_law_chunks")
print("")

# Check old tables
old_tables = [
    ("document_chunks", "Old chunks table - replaced by tax_law_chunks"),
    ("legal_documents", "Old documents table - replaced by knowledge_documents"),
]

total_rows = 0
tables_with_data = []

for table_name, description in old_tables:
    count = check_and_clear_table(table_name, description)
    if count:
        total_rows += count
        tables_with_data.append((table_name, count))

print("\n" + "=" * 80)

if total_rows == 0:
    print("\n✅ SUCCESS: All old schema tables are empty!")
    print("   Old tables contain no data. Safe to drop if desired.")
    print("   See: database/drop_unused_tables.sql")
else:
    print(f"\n⚠️  FOUND {total_rows:,} rows in old schema tables")
    print("\n📋 Tables with data:")
    for table_name, count in tables_with_data:
        print(f"   - {table_name}: {count:,} rows")

    print("\n⚠️  WARNING: The old tables should be empty after migration!")
    print("   Current schema uses knowledge_documents and tax_law_chunks.")
    print("   If old tables have data, it may be residual from before migration.")

    # Safety check - don't auto-delete
    print("\n❌ Auto-deletion disabled for safety.")
    print("   If you need to clear this data:")
    print("   1. Verify migration is complete (check knowledge_documents has data)")
    print(
        "   2. Manually run SQL: DELETE FROM document_chunks; DELETE FROM legal_documents;"
    )
    print("   3. Or use Supabase dashboard")

print("\n" + "=" * 80 + "\n")
