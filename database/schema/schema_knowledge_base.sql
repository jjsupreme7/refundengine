-- ============================================================================
-- KNOWLEDGE BASE SCHEMA
-- Separate storage for Tax Law Documents and Vendor Background Documents
-- ============================================================================

-- Table: knowledge_documents
-- Master table for all knowledge base documents
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Document classification
    document_type TEXT NOT NULL, -- 'tax_law' or 'vendor_background'

    -- Document metadata
    title TEXT NOT NULL,
    source_file TEXT,
    file_url TEXT, -- Cloud storage URL if using Supabase Storage

    -- For tax law documents
    citation TEXT, -- RCW/WAC reference
    effective_date DATE,
    law_category TEXT, -- 'exemption', 'rate', 'definition', etc.
    jurisdiction TEXT DEFAULT 'Washington State',

    -- For vendor documents
    vendor_name TEXT, -- Only for vendor_background docs
    vendor_category TEXT, -- 'manufacturer', 'distributor', 'service provider'

    -- Processing metadata
    total_chunks INT,
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'error'
    processed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table: tax_law_chunks
-- Stores chunked tax law documents with embeddings
CREATE TABLE IF NOT EXISTS tax_law_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,

    -- Chunk content
    chunk_text TEXT NOT NULL,
    chunk_number INT NOT NULL,

    -- Tax law specific metadata
    citation TEXT, -- RCW/WAC reference for this chunk
    section_title TEXT,
    law_category TEXT, -- 'exemption', 'rate', 'definition', 'procedure'
    keywords TEXT[], -- Array of relevant keywords

    -- Hierarchy (for nested regulations)
    hierarchy_level INT DEFAULT 1,
    parent_section TEXT,

    -- Vector embedding
    embedding vector(1536),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(document_id, chunk_number)
);

-- Table: vendor_background_chunks
-- Stores chunked vendor background documents with embeddings
CREATE TABLE IF NOT EXISTS vendor_background_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,

    -- Chunk content
    chunk_text TEXT NOT NULL,
    chunk_number INT NOT NULL,

    -- Vendor specific metadata
    vendor_name TEXT NOT NULL,
    vendor_category TEXT, -- 'manufacturer', 'distributor', 'service provider'
    document_category TEXT, -- 'company_profile', 'product_catalog', 'industry_info', 'contract'

    -- Product information
    product_categories TEXT[], -- Array of product types this vendor sells
    industry_sector TEXT, -- 'telecommunications', 'electronics', 'software', etc.

    -- Vector embedding
    embedding vector(1536),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(document_id, chunk_number)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- knowledge_documents indexes
CREATE INDEX idx_knowledge_docs_type ON knowledge_documents(document_type);
CREATE INDEX idx_knowledge_docs_vendor ON knowledge_documents(vendor_name);
CREATE INDEX idx_knowledge_docs_citation ON knowledge_documents(citation);
CREATE INDEX idx_knowledge_docs_status ON knowledge_documents(processing_status);

-- tax_law_chunks indexes
CREATE INDEX idx_tax_chunks_document ON tax_law_chunks(document_id);
CREATE INDEX idx_tax_chunks_citation ON tax_law_chunks(citation);
CREATE INDEX idx_tax_chunks_category ON tax_law_chunks(law_category);
CREATE INDEX idx_tax_chunks_embedding ON tax_law_chunks USING ivfflat (embedding vector_cosine_ops);

-- vendor_background_chunks indexes
CREATE INDEX idx_vendor_chunks_document ON vendor_background_chunks(document_id);
CREATE INDEX idx_vendor_chunks_vendor ON vendor_background_chunks(vendor_name);
CREATE INDEX idx_vendor_chunks_category ON vendor_background_chunks(document_category);
CREATE INDEX idx_vendor_chunks_embedding ON vendor_background_chunks USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- RPC FUNCTIONS FOR VECTOR SEARCH
-- ============================================================================

-- Function: Search tax law knowledge base
CREATE OR REPLACE FUNCTION search_tax_law(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5,
    law_category_filter text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    citation text,
    section_title text,
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
        tc.section_title,
        tc.law_category,
        1 - (tc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tc
    WHERE tc.embedding IS NOT NULL
        AND 1 - (tc.embedding <=> query_embedding) > match_threshold
        AND (law_category_filter IS NULL OR tc.law_category = law_category_filter)
    ORDER BY tc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Search vendor background knowledge base
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
    vendor_category text,
    document_category text,
    product_categories text[],
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
        vc.vendor_category,
        vc.document_category,
        vc.product_categories,
        1 - (vc.embedding <=> query_embedding) as similarity
    FROM vendor_background_chunks vc
    WHERE vc.embedding IS NOT NULL
        AND 1 - (vc.embedding <=> query_embedding) > match_threshold
        AND (vendor_filter IS NULL OR vc.vendor_name = vendor_filter)
    ORDER BY vc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Combined search (both tax law and vendor background)
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    vendor_name_filter text DEFAULT NULL,
    include_tax_law boolean DEFAULT true,
    include_vendor_bg boolean DEFAULT true,
    match_threshold float DEFAULT 0.5,
    tax_law_count int DEFAULT 5,
    vendor_bg_count int DEFAULT 3
)
RETURNS TABLE (
    source_type text,
    id uuid,
    chunk_text text,
    citation text,
    vendor_name text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY

    -- Tax law results
    SELECT
        'tax_law'::text as source_type,
        tc.id,
        tc.chunk_text,
        tc.citation,
        NULL::text as vendor_name,
        1 - (tc.embedding <=> query_embedding) as similarity
    FROM tax_law_chunks tc
    WHERE include_tax_law
        AND tc.embedding IS NOT NULL
        AND 1 - (tc.embedding <=> query_embedding) > match_threshold
    ORDER BY tc.embedding <=> query_embedding
    LIMIT tax_law_count

    UNION ALL

    -- Vendor background results
    SELECT
        'vendor_background'::text as source_type,
        vc.id,
        vc.chunk_text,
        NULL::text as citation,
        vc.vendor_name,
        1 - (vc.embedding <=> query_embedding) as similarity
    FROM vendor_background_chunks vc
    WHERE include_vendor_bg
        AND vc.embedding IS NOT NULL
        AND 1 - (vc.embedding <=> query_embedding) > match_threshold
        AND (vendor_name_filter IS NULL OR vc.vendor_name = vendor_name_filter)
    ORDER BY vc.embedding <=> query_embedding
    LIMIT vendor_bg_count;
END;
$$;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Tax law documents with chunk counts
CREATE OR REPLACE VIEW tax_law_documents_summary AS
SELECT
    kd.id,
    kd.title,
    kd.citation,
    kd.law_category,
    kd.effective_date,
    COUNT(tc.id) as chunk_count,
    SUM(CASE WHEN tc.embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded_chunks,
    kd.processing_status,
    kd.created_at
FROM knowledge_documents kd
LEFT JOIN tax_law_chunks tc ON kd.id = tc.document_id
WHERE kd.document_type = 'tax_law'
GROUP BY kd.id, kd.title, kd.citation, kd.law_category, kd.effective_date, kd.processing_status, kd.created_at;

-- View: Vendor documents with chunk counts
CREATE OR REPLACE VIEW vendor_documents_summary AS
SELECT
    kd.id,
    kd.vendor_name,
    kd.title,
    kd.vendor_category,
    COUNT(vc.id) as chunk_count,
    SUM(CASE WHEN vc.embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded_chunks,
    kd.processing_status,
    kd.created_at
FROM knowledge_documents kd
LEFT JOIN vendor_background_chunks vc ON kd.id = vc.document_id
WHERE kd.document_type = 'vendor_background'
GROUP BY kd.id, kd.vendor_name, kd.title, kd.vendor_category, kd.processing_status, kd.created_at;

-- View: Complete knowledge base stats
CREATE OR REPLACE VIEW knowledge_base_stats AS
SELECT
    'tax_law' as doc_type,
    COUNT(DISTINCT kd.id) as document_count,
    COUNT(tc.id) as total_chunks,
    SUM(CASE WHEN tc.embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded_chunks
FROM knowledge_documents kd
LEFT JOIN tax_law_chunks tc ON kd.id = tc.document_id
WHERE kd.document_type = 'tax_law'

UNION ALL

SELECT
    'vendor_background' as doc_type,
    COUNT(DISTINCT kd.id) as document_count,
    COUNT(vc.id) as total_chunks,
    SUM(CASE WHEN vc.embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded_chunks
FROM knowledge_documents kd
LEFT JOIN vendor_background_chunks vc ON kd.id = vc.document_id
WHERE kd.document_type = 'vendor_background';

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT EXECUTE ON FUNCTION search_tax_law TO authenticated, anon;
GRANT EXECUTE ON FUNCTION search_vendor_background TO authenticated, anon;
GRANT EXECUTE ON FUNCTION search_knowledge_base TO authenticated, anon;

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================

-- If you have existing legal_chunks table, migrate with:
--
-- INSERT INTO knowledge_documents (document_type, title, citation, total_chunks)
-- SELECT 'tax_law', title, citation, COUNT(*)
-- FROM legal_documents
-- GROUP BY title, citation;
--
-- INSERT INTO tax_law_chunks (document_id, chunk_text, chunk_number, citation, embedding)
-- SELECT kd.id, lc.chunk_text, lc.chunk_number, lc.citation, lc.embedding
-- FROM legal_chunks lc
-- JOIN legal_documents ld ON lc.document_id = ld.id
-- JOIN knowledge_documents kd ON kd.citation = ld.citation AND kd.document_type = 'tax_law';
