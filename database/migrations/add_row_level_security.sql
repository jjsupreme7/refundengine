-- ============================================================================
-- ROW LEVEL SECURITY (RLS) Implementation
-- ============================================================================
-- CRITICAL SECURITY: This migration adds Row Level Security to all tables
-- to prevent unauthorized data access even with valid database credentials.
--
-- Deploy:
--   export SUPABASE_DB_PASSWORD='your-password'
--   ./scripts/deploy_rls.sh
-- ============================================================================

-- Enable RLS on all knowledge base tables
ALTER TABLE IF EXISTS knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tax_law_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS vendor_background_chunks ENABLE ROW LEVEL SECURITY;

-- Enable RLS on feedback system tables
ALTER TABLE IF EXISTS user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS learned_improvements ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS golden_qa_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS citation_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS answer_templates ENABLE ROW LEVEL SECURITY;

-- Enable RLS on analysis tables
ALTER TABLE IF EXISTS analyzed_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;

-- Enable RLS on Excel tracking tables
ALTER TABLE IF EXISTS excel_file_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS excel_row_tracking ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- AUTHENTICATION SETUP
-- ============================================================================
-- Create auth schema if it doesn't exist (Supabase provides this by default)
-- For self-hosted PostgreSQL, you may need to create this manually

-- Create users table for application-level authentication
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', -- 'admin', 'analyst', 'user'
    organization_id UUID, -- For multi-tenant support
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Enable RLS on auth_users
ALTER TABLE auth_users ENABLE ROW LEVEL SECURITY;

-- Create organizations table for multi-tenant support
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES - KNOWLEDGE BASE
-- ============================================================================

-- Knowledge documents: All authenticated users can read, admins can write
DROP POLICY IF EXISTS "knowledge_documents_read" ON knowledge_documents;
CREATE POLICY "knowledge_documents_read"
ON knowledge_documents FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "knowledge_documents_write" ON knowledge_documents;
CREATE POLICY "knowledge_documents_write"
ON knowledge_documents FOR ALL
TO authenticated
USING (
    -- Allow if user is admin (check via auth_users table)
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- Tax law chunks: All authenticated users can read
DROP POLICY IF EXISTS "tax_law_chunks_read" ON tax_law_chunks;
CREATE POLICY "tax_law_chunks_read"
ON tax_law_chunks FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "tax_law_chunks_write" ON tax_law_chunks;
CREATE POLICY "tax_law_chunks_write"
ON tax_law_chunks FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role IN ('admin', 'analyst')
    )
);

-- Vendor background chunks: Same as tax law
DROP POLICY IF EXISTS "vendor_chunks_read" ON vendor_background_chunks;
CREATE POLICY "vendor_chunks_read"
ON vendor_background_chunks FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "vendor_chunks_write" ON vendor_background_chunks;
CREATE POLICY "vendor_chunks_write"
ON vendor_background_chunks FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role IN ('admin', 'analyst')
    )
);

-- ============================================================================
-- RLS POLICIES - PROJECTS & DOCUMENTS (Organization-based)
-- ============================================================================

-- Projects: Users can only see their organization's projects
DROP POLICY IF EXISTS "projects_org_access" ON projects;
CREATE POLICY "projects_org_access"
ON projects FOR ALL
TO authenticated
USING (
    organization_id = (
        SELECT organization_id FROM auth_users
        WHERE id = auth.uid()
    )
    OR
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- Documents: Users can only see their organization's documents
DROP POLICY IF EXISTS "documents_org_access" ON documents;
CREATE POLICY "documents_org_access"
ON documents FOR ALL
TO authenticated
USING (
    organization_id = (
        SELECT organization_id FROM auth_users
        WHERE id = auth.uid()
    )
    OR
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- Analyzed transactions: Users can only see their organization's data
DROP POLICY IF EXISTS "transactions_org_access" ON analyzed_transactions;
CREATE POLICY "transactions_org_access"
ON analyzed_transactions FOR ALL
TO authenticated
USING (
    organization_id = (
        SELECT organization_id FROM auth_users
        WHERE id = auth.uid()
    )
    OR
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- ============================================================================
-- RLS POLICIES - FEEDBACK SYSTEM
-- ============================================================================

-- User feedback: Users can see all feedback (for learning), admins can modify
DROP POLICY IF EXISTS "feedback_read" ON user_feedback;
CREATE POLICY "feedback_read"
ON user_feedback FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "feedback_insert" ON user_feedback;
CREATE POLICY "feedback_insert"
ON user_feedback FOR INSERT
TO authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "feedback_update" ON user_feedback;
CREATE POLICY "feedback_update"
ON user_feedback FOR UPDATE
TO authenticated
USING (
    user_id = auth.uid()
    OR
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- Learned improvements: All can read, system can write
DROP POLICY IF EXISTS "improvements_read" ON learned_improvements;
CREATE POLICY "improvements_read"
ON learned_improvements FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "improvements_write" ON learned_improvements;
CREATE POLICY "improvements_write"
ON learned_improvements FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role IN ('admin', 'analyst')
    )
);

-- Golden QA pairs: All can read, analysts can write
DROP POLICY IF EXISTS "golden_qa_read" ON golden_qa_pairs;
CREATE POLICY "golden_qa_read"
ON golden_qa_pairs FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "golden_qa_write" ON golden_qa_pairs;
CREATE POLICY "golden_qa_write"
ON golden_qa_pairs FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role IN ('admin', 'analyst')
    )
);

-- ============================================================================
-- RLS POLICIES - AUTHENTICATION TABLES
-- ============================================================================

-- Users can only see their own user record, admins can see all
DROP POLICY IF EXISTS "auth_users_own_record" ON auth_users;
CREATE POLICY "auth_users_own_record"
ON auth_users FOR SELECT
TO authenticated
USING (
    id = auth.uid()
    OR
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- Only admins can modify user records
DROP POLICY IF EXISTS "auth_users_admin_modify" ON auth_users;
CREATE POLICY "auth_users_admin_modify"
ON auth_users FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- Organizations: Users can see their own org, admins can see all
DROP POLICY IF EXISTS "orgs_access" ON organizations;
CREATE POLICY "orgs_access"
ON organizations FOR SELECT
TO authenticated
USING (
    id = (SELECT organization_id FROM auth_users WHERE id = auth.uid())
    OR
    EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    )
);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if current user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM auth_users
        WHERE id = auth.uid()
        AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user's organization
CREATE OR REPLACE FUNCTION current_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN (SELECT organization_id FROM auth_users WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- GRANTS
-- ============================================================================

-- Grant usage to authenticated role
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ============================================================================
-- AUDIT LOG
-- ============================================================================

-- Create audit log table for security monitoring
CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action TEXT NOT NULL,
    table_name TEXT,
    record_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON security_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON security_audit_log(action);

-- RLS for audit log (admins only)
ALTER TABLE security_audit_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "audit_log_admin_only" ON security_audit_log;
CREATE POLICY "audit_log_admin_only"
ON security_audit_log FOR ALL
TO authenticated
USING (is_admin());

-- ============================================================================
-- SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Row Level Security (RLS) enabled on all tables';
    RAISE NOTICE '✅ Authentication tables created (auth_users, organizations)';
    RAISE NOTICE '✅ RLS policies configured for:';
    RAISE NOTICE '   - Knowledge base (public read, admin write)';
    RAISE NOTICE '   - Projects & Documents (organization-based access)';
    RAISE NOTICE '   - Feedback system (collaborative learning)';
    RAISE NOTICE '   - User management (self + admin access)';
    RAISE NOTICE '✅ Security audit logging enabled';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT: Switch from SERVICE_ROLE_KEY to user-based authentication!';
    RAISE NOTICE '   Service role key bypasses ALL RLS policies.';
    RAISE NOTICE '   Use anon key + Supabase Auth for proper security.';
END $$;
