# Knowledge Base

This folder contains source documents that power the RAG (Retrieval-Augmented Generation) system.

## Folder Structure

```
knowledge_base/
├── states/
│   └── washington/
│       └── legal_documents/
│           ├── WAC_458-20-*.pdf          # Washington Administrative Code
│           ├── RCW_82-*.pdf              # Revised Code of Washington
│           └── WTD_*.pdf                 # Washington Tax Decisions
│
└── vendors/
    ├── Nokia/
    ├── Ericsson/
    └── [other vendors]/
```

---

## Document Types

### Tax Law Documents (`states/washington/legal_documents/`)

#### Washington Administrative Code (WAC)
- **Prefix**: `WAC_458-20-`
- **Example**: `WAC_458-20-15502.pdf`
- **Content**: Administrative regulations for tax law
- **Source**: https://app.leg.wa.gov/wac/default.aspx?cite=458

#### Revised Code of Washington (RCW)
- **Prefix**: `RCW_82-`
- **Example**: `RCW_82-04-050.pdf`
- **Content**: State statutes and laws
- **Source**: https://app.leg.wa.gov/rcw/default.aspx?cite=82

#### Washington Tax Decisions (WTD)
- **Prefix**: `WTD_` or `Det_No_`
- **Example**: `Det_No_18-0001.pdf`
- **Content**: Department of Revenue rulings and determinations
- **Source**: https://dor.wa.gov/about/statistics-reports/tax-decisions

---

### Vendor Background Documents (`vendors/`)

**Purpose**: Context about vendors and their products to improve analysis accuracy

**Organization**: One folder per vendor
```
vendors/
├── Nokia/
│   ├── Nokia_Company_Profile.pdf
│   ├── Nokia_Product_Catalog.pdf
│   └── Nokia_Industry_Analysis.pdf
```

**What to include**:
- Company profiles
- Product catalogs
- Industry information
- Service descriptions
- Historical context

---

## Adding Documents

### Adding Tax Law Documents

#### Option 1: Download with Scripts
```bash
# Download all WAC Title 458
python scripts/download_wac_title_458.py

# Download all RCW Title 82
python scripts/download_rcw_title_82.py

# Download Washington Tax Decisions
python scripts/download_tax_decisions.py
```

#### Option 2: Add Manually
1. Download PDF from official source
2. Name using standard convention:
   - WAC: `WAC_458-20-XXXXX.pdf`
   - RCW: `RCW_82-XX-XXX.pdf`
   - WTD: `Det_No_XX-XXXX.pdf`
3. Place in `knowledge_base/states/washington/legal_documents/`
4. Run ingestion (see below)

---

### Adding Vendor Documents

1. Create vendor folder: `knowledge_base/vendors/VendorName/`
2. Add PDF documents to vendor folder
3. Use descriptive filenames: `VendorName_DocumentType.pdf`
4. Run ingestion (see below)

---

## Ingesting Documents

After adding documents to the knowledge_base folder, ingest them into the database:

### Ingest Tax Law Documents
```bash
# Ingest single file
python core/ingest_documents.py knowledge_base/states/washington/legal_documents/WAC_458-20-15502.pdf

# Ingest entire folder
python core/ingest_documents.py knowledge_base/states/washington/legal_documents/
```

### Ingest Vendor Documents
```bash
# Ingest vendor folder
python core/ingest_documents.py knowledge_base/vendors/Nokia/
```

See [core/README.md](../core/README.md) for detailed ingestion instructions.

---

## Syncing Across Machines

### Upload to Cloud
```bash
# Upload your local knowledge_base to Supabase Storage
python scripts/upload_knowledge_base_to_storage.py
```

### Download from Cloud
```bash
# Download knowledge_base from Supabase Storage
python scripts/download_knowledge_base_from_storage.py
```

This allows team members to share the same knowledge base without manually copying files.

See [KNOWLEDGE_BASE_SYNC](../docs/security/KNOWLEDGE_BASE_SYNC.md) for details.

---

## File Naming Conventions

### Tax Law Documents
**Format**: `TYPE_SECTION-NUMBER.pdf`

**Examples**:
- `WAC_458-20-15502.pdf` - WAC section 458-20-15502
- `RCW_82-04-050.pdf` - RCW section 82.04.050
- `Det_No_18-0001.pdf` - Determination Number 18-0001

### Vendor Documents
**Format**: `VendorName_DocumentType.pdf`

**Examples**:
- `Nokia_Company_Profile.pdf`
- `Ericsson_Product_Catalog_2024.pdf`
- `SAP_Cloud_Services_Overview.pdf`

---

## Best Practices

### Document Quality
1. **Use official sources** - Download from wa.gov when possible
2. **Check OCR** - Ensure PDFs have extractable text (not just images)
3. **Verify completeness** - Ensure documents aren't truncated
4. **Update regularly** - Tax law changes, keep KB current

### Organization
1. **Consistent naming** - Follow naming conventions above
2. **Proper folders** - Tax law vs vendor documents
3. **No duplicates** - Check before adding
4. **Version control** - Keep only current versions (unless historical context needed)

### Performance
1. **Don't over-ingest** - More documents = slower search
2. **Relevance first** - Only add relevant documents
3. **Chunk wisely** - Large documents are automatically chunked (see chunking.py)
4. **Monitor size** - Check Supabase storage limits

---

## Current Contents

### Tax Law Documents
- **WAC Sections**: ~755 sections from Title 458
- **RCW Sections**: ~1,128 sections from Title 82
- **Tax Decisions**: Varies (download script gets latest)

### Vendor Documents
Check subfolders in `vendors/` for current vendor documentation.

---

## Troubleshooting

### "No text extracted from PDF"
**Cause**: PDF is scanned image, no OCR text
**Solution**:
1. Use `pdftotext` to verify: `pdftotext file.pdf -`
2. Run OCR tool if needed: `ocrmypdf input.pdf output.pdf`

### "Duplicate document" warning
**Cause**: Document already in database
**Solution**:
- Check if you've already ingested this file
- Use `--force` flag to re-ingest: `python core/ingest_documents.py file.pdf --force`

### Storage space issues
**Check usage**:
```bash
python scripts/check_storage_usage.py
```

**Solutions**:
- Remove old/unused documents
- Compress PDFs before adding
- Upgrade Supabase plan if needed

---

## Related Documentation

- [Knowledge Base Guide](../docs/guides/KNOWLEDGE_BASE_GUIDE.md) - Comprehensive KB guide
- [Web Scraping Guide](../docs/guides/WEB_SCRAPING_GUIDE.md) - Download tax law
- [Core Ingestion](../core/README.md) - Document ingestion details
- [KB Sync Guide](../docs/security/KNOWLEDGE_BASE_SYNC.md) - Multi-machine sync

---

**Last Updated**: 2025-11-13

**Current Status**: 1,681 documents, 4,226 chunks in database
