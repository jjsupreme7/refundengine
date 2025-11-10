-- ============================================================================
-- VENDOR METADATA ENHANCEMENT MIGRATION
-- Adds rich vendor metadata fields to knowledge base schema
-- Safe to run - only adds new columns, doesn't modify existing data
-- ============================================================================

-- Purpose: Enhance vendor knowledge base with structured metadata for:
--   - Industry classification
--   - Business model identification
--   - Product/service cataloging
--   - Tax treatment hints
--   - Automated vendor research integration

-- ============================================================================
-- STEP 1: Add vendor metadata columns to knowledge_documents table
-- ============================================================================

ALTER TABLE knowledge_documents
ADD COLUMN IF NOT EXISTS industry TEXT,
ADD COLUMN IF NOT EXISTS business_model TEXT,
ADD COLUMN IF NOT EXISTS primary_products TEXT[],
ADD COLUMN IF NOT EXISTS typical_delivery TEXT,
ADD COLUMN IF NOT EXISTS tax_notes TEXT,
ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'manual';

-- Add comments for documentation
COMMENT ON COLUMN knowledge_documents.industry IS 'Primary industry/sector (e.g., Technology, Professional Services, Manufacturing)';
COMMENT ON COLUMN knowledge_documents.business_model IS 'Business model type (e.g., B2B SaaS, Manufacturing, Consulting, Retail)';
COMMENT ON COLUMN knowledge_documents.primary_products IS 'Array of main products/services offered';
COMMENT ON COLUMN knowledge_documents.typical_delivery IS 'How products/services are delivered (e.g., Cloud-based, On-premise, In-person)';
COMMENT ON COLUMN knowledge_documents.tax_notes IS 'Tax-relevant notes (e.g., Digital automated services, MPU analysis required)';
COMMENT ON COLUMN knowledge_documents.confidence_score IS 'Confidence in metadata accuracy (0.0-100.0, higher is better)';
COMMENT ON COLUMN knowledge_documents.data_source IS 'Source of metadata (manual, ai_research, web_scrape, pdf_extraction)';

-- ============================================================================
-- STEP 2: Add vendor metadata columns to vendor_background_chunks table
-- ============================================================================

ALTER TABLE vendor_background_chunks
ADD COLUMN IF NOT EXISTS industries TEXT[],
ADD COLUMN IF NOT EXISTS product_types TEXT[],
ADD COLUMN IF NOT EXISTS keywords TEXT[];

-- Add comments for documentation
COMMENT ON COLUMN vendor_background_chunks.industries IS 'Industries served or applicable to this vendor chunk';
COMMENT ON COLUMN vendor_background_chunks.product_types IS 'Product types mentioned in this chunk (e.g., software, hardware, services)';
COMMENT ON COLUMN vendor_background_chunks.keywords IS 'Relevant keywords extracted from chunk for search enhancement';

-- ============================================================================
-- STEP 3: Create indexes for performance
-- ============================================================================

-- Index for industry-based queries
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_industry
ON knowledge_documents(industry)
WHERE document_type = 'vendor_background';

-- Index for business model queries
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_business_model
ON knowledge_documents(business_model)
WHERE document_type = 'vendor_background';

-- Index for confidence score filtering (to find high-quality data)
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_confidence
ON knowledge_documents(confidence_score DESC)
WHERE document_type = 'vendor_background';

-- GIN indexes for array searches on chunks
CREATE INDEX IF NOT EXISTS idx_vendor_chunks_industries
ON vendor_background_chunks USING GIN (industries);

CREATE INDEX IF NOT EXISTS idx_vendor_chunks_product_types
ON vendor_background_chunks USING GIN (product_types);

CREATE INDEX IF NOT EXISTS idx_vendor_chunks_keywords
ON vendor_background_chunks USING GIN (keywords);

-- ============================================================================
-- STEP 4: Create helper view for vendor analysis
-- ============================================================================

CREATE OR REPLACE VIEW v_vendor_directory AS
SELECT
    kd.id,
    kd.vendor_name,
    kd.vendor_category,
    kd.industry,
    kd.business_model,
    kd.primary_products,
    kd.typical_delivery,
    kd.tax_notes,
    kd.confidence_score,
    kd.data_source,
    kd.total_chunks,
    kd.processing_status,
    kd.created_at,
    kd.updated_at
FROM knowledge_documents kd
WHERE kd.document_type = 'vendor_background'
ORDER BY kd.vendor_name;

COMMENT ON VIEW v_vendor_directory IS 'Vendor directory view showing all vendors with their metadata';

-- ============================================================================
-- STEP 5: Create helper function to search vendors by metadata
-- ============================================================================

CREATE OR REPLACE FUNCTION search_vendors_by_metadata(
    industry_filter TEXT DEFAULT NULL,
    business_model_filter TEXT DEFAULT NULL,
    min_confidence FLOAT DEFAULT 0.0
)
RETURNS TABLE (
    id UUID,
    vendor_name TEXT,
    vendor_category TEXT,
    industry TEXT,
    business_model TEXT,
    primary_products TEXT[],
    confidence_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kd.id,
        kd.vendor_name,
        kd.vendor_category,
        kd.industry,
        kd.business_model,
        kd.primary_products,
        kd.confidence_score
    FROM knowledge_documents kd
    WHERE kd.document_type = 'vendor_background'
        AND (industry_filter IS NULL OR kd.industry = industry_filter)
        AND (business_model_filter IS NULL OR kd.business_model = business_model_filter)
        AND kd.confidence_score >= min_confidence
    ORDER BY kd.confidence_score DESC, kd.vendor_name;
END;
$$;

COMMENT ON FUNCTION search_vendors_by_metadata IS 'Search vendors by industry, business model, and confidence score';

-- ============================================================================
-- STEP 6: Migration of existing static vendor data (if any)
-- ============================================================================

-- This would migrate data from vendor_database.json if you want to sync existing data
-- For now, this is a placeholder - we'll populate via the vendor research script

-- Example usage after migration:
-- INSERT INTO knowledge_documents (document_type, vendor_name, vendor_category, industry,
--                                   business_model, primary_products, typical_delivery,
--                                   tax_notes, confidence_score, data_source)
-- VALUES ('vendor_background', 'Microsoft', 'service_provider', 'Technology',
--         'B2B SaaS', ARRAY['Azure', 'Office 365', 'Dynamics'], 'Cloud-based',
--         'Digital automated services, MPU analysis required', 95.0, 'manual');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check new columns exist on knowledge_documents
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'knowledge_documents'
  AND column_name IN ('industry', 'business_model', 'primary_products', 'typical_delivery',
                      'tax_notes', 'confidence_score', 'data_source')
ORDER BY ordinal_position;

-- Check new columns exist on vendor_background_chunks
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'vendor_background_chunks'
  AND column_name IN ('industries', 'product_types', 'keywords')
ORDER BY ordinal_position;

-- Check new indexes exist
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('knowledge_documents', 'vendor_background_chunks')
  AND indexname LIKE '%vendor%' OR indexname LIKE '%industry%' OR indexname LIKE '%business_model%'
ORDER BY tablename, indexname;

-- Check view exists
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_name = 'v_vendor_directory';

-- Check function exists
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name = 'search_vendors_by_metadata';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✓ Vendor metadata enhancement migration completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Added to knowledge_documents:';
    RAISE NOTICE '  - industry (TEXT)';
    RAISE NOTICE '  - business_model (TEXT)';
    RAISE NOTICE '  - primary_products (TEXT[])';
    RAISE NOTICE '  - typical_delivery (TEXT)';
    RAISE NOTICE '  - tax_notes (TEXT)';
    RAISE NOTICE '  - confidence_score (FLOAT)';
    RAISE NOTICE '  - data_source (TEXT)';
    RAISE NOTICE '';
    RAISE NOTICE 'Added to vendor_background_chunks:';
    RAISE NOTICE '  - industries (TEXT[])';
    RAISE NOTICE '  - product_types (TEXT[])';
    RAISE NOTICE '  - keywords (TEXT[])';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - v_vendor_directory view';
    RAISE NOTICE '  - search_vendors_by_metadata() function';
    RAISE NOTICE '  - 6 new indexes for performance';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Run vendor research script to populate metadata';
    RAISE NOTICE '  2. Update ingestion scripts to use new fields';
    RAISE NOTICE '  3. Sync with vendor_database.json if needed';
    RAISE NOTICE '';
END $$;
