# Metadata Management Guide

Complete guide for managing and filtering your knowledge base metadata.

---

## 🎯 Quick Start

### 1. Export Current Metadata
```bash
python scripts/export_metadata.py
```

This exports all metadata to `metadata_exports/`:
- `documents_metadata_*.csv` - Document-level metadata
- `tax_law_chunks_metadata_*.csv` - Tax law chunk metadata
- `vendor_chunks_metadata_*.csv` - Vendor chunk metadata (if any)

### 2. Edit Metadata in Excel/Google Sheets

Open the CSV files and edit fields like:
- `law_category` (e.g., "software", "digital_goods", "manufacturing")
- `citation` (e.g., "WAC 458-20-15502")
- `effective_date` (YYYY-MM-DD format)
- `section_title` (section names)

**Important:** Don't edit `id` or `document_id` columns!

### 3. Import Changes
```bash
python scripts/import_metadata.py --file metadata_exports/documents_metadata_EDITED.csv
```

The script will:
- Show you a diff of what changed
- Ask for confirmation
- Update only changed fields in Supabase
- Preserve embeddings and chunk text

---

## 📊 Database Structure

Your Supabase database has **two separate knowledge bases**:

### Tax Law Knowledge Base
**Table:** `tax_law_chunks`
- `citation` - Legal citation (WAC 458-20-15502)
- `law_category` - Category for filtering (software, digital_goods, etc.)
- `section_title` - Section name/page number
- `embedding` - Vector embedding for RAG search

**Search Function:** `search_tax_law()`
- Supports `law_category_filter` parameter

### Vendor Background Knowledge Base
**Table:** `vendor_background_chunks`
- `vendor_name` - Vendor name
- `vendor_category` - Type of vendor
- `document_category` - Type of document
- `embedding` - Vector embedding for RAG search

**Search Function:** `search_vendor_background()`
- Supports `vendor_filter` parameter

---

## 🔍 Using Metadata Filters in RAG Chatbot

### Start the Chatbot
```bash
python scripts/chat_rag.py
```

### Filter Commands

#### Show Active Filters
```
❓ You: filters
```

#### Set a Filter
```
❓ You: filter law_category software
✅ Filter set: law_category = 'software'

❓ You: filter citation WAC-458-20-15502
✅ Filter set: citation = 'WAC-458-20-15502'

❓ You: filter vendor_name AT&T
✅ Filter set: vendor_name = 'AT&T'
```

#### Clear a Filter
```
❓ You: filter law_category clear
✅ Filter cleared: law_category
```

### Example Workflow

```
❓ You: filters
🔍 No filters active (searching all documents)

❓ You: filter law_category software
✅ Filter set: law_category = 'software'

❓ You: How is SaaS taxed in Washington?
💭 Searching knowledge base... Found 3 relevant documents!

🤖 Assistant: According to WAC 458-20-15502...
[Only searches documents with law_category='software']

❓ You: filter law_category clear
✅ Filter cleared: law_category

❓ You: filters
🔍 No filters active (searching all documents)
```

---

## 📝 Available Metadata Fields

### Documents Table (`knowledge_documents`)
| Field | Editable | Example Values |
|-------|----------|----------------|
| `id` | ❌ No | UUID (don't edit) |
| `document_type` | ✅ Yes | `tax_law`, `vendor_background` |
| `title` | ✅ Yes | "Taxation of Computer Software" |
| `citation` | ✅ Yes | "WAC 458-20-15502" |
| `law_category` | ✅ Yes | `software`, `digital_goods`, `manufacturing` |
| `effective_date` | ✅ Yes | "2020-01-15" |
| `vendor_name` | ✅ Yes | "AT&T", "Verizon" |
| `vendor_category` | ✅ Yes | `manufacturer`, `distributor`, `service_provider` |

### Tax Law Chunks Table (`tax_law_chunks`)
| Field | Editable | Example Values |
|-------|----------|----------------|
| `id` | ❌ No | UUID (don't edit) |
| `document_id` | ❌ No | UUID (don't edit) |
| `citation` | ✅ Yes | "WAC 458-20-15502" |
| `section_title` | ✅ Yes | "Page 1", "Section 3(a)" |
| `law_category` | ✅ Yes | `software`, `exemption`, `procedure` |

---

## 🎨 Suggested Category Taxonomy

### Law Categories
- `software` - Computer software taxation
- `digital_goods` - Digital products (downloads, streaming)
- `manufacturing` - Manufacturing exemptions
- `resale` - Resale certificates
- `exemption` - General exemptions
- `procedure` - Tax procedures and filing
- `saas` - Software as a Service
- `cloud` - Cloud computing services

### Vendor Categories
- `manufacturer` - Product manufacturers
- `distributor` - Distribution companies
- `service_provider` - Service-based vendors
- `contractor` - Installation/construction contractors
- `telecommunications` - Telecom providers

---

## 🔧 Advanced Usage

### Export to Custom Directory
```bash
python scripts/export_metadata.py --output-dir ./my_exports
```

### Auto-Confirm Import (Skip Prompt)
```bash
python scripts/import_metadata.py --file metadata.csv --auto-confirm
```

### Programmatic Filter Usage
```python
from scripts.chat_rag import RAGChatbot

chatbot = RAGChatbot()

# Set filters programmatically
chatbot.filters['law_category'] = 'software'
chatbot.filters['citation'] = 'WAC-458-20-15502'

# Search with filters
results = chatbot.search_knowledge_base("How is SaaS taxed?")

# Clear filters
chatbot.filters['law_category'] = None
```

---

## 🚀 Workflow Examples

### Example 1: Organize by Topic
1. Export metadata: `python scripts/export_metadata.py`
2. Open CSV in Excel
3. Add consistent `law_category` tags:
   - All software docs → `software`
   - All manufacturing docs → `manufacturing`
4. Import: `python scripts/import_metadata.py --file metadata.csv`
5. Use chatbot with filters: `filter law_category software`

### Example 2: Add Effective Dates
1. Export metadata
2. Research and add `effective_date` for each law
3. Import changes
4. Now you can filter by date ranges (future feature)

### Example 3: Vendor-Specific Search
1. Ingest vendor documents with `vendor_name` metadata
2. Use chatbot: `filter vendor_name AT&T`
3. Ask: "What products does this vendor sell?"
4. Get answers from only that vendor's documents

---

## ✅ Best Practices

1. **Consistent Naming:** Use lowercase with underscores (e.g., `digital_goods`, not "Digital Goods")
2. **Backup Before Import:** Keep original CSV files before importing
3. **Test with One Record:** Test metadata changes on one record first
4. **Use Version Control:** Keep CSV files in git to track metadata changes
5. **Document Your Categories:** Maintain a list of allowed category values
6. **Regular Exports:** Export metadata periodically as backup

---

## 🛠️ Troubleshooting

### Import shows no changes
- Check that you edited the correct CSV file
- Verify the `id` column matches database records
- Ensure CSV is properly formatted

### Filter not working
- Check spelling of filter name (`law_category`, not `category`)
- Verify metadata values exist in database
- Use `stats` command to see available documents

### CSV editing issues
- Save as CSV, not XLSX
- Don't use formulas in cells
- Keep UTF-8 encoding
- Don't add extra columns

---

## 📚 Related Files

- `scripts/export_metadata.py` - Export script
- `scripts/import_metadata.py` - Import script with diff detection
- `scripts/chat_rag.py` - RAG chatbot with filtering
- `metadata_exports/README.md` - Generated with each export
- `database/schema_knowledge_base.sql` - Database schema

---

## 🎯 Next Steps

1. ✅ Export current metadata
2. ✅ Add consistent `law_category` tags
3. ✅ Import and verify changes
4. ✅ Test filters in chatbot
5. 🔄 Ingest more documents with metadata
6. 🔄 Build vendor knowledge base
7. 🔄 Create custom categories for your use case
