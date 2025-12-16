-- Migration 007: Add Full-Text Search for BM25/RRF Hybrid Retrieval
-- Purpose: Enable PostgreSQL full-text search to complement vector search
-- Date: 2024-12-14

-- Add tsvector column for full-text search
ALTER TABLE tax_law_chunks
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Populate search_vector from existing chunk_text
UPDATE tax_law_chunks
SET search_vector = to_tsvector('english', coalesce(chunk_text, ''));

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_tax_chunks_search_vector
ON tax_law_chunks USING gin(search_vector);

-- Create trigger to auto-update search_vector on insert/update
CREATE OR REPLACE FUNCTION update_tax_chunk_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', coalesce(NEW.chunk_text, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tax_law_chunks_search_vector_trigger ON tax_law_chunks;
CREATE TRIGGER tax_law_chunks_search_vector_trigger
BEFORE INSERT OR UPDATE OF chunk_text ON tax_law_chunks
FOR EACH ROW EXECUTE FUNCTION update_tax_chunk_search_vector();

-- BM25-style full-text search function using ts_rank_cd
-- ts_rank_cd uses cover density ranking which is similar to BM25
CREATE OR REPLACE FUNCTION search_tax_law_fulltext(
    search_query text,
    match_count int DEFAULT 20
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    section_title text,
    law_category text,
    chunk_role text,
    file_url text,
    ts_rank float
)
LANGUAGE plpgsql
AS $$
DECLARE
    tsquery_val tsquery;
BEGIN
    -- Convert search query to tsquery with OR logic for better recall
    tsquery_val := plainto_tsquery('english', search_query);

    RETURN QUERY
    SELECT
        tc.id,
        tc.document_id,
        tc.chunk_text,
        tc.citation,
        tc.section_title,
        tc.law_category,
        tc.chunk_role,
        kd.file_url,
        ts_rank_cd(tc.search_vector, tsquery_val, 32) as ts_rank
    FROM tax_law_chunks tc
    LEFT JOIN knowledge_documents kd ON tc.document_id = kd.id
    WHERE tc.search_vector @@ tsquery_val
    ORDER BY ts_rank DESC
    LIMIT match_count;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION search_tax_law_fulltext TO authenticated, anon;

-- Add comment for documentation
COMMENT ON FUNCTION search_tax_law_fulltext IS 'BM25-style full-text search for hybrid retrieval with RRF fusion';
COMMENT ON COLUMN tax_law_chunks.search_vector IS 'tsvector column for PostgreSQL full-text search';
