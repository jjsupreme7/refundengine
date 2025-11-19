-- ============================================================================
-- PII Protection Schema Extensions
-- ============================================================================
-- Adds encryption support and audit logging for PII handling
--
-- This schema extends existing tables with:
-- 1. Encrypted field markers
-- 2. PII access audit log
-- 3. Data retention policies
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Add encrypted field markers to existing tables
-- ----------------------------------------------------------------------------

-- Add encryption status columns to analysis_results
ALTER TABLE IF EXISTS analysis_results
ADD COLUMN IF NOT EXISTS contact_email_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS contact_phone_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_pii_redacted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS pii_redaction_report JSONB;

COMMENT ON COLUMN analysis_results.contact_email_encrypted IS 'True if contact_email is encrypted';
COMMENT ON COLUMN analysis_results.contact_phone_encrypted IS 'True if contact_phone is encrypted';
COMMENT ON COLUMN analysis_results.is_pii_redacted IS 'True if invoice text was redacted before analysis';
COMMENT ON COLUMN analysis_results.pii_redaction_report IS 'Report of PII types redacted from invoice';

-- ----------------------------------------------------------------------------
-- 2. PII Access Audit Log
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pii_access_log (
    id BIGSERIAL PRIMARY KEY,
    access_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_email TEXT,
    action TEXT NOT NULL,  -- 'encrypt', 'decrypt', 'mask', 'export', 'view'
    table_name TEXT,
    record_id BIGINT,
    field_name TEXT,
    pii_type TEXT,  -- 'email', 'phone', 'account', 'tax_id', etc.
    access_reason TEXT,  -- Why this PII was accessed
    ip_address TEXT,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB  -- Additional context
);

CREATE INDEX IF NOT EXISTS idx_pii_access_log_timestamp ON pii_access_log(access_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pii_access_log_user ON pii_access_log(user_email);
CREATE INDEX IF NOT EXISTS idx_pii_access_log_action ON pii_access_log(action);
CREATE INDEX IF NOT EXISTS idx_pii_access_log_record ON pii_access_log(table_name, record_id);

COMMENT ON TABLE pii_access_log IS 'Audit log of all PII access events';
COMMENT ON COLUMN pii_access_log.action IS 'Type of PII operation performed';
COMMENT ON COLUMN pii_access_log.access_reason IS 'Business justification for accessing PII';

-- ----------------------------------------------------------------------------
-- 3. PII Redaction Tracking
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pii_redaction_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_type TEXT NOT NULL,  -- 'invoice', 'po', 'analysis'
    source_id TEXT,  -- invoice number, PO number, etc.
    original_text_hash TEXT,  -- SHA-256 hash of original text (for verification)
    pii_types_found TEXT[],  -- Array of PII types detected
    redaction_count INTEGER,  -- Total number of redactions
    redaction_details JSONB,  -- Detailed redaction report
    was_sent_to_api BOOLEAN DEFAULT FALSE,
    api_provider TEXT,  -- 'openai', 'anthropic', etc.
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_pii_redaction_log_source ON pii_redaction_log(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_pii_redaction_log_created ON pii_redaction_log(created_at DESC);

COMMENT ON TABLE pii_redaction_log IS 'Log of all PII redaction operations before API calls';
COMMENT ON COLUMN pii_redaction_log.original_text_hash IS 'Hash of original text for verification (not the actual text)';

-- ----------------------------------------------------------------------------
-- 4. Data Retention Policy Table
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS data_retention_policy (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL UNIQUE,
    field_name TEXT,
    data_type TEXT NOT NULL,  -- 'pii', 'business', 'audit'
    retention_days INTEGER,  -- NULL = keep forever
    auto_delete BOOLEAN DEFAULT FALSE,
    encryption_required BOOLEAN DEFAULT FALSE,
    last_cleanup TIMESTAMPTZ,
    policy_description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE data_retention_policy IS 'Data retention policies for compliance (GDPR, CCPA)';
COMMENT ON COLUMN data_retention_policy.retention_days IS 'Days to retain data (NULL = indefinite)';
COMMENT ON COLUMN data_retention_policy.auto_delete IS 'Automatically delete after retention period';

-- Default retention policies
INSERT INTO data_retention_policy (table_name, data_type, retention_days, auto_delete, encryption_required, policy_description)
VALUES
    ('pii_access_log', 'audit', 2555, FALSE, FALSE, 'PII access logs retained for 7 years per compliance'),
    ('pii_redaction_log', 'audit', 2555, FALSE, FALSE, 'Redaction logs retained for 7 years per compliance'),
    ('analysis_results', 'business', NULL, FALSE, TRUE, 'Analysis results retained indefinitely, PII fields encrypted')
ON CONFLICT (table_name) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 5. Helper Functions
-- ----------------------------------------------------------------------------

-- Function to log PII access
CREATE OR REPLACE FUNCTION log_pii_access(
    p_user_email TEXT,
    p_action TEXT,
    p_table_name TEXT,
    p_record_id BIGINT,
    p_field_name TEXT,
    p_pii_type TEXT,
    p_access_reason TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO pii_access_log (
        user_email, action, table_name, record_id, field_name, pii_type, access_reason
    ) VALUES (
        p_user_email, p_action, p_table_name, p_record_id, p_field_name, p_pii_type, p_access_reason
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_pii_access IS 'Log PII access event for audit trail';

-- Function to log PII redaction
CREATE OR REPLACE FUNCTION log_pii_redaction(
    p_source_type TEXT,
    p_source_id TEXT,
    p_text_hash TEXT,
    p_pii_types TEXT[],
    p_redaction_count INTEGER,
    p_redaction_details JSONB,
    p_api_provider TEXT DEFAULT 'openai'
)
RETURNS BIGINT AS $$
DECLARE
    v_log_id BIGINT;
BEGIN
    INSERT INTO pii_redaction_log (
        source_type, source_id, original_text_hash, pii_types_found,
        redaction_count, redaction_details, was_sent_to_api, api_provider
    ) VALUES (
        p_source_type, p_source_id, p_text_hash, p_pii_types,
        p_redaction_count, p_redaction_details, TRUE, p_api_provider
    ) RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_pii_redaction IS 'Log PII redaction before sending to external API';

-- Function to check if data retention period has expired
CREATE OR REPLACE FUNCTION check_retention_expired(
    p_table_name TEXT,
    p_created_at TIMESTAMPTZ
)
RETURNS BOOLEAN AS $$
DECLARE
    v_retention_days INTEGER;
    v_auto_delete BOOLEAN;
BEGIN
    SELECT retention_days, auto_delete
    INTO v_retention_days, v_auto_delete
    FROM data_retention_policy
    WHERE table_name = p_table_name;

    -- If no policy or retention is NULL, keep forever
    IF v_retention_days IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if retention period has expired
    IF p_created_at + (v_retention_days || ' days')::INTERVAL < NOW() THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_retention_expired IS 'Check if record has exceeded retention period';

-- ----------------------------------------------------------------------------
-- 6. Compliance Views
-- ----------------------------------------------------------------------------

-- View: Recent PII Access Summary
CREATE OR REPLACE VIEW v_pii_access_summary AS
SELECT
    date_trunc('day', access_timestamp) AS access_date,
    action,
    pii_type,
    COUNT(*) AS access_count,
    COUNT(DISTINCT user_email) AS unique_users,
    COUNT(CASE WHEN success = FALSE THEN 1 END) AS failed_attempts
FROM pii_access_log
WHERE access_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY date_trunc('day', access_timestamp), action, pii_type
ORDER BY access_date DESC, access_count DESC;

COMMENT ON VIEW v_pii_access_summary IS 'Summary of PII access events (last 30 days)';

-- View: PII Redaction Summary
CREATE OR REPLACE VIEW v_pii_redaction_summary AS
SELECT
    date_trunc('day', created_at) AS redaction_date,
    source_type,
    api_provider,
    COUNT(*) AS redaction_count,
    SUM(redaction_count) AS total_redactions,
    COUNT(DISTINCT source_id) AS unique_documents
FROM pii_redaction_log
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY date_trunc('day', created_at), source_type, api_provider
ORDER BY redaction_date DESC;

COMMENT ON VIEW v_pii_redaction_summary IS 'Summary of PII redactions (last 30 days)';

-- ----------------------------------------------------------------------------
-- 7. Grants (adjust as needed for your setup)
-- ----------------------------------------------------------------------------

-- Grant read access to compliance views
-- GRANT SELECT ON v_pii_access_summary TO compliance_role;
-- GRANT SELECT ON v_pii_redaction_summary TO compliance_role;

-- Restrict direct access to PII logs (use functions instead)
-- REVOKE ALL ON pii_access_log FROM PUBLIC;
-- REVOKE ALL ON pii_redaction_log FROM PUBLIC;

PRINT 'PII Protection schema extensions applied successfully';
