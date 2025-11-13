-- ============================================================================
-- Migration 003: Analysis & Learning Tables
-- Created: 2025-11-12
-- Purpose: Set up tables for invoice/PO analysis workflow
-- ============================================================================
--
-- This migration creates the tables needed for:
-- 1. Storing refund analysis results
-- 2. Human review and corrections
-- 3. Vendor pattern learning
-- 4. Audit trail for changes
--
-- SAFE TO RUN: This migration is idempotent (can run multiple times)
-- ============================================================================

-- ============================================================================
-- STEP 1: Create analysis_results table
-- ============================================================================
-- Stores AI analysis of each invoice line item from Excel

CREATE TABLE IF NOT EXISTS analysis_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Excel/Source data
    row_id integer NOT NULL,
    vendor_name text NOT NULL,
    invoice_number text,
    po_number text,

    -- Financial data
    amount decimal(12,2) NOT NULL,
    tax_amount decimal(12,2) NOT NULL,

    -- AI Analysis results
    ai_product_desc text,
    ai_product_type text,
    ai_product_details text,
    ai_refund_basis text,
    ai_exemption_type text,
    ai_citation text,
    ai_confidence integer CHECK (ai_confidence >= 0 AND ai_confidence <= 100),
    ai_refund_percentage decimal(5,2),
    ai_estimated_refund decimal(12,2),
    ai_explanation text,
    ai_key_factors text,

    -- Supporting documents
    invoice_files text[],
    po_files text[],

    -- Status tracking
    analysis_status text DEFAULT 'pending_review'
        CHECK (analysis_status IN ('pending_review', 'approved', 'corrected', 'rejected')),

    -- Timestamps
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_analysis_results_vendor ON analysis_results(vendor_name);
CREATE INDEX IF NOT EXISTS idx_analysis_results_status ON analysis_results(analysis_status);
CREATE INDEX IF NOT EXISTS idx_analysis_results_row_id ON analysis_results(row_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_invoice ON analysis_results(invoice_number);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_analysis_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_analysis_results_updated_at ON analysis_results;
CREATE TRIGGER trigger_update_analysis_results_updated_at
    BEFORE UPDATE ON analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION update_analysis_results_updated_at();

COMMENT ON TABLE analysis_results IS
'Stores AI analysis results for each invoice line item. Each row represents one line from the Excel file that has been analyzed for refund eligibility.';

SELECT '✅ Step 1 complete: analysis_results table created' as status;


-- ============================================================================
-- STEP 2: Create analysis_reviews table
-- ============================================================================
-- Stores human corrections and reviews of AI analysis

CREATE TABLE IF NOT EXISTS analysis_reviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to original analysis
    analysis_id uuid REFERENCES analysis_results(id) ON DELETE CASCADE,
    row_id integer NOT NULL,

    -- Review status
    review_status text NOT NULL
        CHECK (review_status IN ('approved', 'corrected', 'rejected')),

    -- Corrected values (only if status = 'corrected')
    corrected_product_desc text,
    corrected_product_type text,
    corrected_refund_basis text,
    corrected_citation text,
    corrected_refund_percentage decimal(5,2),
    corrected_estimated_refund decimal(12,2),

    -- Fields that were corrected
    fields_corrected text[],

    -- Review metadata
    reviewer_notes text,
    reviewed_by text NOT NULL,
    reviewed_at timestamptz DEFAULT now(),

    -- Timestamps
    created_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_analysis_reviews_analysis_id ON analysis_reviews(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_reviews_status ON analysis_reviews(review_status);
CREATE INDEX IF NOT EXISTS idx_analysis_reviews_reviewed_by ON analysis_reviews(reviewed_by);

COMMENT ON TABLE analysis_reviews IS
'Human review and corrections for AI analysis. When a human corrects an analysis, this table stores what was changed and why.';

SELECT '✅ Step 2 complete: analysis_reviews table created' as status;


-- ============================================================================
-- STEP 3: Create vendor_products table
-- ============================================================================
-- Learning database: stores known vendor products for faster analysis

CREATE TABLE IF NOT EXISTS vendor_products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Vendor and product info
    vendor_name text NOT NULL,
    product_description text NOT NULL,
    product_type text,

    -- Tax treatment info
    tax_treatment text,
    typical_refund_percentage decimal(5,2),

    -- Learning metadata
    learning_source text DEFAULT 'ai_analysis'
        CHECK (learning_source IN ('ai_analysis', 'human_correction', 'manual_entry')),
    confidence_score decimal(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 100),

    -- Usage tracking
    frequency integer DEFAULT 1,
    first_seen_date timestamptz DEFAULT now(),
    last_seen_date timestamptz DEFAULT now(),

    -- Timestamps
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),

    -- Unique constraint: one entry per vendor+product combo
    UNIQUE(vendor_name, product_description)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_vendor_products_vendor ON vendor_products(vendor_name);
CREATE INDEX IF NOT EXISTS idx_vendor_products_type ON vendor_products(product_type);
CREATE INDEX IF NOT EXISTS idx_vendor_products_confidence ON vendor_products(confidence_score DESC);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_vendor_products_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_vendor_products_updated_at ON vendor_products;
CREATE TRIGGER trigger_update_vendor_products_updated_at
    BEFORE UPDATE ON vendor_products
    FOR EACH ROW
    EXECUTE FUNCTION update_vendor_products_updated_at();

COMMENT ON TABLE vendor_products IS
'Learning database of known vendor products. When we analyze the same product multiple times, we learn and improve. Used to speed up future analysis.';

SELECT '✅ Step 3 complete: vendor_products table created' as status;


-- ============================================================================
-- STEP 4: Create vendor_product_patterns table
-- ============================================================================
-- Pattern matching: recognize products by keywords

CREATE TABLE IF NOT EXISTS vendor_product_patterns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern definition
    vendor_name text NOT NULL,
    product_keyword text NOT NULL,
    product_pattern text,

    -- What this pattern means
    correct_product_type text NOT NULL,
    correct_tax_treatment text,

    -- Pattern confidence
    confidence_score decimal(5,2) DEFAULT 80.0
        CHECK (confidence_score >= 0 AND confidence_score <= 100),
    times_confirmed integer DEFAULT 1,

    -- Learning source
    learned_from_correction_id uuid REFERENCES analysis_reviews(id),

    -- Active status
    is_active boolean DEFAULT true,

    -- Timestamps
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),

    -- Unique constraint
    UNIQUE(vendor_name, product_keyword)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_vendor ON vendor_product_patterns(vendor_name);
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_keyword ON vendor_product_patterns(product_keyword);
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_active ON vendor_product_patterns(is_active) WHERE is_active = true;

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_vendor_patterns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_vendor_patterns_updated_at ON vendor_product_patterns;
CREATE TRIGGER trigger_update_vendor_patterns_updated_at
    BEFORE UPDATE ON vendor_product_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_vendor_patterns_updated_at();

COMMENT ON TABLE vendor_product_patterns IS
'Pattern recognition for vendor products. Example: If description contains "EC2", it''s IaaS from AWS. Learned from human corrections.';

SELECT '✅ Step 4 complete: vendor_product_patterns table created' as status;


-- ============================================================================
-- STEP 5: Create audit_trail table
-- ============================================================================
-- Tracks all changes for compliance and debugging

CREATE TABLE IF NOT EXISTS audit_trail (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What happened
    event_type text NOT NULL
        CHECK (event_type IN ('human_correction', 'status_change', 'bulk_update', 'deletion', 'creation')),
    entity_type text NOT NULL
        CHECK (entity_type IN ('analysis_result', 'analysis_review', 'vendor_product', 'vendor_pattern')),
    entity_id uuid,

    -- What changed
    field_name text,
    old_value text,
    new_value text,

    -- Who and when
    changed_by text NOT NULL,
    change_reason text,

    -- Context
    row_id integer,
    vendor_name text,

    -- Timestamp
    created_at timestamptz DEFAULT now()
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type ON audit_trail(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_trail_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_changed_by ON audit_trail(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_trail_created_at ON audit_trail(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_vendor ON audit_trail(vendor_name);

COMMENT ON TABLE audit_trail IS
'Complete audit log of all changes to analysis data. Used for compliance, debugging, and understanding what corrections were made.';

SELECT '✅ Step 5 complete: audit_trail table created' as status;


-- ============================================================================
-- STEP 6: Grant permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON analysis_results TO authenticated, anon;
GRANT SELECT, INSERT ON analysis_reviews TO authenticated, anon;
GRANT SELECT, INSERT, UPDATE ON vendor_products TO authenticated, anon;
GRANT SELECT, INSERT, UPDATE ON vendor_product_patterns TO authenticated, anon;
GRANT SELECT, INSERT ON audit_trail TO authenticated, anon;

SELECT '✅ Step 6 complete: Permissions granted' as status;


-- ============================================================================
-- STEP 7: Verification
-- ============================================================================

SELECT
    '✅✅✅ MIGRATION 003 COMPLETE! ✅✅✅' as status,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'analysis_results') as analysis_results_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'analysis_reviews') as analysis_reviews_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'vendor_products') as vendor_products_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'vendor_product_patterns') as vendor_patterns_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'audit_trail') as audit_trail_exists;

SELECT '
🎉 Analysis tables deployed successfully!

Your database now has:
  ✅ analysis_results       - Store analysis of each invoice line
  ✅ analysis_reviews        - Human corrections and reviews
  ✅ vendor_products         - Learning database for products
  ✅ vendor_product_patterns - Pattern recognition
  ✅ audit_trail            - Complete change history

You can now run:
  python analysis/analyze_refunds.py --input invoices.xlsx

The analysis will save to the database automatically!

Next steps:
1. Prepare an Excel file with invoice data
2. Run analyze_refunds.py
3. Review results in analysis_results table
4. Make corrections and save to analysis_reviews
5. System learns from corrections automatically!

' as next_steps;


-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
/*
-- Run this if you need to remove the tables:

DROP TABLE IF EXISTS audit_trail CASCADE;
DROP TABLE IF EXISTS vendor_product_patterns CASCADE;
DROP TABLE IF EXISTS vendor_products CASCADE;
DROP TABLE IF EXISTS analysis_reviews CASCADE;
DROP TABLE IF EXISTS analysis_results CASCADE;

DROP FUNCTION IF EXISTS update_analysis_results_updated_at() CASCADE;
DROP FUNCTION IF EXISTS update_vendor_products_updated_at() CASCADE;
DROP FUNCTION IF EXISTS update_vendor_patterns_updated_at() CASCADE;
*/
