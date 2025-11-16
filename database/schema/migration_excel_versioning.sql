-- ============================================================================
-- EXCEL VERSIONING & COLLABORATION SCHEMA
-- Extends existing excel_file_tracking for version control
-- ============================================================================

-- ============================================================================
-- STEP 1: Add versioning columns to excel_file_tracking
-- ============================================================================

ALTER TABLE excel_file_tracking
ADD COLUMN IF NOT EXISTS storage_bucket TEXT DEFAULT 'excel-files',
ADD COLUMN IF NOT EXISTS storage_path TEXT, -- Path in Supabase Storage
ADD COLUMN IF NOT EXISTS current_version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS locked_by TEXT, -- Email of user editing
ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
ADD COLUMN IF NOT EXISTS project_id UUID; -- Link to projects

-- ============================================================================
-- STEP 2: Create excel_file_versions table (version history)
-- ============================================================================

CREATE TABLE IF NOT EXISTS excel_file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to parent file
    file_id UUID NOT NULL REFERENCES excel_file_tracking(id) ON DELETE CASCADE,

    -- Version metadata
    version_number INT NOT NULL,
    storage_path TEXT NOT NULL, -- Path to this version in storage
    file_hash TEXT NOT NULL, -- SHA256 of this version

    -- Change metadata
    created_by TEXT NOT NULL, -- User email
    created_at TIMESTAMP DEFAULT NOW(),
    change_summary TEXT, -- Brief description of changes
    rows_added INT DEFAULT 0,
    rows_modified INT DEFAULT 0,
    rows_deleted INT DEFAULT 0,

    -- File metadata
    file_size_bytes BIGINT,
    row_count INT,

    UNIQUE(file_id, version_number)
);

CREATE INDEX idx_excel_file_versions_file_id ON excel_file_versions(file_id);
CREATE INDEX idx_excel_file_versions_created_at ON excel_file_versions(created_at DESC);

COMMENT ON TABLE excel_file_versions IS 'Version history for Excel files with change tracking';

-- ============================================================================
-- STEP 3: Create excel_cell_changes table (granular change tracking)
-- ============================================================================

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

CREATE INDEX idx_excel_cell_changes_version_id ON excel_cell_changes(version_id);
CREATE INDEX idx_excel_cell_changes_file_id ON excel_cell_changes(file_id);
CREATE INDEX idx_excel_cell_changes_critical ON excel_cell_changes(is_critical_field) WHERE is_critical_field = TRUE;

COMMENT ON TABLE excel_cell_changes IS 'Granular cell-level change tracking for audit trail';

-- ============================================================================
-- STEP 4: Create excel_file_locks view (active locks)
-- ============================================================================

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

COMMENT ON VIEW v_excel_file_locks IS 'Active file locks with auto-expiry detection';

-- ============================================================================
-- STEP 5: Create helper functions
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

COMMENT ON FUNCTION acquire_file_lock IS 'Attempt to acquire exclusive lock on Excel file';

-- Function: Release lock
CREATE OR REPLACE FUNCTION release_file_lock(
    file_id_param UUID,
    user_email_param TEXT
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
    WHERE id = file_id_param
        AND locked_by = user_email_param;

    RETURN FOUND;
END;
$$;

COMMENT ON FUNCTION release_file_lock IS 'Release file lock (only by lock owner)';

-- Function: Create new version
CREATE OR REPLACE FUNCTION create_file_version(
    file_id_param UUID,
    user_email_param TEXT,
    change_summary_param TEXT,
    storage_path_param TEXT,
    file_hash_param TEXT,
    file_size_param BIGINT,
    row_count_param INT
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    new_version_number INT;
    new_version_id UUID;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(current_version), 0) + 1 INTO new_version_number
    FROM excel_file_tracking
    WHERE id = file_id_param;

    -- Create version record
    INSERT INTO excel_file_versions (
        file_id, version_number, storage_path, file_hash,
        created_by, change_summary, file_size_bytes, row_count
    ) VALUES (
        file_id_param, new_version_number, storage_path_param, file_hash_param,
        user_email_param, change_summary_param, file_size_param, row_count_param
    ) RETURNING id INTO new_version_id;

    -- Update parent file
    UPDATE excel_file_tracking
    SET
        current_version = new_version_number,
        file_hash = file_hash_param,
        storage_path = storage_path_param,
        file_size_bytes = file_size_param,
        row_count = row_count_param,
        last_processed = NOW(),
        updated_at = NOW()
    WHERE id = file_id_param;

    RETURN new_version_id;
END;
$$;

COMMENT ON FUNCTION create_file_version IS 'Create new version of Excel file with metadata';

-- ============================================================================
-- STEP 6: Create monitoring views
-- ============================================================================

-- View: File version history with stats
CREATE OR REPLACE VIEW v_file_version_history AS
SELECT
    f.id AS file_id,
    f.file_name,
    f.file_path,
    f.current_version,
    v.version_number,
    v.created_by,
    v.created_at,
    v.change_summary,
    v.rows_added,
    v.rows_modified,
    v.rows_deleted,
    v.file_size_bytes,
    COUNT(c.id) AS cell_changes_count
FROM excel_file_tracking f
LEFT JOIN excel_file_versions v ON f.id = v.file_id
LEFT JOIN excel_cell_changes c ON v.id = c.version_id
GROUP BY f.id, f.file_name, f.file_path, f.current_version,
         v.id, v.version_number, v.created_by, v.created_at,
         v.change_summary, v.rows_added, v.rows_modified, v.rows_deleted,
         v.file_size_bytes
ORDER BY f.file_name, v.version_number DESC;

COMMENT ON VIEW v_file_version_history IS 'Complete version history with change statistics';

-- View: Recent activity feed
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    'version_created' AS activity_type,
    v.created_by AS user_email,
    v.created_at AS activity_time,
    f.file_name,
    v.change_summary AS description,
    v.version_number
FROM excel_file_versions v
JOIN excel_file_tracking f ON v.file_id = f.id
ORDER BY v.created_at DESC
LIMIT 50;

COMMENT ON VIEW v_recent_activity IS 'Recent user activity for dashboard feed';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ Excel Versioning & Collaboration Schema Created Successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Extended/Created:';
    RAISE NOTICE '  - excel_file_tracking (extended with versioning columns)';
    RAISE NOTICE '  - excel_file_versions (version history)';
    RAISE NOTICE '  - excel_cell_changes (granular change tracking)';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions Created:';
    RAISE NOTICE '  - acquire_file_lock(file_id, user_email)';
    RAISE NOTICE '  - release_file_lock(file_id, user_email)';
    RAISE NOTICE '  - create_file_version(file_id, user_email, summary, ...)';
    RAISE NOTICE '';
    RAISE NOTICE 'Views Created:';
    RAISE NOTICE '  - v_excel_file_locks (active locks)';
    RAISE NOTICE '  - v_file_version_history (version history)';
    RAISE NOTICE '  - v_recent_activity (activity feed)';
    RAISE NOTICE '';
END $$;
