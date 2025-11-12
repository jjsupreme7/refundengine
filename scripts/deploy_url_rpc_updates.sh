#!/bin/bash
#
# Deploy Updated RPC Functions with file_url Support
#
# This script deploys only the updated search_tax_law and search_knowledge_base
# functions that now return file_url from the knowledge_documents table.
#
# Usage:
#   ./scripts/deploy_url_rpc_updates.sh
#

set -e  # Exit on error

echo "=========================================="
echo "Deploying Updated RPC Functions"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check required environment variables
if [ -z "$SUPABASE_DB_PASSWORD" ] || [ -z "$SUPABASE_URL" ]; then
    echo "❌ Error: Missing required environment variables"
    echo "   Required: SUPABASE_DB_PASSWORD, SUPABASE_URL"
    exit 1
fi

# Extract host from SUPABASE_URL
DB_HOST=$(echo $SUPABASE_URL | sed -E 's|https://([^.]+)\.supabase\.co.*|\1.db.supabase.co|')
DB_NAME="postgres"
DB_USER="postgres"
DB_PORT="5432"

echo "📡 Connecting to: $DB_HOST"
echo ""

# Create temporary SQL file with just the RPC function updates
cat > /tmp/rpc_update.sql << 'EOF'
-- ============================================================================
-- Updated RPC Functions with file_url Support
-- ============================================================================

-- Function: Search tax law knowledge base (with file_url)
CREATE OR REPLACE FUNCTION search_tax_law(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5,
    law_category_filter text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    section_title text,
    law_category text,
    file_url text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tc.id,
        tc.document_id,
        tc.chunk_text,
        tc.citation,
        tc.section_title,
        tc.law_category,
        kd.file_url,
        1 - (tc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tc
    LEFT JOIN knowledge_documents kd ON tc.document_id = kd.id
    WHERE tc.embedding IS NOT NULL
        AND 1 - (tc.embedding <=> query_embedding) > match_threshold
        AND (law_category_filter IS NULL OR tc.law_category = law_category_filter)
    ORDER BY tc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Combined search (with file_url)
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    vendor_name_filter text DEFAULT NULL,
    include_tax_law boolean DEFAULT true,
    include_vendor_bg boolean DEFAULT true,
    match_threshold float DEFAULT 0.5,
    tax_law_count int DEFAULT 5,
    vendor_bg_count int DEFAULT 3
)
RETURNS TABLE (
    source_type text,
    id uuid,
    chunk_text text,
    citation text,
    vendor_name text,
    file_url text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY

    -- Tax law results
    SELECT
        'tax_law'::text as source_type,
        tc.id,
        tc.chunk_text,
        tc.citation,
        NULL::text as vendor_name,
        kd_tax.file_url,
        1 - (tc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tc
    LEFT JOIN knowledge_documents kd_tax ON tc.document_id = kd_tax.id
    WHERE include_tax_law
        AND tc.embedding IS NOT NULL
        AND 1 - (tc.embedding <=> query_embedding) > match_threshold
    ORDER BY tc.embedding <=> query_embedding
    LIMIT tax_law_count

    UNION ALL

    -- Vendor background results
    SELECT
        'vendor_background'::text as source_type,
        vc.id,
        vc.chunk_text,
        NULL::text as citation,
        vc.vendor_name,
        kd_vendor.file_url,
        1 - (vc.embedding <=> query_embedding) as similarity
    FROM vendor_background_chunks vc
    LEFT JOIN knowledge_documents kd_vendor ON vc.document_id = kd_vendor.id
    WHERE include_vendor_bg
        AND vc.embedding IS NOT NULL
        AND 1 - (vc.embedding <=> query_embedding) > match_threshold
        AND (vendor_name_filter IS NULL OR vc.vendor_name = vendor_name_filter)
    ORDER BY vc.embedding <=> query_embedding
    LIMIT vendor_bg_count;
END;
$$;

EOF

echo "🚀 Deploying updated RPC functions..."
echo ""

# Deploy the SQL
PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /tmp/rpc_update.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ RPC Functions Updated Successfully!"
    echo "=========================================="
    echo ""
    echo "Updated functions:"
    echo "  • search_tax_law() - now returns file_url"
    echo "  • search_knowledge_base() - now returns file_url"
    echo ""
    echo "Next steps:"
    echo "  1. Run: python scripts/populate_file_urls.py"
    echo "  2. Test with: python chatbot/web_chat.py"
    echo ""
else
    echo ""
    echo "❌ Deployment failed"
    exit 1
fi

# Cleanup
rm /tmp/rpc_update.sql
