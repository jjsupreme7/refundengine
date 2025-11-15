# How ESSB 5814 Documents Will Be Ingested to Supabase

## 📊 No New Tables - Uses Existing Schema

**Answer: NO, this will NOT create new tables.**

Your ingestion will use the **same existing tables** you already have:
- `knowledge_documents` (1,681 rows currently)
- `tax_law_chunks` (4,226 rows currently)

---

## 🔄 Ingestion Flow

```
Excel Metadata (outputs/ESSB_5814_Metadata.xlsx)
    ↓
Read metadata for each document
    ↓
For each PDF:
    ├─→ Extract full text from PDF
    ├─→ Store metadata in knowledge_documents table (1 row per PDF)
    ├─→ Chunk the text (target: 800 words per chunk)
    ├─→ Generate embeddings for each chunk
    └─→ Store chunks in tax_law_chunks table (many rows per PDF)
```

---

## 📋 Table 1: `knowledge_documents`

**What gets stored**: One row per PDF (5 new rows)

**Schema** (existing):
```sql
knowledge_documents
├── id (auto-generated UUID)
├── document_type = "tax_law"
├── title = "ESSB 5814 Session Law - Expanding Retail Sales Tax..."
├── source_file = "01_ESSB_5814_Session_Law.pdf"
├── citation = "ESSB 5814, Chapter 422, Laws of 2025"
├── law_category = "law_change"
├── effective_date = "2025-10-01"
├── total_chunks = 15 (varies by document)
├── processing_status = "completed"
├── topic_tags = ["law change", "newly taxable services", ...]
├── tax_types = ["retail sales tax", "retailing B&O tax"]
├── industries = ["general", "technology", "services", ...]
├── referenced_statutes = ["ESSB 5814", "Chapter 422", "RCW 82.04.050", ...]
├── created_at (timestamp)
└── updated_at (timestamp)
```

**After ingestion**: 1,681 + 5 = **1,686 rows**

---

## 📝 Table 2: `tax_law_chunks`

**What gets stored**: One row per chunk (estimated 50-100 new rows total)

**Schema** (existing):
```sql
tax_law_chunks
├── id (auto-generated UUID)
├── document_id (foreign key → knowledge_documents.id)
├── chunk_number = 1, 2, 3, ...
├── chunk_text = "Full text of chunk (~800 words)"
├── citation = "ESSB 5814, Chapter 422, Laws of 2025"
├── section_title = "Page 1" or "Section 101"
├── law_category = "law_change"
├── embedding = [vector of 1536 dimensions]
├── topic_tags = ["law change", "newly taxable services"]
├── tax_types = ["retail sales tax", "retailing B&O tax"]
├── industries = ["general", "technology", "services"]
├── referenced_statutes = ["ESSB 5814", "RCW 82.04.050"]
└── created_at (timestamp)
```

**Chunking estimate**:
- Session Law PDF (8 pages): ~10-15 chunks
- Final Bill Report (4 pages): ~5-8 chunks
- KPMG October (multi-page): ~15-20 chunks
- KPMG May (multi-page): ~15-20 chunks
- Deloitte Alert (multi-page): ~10-15 chunks

**After ingestion**: 4,226 + ~70 = **~4,296 rows**

---

## 🔍 How Your RAG Will Use This Data

### **Basic Search** (Current RPC Function)

```sql
-- Your existing search_tax_law RPC function
SELECT
  id,
  chunk_text,
  citation,
  law_category,
  section_title,
  1 - (embedding <=> query_embedding) as similarity
FROM tax_law_chunks
WHERE 1 - (embedding <=> query_embedding) > match_threshold
ORDER BY embedding <=> query_embedding
LIMIT match_count;
```

### **Filtered Search** (Law Change Only)

```sql
-- Search for ESSB 5814 documents specifically
SELECT *
FROM tax_law_chunks
WHERE law_category = 'law_change'
  AND citation LIKE '%ESSB 5814%'
  AND 1 - (embedding <=> query_embedding) > 0.3
ORDER BY similarity DESC;
```

### **Example Query Flow**

**User asks**: "Are IT services taxable in Washington?"

**RAG retrieves**:
```python
# Query embedding
query_embedding = get_embedding("Are IT services taxable in Washington?")

# Search
results = supabase.rpc('search_tax_law', {
    'query_embedding': query_embedding,
    'match_threshold': 0.3,
    'match_count': 5
}).execute()

# Results will include ESSB 5814 chunks
for result in results.data:
    print(f"Citation: {result['citation']}")
    print(f"Category: {result['law_category']}")  # "law_change"
    print(f"Text: {result['chunk_text'][:200]}...")
```

**Retrieved chunks might be**:
```
[1] Citation: ESSB 5814, Chapter 422, Laws of 2025
    Category: law_change
    Text: "Effective October 1, 2025, information technology services
           became subject to retail sales tax. IT services include help
           desk support, network administration, system configuration..."

[2] Citation: ESSB 5814 Analysis (KPMG)
    Category: compliance
    Text: "Prior to October 1, 2025, IT services were subject to Service
           & Other B&O tax but not retail sales tax. The new law..."
```

**GPT generates answer**:
```
Information technology services tax treatment CHANGED on October 1, 2025:

BEFORE October 1, 2025:
- IT services were NOT subject to retail sales tax
- Only Service & Other B&O tax applied

AFTER October 1, 2025:
- IT services ARE subject to retail sales tax
- Also subject to Retailing B&O tax
- This change was enacted under ESSB 5814 (Chapter 422, Laws of 2025)

Source: ESSB 5814, Chapter 422, Laws of 2025
```

---

## 🎯 Key Integration Points

### **1. Metadata Propagation**

Metadata from Excel flows to BOTH tables:

```
Excel Metadata
    ↓
knowledge_documents (document-level metadata)
    ↓
tax_law_chunks (chunk-level metadata - inherited from parent document)
```

Each chunk inherits:
- `citation` from parent document
- `law_category` from parent document
- `topic_tags` from parent document
- `tax_types` from parent document
- `industries` from parent document
- `referenced_statutes` from parent document

### **2. Relationship**

```
knowledge_documents.id ←→ tax_law_chunks.document_id (foreign key)

One document → Many chunks (1:N relationship)
```

### **3. Search Integration**

Your existing RPC function `search_tax_law` already knows how to:
- Search by embedding similarity (vector search)
- Filter by law_category
- Filter by citation
- Return chunks with metadata

**No changes needed to search infrastructure!**

---

## 📈 Before vs After Ingestion

### **Before**

```
knowledge_documents: 1,681 rows
    ├─ RCW documents
    ├─ WAC documents
    └─ WTD documents

tax_law_chunks: 4,226 rows
    ├─ RCW chunks
    ├─ WAC chunks
    └─ WTD chunks
```

### **After**

```
knowledge_documents: 1,686 rows
    ├─ RCW documents
    ├─ WAC documents
    ├─ WTD documents
    └─ ESSB 5814 documents (5 new) ← NEW!

tax_law_chunks: ~4,296 rows
    ├─ RCW chunks
    ├─ WAC chunks
    ├─ WTD chunks
    └─ ESSB 5814 chunks (~70 new) ← NEW!
```

---

## ⚠️ Important: Temporal Awareness

### **Current Schema Limitation**

Your `tax_law_chunks` table does NOT have:
- `effective_date` column (stored in parent `knowledge_documents` only)
- `supersedes_date` column

This means:
- ✅ You CAN search for "law_change" category
- ✅ You CAN filter by citation containing "ESSB 5814"
- ❌ You CANNOT directly filter chunks by effective_date in RPC

### **Workaround Options**

**Option 1**: Join with parent document (slower)
```sql
SELECT c.*
FROM tax_law_chunks c
JOIN knowledge_documents d ON c.document_id = d.id
WHERE d.effective_date >= '2025-10-01'
```

**Option 2**: Add effective_date to chunks table (recommended)
```sql
ALTER TABLE tax_law_chunks
ADD COLUMN effective_date DATE,
ADD COLUMN supersedes_date DATE;

-- Then update ingestion to populate these fields
```

**Option 3**: Use application-level filtering (current approach)
```python
# Retrieve all results, then filter by metadata
results = rag.search("IT services taxable?")
essb_results = [r for r in results if 'ESSB 5814' in r['citation']]
```

---

## 🚀 Command to Ingest

When you're ready:

```bash
python core/ingest_documents.py --import-metadata outputs/ESSB_5814_Metadata.xlsx
```

This will:
1. ✅ Read 5 rows from Excel
2. ✅ Extract text from 5 PDFs
3. ✅ Insert 5 rows into `knowledge_documents`
4. ✅ Create ~70 chunks total
5. ✅ Generate embeddings for each chunk
6. ✅ Insert ~70 rows into `tax_law_chunks`
7. ✅ Link chunks to parent documents via `document_id`

**Estimated time**: 3-5 minutes
**Estimated cost**: ~$0.10 (embeddings + chunking)

---

## ✅ Summary

- **No new tables**: Uses existing `knowledge_documents` and `tax_law_chunks`
- **5 new documents**: One row per PDF in `knowledge_documents`
- **~70 new chunks**: Multiple rows in `tax_law_chunks` (one per chunk)
- **Metadata inheritance**: Chunks inherit metadata from parent document
- **Search integration**: Works with existing `search_tax_law` RPC
- **Temporal awareness**: Use `law_category='law_change'` and citation filters

The ESSB 5814 documents will seamlessly integrate with your existing 1,681 documents and 4,226 chunks!
