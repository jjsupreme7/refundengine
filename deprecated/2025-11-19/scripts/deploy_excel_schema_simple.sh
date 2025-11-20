#!/bin/bash
# Simple Excel Versioning Schema Deployment
# Uses correct Supabase connection parameters

set -e

echo "🚀 Deploying Excel Versioning Schema"
echo "======================================================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check password is set
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "❌ Error: SUPABASE_DB_PASSWORD not set"
    echo ""
    echo "Please set it:"
    echo "  export SUPABASE_DB_PASSWORD='your-password-here'"
    echo ""
    echo "Or add it to your .env file"
    exit 1
fi

# Database connection details
# Your Supabase project: yzycrptfkxszeutvhuhm
DB_HOST="aws-0-us-west-1.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.yzycrptfkxszeutvhuhm"
DB_NAME="postgres"

echo "📡 Connection Details:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "❌ psql not found"
    echo ""
    echo "Please install PostgreSQL client:"
    echo "  macOS: brew install postgresql@15"
    echo "  Linux: sudo apt-get install postgresql-client"
    echo ""
    echo "OR use the manual method (copy/paste SQL to Supabase Dashboard)"
    exit 1
fi

echo "✅ psql found"
echo ""

# Deploy schema
echo "📊 Deploying schema..."
echo ""

export PGPASSWORD="$SUPABASE_DB_PASSWORD"

psql -h "$DB_HOST" \
     -p "$DB_PORT" \
     -U "$DB_USER" \
     -d "$DB_NAME" \
     -f database/schema/migration_excel_versioning.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo "======================================================================"
    echo ""
    echo "Tables created:"
    echo "  • excel_file_versions"
    echo "  • excel_cell_changes"
    echo ""
    echo "Next steps:"
    echo "  1. Set up storage buckets: python3 scripts/setup_excel_storage.py"
    echo "  2. Test the system: python3 scripts/test_excel_versioning.py"
    echo "  3. Start dashboard: streamlit run dashboard/Dashboard.py --server.port 5001"
    echo ""
else
    echo ""
    echo "❌ Deployment failed"
    echo ""
    echo "Try the manual method instead:"
    echo "  1. cat database/schema/migration_excel_versioning.sql"
    echo "  2. Copy the output"
    echo "  3. Go to: https://supabase.com/dashboard → SQL Editor"
    echo "  4. Paste and run"
    echo ""
fi
