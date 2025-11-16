-- ============================================================================
-- EXCEL FILE TRACKING MIGRATION
-- Enables automatic detection of Excel file changes for incremental processing
-- ============================================================================

-- Purpose: Track Excel claim sheet files and detect changes to trigger
--          incremental processing of only new or modified rows

-- ============================================================================
-- STEP 1: Create excel_file_tracking table (file-level metadata)
-- ============================================================================

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

-- Add comments
COMMENT ON TABLE excel_file_tracking IS 'Tracks Excel claim sheet files for change detection';
COMMENT ON COLUMN excel_file_tracking.file_hash IS 'SHA256 hash of entire file for quick change detection';
COMMENT ON COLUMN excel_file_tracking.last_modified IS 'File system last modified timestamp';
COMMENT ON COLUMN excel_file_tracking.last_processed IS 'When this file was last processed by the system';
COMMENT ON COLUMN excel_file_tracking.row_count IS 'Total number of rows in the Excel file';

-- ============================================================================
-- STEP 2: Create excel_row_tracking table (row-level change detection)
-- ============================================================================

CREATE TABLE IF NOT EXISTS excel_row_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Row identification
    file_path TEXT NOT NULL, -- References excel_file_tracking.file_path
    row_index INT NOT NULL, -- Row number in Excel (0-indexed from DataFrame)
    row_hash TEXT NOT NULL, -- MD5 hash of row content for change detection

    -- Row metadata (extracted from Excel)
    vendor_name TEXT,
    invoice_number TEXT,
    po_number TEXT,
    line_item_amount DECIMAL(12, 2),
    tax_remitted DECIMAL(12, 2),

    -- Processing status
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'error'
    last_processed TIMESTAMP,
    error_message TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(file_path, row_index)
);

-- Add comments
COMMENT ON TABLE excel_row_tracking IS 'Tracks individual rows in Excel files for incremental processing';
COMMENT ON COLUMN excel_row_tracking.row_hash IS 'MD5 hash of entire row content to detect changes';
COMMENT ON COLUMN excel_row_tracking.row_index IS 'Row index in Excel file (0-indexed from pandas DataFrame)';

-- ============================================================================
-- STEP 3: Create indexes for performance
-- ============================================================================

-- File-level indexes
CREATE INDEX IF NOT EXISTS idx_excel_file_tracking_file_path
ON excel_file_tracking(file_path);

CREATE INDEX IF NOT EXISTS idx_excel_file_tracking_status
ON excel_file_tracking(processing_status);

CREATE INDEX IF NOT EXISTS idx_excel_file_tracking_last_modified
ON excel_file_tracking(last_modified DESC);

-- Row-level indexes
CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_file_path
ON excel_row_tracking(file_path);

CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_row_index
ON excel_row_tracking(row_index);

CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_status
ON excel_row_tracking(processing_status);

CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_invoice
ON excel_row_tracking(invoice_number);

-- Composite index for lookup
CREATE INDEX IF NOT EXISTS idx_excel_row_tracking_file_row
ON excel_row_tracking(file_path, row_index);

-- ============================================================================
-- STEP 4: Create helper functions
-- ============================================================================

-- Function to get unprocessed rows for a file
CREATE OR REPLACE FUNCTION get_unprocessed_rows(file_path_param TEXT)
RETURNS TABLE (
    id UUID,
    row_index INT,
    vendor_name TEXT,
    invoice_number TEXT,
    processing_status TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.row_index,
        r.vendor_name,
        r.invoice_number,
        r.processing_status
    FROM excel_row_tracking r
    WHERE r.file_path = file_path_param
        AND r.processing_status IN ('pending', 'error')
    ORDER BY r.row_index;
END;
$$;

COMMENT ON FUNCTION get_unprocessed_rows IS 'Get all unprocessed rows for a specific Excel file';

-- Function to mark file as processed
CREATE OR REPLACE FUNCTION mark_file_processed(file_path_param TEXT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE excel_file_tracking
    SET
        processing_status = 'completed',
        last_processed = NOW(),
        updated_at = NOW()
    WHERE file_path = file_path_param;
END;
$$;

COMMENT ON FUNCTION mark_file_processed IS 'Mark an Excel file as fully processed';

-- Function to mark row as processed
CREATE OR REPLACE FUNCTION mark_row_processed(file_path_param TEXT, row_index_param INT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE excel_row_tracking
    SET
        processing_status = 'completed',
        last_processed = NOW(),
        updated_at = NOW()
    WHERE file_path = file_path_param
        AND row_index = row_index_param;
END;
$$;

COMMENT ON FUNCTION mark_row_processed IS 'Mark a specific row as processed';

-- ============================================================================
-- STEP 5: Create trigger to auto-update updated_at timestamp
-- ============================================================================

-- Trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to excel_file_tracking
CREATE TRIGGER update_excel_file_tracking_updated_at
BEFORE UPDATE ON excel_file_tracking
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to excel_row_tracking
CREATE TRIGGER update_excel_row_tracking_updated_at
BEFORE UPDATE ON excel_row_tracking
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 6: Create helper view for monitoring
-- ============================================================================

CREATE OR REPLACE VIEW v_excel_file_status AS
SELECT
    f.file_path,
    f.file_name,
    f.row_count,
    f.last_modified,
    f.last_processed,
    f.processing_status,
    COUNT(r.id) FILTER (WHERE r.processing_status = 'pending') AS pending_rows,
    COUNT(r.id) FILTER (WHERE r.processing_status = 'completed') AS completed_rows,
    COUNT(r.id) FILTER (WHERE r.processing_status = 'error') AS error_rows,
    COUNT(r.id) AS total_tracked_rows
FROM excel_file_tracking f
LEFT JOIN excel_row_tracking r ON f.file_path = r.file_path
GROUP BY f.id, f.file_path, f.file_name, f.row_count, f.last_modified,
         f.last_processed, f.processing_status
ORDER BY f.last_modified DESC;

COMMENT ON VIEW v_excel_file_status IS 'Overview of Excel files and their processing status';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check tables exist
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_name IN ('excel_file_tracking', 'excel_row_tracking')
ORDER BY table_name;

-- Check indexes exist
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('excel_file_tracking', 'excel_row_tracking')
ORDER BY tablename, indexname;

-- Check functions exist
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name IN (
    'get_unprocessed_rows',
    'mark_file_processed',
    'mark_row_processed',
    'update_updated_at_column'
)
ORDER BY routine_name;

-- Check view exists
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_name = 'v_excel_file_status';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✓ Excel file tracking migration completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - excel_file_tracking (file-level metadata and change detection)';
    RAISE NOTICE '  - excel_row_tracking (row-level change detection)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created functions:';
    RAISE NOTICE '  - get_unprocessed_rows(file_path)';
    RAISE NOTICE '  - mark_file_processed(file_path)';
    RAISE NOTICE '  - mark_row_processed(file_path, row_index)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created view:';
    RAISE NOTICE '  - v_excel_file_status (monitoring dashboard)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created indexes:';
    RAISE NOTICE '  - 9 indexes for optimized queries';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Use ExcelFileWatcher class to monitor claim sheets';
    RAISE NOTICE '  2. Integrate with refund analysis engine';
    RAISE NOTICE '  3. Set up automated monitoring (cron or file watcher daemon)';
    RAISE NOTICE '';
END $$;
