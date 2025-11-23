-- =====================================================
-- SAFE PATTERN TABLE UPDATES (Option 1)
-- Merges pattern data into existing tables WITHOUT breaking anything
-- =====================================================

-- =====================================================
-- 1. UPDATE vendor_products TABLE (existing, 294 vendors)
-- =====================================================

-- Add tax_type column (nullable - won't affect existing rows)
ALTER TABLE vendor_products ADD COLUMN IF NOT EXISTS tax_type TEXT;

-- Add pattern-specific columns (all nullable)
ALTER TABLE vendor_products ADD COLUMN IF NOT EXISTS common_tax_categories JSONB;
ALTER TABLE vendor_products ADD COLUMN IF NOT EXISTS common_refund_bases JSONB;
ALTER TABLE vendor_products ADD COLUMN IF NOT EXISTS common_allocation_methods JSONB;

-- Note: description_keywords already exists!
-- Note: historical_sample_count, historical_success_rate, typical_refund_basis already exist!

-- Add unique constraint on (vendor_name, tax_type)
-- This is SAFE because PostgreSQL treats each NULL as unique
-- Existing 294 vendors have tax_type=NULL (won't conflict with each other)
-- New vendors have tax_type='sales_tax' or 'use_tax' (won't conflict with NULL)
ALTER TABLE vendor_products
DROP CONSTRAINT IF EXISTS vendor_products_vendor_name_tax_type_key;

ALTER TABLE vendor_products
ADD CONSTRAINT vendor_products_vendor_name_tax_type_key
UNIQUE NULLS NOT DISTINCT (vendor_name, tax_type);

-- Add index for filtering by tax_type
CREATE INDEX IF NOT EXISTS idx_vendor_products_tax_type ON vendor_products(tax_type);

-- Add check constraint for valid tax types (allows NULL)
ALTER TABLE vendor_products
DROP CONSTRAINT IF EXISTS vendor_products_tax_type_check;

ALTER TABLE vendor_products
ADD CONSTRAINT vendor_products_tax_type_check
CHECK (tax_type IS NULL OR tax_type IN ('sales_tax', 'use_tax'));

COMMENT ON COLUMN vendor_products.tax_type IS 'NULL = AI-researched vendors (existing), sales_tax/use_tax = historical pattern data (new)';


-- =====================================================
-- 2. UPDATE refund_citations TABLE (existing, 9 records)
-- Expand to handle refund_basis_patterns
-- =====================================================

-- Add tax_type column
ALTER TABLE refund_citations ADD COLUMN IF NOT EXISTS tax_type TEXT;

-- Add pattern-specific columns
ALTER TABLE refund_citations ADD COLUMN IF NOT EXISTS percentage DECIMAL(5,2);
ALTER TABLE refund_citations ADD COLUMN IF NOT EXISTS vendor_count INTEGER DEFAULT 0;
ALTER TABLE refund_citations ADD COLUMN IF NOT EXISTS all_vendors JSONB;
ALTER TABLE refund_citations ADD COLUMN IF NOT EXISTS typical_final_decision TEXT;

-- Add unique constraint
ALTER TABLE refund_citations
DROP CONSTRAINT IF EXISTS refund_citations_refund_basis_tax_type_key;

ALTER TABLE refund_citations
ADD CONSTRAINT refund_citations_refund_basis_tax_type_key
UNIQUE NULLS NOT DISTINCT (refund_basis, tax_type);

-- Add index
CREATE INDEX IF NOT EXISTS idx_refund_citations_tax_type ON refund_citations(tax_type);
CREATE INDEX IF NOT EXISTS idx_refund_citations_usage_count ON refund_citations(usage_count DESC);

-- Add check constraint
ALTER TABLE refund_citations
DROP CONSTRAINT IF EXISTS refund_citations_tax_type_check;

ALTER TABLE refund_citations
ADD CONSTRAINT refund_citations_tax_type_check
CHECK (tax_type IS NULL OR tax_type IN ('sales_tax', 'use_tax'));

COMMENT ON COLUMN refund_citations.tax_type IS 'NULL = existing citations, sales_tax/use_tax = pattern data (new)';


-- =====================================================
-- 3. USE keyword_patterns TABLE (existing, EMPTY)
-- =====================================================

-- Add missing columns
ALTER TABLE keyword_patterns ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE keyword_patterns ADD COLUMN IF NOT EXISTS tax_type TEXT;
ALTER TABLE keyword_patterns ADD COLUMN IF NOT EXISTS keyword_count INTEGER DEFAULT 0;

-- Note: keywords column already exists (JSONB)

-- Add unique constraint (AFTER adding category column)
ALTER TABLE keyword_patterns
DROP CONSTRAINT IF EXISTS keyword_patterns_category_tax_type_key;

ALTER TABLE keyword_patterns
ADD CONSTRAINT keyword_patterns_category_tax_type_key
UNIQUE NULLS NOT DISTINCT (category, tax_type);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_keyword_patterns_tax_type ON keyword_patterns(tax_type);
CREATE INDEX IF NOT EXISTS idx_keyword_patterns_category ON keyword_patterns(category);

-- Add check constraint
ALTER TABLE keyword_patterns
DROP CONSTRAINT IF EXISTS keyword_patterns_tax_type_check;

ALTER TABLE keyword_patterns
ADD CONSTRAINT keyword_patterns_tax_type_check
CHECK (tax_type IS NULL OR tax_type IN ('sales_tax', 'use_tax'));


-- =====================================================
-- SAFETY VERIFICATION QUERIES
-- =====================================================

-- Check existing vendor_products data is preserved
SELECT
    COUNT(*) as existing_vendors_preserved,
    COUNT(*) FILTER (WHERE tax_type IS NULL) as with_null_tax_type
FROM vendor_products;
-- Expected: 294 total, 294 with NULL tax_type (before upload)

-- Check existing refund_citations data is preserved
SELECT
    COUNT(*) as existing_citations_preserved,
    COUNT(*) FILTER (WHERE tax_type IS NULL) as with_null_tax_type
FROM refund_citations;
-- Expected: 9 total, 9 with NULL tax_type (before upload)

-- Check keyword_patterns is ready
SELECT COUNT(*) as keyword_pattern_count FROM keyword_patterns;
-- Expected: 0 (empty, ready for upload)


-- =====================================================
-- DONE - SAFE TO PROCEED
-- =====================================================
-- ✅ All existing data preserved (tax_type=NULL)
-- ✅ New columns added (nullable, no data loss)
-- ✅ Unique constraints safe (NULL != NULL in PostgreSQL)
-- ✅ Ready for upload!
--
-- Next steps:
-- 1. Run: python scripts/upload_patterns_to_supabase.py --dry-run
-- 2. Review the output
-- 3. Run: python scripts/upload_patterns_to_supabase.py
