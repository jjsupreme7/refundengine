#!/usr/bin/env python3
"""
Deploy Updated RPC Functions with file_url Support

This script deploys the updated search_tax_law and search_knowledge_base
functions that now return file_url from the knowledge_documents table.

Usage:
    python scripts/deploy_url_rpc_updates.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.database import get_supabase_client

# Load environment variables
load_dotenv()

# SQL for updated RPC functions
UPDATE_RPC_SQL = """
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
"""


def main():
    print("=" * 70)
    print("Deploying Updated RPC Functions")
    print("=" * 70)

    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: Missing required environment variables")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        return 1

    print(f"📡 Connecting to Supabase...")

    try:
        # Initialize Supabase client
        supabase = get_supabase_client()

        print("🚀 Deploying updated RPC functions...\n")

        # Execute SQL using Supabase RPC
        # Note: Supabase Python client doesn't directly support raw SQL execution
        # We need to use the PostgREST API or a direct database connection

        # For now, let's provide instructions for manual deployment
        print("⚠️  Note: The Supabase Python client does not support direct SQL execution.")
        print("   You have two options to deploy these changes:\n")

        print("Option 1: Use Supabase Dashboard")
        print("-" * 70)
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to 'SQL Editor'")
        print("4. Copy the SQL from: database/schema/schema_knowledge_base.sql")
        print("   (lines 123-263 - the updated search functions)")
        print("5. Paste and run the SQL\n")

        print("Option 2: Use psql command-line tool")
        print("-" * 70)
        print("1. Install PostgreSQL client: brew install postgresql")
        print("2. Run: ./scripts/deploy_url_rpc_updates.sh\n")

        print("Option 3: Manual SQL File")
        print("-" * 70)

        # Save SQL to a file
        sql_file = Path("database/migrations/add_file_url_to_rpc.sql")
        sql_file.parent.mkdir(parents=True, exist_ok=True)

        with open(sql_file, "w") as f:
            f.write(UPDATE_RPC_SQL)

        print(f"✅ SQL saved to: {sql_file}")
        print("   Run this file in your Supabase SQL Editor\n")

        print("=" * 70)
        print("📋 After deploying the RPC functions, run:")
        print("   python scripts/populate_file_urls.py")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
