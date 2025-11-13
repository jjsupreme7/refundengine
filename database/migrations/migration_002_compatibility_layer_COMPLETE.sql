-- ============================================================================
-- Migration 002: Compatibility Layer (COMPLETE - RUN THIS ONE)
-- Created: 2025-11-12
-- Purpose: Bridge OLD schema → NEW schema during migration period
-- ============================================================================
--
-- This version handles:
-- - Simple schema (no hierarchy_level columns)
-- - Existing functions (drops and recreates them)
-- - All edge cases discovered during deployment
--
-- SAFE TO RUN: This migration is idempotent (can run multiple times)
-- ============================================================================

-- ============================================================================
-- STEP 1: Create compatibility VIEW for legal_chunks
-- ============================================================================

-- Drop view if it exists first
DROP VIEW IF EXISTS legal_chunks;

-- Create the view pointing to tax_law_chunks
CREATE VIEW legal_chunks AS
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

GRANT SELECT ON legal_chunks TO authenticated, anon;

SELECT '✅ Step 1 complete: legal_chunks view created' as status;


-- ============================================================================
-- STEP 2: Create/replace match_legal_chunks() function
-- ============================================================================

-- Drop old function if exists (any signature)
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int) CASCADE;

-- Create the compatibility function
CREATE FUNCTION match_legal_chunks(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    hierarchy_level int,  -- Returns 0 (column doesn't exist in simple schema)
    chunk_number int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE WARNING 'match_legal_chunks() is DEPRECATED. Please use search_tax_law() instead. This function will be removed in 90 days.';

    RETURN QUERY
    SELECT
        tlc.id,
        tlc.document_id,
        tlc.chunk_text,
        tlc.citation,
        0 as hierarchy_level,  -- Default value
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
Migration date: 2025-11-12. Will be removed in 90 days.';

GRANT EXECUTE ON FUNCTION match_legal_chunks TO authenticated, anon;

SELECT '✅ Step 2 complete: match_legal_chunks() function created' as status;


-- ============================================================================
-- STEP 3: Create/replace match_documents() function
-- ============================================================================

-- Drop ALL existing match_documents functions (handles multiple signatures)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            ns.nspname || '.' || p.proname ||
            '(' || pg_get_function_identity_arguments(p.oid) || ')' as func_signature
        FROM pg_proc p
        JOIN pg_namespace ns ON p.pronamespace = ns.oid
        WHERE p.proname = 'match_documents'
          AND ns.nspname = 'public'
    LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || r.func_signature || ' CASCADE';
        RAISE NOTICE 'Dropped old function: %', r.func_signature;
    END LOOP;
END $$;

-- Create the new compatibility function
CREATE FUNCTION match_documents(
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
Migration date: 2025-11-12. Will be removed in 90 days.';

GRANT EXECUTE ON FUNCTION match_documents TO authenticated, anon;

SELECT '✅ Step 3 complete: match_documents() function created' as status;


-- ============================================================================
-- STEP 4: Add helpful comments to existing functions (if they exist)
-- ============================================================================

DO $$
BEGIN
    -- Add comment to search_tax_law if it exists
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_tax_law') THEN
        COMMENT ON FUNCTION search_tax_law IS
        '✅ CURRENT - Use this function for tax law vector search.
Searches tax_law_chunks table with optional category filtering.';
    END IF;

    -- Add comment to search_vendor_background if it exists
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_vendor_background') THEN
        COMMENT ON FUNCTION search_vendor_background IS
        '✅ CURRENT - Use this function for vendor documentation search.';
    END IF;

    -- Add comment to search_knowledge_base if it exists
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_knowledge_base') THEN
        COMMENT ON FUNCTION search_knowledge_base IS
        '✅ CURRENT - Use this function for combined search across tax law + vendor docs.';
    END IF;
END $$;

SELECT '✅ Step 4 complete: Function comments added' as status;


-- ============================================================================
-- STEP 5: Add table comments
-- ============================================================================

COMMENT ON TABLE tax_law_chunks IS
'✅ CURRENT - Text chunks from tax law documents with vector embeddings.
Use search_tax_law() function to query this table.';

COMMENT ON TABLE knowledge_documents IS
'✅ CURRENT - Master registry of all knowledge base documents.
Links to tax_law_chunks or vendor_background_chunks.';

SELECT '✅ Step 5 complete: Table comments added' as status;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check that everything was created successfully
SELECT
    '✅✅✅ MIGRATION 002 COMPLETE! ✅✅✅' as status,
    (SELECT COUNT(*) FROM legal_chunks) as legal_chunks_count,
    (SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'match_legal_chunks')) as match_legal_chunks_exists,
    (SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'match_documents')) as match_documents_exists;

-- Show summary
SELECT '
🎉 Compatibility layer deployed successfully!

Next steps:
1. Test old code still works: python3 -c "from core.enhanced_rag import EnhancedRAG; ..."
2. Test new code still works: python3 chatbot/simple_chat.py
3. Check for deprecation warnings in Supabase logs
4. Continue with Phase 2 migration (remaining files)

Deprecation timeline: 90 days from today
' as next_steps;


-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- If something goes wrong, run this to remove compatibility layer:
/*
DROP VIEW IF EXISTS legal_chunks;
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int);
DROP FUNCTION IF EXISTS match_documents(vector, float, int);
*/
