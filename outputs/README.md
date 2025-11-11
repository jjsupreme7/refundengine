# Outputs Folder

This folder contains Excel files for managing your knowledge base.

## File Conventions

### 📄 `WA_Tax_Law.xlsx` - Tax Law Document Ingestion Workflow
**Purpose**: Ingest NEW tax law documents into the knowledge base

**When to use**:
- Adding new tax law PDFs to the knowledge base
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

# Step 3: Import approved documents (with auto-confirm flag)
python core/ingest_documents.py --import-metadata outputs/WA_Tax_Law.xlsx --yes
```

**Duplicate Protection**: Documents are checked by filename - if a PDF with the same filename already exists in the database, it will be skipped automatically (even if marked "Approved")

**Keep this file**: Yes, update it whenever you want to ingest more documents

---

### 📦 `Vendor_Background.xlsx` - Vendor Document Ingestion Workflow
**Purpose**: Ingest NEW vendor documents into the knowledge base

**When to use**:
- Adding new vendor PDFs to the knowledge base
- AI will extract vendor metadata (vendor_name, industry, business_model, etc.)
- Review and approve vendor documents before ingestion

**Workflow**:
```bash
# Step 1: Export metadata from vendor PDFs (AI extraction)
python core/ingest_documents.py --type vendor \
  --folder knowledge_base/vendors \
  --export-metadata outputs/Vendor_Background.xlsx

# Step 2: Open Vendor_Background.xlsx in Excel
# - Review AI-suggested metadata (vendor_name, industry, business_model, primary_products, etc.)
# - Change Status from "Review" to "Approved" for vendors you want to ingest
# - Edit any metadata as needed

# Step 3: Import approved vendors (with auto-confirm flag)
python core/ingest_documents.py --import-metadata outputs/Vendor_Background.xlsx --yes
```

**Duplicate Protection**: Documents are checked by filename - if a PDF with the same filename already exists in the database, it will be skipped automatically (even if marked "Approved")

**Keep this file**: Yes, update it whenever you want to ingest more vendor documents

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
| Add new tax law documents | `WA_Tax_Law.xlsx` | `python core/ingest_documents.py --import-metadata outputs/WA_Tax_Law.xlsx --yes` |
| Add new vendor documents | `Vendor_Background.xlsx` | `python core/ingest_documents.py --import-metadata outputs/Vendor_Background.xlsx --yes` |
| Edit existing metadata | `metadata.xlsx` | `python scripts/import_metadata_excel.py --file outputs/metadata.xlsx` |
| Export current data | Generate new `metadata.xlsx` | `python scripts/export_metadata_excel.py --output outputs/metadata.xlsx` |

---

## Metadata Fields (Array Fields)

When editing these fields, use **comma-separated values**:

### Tax Law Documents
- **topic_tags**: `digital products, exemptions, cloud computing`
- **tax_types**: `sales tax, use tax, B&O tax`
- **industries**: `retail, technology, manufacturing`
- **referenced_statutes**: `RCW 82.04.215, WAC 458-20-15502`

### Vendor Documents
- **vendor_name**: Name of the vendor (single text value)
- **vendor_category**: Category (e.g., `service_provider`, `product_vendor`)
- **industry**: Primary industry (e.g., `Technology`, `Manufacturing`)
- **business_model**: Business model (e.g., `B2B SaaS`, `Consulting`, `Retail`)
- **primary_products**: `Azure, Office 365, Dynamics` (comma-separated)
- **typical_delivery**: Delivery method (e.g., `Cloud-based`, `On-premise`, `In-person`)
- **tax_notes**: Tax-relevant notes (e.g., `Digital automated services, MPU analysis required`)
- **confidence_score**: Confidence in metadata accuracy (0.0-100.0)
- **data_source**: Source of metadata (`manual`, `ai_research`, `web_scrape`, `pdf_extraction`)

The import script will automatically convert comma-separated values to database arrays.

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
