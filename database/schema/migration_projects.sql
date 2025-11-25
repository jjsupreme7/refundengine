-- ============================================================================
-- PROJECTS TABLE MIGRATION
-- Enables multi-project organization for different tax claim projects
-- ============================================================================

-- Purpose: Organize Excel files by project (e.g., "WA Sales Tax 2024",
--          "WA Use Tax 2024", "WA Sales Tax 2025") to separate different
--          claim types and years

-- ============================================================================
-- STEP 1: Create projects table
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Project identification
    name TEXT NOT NULL UNIQUE,
    description TEXT,

    -- Tax classification
    tax_type TEXT, -- 'sales_tax', 'use_tax', or NULL if mixed
    tax_year INTEGER, -- 2024, 2025, etc.
    state_code TEXT DEFAULT 'WA', -- 'WA', 'OR', 'CA', etc.

    -- Project metadata
    client_name TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'completed', 'archived'

    -- Filing information
    filing_status TEXT, -- 'draft', 'ready_to_file', 'filed', 'approved'
    filed_date DATE,
    estimated_refund_amount DECIMAL(12, 2),

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT,
    archived_at TIMESTAMP
);

-- Add comments
COMMENT ON TABLE projects IS 'Tax refund claim projects - organizes Excel files by tax type, year, and client';
COMMENT ON COLUMN projects.name IS 'Unique project name (e.g., "WA Sales Tax 2024")';
COMMENT ON COLUMN projects.tax_type IS 'Type of tax: sales_tax, use_tax, or NULL for mixed';
COMMENT ON COLUMN projects.tax_year IS 'Tax year for this claim (e.g., 2024)';
COMMENT ON COLUMN projects.state_code IS 'State code (WA, OR, CA, etc.)';
COMMENT ON COLUMN projects.status IS 'Project status: active, completed, archived';
COMMENT ON COLUMN projects.filing_status IS 'Filing status: draft, ready_to_file, filed, approved';
COMMENT ON COLUMN projects.estimated_refund_amount IS 'Total estimated refund for this project';

-- ============================================================================
-- STEP 2: Create indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_projects_tax_type ON projects(tax_type);
CREATE INDEX IF NOT EXISTS idx_projects_tax_year ON projects(tax_year);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_state_code ON projects(state_code);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);

-- ============================================================================
-- STEP 3: Add foreign key constraint to excel_file_tracking
-- ============================================================================

-- Add foreign key if not already constrained
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_excel_file_tracking_project'
    ) THEN
        ALTER TABLE excel_file_tracking
        ADD CONSTRAINT fk_excel_file_tracking_project
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Index for project lookups
CREATE INDEX IF NOT EXISTS idx_excel_file_tracking_project_id ON excel_file_tracking(project_id);

-- ============================================================================
-- STEP 4: Create helper view for project summaries
-- ============================================================================

CREATE OR REPLACE VIEW v_project_summaries AS
SELECT
    p.id,
    p.name,
    p.tax_type,
    p.tax_year,
    p.state_code,
    p.status,
    p.filing_status,
    p.estimated_refund_amount,
    p.created_at,

    -- Count of Excel files in this project
    COUNT(DISTINCT eft.id) AS file_count,

    -- Total rows across all Excel files
    COALESCE(SUM(eft.row_count), 0) AS total_rows,

    -- Latest file upload
    MAX(eft.created_at) AS latest_file_upload,

    -- Processing status summary
    COUNT(CASE WHEN eft.processing_status = 'completed' THEN 1 END) AS files_completed,
    COUNT(CASE WHEN eft.processing_status = 'processing' THEN 1 END) AS files_processing,
    COUNT(CASE WHEN eft.processing_status = 'error' THEN 1 END) AS files_error

FROM projects p
LEFT JOIN excel_file_tracking eft ON eft.project_id = p.id
GROUP BY p.id, p.name, p.tax_type, p.tax_year, p.state_code,
         p.status, p.filing_status, p.estimated_refund_amount, p.created_at;

COMMENT ON VIEW v_project_summaries IS 'Summary view of projects with file counts and processing status';

-- ============================================================================
-- STEP 5: Create updated_at trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_projects_updated_at ON projects;
CREATE TRIGGER trigger_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_projects_updated_at();

-- ============================================================================
-- DEPLOYMENT COMPLETE
-- ============================================================================

-- Verify table creation
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
        RAISE NOTICE '✓ Projects table created successfully';
        RAISE NOTICE '✓ Foreign key constraint added to excel_file_tracking';
        RAISE NOTICE '✓ Indexes created';
        RAISE NOTICE '✓ Summary view created';
        RAISE NOTICE '✓ Updated trigger created';
    ELSE
        RAISE EXCEPTION 'Failed to create projects table';
    END IF;
END $$;
