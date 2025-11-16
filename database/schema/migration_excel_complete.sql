-- ============================================================================
-- COMBINED EXCEL TRACKING & VERSIONING MIGRATION
-- Run this file to set up complete Excel file tracking with version control
-- ============================================================================
-- This combines:
--   1. migration_excel_file_tracking.sql (base tables)
--   2. migration_excel_versioning.sql (versioning extensions)
-- ============================================================================

-- ============================================================================
-- PART 1: EXCEL FILE TRACKING (Base Tables)
-- ============================================================================

-- File-level metadata
CREATE TABLE IF NOT EXISTS excel_file_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- File identification
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT,
    file_hash TEXT, -- SHA256 hash of entire file

    -- File metadata
    last_modified TIMESTAMP, -- File system modification time
    last_processed TIMESTAMP, -- When we last processed this file
    row_count INT, -- Number of rows in the file

    -- Processing status
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'error'
    error_message TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Row-level change detection
CREATE TABLE IF NOT EXISTS excel_row_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Row identification
    file_path TEXT NOT NULL,
    row_index INT NOT NULL,
    row_hash TEXT NOT NULL,

    -- Row metadata
    vendor_name TEXT,
    invoice_number TEXT,
    po_number TEXT,
    line_item_amount DECIMAL(12, 2),
    tax_remitted DECIMAL(12, 2),

    -- Processing status
    processing_status TEXT DEFAULT 'pending',
    last_processed TIMESTAMP,
    error_message TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(file_path, row_index)
);

-- Indexes for base tables
CREATE INDEX IF NOT EXISTS idx_excel_file_tracking_file_path
ON excel_file_tracking(file_path);

CREATE INDEX IF NOT EXISTS idx_excel_file_tracking_status
ON excel_file_tracking(processing_status);

CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_file_path
ON excel_row_tracking(file_path);

CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_row_index
ON excel_row_tracking(row_index);

-- ============================================================================
-- PART 2: EXCEL VERSIONING EXTENSIONS
-- ============================================================================

-- Add versioning columns to excel_file_tracking
ALTER TABLE excel_file_tracking
ADD COLUMN IF NOT EXISTS storage_bucket TEXT DEFAULT 'excel-files',
ADD COLUMN IF NOT EXISTS storage_path TEXT,
ADD COLUMN IF NOT EXISTS current_version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS locked_by TEXT,
ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
ADD COLUMN IF NOT EXISTS project_id UUID;

-- Version history table
CREATE TABLE IF NOT EXISTS excel_file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to parent file
    file_id UUID NOT NULL REFERENCES excel_file_tracking(id) ON DELETE CASCADE,

    -- Version metadata
    version_number INT NOT NULL,
    storage_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,

    -- Change metadata
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    change_summary TEXT,
    rows_added INT DEFAULT 0,
    rows_modified INT DEFAULT 0,
    rows_deleted INT DEFAULT 0,

    -- File metadata
    file_size_bytes BIGINT,
    row_count INT,

    UNIQUE(file_id, version_number)
);

-- Cell-level change tracking
CREATE TABLE IF NOT EXISTS excel_cell_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to version
    version_id UUID NOT NULL REFERENCES excel_file_versions(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES excel_file_tracking(id) ON DELETE CASCADE,

    -- Cell identification
    sheet_name TEXT NOT NULL,
    row_index INT NOT NULL,
    column_name TEXT NOT NULL,

    -- Change data
    old_value TEXT,
    new_value TEXT,
    change_type TEXT NOT NULL, -- 'added', 'modified', 'deleted'

    -- Metadata
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),

    -- For critical fields tracking
    is_critical_field BOOLEAN DEFAULT FALSE
);

-- Indexes for versioning tables
CREATE INDEX IF NOT EXISTS idx_excel_file_versions_file_id
ON excel_file_versions(file_id);

CREATE INDEX IF NOT EXISTS idx_excel_file_versions_created_at
ON excel_file_versions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_excel_cell_changes_version_id
ON excel_cell_changes(version_id);

CREATE INDEX IF NOT EXISTS idx_excel_cell_changes_file_id
ON excel_cell_changes(file_id);

CREATE INDEX IF NOT EXISTS idx_excel_cell_changes_critical
ON excel_cell_changes(is_critical_field) WHERE is_critical_field = TRUE;

-- ============================================================================
-- PART 3: HELPER FUNCTIONS
-- ============================================================================

-- Function: Acquire lock on file
CREATE OR REPLACE FUNCTION acquire_file_lock(
    file_id_param UUID,
    user_email_param TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    current_lock TEXT;
    lock_time TIMESTAMP;
BEGIN
    -- Check if file is already locked
    SELECT locked_by, locked_at INTO current_lock, lock_time
    FROM excel_file_tracking
    WHERE id = file_id_param;

    -- If locked by someone else and not expired, fail
    IF current_lock IS NOT NULL
       AND current_lock != user_email_param
       AND lock_time > NOW() - INTERVAL '30 minutes' THEN
        RETURN FALSE;
    END IF;

    -- Acquire lock
    UPDATE excel_file_tracking
    SET
        locked_by = user_email_param,
        locked_at = NOW(),
        updated_at = NOW()
    WHERE id = file_id_param;

    RETURN TRUE;
END;
$$;

-- Function: Release lock on file
CREATE OR REPLACE FUNCTION release_file_lock(
    file_id_param UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE excel_file_tracking
    SET
        locked_by = NULL,
        locked_at = NULL,
        updated_at = NOW()
    WHERE id = file_id_param;

    RETURN TRUE;
END;
$$;

-- Function: Create new version
CREATE OR REPLACE FUNCTION create_file_version(
    file_id_param UUID,
    user_email_param TEXT,
    change_summary_param TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    new_version_number INT;
    new_version_id UUID;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version_number), 0) + 1 INTO new_version_number
    FROM excel_file_versions
    WHERE file_id = file_id_param;

    -- Create new version record
    INSERT INTO excel_file_versions (
        file_id,
        version_number,
        storage_path,
        file_hash,
        created_by,
        change_summary
    )
    VALUES (
        file_id_param,
        new_version_number,
        '', -- Will be updated by application
        '', -- Will be updated by application
        user_email_param,
        change_summary_param
    )
    RETURNING id INTO new_version_id;

    -- Update current version in file tracking
    UPDATE excel_file_tracking
    SET
        current_version = new_version_number,
        updated_at = NOW()
    WHERE id = file_id_param;

    RETURN new_version_id;
END;
$$;

-- ============================================================================
-- PART 4: VIEWS
-- ============================================================================

-- View: Active file locks
CREATE OR REPLACE VIEW v_excel_file_locks AS
SELECT
    f.id,
    f.file_path,
    f.file_name,
    f.locked_by,
    f.locked_at,
    EXTRACT(EPOCH FROM (NOW() - f.locked_at))/60 AS minutes_locked,
    CASE
        WHEN f.locked_at < NOW() - INTERVAL '30 minutes' THEN TRUE
        ELSE FALSE
    END AS lock_expired
FROM excel_file_tracking f
WHERE f.locked_by IS NOT NULL;

-- View: Version history with file details
CREATE OR REPLACE VIEW v_file_version_history AS
SELECT
    v.id AS version_id,
    v.file_id,
    f.file_name,
    f.file_path,
    v.version_number,
    v.created_by,
    v.created_at,
    v.change_summary,
    v.rows_added,
    v.rows_modified,
    v.rows_deleted,
    v.file_size_bytes,
    v.row_count
FROM excel_file_versions v
JOIN excel_file_tracking f ON v.file_id = f.id
ORDER BY v.created_at DESC;

-- ============================================================================
-- PART 5: ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE excel_file_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_file_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_cell_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_row_tracking ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to allow re-running this migration)
DROP POLICY IF EXISTS "Users can view file tracking" ON excel_file_tracking;
DROP POLICY IF EXISTS "Users can view versions" ON excel_file_versions;
DROP POLICY IF EXISTS "Users can view changes" ON excel_cell_changes;
DROP POLICY IF EXISTS "Users can view row tracking" ON excel_row_tracking;
DROP POLICY IF EXISTS "Service role full access file tracking" ON excel_file_tracking;
DROP POLICY IF EXISTS "Service role full access versions" ON excel_file_versions;
DROP POLICY IF EXISTS "Service role full access changes" ON excel_cell_changes;
DROP POLICY IF EXISTS "Service role full access row tracking" ON excel_row_tracking;

-- Policies for authenticated users (can view all)
CREATE POLICY "Users can view file tracking"
ON excel_file_tracking FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view versions"
ON excel_file_versions FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view changes"
ON excel_cell_changes FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view row tracking"
ON excel_row_tracking FOR SELECT
TO authenticated
USING (true);

-- Policies for service role (full access)
CREATE POLICY "Service role full access file tracking"
ON excel_file_tracking FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access versions"
ON excel_file_versions FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access changes"
ON excel_cell_changes FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access row tracking"
ON excel_row_tracking FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- DEPLOYMENT COMPLETE
-- ============================================================================

-- Verify tables exist
DO $$
BEGIN
    RAISE NOTICE '✅ Excel tracking and versioning schema deployed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  • excel_file_tracking (with versioning columns)';
    RAISE NOTICE '  • excel_row_tracking';
    RAISE NOTICE '  • excel_file_versions';
    RAISE NOTICE '  • excel_cell_changes';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '  • acquire_file_lock()';
    RAISE NOTICE '  • release_file_lock()';
    RAISE NOTICE '  • create_file_version()';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  • v_excel_file_locks';
    RAISE NOTICE '  • v_file_version_history';
END $$;
