-- ============================================================================
-- Migration 003: Add SQL Documentation Comments
-- Created: 2025-11-12
-- Purpose: Add inline documentation to all database objects
-- ============================================================================
--
-- This migration adds COMMENT statements to document:
-- - What each table is for
-- - What each column stores
-- - What each function does
-- - Which objects are current vs deprecated
--
-- Benefits:
-- - Self-documenting database
-- - Clear for new developers
-- - Visible in database tools (pgAdmin, DataGrip, etc.)
-- - Helps maintain consistency
-- ============================================================================

-- ============================================================================
-- TABLES: Master Documents
-- ============================================================================

COMMENT ON TABLE knowledge_documents IS
'✅ CURRENT - Master registry of all knowledge base documents.
Stores metadata for tax law documents (RCW/WAC) and vendor product documentation.
Links to tax_law_chunks (if document_type=''tax_law'') or vendor_background_chunks (if document_type=''vendor_background'').
Replaces old legal_documents table.';

COMMENT ON COLUMN knowledge_documents.id IS
'Primary key (UUID). Generated automatically.';

COMMENT ON COLUMN knowledge_documents.document_type IS
'Document category: ''tax_law'' for legal documents or ''vendor_background'' for vendor/product docs.';

COMMENT ON COLUMN knowledge_documents.title IS
'Human-readable document title. Example: "Computer Software - Sales and Use Tax"';

COMMENT ON COLUMN knowledge_documents.citation IS
'Official citation for tax law (e.g., "WAC 458-20-15502" or "RCW 82.04.050"). NULL for vendor docs.';

COMMENT ON COLUMN knowledge_documents.law_category IS
'Category for tax law: exemption, rate, definition, software, digital_goods, manufacturing, etc.';

COMMENT ON COLUMN knowledge_documents.vendor_name IS
'Vendor name for vendor_background documents (e.g., "Microsoft", "Amazon"). NULL for tax law.';

COMMENT ON COLUMN knowledge_documents.source_file IS
'Original file path where PDF was located (e.g., "knowledge_base/states/washington/legal_documents/WAC_458-20-15502.pdf")';

COMMENT ON COLUMN knowledge_documents.file_url IS
'Public URL to access document. Can be Supabase Storage URL, official legislature URL, or vendor URL.';

COMMENT ON COLUMN knowledge_documents.processing_status IS
'Processing state: pending → processing → completed or error. Tracks ingestion progress.';

COMMENT ON COLUMN knowledge_documents.total_chunks IS
'Number of text chunks generated from this document. Typically 50-200 chunks per document.';

COMMENT ON COLUMN knowledge_documents.effective_date IS
'Date the law took effect (for tax law) or document publication date (for vendor docs).';

-- ============================================================================
-- TABLES: Tax Law Chunks
-- ============================================================================

COMMENT ON TABLE tax_law_chunks IS
'✅ CURRENT - Text chunks from tax law documents with vector embeddings.
Each row is a searchable segment (500-1500 words) from a tax law document.
Embeddings enable semantic search via search_tax_law() function.
Replaces old document_chunks table.';

COMMENT ON COLUMN tax_law_chunks.id IS
'Primary key (UUID).';

COMMENT ON COLUMN tax_law_chunks.document_id IS
'Foreign key to knowledge_documents.id. Links chunk to parent document.';

COMMENT ON COLUMN tax_law_chunks.chunk_number IS
'Sequential number within document (1, 2, 3...). Preserves reading order.';

COMMENT ON COLUMN tax_law_chunks.chunk_text IS
'Actual text content of the chunk (500-1500 words). Full searchable text.';

COMMENT ON COLUMN tax_law_chunks.embedding IS
'1536-dimension vector from OpenAI text-embedding-3-small model. Used for semantic similarity search.';

COMMENT ON COLUMN tax_law_chunks.citation IS
'RCW/WAC reference (denormalized from parent document for faster queries). Example: "WAC 458-20-15502"';

COMMENT ON COLUMN tax_law_chunks.section_title IS
'Section heading and page number. Format: "Section heading text (Page X)". Helps locate text in original PDF.';

COMMENT ON COLUMN tax_law_chunks.law_category IS
'Category (denormalized from parent). Values: exemption, rate, software, digital_goods, manufacturing, general, etc.';

COMMENT ON COLUMN tax_law_chunks.hierarchy_level IS
'Nesting level in document structure. 1 = top level, 2 = subsection, 3 = sub-subsection, etc.';

COMMENT ON COLUMN tax_law_chunks.parent_section IS
'Reference to parent section for nested content. Example: "Section 1" for "Section 1(a)".';

-- ============================================================================
-- TABLES: Vendor Background Chunks
-- ============================================================================

COMMENT ON TABLE vendor_background_chunks IS
'✅ CURRENT - Text chunks from vendor/product documentation with vector embeddings.
Stores product catalogs, specs, manuals for vendor research.
Separate from tax law for cleaner organization and metadata.';

COMMENT ON COLUMN vendor_background_chunks.id IS
'Primary key (UUID).';

COMMENT ON COLUMN vendor_background_chunks.document_id IS
'Foreign key to knowledge_documents.id.';

COMMENT ON COLUMN vendor_background_chunks.chunk_number IS
'Sequential number within document.';

COMMENT ON COLUMN vendor_background_chunks.chunk_text IS
'Actual text content (500-1500 words).';

COMMENT ON COLUMN vendor_background_chunks.embedding IS
'1536-dimension vector from OpenAI text-embedding-3-small.';

COMMENT ON COLUMN vendor_background_chunks.vendor_name IS
'Vendor name (denormalized). Example: "Microsoft", "Amazon".';

COMMENT ON COLUMN vendor_background_chunks.vendor_category IS
'Vendor type: manufacturer, distributor, retailer, service_provider, etc.';

COMMENT ON COLUMN vendor_background_chunks.document_category IS
'Document type: catalog, specification, manual, contract, etc.';

COMMENT ON COLUMN vendor_background_chunks.product_categories IS
'Array of product categories. Example: {software, cloud_services, SaaS}. Enables multi-category filtering.';

-- ============================================================================
-- FUNCTIONS: Current Vector Search Functions
-- ============================================================================

COMMENT ON FUNCTION search_tax_law(vector, float, int, text) IS
'✅ CURRENT - Search tax law chunks using vector similarity.

Usage:
  SELECT * FROM search_tax_law(
    query_embedding := ''[0.1, 0.2, ...]''::vector(1536),
    match_threshold := 0.7,
    match_count := 5,
    law_category_filter := ''software''
  );

Parameters:
  - query_embedding: 1536-dim vector from OpenAI text-embedding-3-small
  - match_threshold: Minimum similarity (0-1). Higher = stricter. Recommended: 0.5-0.8
  - match_count: Max results to return. Recommended: 3-10
  - law_category_filter: Optional category filter (software, exemption, etc.)

Returns:
  - id, document_id, chunk_text, citation, section_title, law_category, file_url, similarity

Algorithm:
  Calculates cosine similarity: 1 - (embedding <=> query_embedding)
  Filters by threshold and optional category
  Returns top N most similar chunks ordered by similarity';

COMMENT ON FUNCTION search_vendor_background(vector, float, int, text) IS
'✅ CURRENT - Search vendor documentation using vector similarity.

Similar to search_tax_law() but searches vendor_background_chunks table.
Supports optional vendor name filtering.

Returns: id, chunk_text, vendor_name, similarity, document_category, vendor_category';

COMMENT ON FUNCTION search_knowledge_base(vector, float, int, int) IS
'✅ CURRENT - Combined search across both tax law AND vendor documentation.

Usage:
  SELECT * FROM search_knowledge_base(
    query_embedding := ''[0.1, ...]''::vector(1536),
    match_threshold := 0.5,
    tax_law_count := 3,
    vendor_bg_count := 2
  );

Returns:
  Combined results from both tax_law_chunks and vendor_background_chunks,
  deduplicated and sorted by similarity. Useful for broad research queries.';

-- ============================================================================
-- DEPRECATED OBJECTS
-- ============================================================================

COMMENT ON VIEW legal_chunks IS
'⚠️ DEPRECATED - Compatibility view redirecting to tax_law_chunks.
For migration purposes only. Will be removed in 90 days.
Use tax_law_chunks table directly instead.';

COMMENT ON FUNCTION match_legal_chunks(vector, float, int) IS
'⚠️ DEPRECATED - Old search function redirecting to search_tax_law().
For migration purposes only. Will be removed in 90 days.
Use search_tax_law() instead.
Deprecation date: 2025-11-12';

COMMENT ON FUNCTION match_documents(vector, float, int) IS
'⚠️ DEPRECATED - Old search function redirecting to new schema.
For migration purposes only. Will be removed in 90 days.
Use search_knowledge_base() instead.
Deprecation date: 2025-11-12';

-- ============================================================================
-- INDEXES (Documentation)
-- ============================================================================

COMMENT ON INDEX idx_tax_chunks_embedding IS
'Vector similarity search index (IVFFlat). Enables fast approximate nearest neighbor search for semantic queries.';

COMMENT ON INDEX idx_tax_chunks_document_id IS
'Foreign key index for joining chunks to documents. Speeds up queries like "get all chunks for document X".';

COMMENT ON INDEX idx_tax_chunks_citation IS
'Filter index for citation searches. Example: WHERE citation = ''WAC 458-20-15502''';

COMMENT ON INDEX idx_tax_chunks_law_category IS
'Filter index for category searches. Example: WHERE law_category = ''software''';

-- ============================================================================
-- SUCCESS VERIFICATION
-- ============================================================================

-- Run these queries to verify comments were added:

-- Check table comments
SELECT
    c.relname as table_name,
    pg_catalog.obj_description(c.oid) as table_comment
FROM pg_catalog.pg_class c
WHERE c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  AND c.relkind = 'r'
  AND c.relname IN ('knowledge_documents', 'tax_law_chunks', 'vendor_background_chunks')
ORDER BY c.relname;

-- Check function comments
SELECT
    p.proname as function_name,
    pg_catalog.obj_description(p.oid) as function_comment
FROM pg_catalog.pg_proc p
WHERE p.pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  AND p.proname LIKE '%search%'
ORDER BY p.proname;

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- If needed, run this to remove all comments:
/*
COMMENT ON TABLE knowledge_documents IS NULL;
COMMENT ON TABLE tax_law_chunks IS NULL;
COMMENT ON TABLE vendor_background_chunks IS NULL;
COMMENT ON FUNCTION search_tax_law IS NULL;
COMMENT ON FUNCTION search_vendor_background IS NULL;
COMMENT ON FUNCTION search_knowledge_base IS NULL;
-- ... etc for all objects
*/
