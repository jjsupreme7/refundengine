-- ============================================================================
-- Fix search_tax_law function overloading issue
-- Drop the old 4-parameter version to resolve ambiguity
-- ============================================================================

-- Drop the old 4-parameter version if it exists
DROP FUNCTION IF EXISTS search_tax_law(vector, float, int, text);

-- Ensure the 6-parameter version exists and is correct
DROP FUNCTION IF EXISTS search_tax_law(vector, float, int, text, text[], text[]);

-- Recreate with all 6 parameters (this is the version we want to keep)
CREATE OR REPLACE FUNCTION search_tax_law(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5,
    law_category_filter text DEFAULT NULL,
    tax_types_filter text[] DEFAULT NULL,
    industries_filter text[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    section_title text,
    law_category text,
    topic_tags text[],
    tax_types text[],
    industries text[],
    referenced_statutes text[],
    file_url text,
    source_file text,
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
        tc.topic_tags,
        tc.tax_types,
        tc.industries,
        tc.referenced_statutes,
        kd.file_url,
        kd.source_file,
        1 - (tc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tc
    LEFT JOIN knowledge_documents kd ON tc.document_id = kd.id
    WHERE tc.embedding IS NOT NULL
        AND 1 - (tc.embedding <=> query_embedding) > match_threshold
        AND (law_category_filter IS NULL OR tc.law_category = law_category_filter)
        AND (tax_types_filter IS NULL OR tc.tax_types && tax_types_filter)
        AND (industries_filter IS NULL OR tc.industries && industries_filter)
    ORDER BY tc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION search_tax_law(vector, float, int, text, text[], text[]) TO anon, authenticated;

-- Verify the function exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'search_tax_law'
    ) THEN
        RAISE NOTICE '✅ search_tax_law function created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create search_tax_law function';
    END IF;
END $$;
