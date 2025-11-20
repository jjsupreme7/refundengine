#!/bin/bash
# Deploy source_file update to search_tax_law function

set -e

echo "============================================================================"
echo "Deploying source_file update to search_tax_law RPC function"
echo "============================================================================"
echo ""

# Database connection details from environment
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "❌ Error: SUPABASE_DB_PASSWORD not set"
    echo "Please set it with: export SUPABASE_DB_PASSWORD='your-password'"
    exit 1
fi

DB_HOST="aws-0-us-west-1.pooler.supabase.com"
DB_PORT="6543"
DB_NAME="postgres"
DB_USER="postgres.mvirvthkxaxdqykdwwdt"

echo "📊 Applying migration: add_source_file_to_search_tax_law.sql"
echo ""

PGPASSWORD="$SUPABASE_DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f database/migrations/add_source_file_to_search_tax_law.sql

echo ""
echo "============================================================================"
echo "✅ Migration applied successfully!"
echo "============================================================================"
echo ""
echo "The search_tax_law() function now returns:"
echo "  - file_url (online URL, if available)"
echo "  - source_file (local file path)"
echo ""
echo "Next steps:"
echo "1. Restart your Streamlit app"
echo "2. All sources should now have clickable links!"
echo ""
