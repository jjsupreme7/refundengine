-- Migration: Add embedding column to user_feedback for similarity-based correction retrieval
-- This enables finding corrections relevant to the current invoice, not just recent ones

-- Add embedding column to user_feedback table
ALTER TABLE user_feedback
ADD COLUMN IF NOT EXISTS query_embedding vector(1536);

-- Create vector index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_feedback_query_embedding
ON user_feedback USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

-- Function: Search corrections by similarity to current invoice context
CREATE OR REPLACE FUNCTION search_corrections(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    query text,
    suggested_answer text,
    feedback_comment text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        uf.query,
        uf.suggested_answer,
        uf.feedback_comment,
        (1 - (uf.query_embedding <=> search_corrections.query_embedding))::float as similarity
    FROM user_feedback uf
    WHERE uf.feedback_type = 'correction'
        AND uf.query_embedding IS NOT NULL
        AND (1 - (uf.query_embedding <=> search_corrections.query_embedding)) > match_threshold
    ORDER BY uf.query_embedding <=> search_corrections.query_embedding
    LIMIT match_count;
END;
$$;
