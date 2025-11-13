-- ============================================================================
-- Migration 002: Compatibility Layer (FIXED)
-- Created: 2025-11-12
-- Purpose: Bridge OLD schema → NEW schema during migration period
-- ============================================================================
--
-- This is a FIXED version that works with the SIMPLE schema
-- (without hierarchy_level, parent_section, keywords columns)
--
-- IMPORTANT: Run this version instead of the original migration_002
-- ============================================================================

-- ============================================================================
-- STEP 1: Create compatibility VIEW for legal_chunks
-- ============================================================================
-- Allows old code using "SELECT * FROM legal_chunks" to work
-- Points to new tax_law_chunks table
-- Only includes columns that actually exist in your database

CREATE OR REPLACE VIEW legal_chunks AS
SELECT
    id,
    document_id,
    chunk_number,
    chunk_text,
    embedding,
    citation,
    section_title,
    law_category,
    created_at
FROM tax_law_chunks;

COMMENT ON VIEW legal_chunks IS
'DEPRECATED: Compatibility view for old code. Use tax_law_chunks table directly.
This view will be removed after migration is complete (90 days).';

-- Grant same permissions as original table
GRANT SELECT ON legal_chunks TO authenticated, anon;


-- ============================================================================
-- STEP 2: Update match_legal_chunks() to call search_tax_law() internally
-- ============================================================================
-- The old function returns hierarchy_level, but your schema doesn't have it
-- We'll return 0 as a default value for that column

CREATE OR REPLACE FUNCTION match_legal_chunks(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    hierarchy_level int,  -- Will return 0 (doesn't exist in your schema)
    chunk_number int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Log deprecation warning (visible in Supabase logs)
    RAISE WARNING 'match_legal_chunks() is DEPRECATED. Please use search_tax_law() instead. This function will be removed in 90 days.';

    -- Call new schema but return structure old code expects
    RETURN QUERY
    SELECT
        tlc.id,
        tlc.document_id,
        tlc.chunk_text,
        tlc.citation,
        0 as hierarchy_level,  -- Default value (column doesn't exist)
        tlc.chunk_number,
        1 - (tlc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tlc
    WHERE tlc.embedding IS NOT NULL
        AND 1 - (tlc.embedding <=> query_embedding) > match_threshold
    ORDER BY tlc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_legal_chunks IS
'DEPRECATED: Use search_tax_law() instead.
This function redirects to the new schema but will be removed in 90 days.
Migration date: 2025-11-12';

-- Grant same permissions as original
GRANT EXECUTE ON FUNCTION match_legal_chunks TO authenticated, anon;


-- ============================================================================
-- STEP 3: Create match_documents() compatibility wrapper (if needed)
-- ============================================================================

CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    chunk_text text,
    citation text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE WARNING 'match_documents() is DEPRECATED. Please use search_tax_law() or search_knowledge_base() instead. This function will be removed in 90 days.';

    -- Simple wrapper to new function
    RETURN QUERY
    SELECT
        tlc.id,
        tlc.chunk_text,
        tlc.citation,
        1 - (tlc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tlc
    WHERE tlc.embedding IS NOT NULL
        AND 1 - (tlc.embedding <=> query_embedding) > match_threshold
    ORDER BY tlc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_documents IS
'DEPRECATED: Use search_knowledge_base() instead.
This function redirects to the new schema but will be removed in 90 days.
Migration date: 2025-11-12';

GRANT EXECUTE ON FUNCTION match_documents TO authenticated, anon;


-- ============================================================================
-- STEP 4: Add helpful comments to existing functions
-- ============================================================================

COMMENT ON FUNCTION search_tax_law IS
'✅ CURRENT - Use this function for tax law vector search.
Searches tax_law_chunks table with optional category filtering.';

-- Only add comment if function exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'search_vendor_background'
    ) THEN
        COMMENT ON FUNCTION search_vendor_background IS
        '✅ CURRENT - Use this function for vendor documentation search.';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'search_knowledge_base'
    ) THEN
        COMMENT ON FUNCTION search_knowledge_base IS
        '✅ CURRENT - Use this function for combined search across tax law + vendor docs.';
    END IF;
END $$;


-- ============================================================================
-- STEP 5: Add table comments
-- ============================================================================

COMMENT ON TABLE tax_law_chunks IS
'✅ CURRENT - Text chunks from tax law documents with vector embeddings.
Use search_tax_law() function to query this table.';

COMMENT ON TABLE knowledge_documents IS
'✅ CURRENT - Master registry of all knowledge base documents.
Links to tax_law_chunks or vendor_background_chunks.';


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these after deployment to verify compatibility layer works:
--
-- Test 1: View exists and returns data
SELECT COUNT(*) as chunk_count FROM legal_chunks;
--
-- Test 2: Old function works
-- SELECT * FROM match_legal_chunks('[0.1,0.2,...]'::vector(1536), 0.5, 1);
--
-- Test 3: Check for deprecation warnings in Supabase logs

-- ============================================================================
-- SUCCESS CRITERIA
-- ============================================================================

-- ✅ legal_chunks view exists and returns data from tax_law_chunks
-- ✅ match_legal_chunks() exists and works
-- ✅ match_documents() exists and works
-- ✅ Old code continues to work without changes
-- ✅ Deprecation warnings logged

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- If something goes wrong, run this to remove compatibility layer:
/*
DROP VIEW IF EXISTS legal_chunks;
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int);
DROP FUNCTION IF EXISTS match_documents(vector, float, int);
*/
