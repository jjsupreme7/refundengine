# Scripts Directory

This folder contains utility scripts for data ingestion, processing, and system maintenance.

## Quick Start

**New to the system? Start here:**
1. Download knowledge base: `python scripts/download_knowledge_base_from_storage.py`
2. Verify setup: `python scripts/verify_setup.py`

## Script Categories

### 📥 Knowledge Base Ingestion

**Download from Cloud**
```bash
# Download all KB documents from Supabase Storage
python scripts/download_knowledge_base_from_storage.py

# Upload local KB to Supabase Storage
python scripts/upload_knowledge_base_to_storage.py
```

**Web Scraping & Download**
```bash
# Download Washington Administrative Code (WAC) Title 458
python scripts/download_wac_title_458.py

# Download Revised Code of Washington (RCW) Title 82
python scripts/download_rcw_title_82.py

# Download Washington Tax Decisions
python scripts/download_tax_decisions.py

# Auto-process WAC/RCW sections
python scripts/auto_process_wac_rcw.py
```

**Test Data Ingestion**
```bash
# Ingest test data (invoices, POs, Excel files)
python scripts/ingest_test_data.py
```

---

### 📊 Metadata Management

**Export & Import**
```bash
# Export metadata to Excel for editing
python scripts/export_metadata_excel.py

# Import edited metadata back to database
python scripts/import_metadata_excel.py

# Combine tax law Excel files
python scripts/combine_tax_law_excel.py
```

**Metadata Enhancement**
```bash
# Add page numbers to existing chunks
python scripts/add_page_numbers_to_chunks.py

# Add file URLs to documents
python scripts/add_file_url_python.py
python scripts/populate_file_urls.py
```

---

### 🔍 Analysis & Research

**Vendor Research**
```bash
# Research vendors for better context
python scripts/research_vendors.py

# Research vendors before ingestion
python scripts/research_vendors_for_ingestion.py
```

**Pattern Extraction**
```bash
# Extract sales tax patterns from Phase 2 Master Refunds
python scripts/extract_patterns_from_phase2.py

# Extract sales tax patterns from Denodo (2019-2023)
python scripts/extract_patterns_from_denodo.py

# Extract use tax patterns
python scripts/extract_patterns_from_use_tax.py

# Upload patterns to Supabase
python scripts/upload_patterns_to_supabase.py

# Upload patterns (dry-run preview)
python scripts/upload_patterns_to_supabase.py --dry-run
```

**Async Processing**
```bash
# Analyze refunds asynchronously (uses Celery)
python scripts/async_analyzer.py
```

---

### 🔧 Database & System Maintenance

**Database Operations**
```bash
# Deploy URL RPC function updates
python scripts/deploy_url_rpc_updates.py

# Apply vendor migration to database
python scripts/apply_vendor_migration.py

# Check Supabase storage usage
python scripts/check_storage_usage.py
```

**Utilities**
```bash
# Check Supabase table status
python scripts/utils/check_supabase_tables.py

# Verify old schema tables are empty
python scripts/utils/clear_old_schema.py
```

---

## Common Workflows

### "I want to set up a new machine"
```bash
# 1. Download knowledge base from cloud
python scripts/download_knowledge_base_from_storage.py

# 2. Verify everything is set up correctly
python scripts/verify_setup.py
```

### "I want to add new tax law documents"
```bash
# Option 1: Download from official sources
python scripts/download_wac_title_458.py
python scripts/download_rcw_title_82.py

# Option 2: Add manually to knowledge_base/ folder
# Then run ingestion (see core/README.md)
```

### "I want to edit document metadata"
```bash
# 1. Export to Excel
python scripts/export_metadata_excel.py

# 2. Edit the Excel file (opens in outputs/)

# 3. Import changes back
python scripts/import_metadata_excel.py path/to/edited.xlsx
```

### "I want to update the knowledge base across machines"
```bash
# On source machine:
python scripts/upload_knowledge_base_to_storage.py

# On destination machine(s):
python scripts/download_knowledge_base_from_storage.py
```

---

## Script Dependencies

Most scripts require:
- Python 3.8+
- Environment variables set (see `.env.example`)
- Supabase connection configured

Some scripts require additional dependencies:
- **Async scripts**: Celery, Redis running
- **Web scraping**: Beautiful Soup, requests
- **Excel scripts**: openpyxl, pandas

Run `pip install -r requirements.txt` to install all dependencies.

---

## Environment Variables

Required for most scripts:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here
OPENAI_API_KEY=sk-your-key-here
```

See `.env.example` for complete list.

---

## Best Practices

1. **Always run from project root**: `python scripts/script_name.py`
2. **Check script help**: Most scripts support `--help` flag
3. **Use dry-run when available**: Many scripts have `--dry-run` option
4. **Back up before bulk operations**: Export metadata before major changes

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Supabase connection failed"
Check your `.env` file has correct credentials:
```bash
python scripts/verify_setup.py
```

### "Permission denied" errors
Some scripts need write access to `knowledge_base/` and `outputs/` folders.

---

## Adding New Scripts

When adding new scripts to this folder:

1. **Name clearly**: `action_object.py` (e.g., `download_tax_law.py`)
2. **Add docstring**: Explain purpose and usage
3. **Support --help**: Use argparse for command-line arguments
4. **Update this README**: Add to appropriate category
5. **Include in requirements.txt**: If new dependencies needed

---

## Related Documentation

- [Core Ingestion](../core/README.md) - Document ingestion pipeline
- [Analysis Modules](../analysis/README.md) - Analysis code
- [Setup Guides](../docs/setup/) - Environment setup
- [Quick Reference](../docs/guides/QUICK_REFERENCE.md) - Command cheatsheet

---

**Last Updated**: 2025-11-13
