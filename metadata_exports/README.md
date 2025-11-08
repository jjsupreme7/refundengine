# Knowledge Base Metadata Editor

## 📋 Exported Files

This directory contains CSV exports of your knowledge base metadata:

- **documents_metadata_*.csv** - Document-level metadata (titles, citations, categories)
- **tax_law_chunks_metadata_*.csv** - Tax law chunk metadata (sections, keywords, hierarchy)
- **vendor_chunks_metadata_*.csv** - Vendor background chunk metadata (if any)

## ✏️ How to Edit

1. **Open in Excel or Google Sheets**
   - Don't edit the `id` or `document_id` columns (used for matching)
   - Edit any other fields as needed

2. **Editable Fields in documents_metadata.csv:**
   - `title` - Document title
   - `citation` - Legal citation (e.g., WAC 458-20-15502)
   - `law_category` - Category tag (e.g., 'software', 'manufacturing', 'exemption')
   - `effective_date` - When the law became effective (YYYY-MM-DD format)
   - `vendor_name` - For vendor documents only
   - `vendor_category` - For vendor documents only

3. **Editable Fields in tax_law_chunks_metadata.csv:**
   - `citation` - Chunk-specific citation
   - `section_title` - Section name/title
   - `law_category` - Category tag for filtering
   - `keywords` - JSON array of keywords like ["software", "exemption", "retail"]
   - `hierarchy_level` - Nesting level (1, 2, 3, etc.)
   - `parent_section` - Parent section reference

4. **Save as CSV**
   - Keep the same filename or rename it
   - Make sure it's still in CSV format

## 🔄 Import Changes

After editing, run:

```bash
python scripts/import_metadata.py --file path/to/your/edited_file.csv
```

The import script will:
- Show you a diff of what changed
- Ask for confirmation
- Update only the changed fields in Supabase
- Preserve embeddings and chunk text

## 🎯 Use Case: RAG with Metadata Filters

After updating metadata, you can filter your RAG searches:

```python
# Search only software-related tax law
results = search_tax_law(
    query_embedding=embedding,
    law_category_filter='software'
)

# Search specific vendor
results = search_vendor_background(
    query_embedding=embedding,
    vendor_filter='AT&T'
)
```

## ⚠️ Important Notes

- **Don't delete rows** - this will not delete from database
- **Don't edit `id` or `document_id`** - these are used to match records
- The import script only updates fields that changed
- No need to worry about embeddings - they're preserved
- Invalid data will be caught during import validation

## 🔍 Metadata Field Guide

### law_category Examples:
- `software` - Computer software taxation
- `manufacturing` - Manufacturing exemptions
- `resale` - Resale certificates
- `digital_goods` - Digital products
- `exemption` - General exemptions
- `procedure` - Tax procedures

### vendor_category Examples:
- `manufacturer` - Product manufacturer
- `distributor` - Distribution company
- `service_provider` - Service-based vendor
- `contractor` - Installation/construction

### document_category Examples (for vendor docs):
- `company_profile` - Company background
- `product_catalog` - Product listings
- `contract` - Service contracts
- `industry_info` - Industry knowledge
