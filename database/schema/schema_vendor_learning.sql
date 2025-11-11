-- ============================================================================
-- VENDOR PRODUCT LEARNING SYSTEM
-- Human-in-the-loop corrections and knowledge base updates
-- ============================================================================

-- Table: vendor_products
-- Stores learned product information from vendors over time
CREATE TABLE IF NOT EXISTS vendor_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_name TEXT NOT NULL,
    product_description TEXT NOT NULL,
    product_type TEXT,
    product_category TEXT,

    -- Tax treatment information
    tax_treatment TEXT, -- 'exempt', 'taxable', 'conditional'
    exemption_type TEXT, -- e.g., 'manufacturing', 'resale', 'agriculture'

    -- Learning metadata
    first_seen_date TIMESTAMP DEFAULT NOW(),
    last_seen_date TIMESTAMP DEFAULT NOW(),
    frequency INT DEFAULT 1,

    -- Confidence and source
    confidence_score DECIMAL(5,2), -- 0-100
    learning_source TEXT, -- 'ai_extraction', 'human_correction', 'manual_entry'

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table: analysis_results
-- Stores AI analysis results for each row/line item
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to original transaction
    row_id INT NOT NULL,
    vendor_name TEXT NOT NULL,
    invoice_number TEXT,
    po_number TEXT,
    amount DECIMAL(12,2),
    tax_amount DECIMAL(12,2),

    -- AI Analysis
    ai_product_desc TEXT,
    ai_product_type TEXT,
    ai_refund_basis TEXT,
    ai_citation TEXT,
    ai_confidence DECIMAL(5,2),
    ai_estimated_refund DECIMAL(12,2),
    ai_refund_percentage DECIMAL(5,2),
    ai_explanation TEXT,

    -- Documents analyzed
    invoice_files TEXT[], -- array of file paths
    po_files TEXT[],

    -- Status
    analysis_status TEXT DEFAULT 'pending_review', -- 'pending_review', 'approved', 'corrected', 'rejected'

    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: analysis_reviews
-- Stores human reviews and corrections
CREATE TABLE IF NOT EXISTS analysis_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analysis_results(id),
    row_id INT NOT NULL,

    -- Review decision
    review_status TEXT NOT NULL, -- 'approved', 'corrected', 'rejected'

    -- Human corrections (NULL if approved)
    corrected_product_desc TEXT,
    corrected_product_type TEXT,
    corrected_refund_basis TEXT,
    corrected_citation TEXT,
    corrected_estimated_refund DECIMAL(12,2),
    corrected_refund_percentage DECIMAL(5,2),

    -- Review metadata
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP DEFAULT NOW(),
    reviewed_by TEXT, -- username/email

    -- Track what changed
    fields_corrected TEXT[], -- array of field names that were corrected

    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: vendor_product_patterns
-- Stores patterns learned from corrections to improve future analysis
CREATE TABLE IF NOT EXISTS vendor_product_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_name TEXT NOT NULL,

    -- Pattern matching
    product_keyword TEXT, -- e.g., "5G Radio", "Installation"
    product_pattern TEXT, -- regex or pattern for matching

    -- Correct classification
    correct_product_type TEXT,
    correct_tax_treatment TEXT,
    correct_exemption_type TEXT,
    typical_refund_percentage DECIMAL(5,2),

    -- Learning source
    learned_from_correction_id UUID REFERENCES analysis_reviews(id),
    times_confirmed INT DEFAULT 1, -- how many times this pattern was confirmed
    confidence_score DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Table: audit_trail
-- Complete audit log of all AI decisions and human overrides
CREATE TABLE IF NOT EXISTS audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL, -- 'ai_analysis', 'human_review', 'correction_applied', 'pattern_learned'
    entity_type TEXT, -- 'analysis_result', 'vendor_product', 'pattern'
    entity_id UUID,

    -- What changed
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,

    -- Who/what made the change
    changed_by TEXT, -- 'ai' or username
    change_reason TEXT,

    -- Context
    row_id INT,
    vendor_name TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_vendor_products_vendor ON vendor_products(vendor_name);
CREATE INDEX idx_vendor_products_type ON vendor_products(product_type);
CREATE INDEX idx_analysis_results_row ON analysis_results(row_id);
CREATE INDEX idx_analysis_results_vendor ON analysis_results(vendor_name);
CREATE INDEX idx_analysis_results_status ON analysis_results(analysis_status);
CREATE INDEX idx_analysis_reviews_analysis ON analysis_reviews(analysis_id);
CREATE INDEX idx_vendor_patterns_vendor ON vendor_product_patterns(vendor_name);
CREATE INDEX idx_audit_trail_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_trail_row ON audit_trail(row_id);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update vendor_products when a correction is approved
CREATE OR REPLACE FUNCTION update_vendor_learning()
RETURNS TRIGGER AS $$
BEGIN
    -- If product was corrected, update or insert into vendor_products
    IF NEW.review_status = 'corrected' AND NEW.corrected_product_type IS NOT NULL THEN
        INSERT INTO vendor_products (
            vendor_name,
            product_description,
            product_type,
            learning_source,
            confidence_score
        ) VALUES (
            (SELECT vendor_name FROM analysis_results WHERE id = NEW.analysis_id),
            NEW.corrected_product_desc,
            NEW.corrected_product_type,
            'human_correction',
            100.0
        )
        ON CONFLICT DO NOTHING;

        -- Also create/update pattern
        INSERT INTO vendor_product_patterns (
            vendor_name,
            product_keyword,
            correct_product_type,
            learned_from_correction_id,
            confidence_score
        ) VALUES (
            (SELECT vendor_name FROM analysis_results WHERE id = NEW.analysis_id),
            NEW.corrected_product_desc,
            NEW.corrected_product_type,
            NEW.id,
            100.0
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically learn from corrections
CREATE TRIGGER trigger_update_vendor_learning
    AFTER INSERT ON analysis_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_vendor_learning();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Combined analysis with reviews
CREATE OR REPLACE VIEW analysis_with_reviews AS
SELECT
    ar.id,
    ar.row_id,
    ar.vendor_name,
    ar.invoice_number,
    ar.amount,
    ar.tax_amount,
    ar.ai_product_desc,
    ar.ai_product_type,
    ar.ai_refund_basis,
    ar.ai_citation,
    ar.ai_confidence,
    ar.ai_estimated_refund,
    ar.analysis_status,
    rv.review_status,
    COALESCE(rv.corrected_product_desc, ar.ai_product_desc) as final_product_desc,
    COALESCE(rv.corrected_product_type, ar.ai_product_type) as final_product_type,
    COALESCE(rv.corrected_refund_basis, ar.ai_refund_basis) as final_refund_basis,
    COALESCE(rv.corrected_estimated_refund, ar.ai_estimated_refund) as final_estimated_refund,
    rv.reviewer_notes,
    rv.reviewed_at
FROM analysis_results ar
LEFT JOIN analysis_reviews rv ON ar.id = rv.analysis_id;

-- View: Vendor learning summary
CREATE OR REPLACE VIEW vendor_learning_summary AS
SELECT
    vendor_name,
    COUNT(DISTINCT product_description) as unique_products,
    COUNT(*) as total_occurrences,
    AVG(confidence_score) as avg_confidence,
    MAX(last_seen_date) as last_activity
FROM vendor_products
GROUP BY vendor_name;
