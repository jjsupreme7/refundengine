#!/usr/bin/env python3
"""
Fix search_tax_law function overloading issue by dropping old version
"""

from core.database import get_supabase_client
from pathlib import Path

# Load environment
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


supabase = get_supabase_client()

print("\n" + "=" * 80)
print("Fixing search_tax_law function overloading issue")
print("=" * 80)

# Read the migration SQL file
migration_path = (
    Path(__file__).parent / "database/migrations/fix_search_tax_law_overload.sql"
)

with open(migration_path, "r") as f:
    sql = f.read()

print("\n📋 SQL Migration to apply:")
print("-" * 80)
print(sql[:500] + "...")
print("-" * 80)

try:
    print("\n🔧 Applying migration via Supabase SQL editor...")
    print("\n⚠️  Note: Direct SQL execution via Supabase client doesn't support DDL.")
    print("You'll need to run this SQL manually in the Supabase SQL Editor:")
    print("\n1. Go to: https://supabase.com/dashboard/project/mpubuoobxctdmswpafzl/sql")
    print(
        "2. Copy and paste the SQL from: database/migrations/fix_search_tax_law_overload.sql"  # noqa: E501
    )
    print("3. Click 'Run' to apply the migration")

    print("\n" + "=" * 80)
    print("SQL to run:")
    print("=" * 80)
    print(sql)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
