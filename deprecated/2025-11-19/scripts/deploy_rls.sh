#!/bin/bash

# Deploy Row Level Security (RLS) Migration
# CRITICAL SECURITY UPDATE

# Supabase connection details
DB_HOST="db.yzycrptfkxszeutvhuhm.supabase.co"
DB_PORT="5432"
DB_USER="postgres"
DB_NAME="postgres"

# Get password from environment variable
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "❌ Error: SUPABASE_DB_PASSWORD environment variable not set"
    echo "Please run: export SUPABASE_DB_PASSWORD='your-password'"
    exit 1
fi

MIGRATION_FILE="database/migrations/add_row_level_security.sql"

echo "========================================================================"
echo "DEPLOYING ROW LEVEL SECURITY (RLS) - CRITICAL SECURITY UPDATE"
echo "========================================================================"
echo "Migration file: $MIGRATION_FILE"
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "⚠️  WARNING: This will enable RLS on ALL tables"
echo "   Ensure your application uses proper authentication tokens!"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Migration file not found: $MIGRATION_FILE"
    exit 1
fi

# Deploy using psql
echo ""
echo "🔄 Deploying RLS migration..."
echo ""

export PGPASSWORD="$SUPABASE_DB_PASSWORD"

psql -h "$DB_HOST" \
     -p "$DB_PORT" \
     -U "$DB_USER" \
     -d "$DB_NAME" \
     -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ RLS DEPLOYMENT SUCCESSFUL"
    echo "========================================================================"
    echo ""
    echo "Security improvements applied:"
    echo "  ✓ Row Level Security enabled on all tables"
    echo "  ✓ Authentication tables created"
    echo "  ✓ Access policies configured"
    echo "  ✓ Audit logging enabled"
    echo ""
    echo "⚠️  NEXT STEPS (CRITICAL):"
    echo "  1. Switch from SERVICE_ROLE_KEY to user-based auth"
    echo "  2. Update core/database.py to use anon key + Supabase Auth"
    echo "  3. Test access with non-admin user"
    echo "  4. Verify RLS policies are working correctly"
    echo ""
else
    echo ""
    echo "❌ Deployment failed"
    exit 1
fi
