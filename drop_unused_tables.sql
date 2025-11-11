-- ============================================================================
-- DROP UNUSED/EMPTY SUPABASE TABLES
-- ============================================================================
--
-- These tables are from old schema (Script 1) and are no longer used.
-- The active schema uses: knowledge_documents, tax_law_chunks, vendor_background_chunks
--
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/YOUR_PROJECT/sql
-- ============================================================================

-- Drop old schema tables (empty and unused)
DROP TABLE IF EXISTS legal_documents CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS document_metadata CASCADE;

-- Verify tables are dropped
SELECT
    tablename
FROM
    pg_tables
WHERE
    schemaname = 'public'
    AND tablename IN ('legal_documents', 'document_chunks', 'document_metadata')
ORDER BY
    tablename;
-- Should return 0 rows if successful

-- Show remaining active tables
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM
    pg_tables
WHERE
    schemaname = 'public'
    AND tablename LIKE '%document%' OR tablename LIKE '%chunk%'
ORDER BY
    tablename;
