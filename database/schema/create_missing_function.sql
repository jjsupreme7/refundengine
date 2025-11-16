-- Create the create_file_version function that's missing

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
