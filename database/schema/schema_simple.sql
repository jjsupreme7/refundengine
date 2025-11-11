-- ============================================================================
-- SIMPLE KNOWLEDGE BASE SCHEMA FOR RAG TESTING
-- Dual knowledge base: Tax Law + Vendor Background
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if they exist (for clean slate)
DROP TABLE IF EXISTS tax_law_chunks CASCADE;
DROP TABLE IF EXISTS vendor_background_chunks CASCADE;
DROP TABLE IF EXISTS knowledge_documents CASCADE;

-- Table: knowledge_documents
-- Master table for all knowledge base documents
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type TEXT NOT NULL CHECK (document_type IN ('tax_law', 'vendor_background')),
    title TEXT NOT NULL,
    source_file TEXT,

    -- Tax law specific
    citation TEXT,
    law_category TEXT,
    effective_date DATE,

    -- Vendor specific
    vendor_name TEXT,
    vendor_category TEXT,

    -- Metadata
    total_chunks INT DEFAULT 0,
    processing_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table: tax_law_chunks
-- Chunked tax law documents with embeddings
CREATE TABLE tax_law_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_number INT NOT NULL,

    -- Tax law metadata
    citation TEXT,
    section_title TEXT,
    law_category TEXT,

    -- Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    embedding vector(1536),

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(document_id, chunk_number)
);

-- Table: vendor_background_chunks
-- Chunked vendor documents with embeddings
CREATE TABLE vendor_background_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_number INT NOT NULL,

    -- Vendor metadata
    vendor_name TEXT NOT NULL,
    vendor_category TEXT,
    document_category TEXT,

    -- Vector embedding
    embedding vector(1536),

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(document_id, chunk_number)
);

-- Indexes for performance
CREATE INDEX idx_knowledge_docs_type ON knowledge_documents(document_type);
CREATE INDEX idx_knowledge_docs_vendor ON knowledge_documents(vendor_name);
CREATE INDEX idx_tax_chunks_document ON tax_law_chunks(document_id);
CREATE INDEX idx_tax_chunks_citation ON tax_law_chunks(citation);
CREATE INDEX idx_vendor_chunks_document ON vendor_background_chunks(document_id);
CREATE INDEX idx_vendor_chunks_vendor ON vendor_background_chunks(vendor_name);

-- Vector indexes using IVFFlat (will create after data is inserted)
-- Commented out for now - will add after ingesting documents
-- CREATE INDEX idx_tax_chunks_embedding ON tax_law_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_vendor_chunks_embedding ON vendor_background_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- RPC FUNCTIONS FOR VECTOR SEARCH
-- ============================================================================

-- Function: Search tax law chunks
CREATE OR REPLACE FUNCTION search_tax_law(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    law_category text,
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
        tc.law_category,
        1 - (tc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tc
    WHERE tc.embedding IS NOT NULL
        AND 1 - (tc.embedding <=> query_embedding) > match_threshold
    ORDER BY tc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Search vendor background chunks
CREATE OR REPLACE FUNCTION search_vendor_background(
    query_embedding vector(1536),
    vendor_filter text DEFAULT NULL,
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 3
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    vendor_name text,
    document_category text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        vc.id,
        vc.document_id,
        vc.chunk_text,
        vc.vendor_name,
        vc.document_category,
        1 - (vc.embedding <=> query_embedding) as similarity
    FROM vendor_background_chunks vc
    WHERE vc.embedding IS NOT NULL
        AND 1 - (vc.embedding <=> query_embedding) > match_threshold
        AND (vendor_filter IS NULL OR vc.vendor_name = vendor_filter)
    ORDER BY vc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant permissions
GRANT ALL ON knowledge_documents TO postgres, anon, authenticated;
GRANT ALL ON tax_law_chunks TO postgres, anon, authenticated;
GRANT ALL ON vendor_background_chunks TO postgres, anon, authenticated;
GRANT EXECUTE ON FUNCTION search_tax_law TO postgres, anon, authenticated;
GRANT EXECUTE ON FUNCTION search_vendor_background TO postgres, anon, authenticated;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✓ Knowledge base schema created successfully!';
    RAISE NOTICE '  - knowledge_documents';
    RAISE NOTICE '  - tax_law_chunks';
    RAISE NOTICE '  - vendor_background_chunks';
    RAISE NOTICE '  - search_tax_law()';
    RAISE NOTICE '  - search_vendor_background()';
END $$;
