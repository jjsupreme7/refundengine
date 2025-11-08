# Outputs Folder

This folder contains Excel files for managing your knowledge base.

## File Conventions

### 📄 `WA_Tax_Law.xlsx` - Document Ingestion Workflow
**Purpose**: Ingest NEW documents into the knowledge base

**When to use**:
- Adding new PDFs to the knowledge base
- AI will extract metadata from PDFs and populate this file
- Review and approve documents before ingestion

**Workflow**:
```bash
# Step 1: Export metadata from PDFs (AI extraction)
python core/ingest_documents.py --type tax_law \
  --folder knowledge_base/states/washington/legal_documents \
  --export-metadata outputs/WA_Tax_Law.xlsx

# Step 2: Open WA_Tax_Law.xlsx in Excel
# - Review AI-suggested metadata (topic_tags, tax_types, industries, etc.)
# - Change Status from "Review" to "Approved" for documents you want to ingest
# - Edit any metadata as needed

# Step 3: Import approved documents
python core/ingest_documents.py --import-metadata outputs/WA_Tax_Law.xlsx
```

**Keep this file**: Yes, update it whenever you want to ingest more documents

---

### 📊 `metadata.xlsx` - Current Metadata Editor
**Purpose**: Edit metadata for EXISTING documents in Supabase

**When to use**:
- Updating metadata for already-ingested documents
- Changing topic_tags, tax_types, industries, etc.
- Editing citations or law categories

**Workflow**:
```bash
# Step 1: Export current metadata from Supabase
python scripts/export_metadata_excel.py --output outputs/metadata.xlsx

# Step 2: Open metadata.xlsx in Excel
# - Edit the Documents sheet (changes cascade to chunks automatically!)
# - Or edit individual chunks in the Tax Law Chunks sheet

# Step 3: Import changes back to Supabase
python scripts/import_metadata_excel.py --file outputs/metadata.xlsx
```

**Keep this file**: Yes, regenerate it whenever you want to edit existing metadata

---

## Quick Reference

| Task | File to Use | Command |
|------|-------------|---------|
| Add new documents | `WA_Tax_Law.xlsx` | `python core/ingest_documents.py --import-metadata outputs/WA_Tax_Law.xlsx` |
| Edit existing metadata | `metadata.xlsx` | `python scripts/import_metadata_excel.py --file outputs/metadata.xlsx` |
| Export current data | Generate new `metadata.xlsx` | `python scripts/export_metadata_excel.py --output outputs/metadata.xlsx` |

---

## Metadata Fields (Array Fields)

When editing these fields, use **comma-separated values**:

- **topic_tags**: `digital products, exemptions, cloud computing`
- **tax_types**: `sales tax, use tax, B&O tax`
- **industries**: `retail, technology, manufacturing`
- **referenced_statutes**: `RCW 82.04.215, WAC 458-20-15502`

The import script will automatically convert these to database arrays.

---

## Cascading Updates

When you edit the **Documents** sheet in `metadata.xlsx`, changes to these fields automatically cascade to ALL chunks:

- citation
- law_category
- topic_tags
- tax_types
- industries
- referenced_statutes
- vendor_name
- vendor_category

This means you only need to edit once, and all chunks from that document update automatically!
