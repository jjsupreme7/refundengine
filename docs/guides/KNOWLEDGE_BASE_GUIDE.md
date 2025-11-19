## Knowledge Base Architecture

Complete guide for managing the dual knowledge base system: Tax Law + Vendor Background

## Overview

The knowledge base is **separated into two distinct systems**:

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE BASE                            │
├──────────────────────────┬──────────────────────────────────┤
│     TAX LAW DOCS         │    VENDOR BACKGROUND DOCS        │
├──────────────────────────┼──────────────────────────────────┤
│ • RCW/WAC regulations    │ • Vendor company profiles        │
│ • Exemptions & rules     │ • Product catalogs               │
│ • Tax rates              │ • Industry information           │
│ • Legal definitions      │ • Contract details               │
│                          │ • Historical context             │
├──────────────────────────┼──────────────────────────────────┤
│ Table: tax_law_chunks    │ Table: vendor_background_chunks  │
│ Metadata: citations,     │ Metadata: vendor, products,      │
│   sections, categories   │   categories, industry           │
└──────────────────────────┴──────────────────────────────────┘
```

## Why Separate?

**Tax Law Documents:**
- Legal precision required
- Section-based structure
- RCW/WAC citations
- Rarely change
- Universal applicability

**Vendor Background Documents:**
- Business context
- Product-specific info
- Vendor relationships
- Frequently updated
- Vendor-specific relevance

**Benefits:**
1. **Better search relevance** - Query tax law OR vendor info separately
2. **Metadata optimization** - Different fields for different purposes
3. **Easier maintenance** - Update vendor info without touching legal docs
4. **Flexible querying** - Combined search when needed

---

## Database Schema

### Tables

**1. knowledge_documents** (Master table)
- `id` - Document ID
- `document_type` - 'tax_law' or 'vendor_background'
- `title` - Document title
- `source_file` - Original PDF path
- `file_url` - Cloud storage URL (optional)

**For tax_law:**
- `citation` - RCW/WAC reference
- `effective_date` - When law took effect
- `law_category` - exemption, rate, definition, etc.
- `jurisdiction` - Default: "Washington State"

**For vendor_background:**
- `vendor_name` - e.g., "Nokia", "Ericsson"
- `vendor_category` - manufacturer, distributor, etc.

---

**2. tax_law_chunks**
- `chunk_text` - Chunk content
- `citation` - RCW/WAC for this chunk
- `section_title` - Section name
- `law_category` - exemption, rate, etc.
- `embedding` - vector(1536)

---

**3. vendor_background_chunks**
- `chunk_text` - Chunk content
- `vendor_name` - Vendor this relates to
- `vendor_category` - Type of vendor
- `document_category` - profile, catalog, contract
- `product_categories` - Array of product types
- `embedding` - vector(1536)

---

## Ingesting Documents

### 1. Ingest Tax Law Documents

```bash
# Single tax law document
python scripts/8_ingest_knowledge_base.py tax_law \
  "knowledge_base/tax_law/RCW_82.08.02565.pdf" \
  --citation "RCW 82.08.02565" \
  --law-category "exemption" \
  --effective-date "2024-01-01" \
  --title "Manufacturing Machinery & Equipment Exemption"

# Folder of tax law documents
python scripts/8_ingest_knowledge_base.py tax_law \
  "knowledge_base/tax_law/" \
  --citation "RCW 82.08" \
  --law-category "exemption"
```

**Law Categories:**
- `exemption` - Tax exemptions
- `rate` - Tax rates
- `definition` - Legal definitions
- `procedure` - Filing procedures
- `general` - General provisions

### 2. Ingest Vendor Background Documents

```bash
# Vendor company profile
python scripts/8_ingest_knowledge_base.py vendor_background \
  "knowledge_base/vendors/Nokia_Company_Profile.pdf" \
  --vendor-name "Nokia" \
  --vendor-category "manufacturer" \
  --doc-category "company_profile" \
  --title "Nokia Corporation Profile"

# Vendor product catalog
python scripts/8_ingest_knowledge_base.py vendor_background \
  "knowledge_base/vendors/Ericsson_Product_Catalog_2024.pdf" \
  --vendor-name "Ericsson" \
  --vendor-category "manufacturer" \
  --doc-category "product_catalog" \
  --title "Ericsson 5G Products 2024"

# Folder of vendor docs for one vendor
python scripts/8_ingest_knowledge_base.py vendor_background \
  "knowledge_base/vendors/Nokia/" \
  --vendor-name "Nokia" \
  --vendor-category "manufacturer"
```

**Vendor Categories:**
- `manufacturer` - Makes products
- `distributor` - Resells products
- `service_provider` - Provides services
- `consultant` - Professional services

**Document Categories:**
- `company_profile` - About the company
- `product_catalog` - Product listings
- `industry_info` - Industry context
- `contract` - Contract/agreement details

---

## Searching the Knowledge Base

### Three Search Functions

**1. Search Tax Law Only**
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Generate query embedding
query_embedding = get_embedding("manufacturing equipment exemption")

# Search tax law
results = supabase.rpc('search_tax_law', {
    'query_embedding': query_embedding,
    'match_threshold': 0.5,
    'match_count': 5,
    'law_category_filter': 'exemption'  # Optional: filter by category
}).execute()

for result in results.data:
    print(f"Citation: {result['citation']}")
    print(f"Text: {result['chunk_text']}")
    print(f"Similarity: {result['similarity']}")
```

**2. Search Vendor Background Only**
```python
# Search vendor background
results = supabase.rpc('search_vendor_background', {
    'query_embedding': query_embedding,
    'vendor_filter': 'Nokia',  # Optional: filter by vendor
    'match_threshold': 0.5,
    'match_count': 3
}).execute()

for result in results.data:
    print(f"Vendor: {result['vendor_name']}")
    print(f"Text: {result['chunk_text']}")
    print(f"Products: {result['product_categories']}")
```

**3. Combined Search (Both)**
```python
# Search both knowledge bases
results = supabase.rpc('search_knowledge_base', {
    'query_embedding': query_embedding,
    'vendor_name_filter': 'Nokia',  # Optional
    'include_tax_law': True,
    'include_vendor_bg': True,
    'match_threshold': 0.5,
    'tax_law_count': 5,
    'vendor_bg_count': 3
}).execute()

for result in results.data:
    if result['source_type'] == 'tax_law':
        print(f"[TAX LAW] {result['citation']}")
    else:
        print(f"[VENDOR] {result['vendor_name']}")
    print(f"Text: {result['chunk_text'][:200]}...")
```

---

## How AI Analysis Uses the Knowledge Base

When analyzing a refund (script 6_analyze_refunds.py):

```python
# For a Nokia transaction:
vendor = "Nokia"
product = "5G Radio Equipment"
amount = 8000
tax = 800

# Step 1: Search vendor background (context)
vendor_context = supabase.rpc('search_vendor_background', {
    'query_embedding': get_embedding(f"{vendor} {product}"),
    'vendor_filter': vendor,
    'match_count': 3
}).execute()
# Returns: Nokia is a telecommunications manufacturer,
#          5G equipment is networking infrastructure

# Step 2: Search tax law (rules)
tax_rules = supabase.rpc('search_tax_law', {
    'query_embedding': get_embedding(
        f"exemption for {product} in telecommunications industry"
    ),
    'law_category_filter': 'exemption',
    'match_count': 5
}).execute()
# Returns: RCW 82.08.02565 - Manufacturing exemption
#          RCW 82.08.0267 - High-tech exemption
#          etc.

# Step 3: AI analyzes with both contexts
analysis = ai_analyze(
    vendor_context=vendor_context,
    tax_rules=tax_rules,
    product=product,
    amount=amount
)
# Determines: Not eligible - networking gear != manufacturing
```

---

## Folder Structure

Recommended organization:

```
knowledge_base/
├── tax_law/
│   ├── exemptions/
│   │   ├── RCW_82.08.02565_Manufacturing.pdf
│   │   ├── RCW_82.08.0267_HighTech.pdf
│   │   └── RCW_82.08.02745_Ag_Equipment.pdf
│   ├── rates/
│   │   └── WAC_458-20-XXX_TaxRates.pdf
│   └── definitions/
│       └── RCW_82.04_Definitions.pdf
└── vendors/
    ├── Nokia/
    │   ├── Nokia_Company_Profile.pdf
    │   ├── Nokia_5G_Product_Catalog.pdf
    │   └── Nokia_Services_Overview.pdf
    ├── Ericsson/
    │   ├── Ericsson_Profile.pdf
    │   └── Ericsson_Products_2024.pdf
    └── Zones/
        └── Zones_Distributor_Info.pdf
```

---

## Maintenance & Updates

### Adding New Tax Law

When WA updates tax law:

```bash
python scripts/8_ingest_knowledge_base.py tax_law \
  "knowledge_base/tax_law/NEW_RCW.pdf" \
  --citation "RCW XX.XX.XXXXX" \
  --law-category "exemption" \
  --effective-date "2025-01-01"
```

### Adding Vendor Information

When you learn about a new vendor:

```bash
# Create vendor background document (can be manual notes as PDF)
python scripts/8_ingest_knowledge_base.py vendor_background \
  "knowledge_base/vendors/NewVendor_Profile.pdf" \
  --vendor-name "New Vendor Inc" \
  --vendor-category "manufacturer" \
  --doc-category "company_profile"
```

### Updating Vendor Info

Vendor product catalog changed:

1. Ingest new version:
```bash
python scripts/8_ingest_knowledge_base.py vendor_background \
  "Nokia_Catalog_2025.pdf" \
  --vendor-name "Nokia" \
  --doc-category "product_catalog" \
  --title "Nokia Products 2025"
```

2. Optionally delete old version from database

---

## Viewing Your Knowledge Base

### SQL Queries (Supabase Dashboard)

**Check stats:**
```sql
SELECT * FROM knowledge_base_stats;
```

Output:
```
doc_type          | document_count | total_chunks | embedded_chunks
------------------+----------------+--------------+----------------
tax_law           | 15             | 342          | 342
vendor_background | 8              | 156          | 156
```

**View tax law documents:**
```sql
SELECT * FROM tax_law_documents_summary;
```

**View vendor documents:**
```sql
SELECT * FROM vendor_documents_summary;
```

**See all vendors in KB:**
```sql
SELECT DISTINCT vendor_name, vendor_category, COUNT(*) as doc_count
FROM knowledge_documents
WHERE document_type = 'vendor_background'
GROUP BY vendor_name, vendor_category;
```

---

## Migration from Old Schema

If you have existing `legal_documents` and `legal_chunks`:

```sql
-- Migrate documents
INSERT INTO knowledge_documents (
  document_type, title, citation, law_category, total_chunks
)
SELECT
  'tax_law',
  title,
  citation,
  'general',
  (SELECT COUNT(*) FROM legal_chunks WHERE document_id = ld.id)
FROM legal_documents ld;

-- Migrate chunks
INSERT INTO tax_law_chunks (
  document_id, chunk_text, chunk_number, citation, embedding
)
SELECT
  kd.id,
  lc.chunk_text,
  lc.chunk_number,
  lc.citation,
  lc.embedding
FROM legal_chunks lc
JOIN legal_documents ld ON lc.document_id = ld.id
JOIN knowledge_documents kd ON kd.citation = ld.citation
  AND kd.document_type = 'tax_law';

-- Update processing status
UPDATE knowledge_documents
SET processing_status = 'completed',
    processed_at = NOW()
WHERE document_type = 'tax_law';
```

---

## Best Practices

### Tax Law Documents

✅ **DO:**
- Use official RCW/WAC citations
- Include effective dates
- Categorize by exemption type
- Keep original PDF filenames descriptive

❌ **DON'T:**
- Mix multiple laws in one document
- Forget to update when laws change
- Use vague categories

### Vendor Documents

✅ **DO:**
- Create vendor profiles for all major vendors
- Update product catalogs annually
- Include industry context documents
- Note vendor category (manufacturer vs distributor)

❌ **DON'T:**
- Mix multiple vendors in one document
- Forget to specify vendor name
- Use outdated catalogs

---

## Example: Complete Setup

```bash
# 1. Deploy database schema
psql -h db.xxx.supabase.co -U postgres -f database/schema_knowledge_base.sql
psql -h db.xxx.supabase.co -U postgres -f database/schema_vendor_learning.sql

# 2. Ingest tax law documents
python scripts/8_ingest_knowledge_base.py tax_law \
  "knowledge_base/tax_law/" \
  --citation "RCW 82.08" \
  --law-category "exemption"

# 3. Ingest vendor documents
python scripts/8_ingest_knowledge_base.py vendor_background \
  "knowledge_base/vendors/Nokia/" \
  --vendor-name "Nokia" \
  --vendor-category "manufacturer"

# 4. Verify ingestion
# Run in Supabase SQL Editor:
# SELECT * FROM knowledge_base_stats;

# 5. Run analysis
python scripts/6_analyze_refunds.py "input.xlsx" --save-db

# 6. Review in Excel, import corrections
python scripts/7_import_corrections.py "input_analyzed.xlsx"

# 7. System learns and gets smarter!
```

---

## Troubleshooting

**"Function search_tax_law does not exist"**
→ Run `database/schema_knowledge_base.sql` to create RPC functions

**"No results from vendor search"**
→ Check you've ingested vendor docs with correct --vendor-name

**"Embeddings are NULL"**
→ OpenAI API key issue, check OPENAI_API_KEY env variable

**"Chunks are too small/large"**
→ Adjust chunk_size in `KnowledgeBaseIngester.__init__`
