-- ============================================================================
-- PROJECT ANALYSIS RESULTS TABLE
-- Stores AI analysis results for each project
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Row identification (from Excel manifest)
    row_index INTEGER NOT NULL,
    vendor_id TEXT,
    vendor_name TEXT,

    -- Document references
    invoice_filename TEXT,
    invoice_filename_2 TEXT,
    po_filename TEXT,
    invoice_number TEXT,
    po_number TEXT,

    -- Financial data
    initial_amount DECIMAL(12, 2),
    tax_paid DECIMAL(12, 2),
    total_amount DECIMAL(12, 2),
    tax_rate DECIMAL(5, 4),

    -- AI Analysis output
    description TEXT,
    ai_confidence DECIMAL(3, 2),  -- 0.00 to 1.00
    taxability TEXT,              -- 'Taxable', 'Exempt'
    refund_basis TEXT,            -- 'MPU', 'Non-taxable', 'OOS Services', 'No Refund'
    refund_eligible TEXT,         -- 'Yes', 'No'
    legal_citation TEXT,
    explanation TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_analysis_results_project_id ON project_analysis_results(project_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_vendor ON project_analysis_results(vendor_name);
CREATE INDEX IF NOT EXISTS idx_analysis_results_taxability ON project_analysis_results(taxability);

-- Updated trigger
CREATE OR REPLACE FUNCTION update_analysis_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_analysis_results_updated_at ON project_analysis_results;
CREATE TRIGGER trigger_analysis_results_updated_at
    BEFORE UPDATE ON project_analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION update_analysis_results_updated_at();

-- Comments
COMMENT ON TABLE project_analysis_results IS 'Stores AI analysis results linked to projects';
COMMENT ON COLUMN project_analysis_results.row_index IS 'Row number from original Excel manifest';
COMMENT ON COLUMN project_analysis_results.ai_confidence IS 'AI confidence score from 0.00 to 1.00';
COMMENT ON COLUMN project_analysis_results.refund_basis IS 'Refund basis: MPU, Non-taxable, OOS Services, No Refund';
