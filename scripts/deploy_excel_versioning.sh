#!/bin/bash
# ============================================================================
# Deploy Excel Versioning System - Phase 1
# ============================================================================
# This script deploys the database schema and sets up Supabase Storage

set -e  # Exit on error

echo "🚀 Deploying Excel Versioning System - Phase 1"
echo "============================================================================"
echo ""

# Check environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] || [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "❌ Error: Required environment variables not set"
    echo ""
    echo "Please set:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_ROLE_KEY"
    echo "  - SUPABASE_DB_PASSWORD"
    echo ""
    exit 1
fi

# Extract database connection details from SUPABASE_URL
DB_HOST=$(echo $SUPABASE_URL | sed 's|https://||' | sed 's|\.supabase\.co.*|.supabase.co|')
DB_NAME="postgres"
DB_USER="postgres"
DB_PORT="5432"

echo "📊 Step 1: Deploying database schema..."
echo "----------------------------------------"

# Deploy schema
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
    -h "db.${DB_HOST#https://}" \
    -U $DB_USER \
    -d $DB_NAME \
    -p $DB_PORT \
    -f database/schema/migration_excel_versioning.sql

echo ""
echo "✅ Database schema deployed successfully"
echo ""

echo "📁 Step 2: Setting up Supabase Storage buckets..."
echo "----------------------------------------"

python3 scripts/setup_excel_storage.py

echo ""
echo "✅ Storage buckets created successfully"
echo ""

echo "🔒 Step 3: Deploying Row Level Security policies..."
echo "----------------------------------------"

# Deploy RLS policies
cat << 'EOF' | PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
    -h "db.${DB_HOST#https://}" \
    -U $DB_USER \
    -d $DB_NAME \
    -p $DB_PORT

-- Enable RLS on new tables
ALTER TABLE excel_file_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_cell_changes ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their project files
CREATE POLICY IF NOT EXISTS "Users can view project files"
ON excel_file_tracking FOR SELECT
TO authenticated
USING (true);  -- Adjust based on your user/project relationship

-- Policy: Users can view version history
CREATE POLICY IF NOT EXISTS "Users can view version history"
ON excel_file_versions FOR SELECT
TO authenticated
USING (true);

-- Policy: Users can view change history
CREATE POLICY IF NOT EXISTS "Users can view change history"
ON excel_cell_changes FOR SELECT
TO authenticated
USING (true);

-- Service role can do everything
CREATE POLICY IF NOT EXISTS "Service role full access files"
ON excel_file_tracking FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Service role full access versions"
ON excel_file_versions FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Service role full access changes"
ON excel_cell_changes FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

EOF

echo ""
echo "✅ RLS policies deployed successfully"
echo ""

echo "============================================================================"
echo "✅ Phase 1 Deployment Complete!"
echo "============================================================================"
echo ""
echo "📋 Summary:"
echo "  ✓ Database schema created"
echo "  ✓ Storage buckets configured"
echo "  ✓ RLS policies applied"
echo ""
echo "📁 Database Tables:"
echo "  - excel_file_tracking (extended with versioning)"
echo "  - excel_file_versions"
echo "  - excel_cell_changes"
echo ""
echo "📦 Storage Buckets:"
echo "  - excel-files (current versions)"
echo "  - excel-versions (version history)"
echo "  - excel-exports (exports and reports)"
echo ""
echo "🔧 Functions Available:"
echo "  - acquire_file_lock(file_id, user_email)"
echo "  - release_file_lock(file_id, user_email)"
echo "  - create_file_version(...)"
echo ""
echo "📊 Views Available:"
echo "  - v_excel_file_locks"
echo "  - v_file_version_history"
echo "  - v_recent_activity"
echo ""
echo "🎯 Next Steps:"
echo "  1. Test upload: python scripts/test_excel_versioning.py"
echo "  2. Build Excel Editor page (Phase 3)"
echo "  3. Integrate with dashboard"
echo ""
