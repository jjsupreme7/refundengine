#!/usr/bin/env python3
"""
Deploy source_file update to search_tax_law RPC function
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize Supabase
supabase = get_supabase_client()

print("=" * 80)
print("Deploying source_file update to search_tax_law RPC function")
print("=" * 80)
print()

# Read the SQL migration file
migration_file = Path(__file__).parent.parent / "database/migrations/add_source_file_to_search_tax_law.sql"

with open(migration_file, 'r') as f:
    sql = f.read()

print(f"📊 Applying migration: {migration_file.name}")
print()

try:
    # Execute the SQL
    supabase.rpc('query', {'query_text': sql}).execute()

    print("=" * 80)
    print("✅ Migration applied successfully!")
    print("=" * 80)
    print()
    print("The search_tax_law() function now returns:")
    print("  - file_url (online URL, if available)")
    print("  - source_file (local file path)")
    print()
    print("Next steps:")
    print("1. Restart your Streamlit app")
    print("2. All sources should now have clickable links!")
    print()

except Exception as e:
    print(f"❌ Error applying migration: {e}")
    print()
    print("Please apply the migration manually via Supabase SQL Editor:")
    print(f"  {migration_file}")
    sys.exit(1)
