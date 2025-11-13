-- Add file_url column to knowledge_documents table
-- This column stores URLs to access the original source documents

ALTER TABLE knowledge_documents
ADD COLUMN IF NOT EXISTS file_url text;

COMMENT ON COLUMN knowledge_documents.file_url IS
'URL to access the original source document (for clickable links in UI)';

SELECT 'Column file_url added successfully' as status;
