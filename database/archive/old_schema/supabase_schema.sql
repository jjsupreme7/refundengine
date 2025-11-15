-- ============================================
-- Washington Tax Refund Engine - Supabase Schema
-- ============================================
-- This schema includes pgvector for RAG search
-- and comprehensive metadata for filtering
-- ============================================

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- CLIENT MANAGEMENT
-- ============================================

CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    client_name TEXT NOT NULL,
    business_entity_type TEXT,
    ubi_number TEXT,
    contact_email TEXT,
    industry_classification TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS client_documents (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    document_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_format TEXT,
    file_size_bytes INTEGER,
    content_hash TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    document_date DATE,
    processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT,
    error_message TEXT,
    classification_confidence INTEGER
);

-- ============================================
-- LEGAL KNOWLEDGE BASE
-- ============================================

CREATE TABLE IF NOT EXISTS legal_documents (
    id SERIAL PRIMARY KEY,
    document_title TEXT NOT NULL,
    file_path TEXT NOT NULL,

    -- Document classification
    document_type TEXT, -- Will store: "RCW", "WAC", "Determination", "Case Law", "Guide"
    citation TEXT, -- Will store statute number (e.g., "458-20-101")

    -- Dates for filtering
    document_date DATE,
    effective_date DATE,
    expiration_date DATE,
    year_issued INTEGER, -- Extracted from document_date for easy filtering

    -- Metadata
    jurisdiction TEXT DEFAULT 'Washington',
    source_type TEXT, -- Same as document_type (keeping for compatibility)
    statute_number TEXT, -- Same as citation (for consistency)

    -- File info
    file_format TEXT,
    file_size_bytes INTEGER,
    content_hash TEXT,
    raw_extracted_text TEXT,

    -- Status
    is_current BOOLEAN DEFAULT TRUE,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES legal_documents(id),

    -- Rich tagging (stored as arrays for easy filtering)
    topic_tags TEXT[], -- e.g., ["digital products", "exemptions", "software"]
    industries TEXT[], -- e.g., ["technology", "SaaS", "e-commerce"]
    tax_types TEXT[], -- e.g., ["sales tax", "use tax", "B&O tax"]
    exemption_categories TEXT[], -- e.g., ["digital goods", "services"]
    product_types TEXT[], -- e.g., ["software", "cloud hosting", "downloads"]
    jurisdictions TEXT[], -- e.g., ["Washington", "King County"]
    referenced_statutes TEXT[], -- e.g., ["RCW 82.04", "RCW 82.08"]
    keywords TEXT[], -- e.g., ["electronic delivery", "tangible personal property"]
    key_concepts TEXT[], -- General concepts from the document

    -- Flexible custom tags (JSONB for any additional metadata)
    custom_tags JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES legal_documents(id),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    page_number INTEGER,
    section_heading TEXT,

    -- CRITICAL: Vector embedding for semantic search
    embedding vector(1536) -- OpenAI ada-002 produces 1536-dim vectors
);

-- Create index for fast vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- BUSINESS DOCUMENTS
-- ============================================

CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    client_document_id INTEGER REFERENCES client_documents(id),

    -- File info
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Vendor information
    vendor_name TEXT,
    vendor_address TEXT,
    vendor_city TEXT,
    vendor_state TEXT,
    vendor_zip TEXT,

    -- Invoice details
    invoice_date DATE,
    invoice_number TEXT,
    purchase_order_number TEXT,

    -- Financial
    total_amount NUMERIC(10,2),
    sales_tax_charged NUMERIC(10,2),
    use_tax_charged NUMERIC(10,2),

    -- Customer info
    customer_name TEXT,
    ship_to_address TEXT,
    ship_to_city TEXT,
    ship_to_state TEXT,
    bill_to_address TEXT,
    payment_terms TEXT,

    -- Extraction metadata
    raw_extracted_text TEXT,
    extraction_confidence INTEGER,

    -- Duplicate detection
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_invoice_id INTEGER REFERENCES invoices(id),
    duplicate_notes TEXT,

    -- File references (for multi-page invoices)
    file_references JSONB -- Array of {filename, path, pages}
);

CREATE TABLE IF NOT EXISTS invoice_line_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    line_number INTEGER,

    -- Product/service details
    item_description TEXT NOT NULL,
    quantity NUMERIC(10,2),
    unit_price NUMERIC(10,2),
    line_total NUMERIC(10,2),
    sales_tax_on_line NUMERIC(10,2),

    -- Classification
    product_code TEXT,
    gl_code TEXT,
    product_category TEXT,

    -- Tax determination flags
    is_digital BOOLEAN,
    is_service BOOLEAN,
    primarily_human_effort BOOLEAN
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    client_document_id INTEGER REFERENCES client_documents(id),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    po_number TEXT,
    po_date DATE,
    vendor_name TEXT,
    total_amount NUMERIC(10,2),
    raw_extracted_text TEXT
);

CREATE TABLE IF NOT EXISTS statements_of_work (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    client_document_id INTEGER REFERENCES client_documents(id),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    sow_number TEXT,
    start_date DATE,
    end_date DATE,
    service_description TEXT,
    deliverables TEXT,
    primarily_human_effort BOOLEAN,
    raw_extracted_text TEXT
);

CREATE TABLE IF NOT EXISTS master_agreements (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    client_document_id INTEGER REFERENCES client_documents(id),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    agreement_name TEXT,
    effective_date DATE,
    expiration_date DATE,
    party_names TEXT[],
    key_terms TEXT,
    raw_extracted_text TEXT
);

-- ============================================
-- DOCUMENT RELATIONSHIPS
-- ============================================

CREATE TABLE IF NOT EXISTS document_relationships (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER NOT NULL REFERENCES client_documents(id),
    source_document_type TEXT NOT NULL,
    target_document_id INTEGER NOT NULL REFERENCES client_documents(id),
    target_document_type TEXT NOT NULL,
    relationship_type TEXT NOT NULL, -- "references", "supports", "supersedes", etc.
    confidence_score INTEGER,
    notes TEXT
);

-- ============================================
-- ANALYSIS & RULES
-- ============================================

CREATE TABLE IF NOT EXISTS legal_rules (
    id SERIAL PRIMARY KEY,
    refund_category TEXT NOT NULL,
    statute_citation TEXT NOT NULL,
    effective_date DATE,
    rule_summary TEXT,
    requirements_json TEXT, -- JSON with eligibility criteria
    statute_of_limitations_years INTEGER,
    typical_refund_percentage INTEGER,
    industry_tags TEXT[]
);

CREATE TABLE IF NOT EXISTS product_identifications (
    id SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_category TEXT,
    tax_treatment TEXT,
    typical_exemptions TEXT[],
    custom_classification JSONB
);

CREATE TABLE IF NOT EXISTS refund_analysis (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    line_item_id INTEGER REFERENCES invoice_line_items(id),
    legal_rule_id INTEGER REFERENCES legal_rules(id),

    -- Analysis results
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    potentially_eligible BOOLEAN,
    confidence_score INTEGER,
    estimated_refund_amount NUMERIC(10,2),
    refund_calculation_method TEXT,

    -- Detailed analysis
    criteria_matching_json TEXT, -- What criteria were matched
    documentation_gaps TEXT, -- What's missing
    red_flags TEXT, -- Potential issues
    next_steps TEXT, -- Recommended actions

    -- Human review
    reviewed_by_human BOOLEAN DEFAULT FALSE,
    human_override BOOLEAN,
    human_notes TEXT
);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to search documents by semantic similarity
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5,
  filter_doc_ids int[] DEFAULT NULL
)
RETURNS TABLE (
  chunk_id int,
  document_id int,
  document_title text,
  chunk_text text,
  page_number int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id AS chunk_id,
    dc.document_id,
    ld.document_title,
    dc.chunk_text,
    dc.page_number,
    1 - (dc.embedding <=> query_embedding) as similarity
  FROM document_chunks dc
  JOIN legal_documents ld ON dc.document_id = ld.id
  WHERE
    (filter_doc_ids IS NULL OR dc.document_id = ANY(filter_doc_ids))
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Function to search with metadata filters
CREATE OR REPLACE FUNCTION search_with_filters(
  query_embedding vector(1536),
  source_types text[] DEFAULT NULL,
  year_from int DEFAULT NULL,
  year_to int DEFAULT NULL,
  topic_tags_filter text[] DEFAULT NULL,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  chunk_id int,
  document_id int,
  document_title text,
  source_type text,
  year_issued int,
  chunk_text text,
  page_number int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id AS chunk_id,
    dc.document_id,
    ld.document_title,
    ld.source_type,
    ld.year_issued,
    dc.chunk_text,
    dc.page_number,
    1 - (dc.embedding <=> query_embedding) as similarity
  FROM document_chunks dc
  JOIN legal_documents ld ON dc.document_id = ld.id
  LEFT JOIN document_metadata dm ON ld.id = dm.document_id
  WHERE
    (source_types IS NULL OR ld.source_type = ANY(source_types))
    AND (year_from IS NULL OR ld.year_issued >= year_from)
    AND (year_to IS NULL OR ld.year_issued <= year_to)
    AND (topic_tags_filter IS NULL OR dm.topic_tags && topic_tags_filter)
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Invoice lookups
CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_vendor_name ON invoices(vendor_name);

-- Line item lookups
CREATE INDEX IF NOT EXISTS idx_line_items_invoice_id ON invoice_line_items(invoice_id);

-- Document lookups
CREATE INDEX IF NOT EXISTS idx_legal_docs_source_type ON legal_documents(source_type);
CREATE INDEX IF NOT EXISTS idx_legal_docs_year_issued ON legal_documents(year_issued);
CREATE INDEX IF NOT EXISTS idx_legal_docs_citation ON legal_documents(citation);

-- Chunk lookups
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);

-- Metadata array lookups (GIN indexes for array containment)
CREATE INDEX IF NOT EXISTS idx_metadata_topic_tags ON document_metadata USING GIN (topic_tags);
CREATE INDEX IF NOT EXISTS idx_metadata_tax_types ON document_metadata USING GIN (tax_types);
CREATE INDEX IF NOT EXISTS idx_metadata_industries ON document_metadata USING GIN (industries);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View: Complete invoice analysis
CREATE OR REPLACE VIEW v_invoice_analysis AS
SELECT
    i.id AS invoice_id,
    i.invoice_number,
    i.vendor_name,
    i.invoice_date,
    ili.id AS line_item_id,
    ili.item_description,
    ili.line_total,
    ili.sales_tax_on_line,
    ra.potentially_eligible,
    ra.confidence_score,
    ra.estimated_refund_amount,
    ra.refund_calculation_method,
    c.client_name
FROM invoices i
LEFT JOIN invoice_line_items ili ON i.id = ili.invoice_id
LEFT JOIN refund_analysis ra ON ili.id = ra.line_item_id
LEFT JOIN clients c ON i.client_id = c.id;

-- View: Document metadata summary
CREATE OR REPLACE VIEW v_document_summary AS
SELECT
    ld.id,
    ld.document_title,
    ld.source_type,
    ld.year_issued,
    ld.citation,
    dm.topic_tags,
    dm.tax_types,
    dm.industries,
    COUNT(dc.id) AS num_chunks
FROM legal_documents ld
LEFT JOIN document_metadata dm ON ld.id = dm.document_id
LEFT JOIN document_chunks dc ON ld.id = dc.document_id
GROUP BY ld.id, ld.document_title, ld.source_type, ld.year_issued, ld.citation,
         dm.topic_tags, dm.tax_types, dm.industries;

-- ============================================
-- GRANT PERMISSIONS (if needed)
-- ============================================

-- Grant usage on all tables (adjust role as needed)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
