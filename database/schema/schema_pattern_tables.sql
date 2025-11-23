-- =====================================================
-- PATTERN TABLES FOR HISTORICAL INTELLIGENCE
-- =====================================================
-- Run this in Supabase SQL Editor to create the tables

-- =====================================================
-- 1. VENDOR PATTERNS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS vendor_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_name TEXT NOT NULL,
    tax_type TEXT NOT NULL CHECK (tax_type IN ('sales_tax', 'use_tax')),

    -- Historical metrics
    historical_sample_count INTEGER DEFAULT 0,
    historical_success_rate DECIMAL(5,4), -- 0.0000 to 1.0000

    -- Typical patterns
    typical_refund_basis TEXT,
    typical_final_decision TEXT,

    -- Categories and keywords (JSONB for flexibility)
    common_tax_categories JSONB, -- ["Services", "Hardware", ...]
    common_refund_bases JSONB, -- ["MPU", "Non-taxable", ...]
    description_keywords JSONB, -- ["cloud", "hosting", ...]
    common_allocation_methods JSONB,

    -- Product type (from Phase 2 data)
    product_type TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one record per vendor per tax type
    UNIQUE(vendor_name, tax_type)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_vendor_name ON vendor_patterns(vendor_name);
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_tax_type ON vendor_patterns(tax_type);
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_vendor_tax ON vendor_patterns(vendor_name, tax_type);

-- RLS Policies (adjust based on your auth setup)
ALTER TABLE vendor_patterns ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read
CREATE POLICY IF NOT EXISTS "Allow authenticated users to read vendor patterns"
ON vendor_patterns FOR SELECT
TO authenticated
USING (true);

-- Allow service role to insert/update
CREATE POLICY IF NOT EXISTS "Allow service role to manage vendor patterns"
ON vendor_patterns FOR ALL
TO service_role
USING (true)
WITH CHECK (true);


-- =====================================================
-- 2. REFUND BASIS PATTERNS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS refund_basis_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    refund_basis TEXT NOT NULL,
    tax_type TEXT NOT NULL CHECK (tax_type IN ('sales_tax', 'use_tax')),

    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    percentage DECIMAL(5,2), -- 0.00 to 100.00

    -- Vendor information
    vendor_count INTEGER DEFAULT 0,
    all_vendors JSONB, -- Complete list: ["VENDOR A", "VENDOR B", ...]

    -- Common outcomes
    typical_final_decision TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique per refund basis per tax type
    UNIQUE(refund_basis, tax_type)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_refund_basis_patterns_tax_type ON refund_basis_patterns(tax_type);
CREATE INDEX IF NOT EXISTS idx_refund_basis_patterns_refund_basis ON refund_basis_patterns(refund_basis);
CREATE INDEX IF NOT EXISTS idx_refund_basis_patterns_usage_count ON refund_basis_patterns(usage_count DESC);

-- RLS Policies
ALTER TABLE refund_basis_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Allow authenticated users to read refund basis patterns"
ON refund_basis_patterns FOR SELECT
TO authenticated
USING (true);

CREATE POLICY IF NOT EXISTS "Allow service role to manage refund basis patterns"
ON refund_basis_patterns FOR ALL
TO service_role
USING (true)
WITH CHECK (true);


-- =====================================================
-- 3. KEYWORD PATTERNS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS keyword_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL, -- 'tax_categories', 'product_types', 'description_keywords'
    tax_type TEXT NOT NULL CHECK (tax_type IN ('sales_tax', 'use_tax')),

    -- Keywords as JSONB array
    keywords JSONB, -- ["keyword1", "keyword2", ...]
    keyword_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique per category per tax type
    UNIQUE(category, tax_type)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_keyword_patterns_category ON keyword_patterns(category);
CREATE INDEX IF NOT EXISTS idx_keyword_patterns_tax_type ON keyword_patterns(tax_type);

-- RLS Policies
ALTER TABLE keyword_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Allow authenticated users to read keyword patterns"
ON keyword_patterns FOR SELECT
TO authenticated
USING (true);

CREATE POLICY IF NOT EXISTS "Allow service role to manage keyword patterns"
ON keyword_patterns FOR ALL
TO service_role
USING (true)
WITH CHECK (true);


-- =====================================================
-- 4. UPDATE PROJECTS TABLE (add tax_type if missing)
-- =====================================================
-- Check if projects table exists and add tax_type column if missing
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'projects') THEN
        -- Add column if it doesn't exist
        IF NOT EXISTS (SELECT FROM information_schema.columns
                       WHERE table_schema = 'public'
                       AND table_name = 'projects'
                       AND column_name = 'tax_type') THEN
            ALTER TABLE projects ADD COLUMN tax_type TEXT CHECK (tax_type IN ('sales_tax', 'use_tax'));
            CREATE INDEX IF NOT EXISTS idx_projects_tax_type ON projects(tax_type);
            RAISE NOTICE 'Added tax_type column to projects table';
        ELSE
            RAISE NOTICE 'projects.tax_type column already exists';
        END IF;
    ELSE
        RAISE NOTICE 'projects table does not exist - skipping';
    END IF;
END $$;


-- =====================================================
-- DONE
-- =====================================================
-- Tables created successfully!
--
-- Next steps:
-- 1. Run: python scripts/upload_patterns_to_supabase.py --dry-run
-- 2. Review the output
-- 3. Run: python scripts/upload_patterns_to_supabase.py
