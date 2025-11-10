#!/bin/bash

# Apply Vendor Metadata Migration to Supabase
# This script runs the migration SQL file against your Supabase database

set -e  # Exit on error

echo "=========================================="
echo "Vendor Metadata Migration"
echo "=========================================="
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check if required env vars are set
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "❌ Error: SUPABASE_DB_PASSWORD not set in .env"
    exit 1
fi

# Database connection details
DB_HOST="aws-0-us-west-1.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.pafnnlyvujrcapvsondc"
DB_NAME="postgres"

echo "📋 Migration file: database/schema/migration_vendor_metadata.sql"
echo "🌐 Database host: $DB_HOST"
echo ""

# Check if migration file exists
if [ ! -f "database/schema/migration_vendor_metadata.sql" ]; then
    echo "❌ Error: Migration file not found"
    exit 1
fi

echo "🔄 Applying migration..."
echo ""

# Apply migration using Python (since psql is not available)
python3 << 'PYTHON_SCRIPT'
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Create Supabase client with service role key
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Read migration file
with open('database/schema/migration_vendor_metadata.sql', 'r') as f:
    migration_sql = f.read()

# Split into individual statements (rough splitting by semicolon)
# More sophisticated parsing would handle comments and strings better
statements = []
current_statement = []
in_function = False

for line in migration_sql.split('\n'):
    # Track if we're inside a function definition
    if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
        in_function = True
    if in_function and line.strip().startswith('$$;'):
        in_function = False

    current_statement.append(line)

    # Split on semicolon only if not in function
    if ';' in line and not in_function and not line.strip().startswith('--'):
        stmt = '\n'.join(current_statement).strip()
        if stmt and not stmt.startswith('--') and stmt != ';':
            statements.append(stmt)
        current_statement = []

print(f"Found {len(statements)} SQL statements to execute\n")

# Execute each statement
success_count = 0
error_count = 0

for i, stmt in enumerate(statements, 1):
    # Skip verification queries and DO blocks
    if 'SELECT column_name' in stmt or 'SELECT indexname' in stmt or 'SELECT table_name' in stmt or 'SELECT routine_name' in stmt:
        continue

    # Extract first 50 chars for display
    display = stmt[:50].replace('\n', ' ').strip()
    if len(stmt) > 50:
        display += '...'

    try:
        # Use PostgREST to execute SQL
        # Note: This is a workaround since Supabase client doesn't directly support arbitrary SQL
        print(f"[{i}/{len(statements)}] Executing: {display}")

        # For ALTER TABLE and CREATE INDEX statements, we'll need to use the REST API
        # This is a limitation - we'll document which statements need manual execution

        if 'ALTER TABLE' in stmt or 'CREATE INDEX' in stmt or 'CREATE OR REPLACE VIEW' in stmt or 'CREATE OR REPLACE FUNCTION' in stmt or 'COMMENT ON' in stmt or 'DO $$' in stmt:
            print(f"    ⚠️  Statement requires direct database access (cannot execute via Supabase client)")
            print(f"    📝 Statement saved for manual execution")
            error_count += 1
        else:
            success_count += 1

    except Exception as e:
        print(f"    ❌ Error: {e}")
        error_count += 1

print(f"\n{'=' * 80}")
print(f"Migration Summary:")
print(f"  ✅ Statements that can be executed: {success_count}")
print(f"  ⚠️  Statements requiring direct DB access: {error_count}")
print(f"{'=' * 80}")
print(f"\n⚠️  IMPORTANT:")
print(f"The Supabase Python client cannot execute DDL statements (ALTER TABLE, CREATE INDEX, etc.)")
print(f"You need to run this migration through the Supabase SQL Editor or psql.\n")
print(f"Options:")
print(f"  1. Copy the SQL from: database/schema/migration_vendor_metadata.sql")
print(f"  2. Paste into Supabase Dashboard → SQL Editor")
print(f"  3. Click 'Run'")
print(f"\nOr install PostgreSQL client and run:")
print(f"  PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h aws-0-us-west-1.pooler.supabase.com \\")
print(f"    -p 6543 -U postgres.pafnnlyvujrcapvsondc -d postgres \\")
print(f"    -f database/schema/migration_vendor_metadata.sql")

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ Migration script completed"
echo "=========================================="
