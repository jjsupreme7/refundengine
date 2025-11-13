# Database Schema Audit Report
**Date**: 2025-11-12
**Issue**: Dual Schema Architecture (Old vs New)

## Executive Summary

🚨 **CRITICAL FINDING**: The codebase has **TWO PARALLEL SCHEMAS** running simultaneously, with Python code using different schemas inconsistently. This creates:
- Data fragmentation
- Confusion about which tables/functions to use
- Maintenance overhead
- Potential data sync issues

---

## Schema Comparison

### OLD SCHEMA (Legacy)
**Tables**:
- `legal_documents` - Master document table
- `document_chunks` - Chunks with embeddings (combined for all document types)
- Also referred to as `legal_chunks` in some RPC functions

**RPC Functions**:
- `match_documents()` - Original search function
- `match_legal_chunks()` - Vector similarity search

**Characteristics**:
- Single combined table for all chunks
- No separation between tax law and vendor documents
- Simpler structure but less flexible

---

### NEW SCHEMA (Current/Recommended)
**Tables**:
- `knowledge_documents` - Master document table (replaces `legal_documents`)
- `tax_law_chunks` - Separate table for tax law chunks
- `vendor_background_chunks` - Separate table for vendor document chunks

**RPC Functions**:
- `search_tax_law()` - Search tax law chunks only
- `search_vendor_background()` - Search vendor chunks only
- `search_knowledge_base()` - Combined search across both types

**Characteristics**:
- Separated chunk tables for better organization
- Type-specific metadata fields
- More flexible filtering and search options
- Supports advanced features (category filters, vendor filters, etc.)

---

## Python Files Using OLD SCHEMA (14 files)

### Core Files
1. **core/enhanced_rag.py** ⚠️ CRITICAL
   - Line 54: `match_legal_chunks` RPC
   - Line 416: Direct `legal_chunks` table access
   - **Impact**: Advanced RAG features using old schema

### Analysis Files
2. **analysis/fast_batch_analyzer.py**
3. **analysis/analyze_refunds.py**

### Utility Scripts
4. **scripts/utils/clean_database.py**
5. **scripts/utils/clear_old_schema.py**
6. **scripts/utils/check_supabase_tables.py**

### Duplicates (refundengine/ mirror)
7-14. Duplicate files in `refundengine/` directory

---

## Python Files Using NEW SCHEMA (30 files)

### Chatbot Interface ✅ GOOD
1. **chatbot/chat_rag.py**
   - Line 72: `search_tax_law()` RPC
   - Line 82: `tax_law_chunks` table
   - Line 116: `search_vendor_background()` RPC
   - Line 308: `knowledge_documents` table
   - **Status**: Fully migrated to new schema

2. **chatbot/simple_chat.py**
3. **chatbot/test_rag.py**
4. **chatbot/web_chat.py**

### Core Ingestion ✅ GOOD
5. **core/ingest_documents.py**
   - Uses `knowledge_documents` table
   - **Status**: Fully migrated

6. **core/ingest_large_document.py**
   - Line 134: `knowledge_documents` table
   - Line 161-163: `tax_law_chunks` / `vendor_background_chunks`
   - **Status**: Fully migrated

### Metadata Management ✅ GOOD
7. **scripts/export_metadata_excel.py**
8. **scripts/import_metadata_excel.py**
9. **scripts/populate_file_urls.py**
10. **scripts/add_page_numbers_to_chunks.py**

### Infrastructure
11. **scripts/deploy_url_rpc_updates.py**
12. **scripts/utils/deploy_simple_schema.py**
13. **scripts/ingest_test_data.py**
14. **scripts/research_vendors.py**
15. **scripts/upload_knowledge_base_to_storage.py**
16. **scripts/download_knowledge_base_from_storage.py**

### Other
17-30. Additional utility and analysis files

---

## Files Creating Supabase Clients (44 files)

**Problem**: Each file creates its own client instance:
```python
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
```

**Impact**:
- 20+ separate client instances
- Connection overhead
- No centralized configuration
- Difficult to implement connection pooling

---

## Migration Priority

### P0 - CRITICAL (Complete This Week)

#### 1. Migrate `core/enhanced_rag.py` to New Schema
**Why Critical**: This file provides advanced RAG features (Corrective RAG, Reranking, Query Expansion, Hybrid Search) but uses the OLD schema.

**Changes Needed**:
- Line 54: Change `match_legal_chunks` → `search_tax_law`
- Line 416: Change `legal_chunks` table → `tax_law_chunks` table
- Update method signatures to support new schema's metadata filters

**Files Impacted**: Any code that imports `EnhancedRAG` class

---

#### 2. Deprecate Old Tables & Functions
**Actions**:
1. Add deprecation notices to old RPC functions
2. Update old functions to redirect to new functions (compatibility layer)
3. Create migration script to copy data from old → new tables (if needed)
4. Set timeline for removing old schema (90 days?)

---

### P1 - HIGH (Complete in 2 Weeks)

#### 3. Update Analysis Scripts
- `analysis/fast_batch_analyzer.py`
- `analysis/analyze_refunds.py`

#### 4. Update Utility Scripts
- `scripts/utils/clean_database.py`
- `scripts/utils/check_supabase_tables.py`

#### 5. Centralize Supabase Client
Create `core/database.py` singleton to replace 44 separate client creations

---

### P2 - MEDIUM (Complete in 1 Month)

#### 6. Remove Duplicate Files
The `refundengine/` directory appears to be a mirror. Investigate if it's needed.

#### 7. Drop Old Tables
After all code is migrated, drop:
- `legal_documents` (if exists)
- `document_chunks` (if exists)
- `legal_chunks` (if exists)

---

## Recommended Migration Path

### Phase 1: Compatibility Layer (Week 1)
1. Update old RPC functions to call new functions internally
2. This allows old code to continue working while using new schema
3. Log deprecation warnings

**Example**:
```sql
-- Old function (deprecated but still works)
CREATE OR REPLACE FUNCTION match_legal_chunks(...)
RETURNS SETOF tax_law_chunks AS $$
BEGIN
    -- Log deprecation
    RAISE WARNING 'match_legal_chunks is deprecated, use search_tax_law instead';

    -- Call new function
    RETURN QUERY SELECT * FROM search_tax_law(...);
END;
$$ LANGUAGE plpgsql;
```

### Phase 2: Code Migration (Week 2)
1. Update `core/enhanced_rag.py` to new schema
2. Update analysis scripts
3. Update utility scripts
4. Test all functionality

### Phase 3: Cleanup (Week 3-4)
1. Remove compatibility layer
2. Drop old tables (after confirming no data needed)
3. Remove old RPC functions
4. Update documentation

---

## SQL Schema Files Status

| File | Purpose | Status |
|------|---------|--------|
| `database/supabase_schema.sql` | Original/legacy schema | OLD |
| `database/schema/schema_knowledge_base.sql` | New knowledge base schema | **CURRENT** ✅ |
| `database/schema/schema_vendor_learning.sql` | Vendor learning system | ACTIVE ✅ |
| `database/schema/schema_pii_protection.sql` | PII compliance | ACTIVE ✅ |
| `database/schema/schema_simple.sql` | Simplified schema | UNCLEAR |
| `database/schema/schema_update.sql` | Schema updates/migrations | MIGRATION |
| `database/migrations/migration_*.sql` | Migration scripts | ACTIVE ✅ |

---

## Action Items

### Immediate (This Week)
- [ ] Create `core/database.py` with singleton Supabase client
- [ ] Migrate `core/enhanced_rag.py` to new schema
- [ ] Add compatibility layer to old RPC functions
- [ ] Test chatbot and ingestion still work

### Short-term (2 Weeks)
- [ ] Migrate analysis scripts to new schema
- [ ] Migrate utility scripts to new schema
- [ ] Update all imports to use centralized database client
- [ ] Create comprehensive database README

### Long-term (1 Month)
- [ ] Remove compatibility layer
- [ ] Drop old tables (after data migration if needed)
- [ ] Remove duplicate `refundengine/` directory if not needed
- [ ] Add query performance monitoring

---

## Questions to Answer

1. **Does `refundengine/` directory need to exist?**
   - Appears to be a duplicate of main code
   - Check if it's imported anywhere

2. **Is there data in old tables that needs migration?**
   - Check `legal_documents` for records
   - Check `document_chunks` / `legal_chunks` for data
   - Migrate if needed before dropping

3. **What is `schema_simple.sql` for?**
   - Purpose unclear
   - Need to investigate if it's used

4. **Migration timeline - how aggressive?**
   - Recommend 90-day deprecation period
   - Or immediate cutover if no production users yet

---

## Conclusion

The dual schema architecture is a **critical architectural debt** that needs immediate attention. The good news: Most code (30 files) already uses the NEW schema. Only 14 files need migration, with **1 critical file** (`enhanced_rag.py`) requiring immediate attention.

**Recommended Action**: Follow Phase 1-3 migration path with compatibility layer to ensure zero downtime.
