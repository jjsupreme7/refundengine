-- ============================================================================
-- Migration 002 - STEP 3 ONLY (FIXED)
-- Fix for: function name "match_documents" is not unique
-- ============================================================================
--
-- This drops any existing match_documents functions first,
-- then creates the new one
-- ============================================================================

-- Drop all existing match_documents functions (any signature)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            'DROP FUNCTION IF EXISTS ' ||
            ns.nspname || '.' || p.proname ||
            '(' || pg_get_function_identity_arguments(p.oid) || ') CASCADE;' as drop_statement
        FROM pg_proc p
        JOIN pg_namespace ns ON p.pronamespace = ns.oid
        WHERE p.proname = 'match_documents'
          AND ns.nspname = 'public'
    LOOP
        EXECUTE r.drop_statement;
        RAISE NOTICE 'Dropped old function: %', r.drop_statement;
    END LOOP;
END $$;

-- Now create the new compatibility function
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

-- Verify it worked
SELECT 'match_documents function created successfully!' as status;
