-- ============================================
-- Schema Update Script
-- Adds pgvector and missing features to existing schema
-- Safe to run - only adds new features, doesn't drop existing data
-- ============================================

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add missing columns to existing tables

-- Add embedding column to document_chunks (CRITICAL for RAG)
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Add metadata fields to legal_documents
ALTER TABLE legal_documents
ADD COLUMN IF NOT EXISTS jurisdiction TEXT DEFAULT 'Washington',
ADD COLUMN IF NOT EXISTS source_type TEXT,
ADD COLUMN IF NOT EXISTS year_issued INTEGER,
ADD COLUMN IF NOT EXISTS statute_number TEXT,
ADD COLUMN IF NOT EXISTS document_title TEXT;

-- Update document_title from title if exists
UPDATE legal_documents
SET document_title = title
WHERE document_title IS NULL AND title IS NOT NULL;

-- Step 3: Convert metadata from TEXT to TEXT[] (arrays)
-- First, add new array columns
ALTER TABLE document_metadata
ADD COLUMN IF NOT EXISTS topic_tags_array TEXT[],
ADD COLUMN IF NOT EXISTS industries_array TEXT[],
ADD COLUMN IF NOT EXISTS tax_types_array TEXT[],
ADD COLUMN IF NOT EXISTS exemption_categories_array TEXT[],
ADD COLUMN IF NOT EXISTS product_types_array TEXT[],
ADD COLUMN IF NOT EXISTS keywords_array TEXT[],
ADD COLUMN IF NOT EXISTS referenced_statutes_array TEXT[];

-- Migrate data from TEXT to TEXT[] if old columns have data
UPDATE document_metadata
SET topic_tags_array = string_to_array(topic_tags, ',')
WHERE topic_tags IS NOT NULL AND topic_tags_array IS NULL;

UPDATE document_metadata
SET industries_array = string_to_array(industries, ',')
WHERE industries IS NOT NULL AND industries_array IS NULL;

UPDATE document_metadata
SET tax_types_array = string_to_array(tax_types, ',')
WHERE tax_types IS NOT NULL AND tax_types_array IS NULL;

-- Add custom_tags JSONB column
ALTER TABLE document_metadata
ADD COLUMN IF NOT EXISTS custom_tags JSONB DEFAULT '{}'::jsonb;

-- Step 4: Create vector index for fast similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 5: Create helper function for RAG search
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
    COALESCE(ld.document_title, ld.title) AS document_title,
    dc.chunk_text,
    dc.page_number,
    1 - (dc.embedding <=> query_embedding) as similarity
  FROM document_chunks dc
  JOIN legal_documents ld ON dc.document_id = ld.id
  WHERE
    dc.embedding IS NOT NULL
    AND (filter_doc_ids IS NULL OR dc.document_id = ANY(filter_doc_ids))
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Step 6: Create advanced search function with filters
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
    COALESCE(ld.document_title, ld.title) AS document_title,
    ld.source_type,
    ld.year_issued,
    dc.chunk_text,
    dc.page_number,
    1 - (dc.embedding <=> query_embedding) as similarity
  FROM document_chunks dc
  JOIN legal_documents ld ON dc.document_id = ld.id
  LEFT JOIN document_metadata dm ON ld.id = dm.document_id
  WHERE
    dc.embedding IS NOT NULL
    AND (source_types IS NULL OR ld.source_type = ANY(source_types))
    AND (year_from IS NULL OR ld.year_issued >= year_from)
    AND (year_to IS NULL OR ld.year_issued <= year_to)
    AND (topic_tags_filter IS NULL OR dm.topic_tags_array && topic_tags_filter)
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Step 7: Create useful indexes for performance
CREATE INDEX IF NOT EXISTS idx_legal_docs_source_type ON legal_documents(source_type);
CREATE INDEX IF NOT EXISTS idx_legal_docs_year_issued ON legal_documents(year_issued);
CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_line_items_invoice_id ON invoice_line_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);

-- Step 8: Create GIN indexes for array searches
CREATE INDEX IF NOT EXISTS idx_metadata_topic_tags
ON document_metadata USING GIN (topic_tags_array);

CREATE INDEX IF NOT EXISTS idx_metadata_tax_types
ON document_metadata USING GIN (tax_types_array);

CREATE INDEX IF NOT EXISTS idx_metadata_industries
ON document_metadata USING GIN (industries_array);

-- Step 9: Create helpful views
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

CREATE OR REPLACE VIEW v_document_summary AS
SELECT
    ld.id,
    COALESCE(ld.document_title, ld.title) as document_title,
    ld.source_type,
    ld.year_issued,
    ld.citation,
    dm.topic_tags_array as topic_tags,
    dm.tax_types_array as tax_types,
    dm.industries_array as industries,
    COUNT(dc.id) AS num_chunks
FROM legal_documents ld
LEFT JOIN document_metadata dm ON ld.id = dm.document_id
LEFT JOIN document_chunks dc ON ld.id = dc.document_id
GROUP BY ld.id, ld.document_title, ld.title, ld.source_type, ld.year_issued,
         ld.citation, dm.topic_tags_array, dm.tax_types_array, dm.industries_array;

-- ============================================
-- Verification Queries
-- ============================================

-- Check if pgvector is enabled
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Check if embedding column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'document_chunks' AND column_name = 'embedding';

-- Check if functions exist
SELECT routine_name
FROM information_schema.routines
WHERE routine_name IN ('match_documents', 'search_with_filters');

-- ============================================
-- Success! You should see:
-- 1. vector extension v0.x.x
-- 2. embedding column with type USER-DEFINED
-- 3. Both functions listed
-- ============================================
