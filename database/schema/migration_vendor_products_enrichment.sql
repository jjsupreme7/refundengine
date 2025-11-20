-- ============================================================================
-- VENDOR PRODUCTS ENRICHMENT MIGRATION
-- Adds detailed product and industry metadata to vendor_products table
-- Safe to run - only adds new columns, doesn't modify existing data
-- ============================================================================

-- Purpose: Enhance vendor_products with detailed business intelligence:
--   - Industry classification
--   - Business model identification
--   - Detailed product catalog (JSONB)
--   - Delivery methods
--   - WA tax classification
--   - Research metadata

BEGIN;

-- ============================================================================
-- STEP 1: Add new metadata columns
-- ============================================================================

ALTER TABLE vendor_products
ADD COLUMN IF NOT EXISTS industry TEXT,
ADD COLUMN IF NOT EXISTS business_model TEXT,
ADD COLUMN IF NOT EXISTS primary_products JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS typical_delivery TEXT,
ADD COLUMN IF NOT EXISTS wa_tax_classification TEXT,
ADD COLUMN IF NOT EXISTS research_notes TEXT,
ADD COLUMN IF NOT EXISTS web_research_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS data_quality_score FLOAT DEFAULT 0.0;

-- Add column comments
COMMENT ON COLUMN vendor_products.industry IS 'Primary industry (e.g., Cybersecurity, Workforce Management, Professional Services)';
COMMENT ON COLUMN vendor_products.business_model IS 'Business model (e.g., B2B SaaS, B2B Consulting, Manufacturing, Wholesale)';
COMMENT ON COLUMN vendor_products.primary_products IS 'JSONB array of products with type, delivery, description';
COMMENT ON COLUMN vendor_products.typical_delivery IS 'How products are delivered (e.g., Cloud-based, On-premise, Human-delivered)';
COMMENT ON COLUMN vendor_products.wa_tax_classification IS 'WA tax classification (e.g., digital_automated_service, professional_services, tangible_property)';
COMMENT ON COLUMN vendor_products.research_notes IS 'Additional notes from research (acquisitions, name changes, etc.)';
COMMENT ON COLUMN vendor_products.web_research_date IS 'When web research was last performed';
COMMENT ON COLUMN vendor_products.data_quality_score IS 'Quality score 0-100 based on data completeness and confidence';

-- ============================================================================
-- STEP 2: Create indexes for new columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_vendor_products_industry
ON vendor_products(industry)
WHERE industry IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_vendor_products_business_model
ON vendor_products(business_model)
WHERE business_model IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_vendor_products_wa_tax_class
ON vendor_products(wa_tax_classification)
WHERE wa_tax_classification IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_vendor_products_data_quality
ON vendor_products(data_quality_score DESC)
WHERE data_quality_score > 0;

-- GIN index for JSONB products search
CREATE INDEX IF NOT EXISTS idx_vendor_products_primary_products_gin
ON vendor_products USING GIN (primary_products);

-- ============================================================================
-- STEP 3: Create enhanced vendor directory view
-- ============================================================================

CREATE OR REPLACE VIEW v_vendor_intelligence AS
SELECT
    v.id,
    v.vendor_name,
    v.industry,
    v.business_model,
    v.primary_products,
    v.product_description,
    v.product_type,
    v.typical_delivery,
    v.wa_tax_classification,
    v.tax_treatment,
    v.typical_refund_basis,
    v.historical_sample_count,
    v.historical_success_rate,
    v.typical_refund_percentage,
    v.vendor_keywords,
    v.description_keywords,
    v.confidence_score,
    v.data_quality_score,
    v.learning_source,
    v.web_research_date,
    v.research_notes,
    v.created_at,
    v.updated_at,
    -- Computed fields
    CASE
        WHEN v.historical_sample_count >= 50 AND v.historical_success_rate >= 0.8 THEN 'very_high'
        WHEN v.historical_sample_count >= 20 AND v.historical_success_rate >= 0.7 THEN 'high'
        WHEN v.historical_sample_count >= 10 AND v.historical_success_rate >= 0.5 THEN 'medium'
        WHEN v.historical_sample_count >= 5 THEN 'low'
        ELSE 'very_low'
    END as value_tier,
    CASE
        WHEN v.industry IS NOT NULL AND v.primary_products IS NOT NULL AND jsonb_array_length(v.primary_products) > 0 THEN 'complete'
        WHEN v.industry IS NOT NULL OR v.primary_products IS NOT NULL THEN 'partial'
        ELSE 'none'
    END as research_status
FROM vendor_products v
ORDER BY v.historical_success_rate DESC NULLS LAST, v.historical_sample_count DESC;

COMMENT ON VIEW v_vendor_intelligence IS 'Comprehensive vendor intelligence view with historical performance and product data';

-- ============================================================================
-- STEP 4: Create helper function to calculate data quality score
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_vendor_data_quality(vendor_id UUID)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
DECLARE
    quality_score FLOAT := 0.0;
    v RECORD;
BEGIN
    SELECT * INTO v FROM vendor_products WHERE id = vendor_id;

    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;

    -- Base score components (out of 100)

    -- Has vendor name (required, 5 points)
    IF v.vendor_name IS NOT NULL AND length(v.vendor_name) > 0 THEN
        quality_score := quality_score + 5;
    END IF;

    -- Has industry (15 points)
    IF v.industry IS NOT NULL AND length(v.industry) > 0 THEN
        quality_score := quality_score + 15;
    END IF;

    -- Has business model (10 points)
    IF v.business_model IS NOT NULL AND length(v.business_model) > 0 THEN
        quality_score := quality_score + 10;
    END IF;

    -- Has primary products (20 points for JSONB array with items)
    IF v.primary_products IS NOT NULL AND jsonb_array_length(v.primary_products) > 0 THEN
        quality_score := quality_score + 20;
    END IF;

    -- Has product description (10 points)
    IF v.product_description IS NOT NULL AND length(v.product_description) > 10 THEN
        quality_score := quality_score + 10;
    END IF;

    -- Has WA tax classification (15 points)
    IF v.wa_tax_classification IS NOT NULL AND length(v.wa_tax_classification) > 0 THEN
        quality_score := quality_score + 15;
    END IF;

    -- Has typical delivery (5 points)
    IF v.typical_delivery IS NOT NULL AND length(v.typical_delivery) > 0 THEN
        quality_score := quality_score + 5;
    END IF;

    -- Has historical data (10 points)
    IF v.historical_sample_count IS NOT NULL AND v.historical_sample_count > 0 THEN
        quality_score := quality_score + 10;
    END IF;

    -- Has vendor keywords (5 points)
    IF v.vendor_keywords IS NOT NULL AND array_length(v.vendor_keywords, 1) > 0 THEN
        quality_score := quality_score + 5;
    END IF;

    -- Has web research date (5 points - indicates freshness)
    IF v.web_research_date IS NOT NULL THEN
        quality_score := quality_score + 5;
    END IF;

    RETURN quality_score;
END;
$$;

COMMENT ON FUNCTION calculate_vendor_data_quality IS 'Calculate data quality score (0-100) based on completeness of vendor information';

-- ============================================================================
-- STEP 5: Create function to bulk update data quality scores
-- ============================================================================

CREATE OR REPLACE FUNCTION update_all_vendor_data_quality_scores()
RETURNS TABLE (
    vendor_id UUID,
    vendor_name TEXT,
    old_score FLOAT,
    new_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    UPDATE vendor_products v
    SET data_quality_score = calculate_vendor_data_quality(v.id)
    RETURNING
        v.id,
        v.vendor_name,
        v.data_quality_score as old_score,
        calculate_vendor_data_quality(v.id) as new_score;
END;
$$;

COMMENT ON FUNCTION update_all_vendor_data_quality_scores IS 'Recalculate and update data quality scores for all vendors';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check new columns exist
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'vendor_products'
  AND column_name IN ('industry', 'business_model', 'primary_products', 'typical_delivery',
                      'wa_tax_classification', 'research_notes', 'web_research_date', 'data_quality_score')
ORDER BY ordinal_position;

-- Check new indexes exist
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'vendor_products'
  AND indexname LIKE '%industry%'
   OR indexname LIKE '%business_model%'
   OR indexname LIKE '%tax_class%'
   OR indexname LIKE '%quality%'
   OR indexname LIKE '%products_gin%'
ORDER BY indexname;

-- Check view exists
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_name = 'v_vendor_intelligence';

-- Check functions exist
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name IN ('calculate_vendor_data_quality', 'update_all_vendor_data_quality_scores')
ORDER BY routine_name;

COMMIT;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✓ Vendor products enrichment migration completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'New columns added to vendor_products:';
    RAISE NOTICE '  - industry (TEXT)';
    RAISE NOTICE '  - business_model (TEXT)';
    RAISE NOTICE '  - primary_products (JSONB)';
    RAISE NOTICE '  - typical_delivery (TEXT)';
    RAISE NOTICE '  - wa_tax_classification (TEXT)';
    RAISE NOTICE '  - research_notes (TEXT)';
    RAISE NOTICE '  - web_research_date (TIMESTAMPTZ)';
    RAISE NOTICE '  - data_quality_score (FLOAT)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - v_vendor_intelligence view (comprehensive vendor data)';
    RAISE NOTICE '  - calculate_vendor_data_quality() function';
    RAISE NOTICE '  - update_all_vendor_data_quality_scores() function';
    RAISE NOTICE '  - 5 new indexes for performance';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Run vendor research script to populate metadata';
    RAISE NOTICE '  2. Run: SELECT update_all_vendor_data_quality_scores();';
    RAISE NOTICE '  3. Query: SELECT * FROM v_vendor_intelligence WHERE research_status = ''complete'';';
    RAISE NOTICE '';
END $$;
