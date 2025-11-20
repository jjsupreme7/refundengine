#!/bin/bash

# Fix search_tax_law function overloading issue
# This script drops the old 4-parameter version and ensures only the 6-parameter version exists

set -e

echo "=========================================="
echo "Fixing search_tax_law function overload"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if required variables are set
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "❌ Error: SUPABASE_DB_PASSWORD not set"
    exit 1
fi

# Database connection details
DB_HOST="aws-0-us-west-1.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.mpubuoobxctdmswpafzl"
DB_NAME="postgres"

echo ""
echo "📋 Checking current function definitions..."
PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\df search_tax_law"

echo ""
echo "🔧 Applying migration..."
PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/migrations/fix_search_tax_law_overload.sql

echo ""
echo "✅ Verifying fix..."
PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\df search_tax_law"

echo ""
echo "=========================================="
echo "✅ Migration complete!"
echo "=========================================="
