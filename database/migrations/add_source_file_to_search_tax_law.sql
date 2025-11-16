-- ============================================================================
-- Add file_url AND source_file to search_tax_law RPC function
-- This migration adds both online URL and local file path to search results
-- ============================================================================

-- Drop the existing function first
DROP FUNCTION IF EXISTS search_tax_law(vector, float, int, text, text[], text[]);

-- Recreate with file_url AND source_file included
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
