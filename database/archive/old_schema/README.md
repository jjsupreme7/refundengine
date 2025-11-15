# Archived Old Schema Files

This folder contains deprecated schema files from the old database structure.

## Status: DEPRECATED - DO NOT USE

These files are kept for historical reference only and should NOT be used for new development.

## Files in This Archive

### supabase_schema.sql
- **Status**: DEPRECATED as of November 2025
- **Replaced by**: `database/schema/schema_knowledge_base.sql`
- **Old tables**: `legal_documents`, `document_chunks`, `document_metadata`
- **New tables**: `knowledge_documents`, `tax_law_chunks`, `vendor_background_chunks`
- **Reason for deprecation**: The new schema provides better separation between tax law and vendor documents, improved metadata structure, and more flexible search capabilities

### rpc_match_legal_chunks.sql
- **Status**: DEPRECATED as of November 2025
- **Replaced by**: `search_tax_law()`, `search_vendor_background()`, `search_knowledge_base()` RPC functions
- **Old function**: `match_legal_chunks()`
- **Reason for deprecation**: New RPC functions support type-specific searching and better metadata filtering

## Migration Information

The codebase was migrated to the new schema in November 2025:
- ✅ Core RAG system migrated to new schema
- ✅ Chatbot files migrated to new schema
- ✅ Ingestion scripts migrated to new schema
- ✅ Compatibility layer deployed (allows old function names to work temporarily)

For migration details, see:
- `database/README.md` - Current schema documentation
- `docs/reports/SCHEMA_AUDIT_REPORT_2025-11-13.md` - Migration audit report
- `database/archive/phase_1_migration/` - Detailed migration plan

## Current Schema

**Always use the current schema**:
- Schema file: `database/schema/schema_knowledge_base.sql`
- Tables: `knowledge_documents`, `tax_law_chunks`, `vendor_background_chunks`
- RPC functions: `search_tax_law()`, `search_vendor_background()`, `search_knowledge_base()`

## Questions?

See the main database README: `database/README.md`
