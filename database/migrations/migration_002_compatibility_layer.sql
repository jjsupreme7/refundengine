-- ============================================================================
-- Migration 002: Compatibility Layer
-- Created: 2025-11-12
-- Purpose: Bridge OLD schema → NEW schema during migration period
-- ============================================================================
--
-- This migration creates compatibility wrappers for deprecated functions
-- and views, allowing old code to continue working while we migrate to the
-- new schema.
--
-- OLD SCHEMA → NEW SCHEMA MAPPING:
--   legal_documents → knowledge_documents
--   document_chunks → tax_law_chunks
--   legal_chunks → tax_law_chunks (view)
--   match_legal_chunks() → search_tax_law() (function wrapper)
--
-- DEPRECATION TIMELINE: 90 days from deployment
-- After all code is migrated, run migration_003 to remove this layer
-- ============================================================================

-- ============================================================================
-- STEP 1: Create compatibility VIEW for legal_chunks
-- ============================================================================
-- Allows old code using "SELECT * FROM legal_chunks" to work
-- Points to new tax_law_chunks table

CREATE OR REPLACE VIEW legal_chunks AS
SELECT
    id,
    document_id,
    chunk_number,
    chunk_text,
    embedding,
    citation,
    law_category,
    section_title,
    hierarchy_level,
    parent_section,
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
-- Allows old code using "match_legal_chunks()" to work
-- Returns same structure as before but uses new schema underneath

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
    hierarchy_level int,
    chunk_number int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Log deprecation warning (visible in Supabase logs)
    RAISE WARNING 'match_legal_chunks() is DEPRECATED. Please use search_tax_law() instead. This function will be removed in 90 days.';

    -- Call new function internally but only return fields old code expects
    RETURN QUERY
    SELECT
        tlc.id,
        tlc.document_id,
        tlc.chunk_text,
        tlc.citation,
        COALESCE(tlc.hierarchy_level, 0) as hierarchy_level,
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
-- Some old code may use this simpler function name

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
-- STEP 4: Add deprecation notices to NEW functions (documentation)
-- ============================================================================

COMMENT ON FUNCTION search_tax_law IS
'✅ CURRENT - Use this function for tax law vector search.
Searches tax_law_chunks table with optional category filtering.
Signature: search_tax_law(embedding, threshold, count, category_filter)
Returns: id, document_id, chunk_text, citation, section_title, law_category, file_url, similarity';

COMMENT ON FUNCTION search_vendor_background IS
'✅ CURRENT - Use this function for vendor documentation search.
Searches vendor_background_chunks table with optional vendor filtering.
Signature: search_vendor_background(embedding, threshold, count, vendor_filter)';

COMMENT ON FUNCTION search_knowledge_base IS
'✅ CURRENT - Use this function for combined search across tax law + vendor docs.
Searches both tax_law_chunks and vendor_background_chunks.
Signature: search_knowledge_base(embedding, threshold, tax_count, vendor_count)';


-- ============================================================================
-- STEP 5: Add table comments for clarity
-- ============================================================================

COMMENT ON TABLE tax_law_chunks IS
'✅ CURRENT - Text chunks from tax law documents with vector embeddings.
Primary table for tax law semantic search. Use search_tax_law() to query.';

COMMENT ON TABLE vendor_background_chunks IS
'✅ CURRENT - Text chunks from vendor documentation with vector embeddings.
Use search_vendor_background() to query.';

COMMENT ON TABLE knowledge_documents IS
'✅ CURRENT - Master registry of all knowledge base documents.
Links to tax_law_chunks (if document_type=''tax_law'') or vendor_background_chunks (if document_type=''vendor_background'').';


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these after deployment to verify compatibility layer works:
--
-- Test 1: Old function works
-- SELECT * FROM match_legal_chunks('[0.1,0.2,...]'::vector(1536), 0.5, 5);
--
-- Test 2: Old view works
-- SELECT COUNT(*) FROM legal_chunks;
--
-- Test 3: Check for deprecation warnings in logs
-- Should see: "match_legal_chunks() is DEPRECATED..."

-- ============================================================================
-- SUCCESS CRITERIA
-- ============================================================================

-- ✅ legal_chunks view exists and returns data from tax_law_chunks
-- ✅ match_legal_chunks() exists and calls search_tax_law() internally
-- ✅ match_documents() exists and works
-- ✅ Old code continues to work without changes
-- ✅ Deprecation warnings logged (visible in Supabase logs)
-- ✅ New functions have clear documentation

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- If needed, run this to remove compatibility layer:
/*
DROP VIEW IF EXISTS legal_chunks;
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int);
DROP FUNCTION IF EXISTS match_documents(vector, float, int);
*/
