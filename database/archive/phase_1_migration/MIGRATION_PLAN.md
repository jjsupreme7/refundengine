# Database Schema Migration Plan
**Goal**: Consolidate from dual schemas (old + new) to single new schema
**Timeline**: 3 weeks (Phase 1-3)
**Risk Level**: Medium (compatibility layer minimizes downtime risk)

---

## Overview

### Current State
- **OLD Schema**: `legal_documents`, `document_chunks`, `match_legal_chunks()`
- **NEW Schema**: `knowledge_documents`, `tax_law_chunks`, `vendor_background_chunks`, `search_tax_law()`
- **Status**: 30 files use NEW, 14 files use OLD

### Target State
- **Single Schema**: NEW schema only
- **All Code**: Uses `knowledge_documents` and separate chunk tables
- **Old Tables**: Dropped (after data migration if needed)

---

## Phase 1: Compatibility Layer & Infrastructure (Week 1)

### Goal
Create compatibility layer so old code continues working while using new schema underneath.

---

### Step 1.1: Check for Data in Old Tables

```bash
# Connect to Supabase and check if old tables have data
psql postgres://postgres:[PASSWORD]@db.[PROJECT].supabase.co/postgres

-- Check if old tables exist and have data
SELECT
    'legal_documents' as table_name,
    COUNT(*) as row_count
FROM legal_documents
UNION ALL
SELECT
    'document_chunks',
    COUNT(*)
FROM document_chunks;

-- If tables don't exist, skip data migration
-- If they have data, proceed with migration
```

**Decision Point**:
- If tables don't exist → Skip to Step 1.2
- If tables exist but empty → Skip to Step 1.2
- If tables have data → Create migration script (see Appendix A)

---

### Step 1.2: Create Compatibility Layer RPC Functions

Create SQL file: `database/migrations/migration_002_compatibility_layer.sql`

```sql
-- ============================================
-- COMPATIBILITY LAYER FOR OLD SCHEMA
-- Allows old code to work with new schema
-- ============================================

-- Function 1: match_legal_chunks (deprecated, redirects to search_tax_law)
CREATE OR REPLACE FUNCTION match_legal_chunks(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    chunk_text text,
    citation text,
    similarity float,
    chunk_number int,
    section_title text,
    law_category text
) AS $$
BEGIN
    -- Log deprecation warning
    RAISE WARNING 'match_legal_chunks() is deprecated. Use search_tax_law() instead.';

    -- Redirect to new function
    RETURN QUERY
    SELECT * FROM search_tax_law(
        query_embedding := query_embedding,
        match_threshold := match_threshold,
        match_count := match_count
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION match_legal_chunks IS
'DEPRECATED: Use search_tax_law() instead. This function will be removed in 90 days.';


-- Function 2: match_documents (if it exists)
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    chunk_text text,
    citation text,
    similarity float
) AS $$
BEGIN
    RAISE WARNING 'match_documents() is deprecated. Use search_knowledge_base() instead.';

    RETURN QUERY
    SELECT
        id,
        chunk_text,
        citation,
        1 - (embedding <=> query_embedding) as similarity
    FROM tax_law_chunks
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION match_documents IS
'DEPRECATED: Use search_knowledge_base() instead. This function will be removed in 90 days.';


-- View: legal_chunks → tax_law_chunks compatibility view
CREATE OR REPLACE VIEW legal_chunks AS
SELECT
    id,
    document_id,
    chunk_number,
    chunk_text,
    embedding,
    citation,
    law_category,
    section_title,
    created_at
FROM tax_law_chunks;

COMMENT ON VIEW legal_chunks IS
'DEPRECATED: Compatibility view for old code. Use tax_law_chunks directly.';
```

**Deploy**:
```bash
# Apply migration
psql $SUPABASE_DB_URL -f database/migrations/migration_002_compatibility_layer.sql

# Or via Supabase dashboard: SQL Editor → paste → run
```

---

### Step 1.3: Create Centralized Database Client

Create file: `core/database.py`

```python
#!/usr/bin/env python3
"""
Centralized Supabase Client
Singleton pattern - creates one client instance for entire application
"""

import os
from typing import Optional
from supabase import Client, create_client
from dotenv import load_dotenv

# Load environment once
load_dotenv()

# Singleton instances
_supabase_client: Optional[Client] = None
_supabase_client_config = {
    'url': None,
    'key': None
}


def get_supabase_client(force_recreate: bool = False) -> Client:
    """
    Get singleton Supabase client instance

    Args:
        force_recreate: Force create new client (for testing)

    Returns:
        Supabase Client instance

    Example:
        from core.database import get_supabase_client

        supabase = get_supabase_client()
        result = supabase.table('tax_law_chunks').select('*').execute()
    """
    global _supabase_client, _supabase_client_config

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )

    # Create new client if:
    # 1. Never created before
    # 2. Force recreate requested
    # 3. Config changed (different URL/key)
    if (
        _supabase_client is None
        or force_recreate
        or _supabase_client_config['url'] != url
        or _supabase_client_config['key'] != key
    ):
        _supabase_client = create_client(url, key)
        _supabase_client_config = {'url': url, 'key': key}
        print("✓ Supabase client initialized")

    return _supabase_client


def reset_client():
    """Reset client (useful for testing)"""
    global _supabase_client
    _supabase_client = None


# Convenience alias
supabase = get_supabase_client

# For backwards compatibility, export the client directly
# (but prefer using get_supabase_client() function)
__all__ = ['get_supabase_client', 'supabase', 'reset_client']
```

**Test**:
```python
# Test the new centralized client
python3 -c "
from core.database import get_supabase_client
sb = get_supabase_client()
result = sb.table('knowledge_documents').select('id', count='exact').execute()
print(f'✓ Database connection works! Found {result.count} documents')
"
```

---

### Step 1.4: Update One File as Proof of Concept

Update `chatbot/simple_chat.py` to use centralized client:

**BEFORE**:
```python
from supabase import create_client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
```

**AFTER**:
```python
from core.database import get_supabase_client
supabase = get_supabase_client()
```

**Test**:
```bash
python3 chatbot/simple_chat.py
# Should work exactly the same
```

---

## Phase 2: Code Migration (Week 2)

### Goal
Migrate all Python files to use new schema and centralized client.

---

### Step 2.1: Migrate Critical File - `core/enhanced_rag.py`

This is the **most important file** because it provides advanced RAG features.

#### Changes Needed:

**File**: `core/enhanced_rag.py`

**Change 1** - Update `basic_search()` method (line 49-62):

**BEFORE**:
```python
def basic_search(self, query: str, top_k: int = 5) -> List[Dict]:
    """Basic vector search (original implementation)"""
    query_embedding = self.get_embedding(query)

    response = self.supabase.rpc(
        "match_legal_chunks",  # ← OLD FUNCTION
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": top_k,
        },
    ).execute()

    return response.data if response.data else []
```

**AFTER**:
```python
def basic_search(self, query: str, top_k: int = 5) -> List[Dict]:
    """Basic vector search using new schema"""
    query_embedding = self.get_embedding(query)

    response = self.supabase.rpc(
        "search_tax_law",  # ← NEW FUNCTION
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": top_k,
        },
    ).execute()

    return response.data if response.data else []
```

**Change 2** - Update `_keyword_search()` method (line 411-432):

**BEFORE**:
```python
def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
    """Keyword-based search using PostgreSQL full-text search"""
    try:
        response = (
            self.supabase.table("legal_chunks")  # ← OLD TABLE
            .select("*")
            .textSearch("chunk_text", query)
            .limit(top_k)
            .execute()
        )
        # ...
```

**AFTER**:
```python
def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
    """Keyword-based search using PostgreSQL full-text search"""
    try:
        response = (
            self.supabase.table("tax_law_chunks")  # ← NEW TABLE
            .select("*")
            .textSearch("chunk_text", query)
            .limit(top_k)
            .execute()
        )
        # ...
```

**Change 3** - Update imports at top of file:

**BEFORE**:
```python
from supabase import Client

class EnhancedRAG:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
```

**AFTER** (two options):

**Option A** - Keep flexible (recommended):
```python
from supabase import Client
from core.database import get_supabase_client

class EnhancedRAG:
    def __init__(self, supabase_client: Client = None):
        """
        Args:
            supabase_client: Optional client. If None, uses centralized client.
        """
        self.supabase = supabase_client or get_supabase_client()
```

**Option B** - Force centralized:
```python
from core.database import get_supabase_client

class EnhancedRAG:
    def __init__(self):
        self.supabase = get_supabase_client()
```

**Test Enhanced RAG**:
```python
# Test script
from core.enhanced_rag import EnhancedRAG

rag = EnhancedRAG()
results = rag.basic_search("How is software taxed in Washington?", top_k=3)
print(f"✓ Found {len(results)} results")
for r in results:
    print(f"  - {r.get('citation')}: {r.get('chunk_text')[:100]}...")
```

---

### Step 2.2: Migrate Analysis Scripts

**Files to update**:
1. `analysis/fast_batch_analyzer.py`
2. `analysis/analyze_refunds.py`

**Pattern** (same for both):

**BEFORE**:
```python
from supabase import create_client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
```

**AFTER**:
```python
from core.database import get_supabase_client
supabase = get_supabase_client()
```

Check for any references to old tables/functions and update them.

---

### Step 2.3: Migrate Utility Scripts

**Files to update**:
1. `scripts/utils/clean_database.py`
2. `scripts/utils/check_supabase_tables.py`
3. `scripts/utils/clear_old_schema.py` (this one specifically references old schema)

For `clear_old_schema.py`, update to reference new tables:
- `legal_documents` → `knowledge_documents`
- `document_chunks` → `tax_law_chunks`, `vendor_background_chunks`

---

### Step 2.4: Bulk Update Remaining Files

Use this script to update all remaining files:

```bash
#!/bin/bash
# scripts/utils/migrate_to_centralized_client.sh

echo "Migrating Python files to use centralized database client..."

# Find all Python files that create Supabase clients
files=$(grep -r "create_client" --include="*.py" \
    --exclude-dir="venv" \
    --exclude-dir="node_modules" \
    --exclude-dir=".git" \
    -l .)

total=0
updated=0

for file in $files; do
    ((total++))

    # Skip if already uses centralized client
    if grep -q "from core.database import get_supabase_client" "$file"; then
        echo "  ✓ $file (already migrated)"
        continue
    fi

    # Check if it creates a client
    if grep -q "supabase.*=.*create_client" "$file"; then
        echo "  → Updating $file"

        # Backup original
        cp "$file" "$file.backup"

        # Update imports
        sed -i '' 's/from supabase import create_client$/from core.database import get_supabase_client/' "$file"

        # Update client creation
        sed -i '' 's/supabase.*=.*create_client(.*$/supabase = get_supabase_client()/' "$file"

        ((updated++))
    fi
done

echo ""
echo "Migration complete!"
echo "  Total files checked: $total"
echo "  Files updated: $updated"
echo ""
echo "⚠️  Please review changes and test each updated file"
echo "    Backup files saved as *.backup"
```

Run:
```bash
chmod +x scripts/utils/migrate_to_centralized_client.sh
./scripts/utils/migrate_to_centralized_client.sh
```

---

### Step 2.5: Test All Updated Files

Create test script:

```bash
#!/bin/bash
# scripts/utils/test_migrated_files.sh

echo "Testing migrated files..."

# Test ingestion
echo "1. Testing document ingestion..."
python3 core/ingest_documents.py --help
if [ $? -eq 0 ]; then echo "  ✓ ingest_documents.py"; else echo "  ✗ FAILED"; fi

# Test chatbot
echo "2. Testing chatbot..."
echo "quit" | python3 chatbot/simple_chat.py
if [ $? -eq 0 ]; then echo "  ✓ simple_chat.py"; else echo "  ✗ FAILED"; fi

# Test enhanced RAG
echo "3. Testing enhanced RAG..."
python3 -c "from core.enhanced_rag import EnhancedRAG; rag = EnhancedRAG(); print('✓ EnhancedRAG works')"

# Test metadata export
echo "4. Testing metadata export..."
python3 scripts/export_metadata_excel.py --dry-run
if [ $? -eq 0 ]; then echo "  ✓ export_metadata_excel.py"; else echo "  ✗ FAILED"; fi

echo ""
echo "Testing complete!"
```

---

## Phase 3: Cleanup & Documentation (Week 3)

### Goal
Remove old schema artifacts and finalize documentation.

---

### Step 3.1: Remove Compatibility Layer

After confirming all code works with new schema for 1 week:

```sql
-- database/migrations/migration_003_remove_compatibility_layer.sql

-- Drop deprecated functions
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int);
DROP FUNCTION IF EXISTS match_documents(vector, float, int);

-- Drop compatibility view
DROP VIEW IF EXISTS legal_chunks;

-- Drop old tables (if they exist and are empty)
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS legal_documents;
```

---

### Step 3.2: Investigate `refundengine/` Directory

```bash
# Check if it's a duplicate
diff -r core/ refundengine/core/
diff -r chatbot/ refundengine/chatbot/

# If identical, remove it
rm -rf refundengine/

# If different, investigate why
```

---

### Step 3.3: Create Database README

Create `database/README.md` (see next step in implementation).

---

### Step 3.4: Add Inline SQL Comments

```sql
-- database/migrations/migration_004_add_documentation.sql

-- Document tables
COMMENT ON TABLE knowledge_documents IS
'Master table for all knowledge base documents (tax law + vendor background). Replaces old legal_documents table.';

COMMENT ON TABLE tax_law_chunks IS
'Text chunks from tax law documents with vector embeddings for semantic search.';

COMMENT ON TABLE vendor_background_chunks IS
'Text chunks from vendor/product documentation with vector embeddings.';

-- Document columns
COMMENT ON COLUMN knowledge_documents.document_type IS
'Type of document: ''tax_law'' or ''vendor_background''';

COMMENT ON COLUMN tax_law_chunks.embedding IS
'1536-dimension vector from OpenAI text-embedding-3-small model';

COMMENT ON COLUMN tax_law_chunks.law_category IS
'Category: exemption, rate, definition, software, digital_goods, etc.';

-- Document functions
COMMENT ON FUNCTION search_tax_law IS
'Search tax law chunks using vector similarity. Returns top N most similar chunks.';

COMMENT ON FUNCTION search_vendor_background IS
'Search vendor background chunks. Supports optional vendor name filtering.';

COMMENT ON FUNCTION search_knowledge_base IS
'Combined search across both tax law and vendor documents.';
```

---

## Rollback Plan

If something goes wrong:

### Rollback Phase 2 (Code Changes)

```bash
# Restore all backup files
for backup in **/*.backup; do
    original="${backup%.backup}"
    cp "$backup" "$original"
    echo "Restored $original"
done
```

### Rollback Phase 1 (Compatibility Layer)

```sql
-- Remove compatibility functions/views
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int);
DROP VIEW IF EXISTS legal_chunks;
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Compatibility layer deployed to Supabase
- [ ] `core/database.py` created and tested
- [ ] At least 1 file successfully using centralized client
- [ ] No errors in logs

### Phase 2 Complete When:
- [ ] `core/enhanced_rag.py` migrated and tested
- [ ] All analysis scripts migrated
- [ ] All utility scripts migrated
- [ ] All 44 files using centralized client
- [ ] No old table/function references remain in code
- [ ] All tests passing

### Phase 3 Complete When:
- [ ] Compatibility layer removed
- [ ] Old tables dropped
- [ ] Documentation complete
- [ ] `refundengine/` directory resolved
- [ ] No deprecation warnings in logs

---

## Appendix A: Data Migration Script

Only needed if old tables contain data:

```sql
-- database/migrations/migration_001_data_migration.sql

-- Migrate legal_documents → knowledge_documents
INSERT INTO knowledge_documents (
    id, document_type, title, citation, law_category,
    source_file, processing_status, created_at
)
SELECT
    id,
    'tax_law' as document_type,
    title,
    citation,
    COALESCE(category, 'general') as law_category,
    source_file,
    status as processing_status,
    created_at
FROM legal_documents
WHERE NOT EXISTS (
    SELECT 1 FROM knowledge_documents WHERE knowledge_documents.id = legal_documents.id
);

-- Migrate document_chunks → tax_law_chunks
INSERT INTO tax_law_chunks (
    id, document_id, chunk_number, chunk_text, embedding,
    citation, law_category, created_at
)
SELECT
    id, document_id, chunk_number, chunk_text, embedding,
    citation,
    COALESCE(category, 'general') as law_category,
    created_at
FROM document_chunks
WHERE NOT EXISTS (
    SELECT 1 FROM tax_law_chunks WHERE tax_law_chunks.id = document_chunks.id
);

-- Verify counts match
SELECT 'legal_documents' as source, COUNT(*) FROM legal_documents
UNION ALL
SELECT 'knowledge_documents', COUNT(*) FROM knowledge_documents;

SELECT 'document_chunks' as source, COUNT(*) FROM document_chunks
UNION ALL
SELECT 'tax_law_chunks', COUNT(*) FROM tax_law_chunks;
```

---

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Phase 1: Infrastructure | Compatibility layer, centralized client, proof of concept |
| 2 | Phase 2: Code Migration | All files migrated, tests passing |
| 3 | Phase 3: Cleanup | Old schema removed, documentation complete |

**Total Duration**: 3 weeks
**Risk**: Medium (compatibility layer reduces risk)
**Reversible**: Yes (until Phase 3 cleanup)
