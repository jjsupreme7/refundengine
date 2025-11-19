#!/usr/bin/env python3
"""
Deploy Excel Versioning Schema using Python

Alternative to bash script - uses Python Supabase client instead of psql
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

print("🚀 Deploying Excel Versioning System - Phase 1")
print("=" * 70)
print()

# Get Supabase client
try:
    supabase = get_supabase_client()
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    sys.exit(1)

# Read SQL file
sql_file = (
    Path(__file__).parent.parent
    / "database"
    / "schema"
    / "migration_excel_versioning.sql"
)

if not sql_file.exists():
    print(f"❌ SQL file not found: {sql_file}")
    sys.exit(1)

print(f"📄 Reading SQL from: {sql_file}")

with open(sql_file, "r") as f:
    sql_content = f.read()

# Split SQL into individual statements
# Skip comments and empty lines
statements = []
current_statement = []

for line in sql_content.split("\n"):
    # Skip comment lines
    if line.strip().startswith("--"):
        continue

    # Skip empty lines
    if not line.strip():
        continue

    current_statement.append(line)

    # If line ends with semicolon, it's end of statement
    if line.strip().endswith(";"):
        statement = "\n".join(current_statement)
        statements.append(statement)
        current_statement = []

print(f"📊 Found {len(statements)} SQL statements to execute")
print()

# Execute statements one by one
success_count = 0
error_count = 0

for i, statement in enumerate(statements, 1):
    # Show what we're executing
    first_line = statement.strip().split("\n")[0][:60]
    print(f"[{i}/{len(statements)}] Executing: {first_line}...")

    try:
        # Execute using Supabase RPC
        # Note: This may not work for all SQL statements
        # We'll need to use psycopg2 for full support

        # For now, just show that we would execute it
        print(f"    ⚠️  Skipping (requires direct database access)")

    except Exception as e:
        print(f"    ❌ Error: {e}")
        error_count += 1

print()
print("=" * 70)
print(f"✅ Completed: {success_count} statements")
if error_count > 0:
    print(f"⚠️  Errors: {error_count} statements failed")
print()

print("⚠️  Note: This script requires direct database access (psql or psycopg2)")
print("Please use one of these methods instead:")
print()
print("1. Install psql and run:")
print("   ./scripts/deploy_excel_versioning.sh")
print()
print("2. Install psycopg2 and run:")
print("   pip install psycopg2-binary")
print("   python scripts/deploy_excel_schema_direct.py")
print()
print("3. Manually run SQL in Supabase SQL Editor:")
print(f"   - Open: https://supabase.com/dashboard/project/YOUR_PROJECT/sql")
print(f"   - Copy/paste: {sql_file}")
print()
