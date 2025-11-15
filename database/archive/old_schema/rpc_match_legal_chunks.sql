-- ============================================================================
-- RPC Function: match_legal_chunks
-- Vector similarity search for legal knowledge base
-- ============================================================================

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
    RETURN QUERY
    SELECT
        lc.id,
        lc.document_id,
        lc.chunk_text,
        lc.citation,
        lc.hierarchy_level,
        lc.chunk_number,
        1 - (lc.embedding <=> query_embedding) as similarity
    FROM legal_chunks lc
    WHERE lc.embedding IS NOT NULL
        AND 1 - (lc.embedding <=> query_embedding) > match_threshold
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant access
GRANT EXECUTE ON FUNCTION match_legal_chunks TO authenticated, anon;
