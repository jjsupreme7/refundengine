-- Migration 006: Add chunk_role column to tax_law_chunks
-- Purpose: Enable semantic classification of chunks (definition, rule, example, exception, procedure)
-- Date: 2024-12-14

-- Add chunk_role column with default value of 'rule'
ALTER TABLE tax_law_chunks
ADD COLUMN IF NOT EXISTS chunk_role TEXT DEFAULT 'rule';

-- Add index for efficient filtering by role
CREATE INDEX IF NOT EXISTS idx_tax_chunks_role ON tax_law_chunks(chunk_role);

-- Add comment for documentation
COMMENT ON COLUMN tax_law_chunks.chunk_role IS 'Semantic role of chunk: definition, rule, example, exception, or procedure';
