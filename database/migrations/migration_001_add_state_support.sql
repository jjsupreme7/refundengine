
-- Add state support to existing schema
ALTER TABLE legal_documents 
ADD COLUMN IF NOT EXISTS state_code VARCHAR(2) DEFAULT 'WA';

ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS state_code VARCHAR(2) DEFAULT 'WA';

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_legal_docs_state 
ON legal_documents(state_code);

CREATE INDEX IF NOT EXISTS idx_chunks_state 
ON document_chunks(state_code);

-- Update existing records
UPDATE legal_documents SET state_code = 'WA' WHERE state_code IS NULL;
UPDATE document_chunks SET state_code = 'WA' WHERE state_code IS NULL;

-- Add state-aware search function
CREATE OR REPLACE FUNCTION match_documents_by_state(
    query_embedding VECTOR(1536),
    target_state VARCHAR(2) DEFAULT 'WA',
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    document_id INT,
    document_title TEXT,
    citation VARCHAR,
    chunk_text TEXT,
    similarity FLOAT
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.document_id,
        ld.document_title,
        ld.citation,
        dc.chunk_text,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    JOIN legal_documents ld ON dc.document_id = ld.id
    WHERE
        dc.state_code = target_state
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
