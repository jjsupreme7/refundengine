# Database Documentation
**Washington State Tax Refund Engine - Database Schema**

📅 **Last Updated**: 2025-11-12
🎯 **Current Schema Version**: Knowledge Base Schema (New)
⚠️ **Migration Status**: In progress (see [MIGRATION_PLAN.md](./MIGRATION_PLAN.md))

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Schema Modules](#schema-modules)
4. [Core Tables](#core-tables)
5. [RPC Functions](#rpc-functions)
6. [Python Integration](#python-integration)
7. [Common Queries](#common-queries)
8. [Maintenance](#maintenance)

---

## Quick Start

### Connect to Database

```python
from core.database import get_supabase_client

# Get centralized client (recommended)
supabase = get_supabase_client()

# Query documents
docs = supabase.table('knowledge_documents').select('*').execute()
```

### Search Tax Law

```python
from openai import OpenAI
client = OpenAI()

# 1. Generate embedding
query = "How is SaaS taxed in Washington?"
embedding = client.embeddings.create(
    input=query,
    model="text-embedding-3-small"
).data[0].embedding

# 2. Search database
results = supabase.rpc('search_tax_law', {
    'query_embedding': embedding,
    'match_threshold': 0.7,
    'match_count': 5
}).execute()

# 3. Use results
for chunk in results.data:
    print(f"{chunk['citation']}: {chunk['chunk_text'][:200]}...")
```

---

## Architecture Overview

### Database Provider
- **Platform**: Supabase (PostgreSQL 15+)
- **Extensions**: pgvector (for vector similarity search)
- **Location**: Cloud-hosted
- **Access**: Via Supabase client SDK

### Schema Philosophy

The database uses a **Knowledge Base** architecture:
- **Separation of Concerns**: Different tables for tax law vs vendor data
- **Vector Search**: pgvector embeddings for semantic similarity
- **Metadata Filtering**: Rich metadata for targeted searches
- **Audit Trail**: PII compliance and data lineage tracking

### Key Features

1. **Semantic Search** - Find relevant law by meaning, not just keywords
2. **Hybrid Search** - Combine vector similarity + text search
3. **Metadata Filters** - Search by category, citation, vendor, etc.
4. **Page Number Tracking** - Link chunks back to source PDF pages
5. **PII Protection** - GDPR/CCPA compliance built-in

---

## Schema Modules

The database is organized into 5 modules:

### 1. Knowledge Base (Core) ✅ **CURRENT**
**File**: `schema/schema_knowledge_base.sql`

**Purpose**: Store and search tax law + vendor documentation

**Tables**:
- `knowledge_documents` - Master document registry
- `tax_law_chunks` - Tax law text chunks with embeddings
- `vendor_background_chunks` - Vendor product chunks with embeddings

**Functions**:
- `search_tax_law()` - Search tax law semantically
- `search_vendor_background()` - Search vendor docs
- `search_knowledge_base()` - Combined search

**Status**: ✅ Active, use this for all new code

---

### 2. Vendor Learning System
**File**: `schema/schema_vendor_learning.sql`

**Purpose**: Human-in-the-loop machine learning for invoice analysis

**Tables**:
- `vendor_products` - Learned product information
- `analysis_results` - AI invoice analysis results
- `analysis_reviews` - Human corrections/feedback
- `vendor_product_patterns` - Extracted patterns for matching
- `audit_trail` - Complete audit log

**Workflow**:
1. AI analyzes invoice → `analysis_results`
2. Human reviews → `analysis_reviews`
3. System learns from corrections → `vendor_products`, `vendor_product_patterns`
4. Future analysis improves based on learned patterns

**Triggers**:
- `update_vendor_learning()` - Auto-learns from human reviews

---

### 3. PII Protection
**File**: `schema/schema_pii_protection.sql`

**Purpose**: GDPR/CCPA compliance, audit trail for PII access

**Tables**:
- `pii_access_log` - Every PII access logged
- `pii_redaction_log` - Text redaction before sending to AI
- `data_retention_policy` - Configurable retention rules

**Functions**:
- `log_pii_access()` - Call before accessing sensitive data
- `log_pii_redaction()` - Call before sending to external APIs
- `check_retention_expired()` - Check if data should be deleted

**Compliance**: Ensures you can answer "Who accessed this data?" and "Was PII sent to AI?"

---

### 4. Legacy Schema ⚠️ **DEPRECATED**
**File**: `supabase_schema.sql`

**Tables**:
- `legal_documents` → Replaced by `knowledge_documents`
- `document_chunks` → Replaced by `tax_law_chunks`

**Functions**:
- `match_documents()` → Use `search_tax_law()` instead
- `match_legal_chunks()` → Use `search_tax_law()` instead

**Status**: ⚠️ Deprecated, do NOT use for new code

---

### 5. Migrations
**Directory**: `migrations/`

**Purpose**: Track schema evolution

**Files**:
- `migration_001_add_state_support.sql` - Multi-state support
- `migration_002_compatibility_layer.sql` - Old → New schema bridge
- `migration_vendor_metadata.sql` - Vendor learning fields

---

## Core Tables

### `knowledge_documents` (Master Registry)

**Purpose**: Central registry of all documents in knowledge base

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `document_type` | TEXT | `'tax_law'` or `'vendor_background'` |
| `title` | TEXT | Document title |
| `citation` | TEXT | RCW/WAC reference (for tax law) |
| `law_category` | TEXT | `'exemption'`, `'rate'`, `'software'`, etc. |
| `vendor_name` | TEXT | Vendor name (for vendor docs) |
| `vendor_category` | TEXT | `'manufacturer'`, `'distributor'`, etc. |
| `source_file` | TEXT | Path to original PDF |
| `file_url` | TEXT | Public URL (Supabase Storage) |
| `processing_status` | TEXT | `'pending'`, `'processing'`, `'completed'`, `'error'` |
| `total_chunks` | INTEGER | Number of chunks generated |
| `effective_date` | DATE | Law effective date |
| `custom_tags` | JSONB | Flexible metadata |

**Example**:
```sql
SELECT * FROM knowledge_documents
WHERE document_type = 'tax_law'
  AND law_category = 'software'
ORDER BY citation;
```

---

### `tax_law_chunks` (Tax Law Text Chunks)

**Purpose**: Searchable text chunks from tax law documents

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `document_id` | UUID | FK → `knowledge_documents.id` |
| `chunk_number` | INTEGER | Sequence number (1, 2, 3...) |
| `chunk_text` | TEXT | Actual text content (500-1500 words) |
| `embedding` | VECTOR(1536) | OpenAI embedding for semantic search |
| `citation` | TEXT | RCW/WAC reference |
| `section_title` | TEXT | Section heading + page number |
| `law_category` | TEXT | Category for filtering |
| `hierarchy_level` | INTEGER | Nesting level (1 = top) |
| `parent_section` | TEXT | Parent section reference |

**Indexes**:
- `idx_tax_chunks_embedding` - IVFFlat vector index for fast similarity search
- `idx_tax_chunks_document_id` - Foreign key index
- `idx_tax_chunks_citation` - Filter by citation
- `idx_tax_chunks_category` - Filter by category

**Example**:
```sql
-- Get all chunks for a specific document
SELECT
    chunk_number,
    citation,
    section_title,
    LEFT(chunk_text, 200) as preview
FROM tax_law_chunks
WHERE document_id = 'your-doc-id-here'
ORDER BY chunk_number;
```

---

### `vendor_background_chunks` (Vendor Documentation)

**Purpose**: Searchable chunks from vendor product documentation

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `document_id` | UUID | FK → `knowledge_documents.id` |
| `chunk_number` | INTEGER | Sequence number |
| `chunk_text` | TEXT | Actual text content |
| `embedding` | VECTOR(1536) | OpenAI embedding |
| `vendor_name` | TEXT | Vendor name |
| `vendor_category` | TEXT | Vendor type |
| `document_category` | TEXT | Document type (catalog, spec, etc.) |
| `product_categories` | TEXT[] | Array of product categories |

**Example**:
```sql
-- Find all Microsoft product docs
SELECT * FROM vendor_background_chunks
WHERE vendor_name = 'Microsoft'
  AND 'software' = ANY(product_categories);
```

---

## RPC Functions

### `search_tax_law()`

**Purpose**: Search tax law chunks using vector similarity

**Signature**:
```sql
search_tax_law(
    query_embedding VECTOR(1536),     -- Query embedding from OpenAI
    match_threshold FLOAT DEFAULT 0.5, -- Similarity threshold (0-1)
    match_count INT DEFAULT 5,         -- Max results to return
    law_category_filter TEXT DEFAULT NULL -- Optional category filter
)
RETURNS TABLE (
    id UUID,
    chunk_text TEXT,
    citation TEXT,
    similarity FLOAT,
    chunk_number INT,
    section_title TEXT,
    law_category TEXT,
    document_id UUID,
    file_url TEXT
)
```

**Python Usage**:
```python
results = supabase.rpc('search_tax_law', {
    'query_embedding': embedding,
    'match_threshold': 0.7,          # 70% similarity minimum
    'match_count': 5,                 # Top 5 results
    'law_category_filter': 'software' # Optional: only software-related
}).execute()
```

**How it Works**:
1. Compares `query_embedding` to all chunk embeddings
2. Calculates cosine similarity: `1 - (embedding <=> query_embedding)`
3. Filters by threshold (keeps similarity > 0.7)
4. Optionally filters by `law_category`
5. Returns top N most similar chunks

---

### `search_vendor_background()`

**Purpose**: Search vendor documentation

**Signature**:
```sql
search_vendor_background(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5,
    vendor_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    chunk_text TEXT,
    vendor_name TEXT,
    similarity FLOAT,
    document_category TEXT,
    vendor_category TEXT
)
```

---

### `search_knowledge_base()`

**Purpose**: Combined search across both tax law AND vendor docs

**Signature**:
```sql
search_knowledge_base(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    tax_law_count INT DEFAULT 3,      -- How many tax law results
    vendor_bg_count INT DEFAULT 2     -- How many vendor results
)
```

**Returns**: Combined results from both tables, deduplicated and sorted by similarity

---

## Python Integration

### Recommended Pattern: Centralized Client

```python
# core/database.py (singleton)
from core.database import get_supabase_client

# Use everywhere
supabase = get_supabase_client()
```

### Document Ingestion

```python
from core.ingest_large_document import ingest_large_document

# Ingest tax law document
success = ingest_large_document(
    pdf_path='knowledge_base/states/washington/legal_documents/WAC_458-20-15502.pdf',
    document_type='tax_law',
    title='Computer Software',
    citation='WAC 458-20-15502',
    law_category='software'
)
```

### RAG Chatbot

```python
from chatbot.chat_rag import RAGChatbot

bot = RAGChatbot()
bot.chat()  # Interactive chat interface
```

### Enhanced RAG (Advanced)

```python
from core.enhanced_rag import EnhancedRAG

rag = EnhancedRAG()

# Method 1: Basic vector search
results = rag.basic_search("How is SaaS taxed?", top_k=5)

# Method 2: Corrective RAG (validates relevance)
results = rag.search_with_correction("How is SaaS taxed?", top_k=5)

# Method 3: Reranking (AI improves order)
results = rag.search_with_reranking("How is SaaS taxed?", top_k=5)

# Method 4: Query expansion (multiple query variations)
results = rag.search_with_expansion("How is SaaS taxed?", top_k=5)

# Method 5: Hybrid (vector + keyword search)
results = rag.search_hybrid("How is SaaS taxed?", top_k=5)

# Method 6: Enhanced (ALL improvements combined)
results = rag.search_enhanced("How is SaaS taxed?", top_k=5)
```

---

## Common Queries

### Get Document Statistics

```sql
SELECT
    document_type,
    law_category,
    COUNT(*) as doc_count,
    SUM(total_chunks) as total_chunks
FROM knowledge_documents
WHERE processing_status = 'completed'
GROUP BY document_type, law_category
ORDER BY doc_count DESC;
```

### Find Documents by Citation

```sql
SELECT
    title,
    citation,
    total_chunks,
    file_url
FROM knowledge_documents
WHERE citation ILIKE '%WAC 458-20-15502%'
  AND document_type = 'tax_law';
```

### Check Vector Search Performance

```sql
-- Enable timing
\timing on

-- Run search
SELECT * FROM search_tax_law(
    '{0.1, 0.2, ...}'::vector,  -- Your embedding here
    0.7,
    10
);

-- Check query plan
EXPLAIN ANALYZE
SELECT * FROM search_tax_law('{0.1, ...}'::vector, 0.7, 10);
```

### Find Chunks with Page Numbers

```sql
SELECT
    citation,
    section_title,  -- Contains "Page X"
    chunk_number,
    LEFT(chunk_text, 150) as preview
FROM tax_law_chunks
WHERE citation = 'WAC 458-20-15502'
  AND section_title LIKE '%Page%'
ORDER BY chunk_number;
```

### Audit PII Access (Last 30 Days)

```sql
SELECT
    user_email,
    action,
    pii_type,
    COUNT(*) as access_count,
    MAX(access_timestamp) as last_access
FROM pii_access_log
WHERE access_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY user_email, action, pii_type
ORDER BY access_count DESC;
```

---

## Maintenance

### Vacuum and Analyze (Monthly)

```sql
-- Reclaim space and update statistics
VACUUM ANALYZE knowledge_documents;
VACUUM ANALYZE tax_law_chunks;
VACUUM ANALYZE vendor_background_chunks;
```

### Check Index Usage

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('tax_law_chunks', 'vendor_background_chunks')
ORDER BY idx_scan ASC;  -- Low idx_scan = unused index
```

### Reindex Vectors (If Search Slows Down)

```sql
-- Rebuild vector indexes
REINDEX INDEX idx_tax_chunks_embedding;
REINDEX INDEX idx_vendor_chunks_embedding;
```

### Monitor Embedding Quality

```sql
-- Check for NULL embeddings (indicates ingestion failure)
SELECT
    document_id,
    COUNT(*) as chunks_missing_embeddings
FROM tax_law_chunks
WHERE embedding IS NULL
GROUP BY document_id;
```

---

## Migration Notes

⚠️ **Currently in migration from OLD → NEW schema**

**Status**: Phase 1 (Compatibility Layer)

**What to Do**:
- ✅ **New Code**: Use `knowledge_documents`, `tax_law_chunks`, `search_tax_law()`
- ⚠️ **Old Code**: Will continue working via compatibility layer
- 🚫 **Don't Use**: `legal_documents`, `document_chunks`, `match_legal_chunks()`

**Timeline**: See [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) for details

---

## Troubleshooting

### "relation does not exist" Error

```
ERROR: relation "legal_chunks" does not exist
```

**Solution**: Update code to use `tax_law_chunks` instead of `legal_chunks`

### Vector Search Returns No Results

**Possible Causes**:
1. Threshold too high → Lower `match_threshold` (try 0.3)
2. Query embedding mismatch → Ensure using same model (text-embedding-3-small)
3. No data in table → Check `SELECT COUNT(*) FROM tax_law_chunks`

### Slow Queries

**Diagnosis**:
```sql
EXPLAIN ANALYZE SELECT * FROM search_tax_law(...);
```

**Look For**:
- `Seq Scan` = BAD (not using index)
- `Index Scan using idx_tax_chunks_embedding` = GOOD

**Fix**: Ensure vector index exists and is fresh

---

## Schema Diagrams

### Knowledge Base Schema

```
knowledge_documents (Master Registry)
├── document_type: 'tax_law' | 'vendor_background'
├── citation, title, source_file, file_url
└── [One-to-Many]
    ├─→ tax_law_chunks (if document_type = 'tax_law')
    │   ├── chunk_text, embedding (VECTOR)
    │   └── citation, law_category, section_title
    │
    └─→ vendor_background_chunks (if document_type = 'vendor_background')
        ├── chunk_text, embedding (VECTOR)
        └── vendor_name, vendor_category, product_categories
```

### Vendor Learning Schema

```
analysis_results (AI Analysis)
└── [One-to-One]
    └─→ analysis_reviews (Human Feedback)
        └── [Triggers]
            ├─→ vendor_products (Learned Products)
            └─→ vendor_product_patterns (Extracted Patterns)
```

---

## Support

**Issues**: See [SCHEMA_AUDIT_REPORT_2025-11-13.md](../docs/reports/SCHEMA_AUDIT_REPORT_2025-11-13.md) for known issues

**Questions**: Check [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) for migration guidance

**Schema Changes**: All schema changes should be in `migrations/` directory
