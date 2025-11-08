# Core - Document Ingestion

This folder contains the **primary ingestion pipeline** for the Refund Engine.

## Main Script: `ingest_documents.py`

**This is the ONE script you need for all document ingestion.**

### Features
- ✅ Handles both tax law AND vendor documents
- ✅ AI metadata suggestions (GPT-4o) for normal files
- ✅ Automatic handling of large files (100+ pages)
- ✅ **ALWAYS exports to Excel for review** (even large files!)
- ✅ Canonical chunking (consistent, deterministic)
- ✅ Stores in `knowledge_documents` schema

### Smart Large File Handling
- Files under 100 pages: Uses AI for rich metadata
- Files 100+ pages: Uses filename-based metadata (faster, no AI errors)
- **Both types export to Excel for your review before ingestion!**

### Usage

**Step 1: Export metadata to Excel for review**
```bash
# Tax law documents
python core/ingest_documents.py --type tax_law \
  --folder knowledge_base/states/washington/legal_documents \
  --export-metadata outputs/excel_exports/Tax_Metadata.xlsx

# Vendor documents
python core/ingest_documents.py --type vendor \
  --folder knowledge_base/vendors \
  --export-metadata outputs/excel_exports/Vendor_Metadata.xlsx
```

**Step 2: Review the Excel file**
- Open the generated Excel file
- Review AI suggestions for each document
- Edit any fields as needed
- Change Status column to "Approved" for documents you want to ingest
- Save the file

**Step 3: Import and ingest**
```bash
python core/ingest_documents.py --import-metadata outputs/excel_exports/Tax_Metadata.xlsx
```

### Document Types

**Tax Law** (`--type tax_law`)
- Metadata: citation, law_category, effective_date
- Stored in: `knowledge_documents` → `tax_law_chunks`

**Vendor** (`--type vendor`)
- Metadata: vendor_name, vendor_category, document_category
- Stored in: `knowledge_documents` → `vendor_background_chunks`

## Supporting Modules

### `chunking.py`
Canonical chunking module used by all ingestion scripts.

**Key features:**
- Semantic chunking preserves document structure
- Target: 800 words, Max: 1500 words, Min: 150 words
- Deterministic (same input always produces same output)

**DO NOT MODIFY** this file unless you want to change chunking behavior project-wide.

### `ingest_large_document.py` (DEPRECATED)
**You don't need this anymore!** The main script now handles large files automatically.

Keep it for reference only.
