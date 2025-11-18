#!/bin/bash
# Deploy Historical Knowledge Schema
# Adds tables and columns needed for historical pattern learning

set -e  # Exit on error

echo "Deploying Historical Knowledge Schema..."

# Source environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required environment variables
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "Error: SUPABASE_DB_PASSWORD not set"
    exit 1
fi

# Run SQL migration
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
    -h aws-0-us-west-1.pooler.supabase.com \
    -p 6543 \
    -d postgres \
    -U postgres.bvrvzjqscrthfldyfqyo \
    << 'EOF'

-- ============================================================================
-- Historical Knowledge Schema Migration
-- ============================================================================

BEGIN;

-- 1. Create refund_citations table
-- Stores mappings: refund basis → legal citation
-- ============================================================================

CREATE TABLE IF NOT EXISTS refund_citations (
    id SERIAL PRIMARY KEY,
    refund_basis TEXT NOT NULL,
    legal_citation TEXT,
    usage_count INTEGER DEFAULT 0,
    example_cases TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(refund_basis)
);

CREATE INDEX IF NOT EXISTS idx_refund_citations_basis ON refund_citations(refund_basis);

COMMENT ON TABLE refund_citations IS 'Historical refund basis to legal citation mappings';
COMMENT ON COLUMN refund_citations.refund_basis IS 'Refund basis (e.g., MPU, Out-of-State Services)';
COMMENT ON COLUMN refund_citations.legal_citation IS 'Legal citation (e.g., RCW 82.04.067)';
COMMENT ON COLUMN refund_citations.usage_count IS 'Number of times this basis was used historically';
COMMENT ON COLUMN refund_citations.example_cases IS 'Example vendor cases using this basis';

-- 2. Enhance vendor_products table
-- Add columns for historical statistics
-- ============================================================================

DO $$
BEGIN
    -- Add historical_sample_count if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_products' AND column_name = 'historical_sample_count'
    ) THEN
        ALTER TABLE vendor_products ADD COLUMN historical_sample_count INTEGER DEFAULT 0;
    END IF;

    -- Add historical_success_rate if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_products' AND column_name = 'historical_success_rate'
    ) THEN
        ALTER TABLE vendor_products ADD COLUMN historical_success_rate DECIMAL(5,4) DEFAULT 0;
    END IF;

    -- Add typical_refund_basis if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_products' AND column_name = 'typical_refund_basis'
    ) THEN
        ALTER TABLE vendor_products ADD COLUMN typical_refund_basis TEXT;
    END IF;

    -- Add vendor_keywords for fuzzy matching if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_products' AND column_name = 'vendor_keywords'
    ) THEN
        ALTER TABLE vendor_products ADD COLUMN vendor_keywords TEXT[];
    END IF;

    -- Add description_keywords for pattern matching if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_products' AND column_name = 'description_keywords'
    ) THEN
        ALTER TABLE vendor_products ADD COLUMN description_keywords TEXT[];
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_vendor_products_success_rate ON vendor_products(historical_success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_vendor_keywords_gin ON vendor_products USING GIN (vendor_keywords);
CREATE INDEX IF NOT EXISTS idx_description_keywords_gin ON vendor_products USING GIN (description_keywords);

COMMENT ON COLUMN vendor_products.historical_sample_count IS 'Number of historical cases for this vendor';
COMMENT ON COLUMN vendor_products.historical_success_rate IS 'Historical refund success rate (0-1)';
COMMENT ON COLUMN vendor_products.typical_refund_basis IS 'Most common refund basis for this vendor';
COMMENT ON COLUMN vendor_products.vendor_keywords IS 'Keywords from vendor name for fuzzy matching (e.g., ["ATC", "TOWER", "SERVICES"])';
COMMENT ON COLUMN vendor_products.description_keywords IS 'Common keywords from product descriptions';

-- 3. Enhance vendor_product_patterns table
-- Add column for typical citation
-- ============================================================================

DO $$
BEGIN
    -- Add typical_citation if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_product_patterns' AND column_name = 'typical_citation'
    ) THEN
        ALTER TABLE vendor_product_patterns ADD COLUMN typical_citation TEXT;
    END IF;

    -- Add typical_basis if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_product_patterns' AND column_name = 'typical_basis'
    ) THEN
        ALTER TABLE vendor_product_patterns ADD COLUMN typical_basis TEXT;
    END IF;

    -- Add success_rate if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_product_patterns' AND column_name = 'success_rate'
    ) THEN
        ALTER TABLE vendor_product_patterns ADD COLUMN success_rate DECIMAL(5,4) DEFAULT 0;
    END IF;

    -- Add sample_count if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendor_product_patterns' AND column_name = 'sample_count'
    ) THEN
        ALTER TABLE vendor_product_patterns ADD COLUMN sample_count INTEGER DEFAULT 0;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_patterns_success_rate ON vendor_product_patterns(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_type_value ON vendor_product_patterns(pattern_type, pattern_value);

COMMENT ON COLUMN vendor_product_patterns.typical_citation IS 'Common legal citation for this pattern';
COMMENT ON COLUMN vendor_product_patterns.typical_basis IS 'Common refund basis for this pattern';
COMMENT ON COLUMN vendor_product_patterns.success_rate IS 'Historical success rate for this pattern';
COMMENT ON COLUMN vendor_product_patterns.sample_count IS 'Number of historical cases';

-- 4. Create helper view for high-confidence patterns
-- ============================================================================

CREATE OR REPLACE VIEW high_confidence_vendor_patterns AS
SELECT
    vendor_name,
    product_type,
    historical_sample_count,
    historical_success_rate,
    typical_refund_basis,
    CASE
        WHEN historical_success_rate >= 0.85 THEN 'Very High'
        WHEN historical_success_rate >= 0.70 THEN 'High'
        WHEN historical_success_rate >= 0.50 THEN 'Medium'
        ELSE 'Low'
    END as confidence_level
FROM vendor_products
WHERE historical_sample_count >= 10
ORDER BY historical_success_rate DESC, historical_sample_count DESC;

COMMENT ON VIEW high_confidence_vendor_patterns IS 'Vendors with high historical refund success rates';

-- 5. Create helper view for category patterns
-- ============================================================================

CREATE OR REPLACE VIEW high_confidence_category_patterns AS
SELECT
    pattern_type,
    pattern_value,
    success_rate,
    sample_count,
    typical_basis,
    typical_citation,
    CASE
        WHEN success_rate >= 0.85 THEN 'Very High'
        WHEN success_rate >= 0.70 THEN 'High'
        WHEN success_rate >= 0.50 THEN 'Medium'
        ELSE 'Low'
    END as confidence_level
FROM vendor_product_patterns
WHERE sample_count >= 10
ORDER BY success_rate DESC, sample_count DESC;

COMMENT ON VIEW high_confidence_category_patterns IS 'Category patterns with high historical success rates';

-- 6. Create keyword_patterns table
-- Stores description-based patterns for matching without Vertex codes
-- ============================================================================

CREATE TABLE IF NOT EXISTS keyword_patterns (
    id SERIAL PRIMARY KEY,
    keyword_signature TEXT NOT NULL,
    keywords TEXT[],
    success_rate DECIMAL(5,4) DEFAULT 0,
    sample_count INTEGER DEFAULT 0,
    typical_basis TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(keyword_signature)
);

CREATE INDEX IF NOT EXISTS idx_keyword_patterns_signature ON keyword_patterns(keyword_signature);
CREATE INDEX IF NOT EXISTS idx_keyword_patterns_keywords_gin ON keyword_patterns USING GIN (keywords);
CREATE INDEX IF NOT EXISTS idx_keyword_patterns_success_rate ON keyword_patterns(success_rate DESC);

COMMENT ON TABLE keyword_patterns IS 'Description-based patterns for matching without Vertex Category codes';
COMMENT ON COLUMN keyword_patterns.keyword_signature IS 'Unique signature from sorted keywords (e.g., "construction|services|tower")';
COMMENT ON COLUMN keyword_patterns.keywords IS 'Full list of keywords in this pattern';
COMMENT ON COLUMN keyword_patterns.success_rate IS 'Historical refund success rate for this keyword pattern';
COMMENT ON COLUMN keyword_patterns.sample_count IS 'Number of historical cases with this keyword pattern';
COMMENT ON COLUMN keyword_patterns.typical_basis IS 'Most common refund basis for this pattern';

-- 7. Grant permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON refund_citations TO authenticated;
GRANT SELECT, INSERT, UPDATE ON keyword_patterns TO authenticated;
GRANT SELECT ON high_confidence_vendor_patterns TO authenticated;
GRANT SELECT ON high_confidence_category_patterns TO authenticated;

COMMIT;

-- Print summary
SELECT 'Historical Knowledge Schema Deployed Successfully!' as status;
SELECT
    'Created refund_citations table' as action,
    COUNT(*) as count
FROM refund_citations;
SELECT
    'Enhanced vendor_products with historical stats' as action,
    COUNT(*) as vendors_with_history
FROM vendor_products
WHERE historical_sample_count > 0;
SELECT
    'Enhanced vendor_product_patterns' as action,
    COUNT(*) as patterns_with_stats
FROM vendor_product_patterns
WHERE sample_count > 0;
SELECT
    'Created keyword_patterns table' as action,
    COUNT(*) as count
FROM keyword_patterns;

EOF

echo "Historical Knowledge Schema deployment complete!"
echo ""
echo "Tables created/enhanced:"
echo "  - refund_citations (new)"
echo "  - keyword_patterns (new)"
echo "  - vendor_products (enhanced with vendor_keywords, description_keywords)"
echo "  - vendor_product_patterns (enhanced)"
echo ""
echo "Next steps:"
echo "1. Run: python scripts/import_historical_knowledge.py --file 'path/to/excel.xlsx' --dry-run"
echo "2. Review the dry run output"
echo "3. Run without --dry-run to actually import"
