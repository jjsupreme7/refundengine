# Washington State Tax Law Web Scraping Guide

This guide explains how to use the web scrapers to download Washington state tax law documents from official government websites.

## Overview

We have three scrapers that download content from:
1. **Tax Decisions** - DOR tax decisions (2015-2025)
2. **WAC Title 458** - Administrative regulations
3. **RCW Title 82** - Statutory law

All scrapers are respectful of server resources with built-in rate limiting.

---

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure beautifulsoup4 is installed
pip install beautifulsoup4==4.12.3
```

---

## 1. Tax Decisions Scraper

**Purpose**: Download Washington State Department of Revenue tax decisions (PDF + metadata)

**Source**: https://dor.wa.gov/washington-tax-decisions

**Script**: `scripts/download_tax_decisions.py`

### Quick Start

```bash
# Download all tax decisions (755 total, ~30-35 hours with rate limiting)
python scripts/download_tax_decisions.py

# Download specific years only
python scripts/download_tax_decisions.py --years 2023,2024,2025

# Test with limited downloads
python scripts/download_tax_decisions.py --limit 10

# Custom output directory
python scripts/download_tax_decisions.py --output-dir custom/path
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir` | Output directory path | `knowledge_base/wa_tax_law/tax_decisions` |
| `--years` | Comma-separated years to download | All years |
| `--limit` | Limit number of downloads (testing) | No limit |
| `--rate-limit` | Seconds between downloads | 1.0 |

### Output Structure

```
knowledge_base/wa_tax_law/tax_decisions/
├── index.json                    # Master index with all decisions
├── 2025/
│   ├── 44WTD070.pdf             # Decision PDF
│   ├── 44WTD070.json            # Metadata (citation, date, summary)
│   ├── 44WTD081.pdf
│   └── 44WTD081.json
├── 2024/
│   └── ...
└── 2023/
    └── ...
```

### Metadata Format

Each JSON file contains:
```json
{
  "citation": "Det. No. 22-0105, 44 WTD 070 (2025)",
  "date": "06/20/2025",
  "summary": "A taxpayer that operates a television station...",
  "pdf_url": "https://dor.wa.gov/sites/default/files/2025-06/44WTD070.pdf",
  "year": "2025",
  "filename": "44WTD070.pdf",
  "downloaded_at": "2025-11-11 08:41:36"
}
```

### Expected Results

- **Total decisions**: ~755 (2015-2025)
- **Download time**: ~12-13 minutes (with 1sec rate limit)
- **Storage**: ~500 MB

---

## 2. WAC Title 458 Scraper

**Purpose**: Download Washington Administrative Code Title 458 (Department of Revenue regulations)

**Source**: https://app.leg.wa.gov/wac/default.aspx?cite=458

**Script**: `scripts/download_wac_title_458.py`

### Quick Start

```bash
# Download priority chapters (458-20 Excise Tax Rules + 3 others)
python scripts/download_wac_title_458.py

# Download specific chapter only
python scripts/download_wac_title_458.py --chapters 458-20

# Download multiple chapters
python scripts/download_wac_title_458.py --chapters 458-20,458-29

# Download ALL chapters (not recommended, 600+ sections)
python scripts/download_wac_title_458.py --all-chapters

# HTML only (faster, no PDF authentication issues)
python scripts/download_wac_title_458.py --format html

# Test with limited sections per chapter
python scripts/download_wac_title_458.py --limit 5
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir` | Output directory path | `knowledge_base/wa_tax_law/wac/title_458` |
| `--chapters` | Comma-separated chapters | Priority chapters (458-20, 458-02, 458-29, 458-30) |
| `--all-chapters` | Download ALL 25 chapters | False |
| `--format` | Download format: `html`, `pdf`, `both` | `both` |
| `--limit` | Limit sections per chapter (testing) | No limit |
| `--rate-limit` | Seconds between downloads | 2.0 |

### Priority Chapters

| Chapter | Title | Sections | Relevance |
|---------|-------|----------|-----------|
| **458-20** | Excise tax rules | ~270 | ⭐⭐⭐ Critical (sales/use tax exemptions, definitions) |
| 458-02 | Consolidated licensing system | ~20 | ⭐⭐ Important |
| 458-29 | Tax appeals | ~30 | ⭐⭐ Important |
| 458-30 | Property tax | ~50 | ⭐ Relevant |

### Output Structure

```
knowledge_base/wa_tax_law/wac/title_458/
├── chapter_458_20_excise_tax_rules/
│   ├── 458_20_100_tax_registration.html
│   ├── 458_20_100_tax_registration.pdf
│   ├── 458_20_100_tax_registration.json
│   ├── 458_20_101_...
│   └── ...
├── chapter_458_29_tax_appeals/
│   └── ...
```

### Expected Results

- **Chapter 458-20**: ~270 sections
- **All priority chapters**: ~370 sections
- **Download time**: ~12-15 hours (with 2sec rate limit)
- **Storage**: ~200 MB

### Note: PDF Authentication

Some PDFs may require authentication. If you encounter issues:
- Use `--format html` to download HTML only
- HTML contains the same content and is easier to parse

---

## 3. RCW Title 82 Scraper

**Purpose**: Download Revised Code of Washington Title 82 (Revenue statutory law)

**Source**: https://app.leg.wa.gov/rcw/default.aspx?Cite=82

**Script**: `scripts/download_rcw_title_82.py`

### Quick Start

```bash
# Download priority chapters (82.04, 82.08, 82.12, 82.14, 82.32)
python scripts/download_rcw_title_82.py

# Download specific chapters only
python scripts/download_rcw_title_82.py --chapters 82.08,82.12

# Download ALL chapters (48 total, ~4,800 sections - not recommended)
python scripts/download_rcw_title_82.py --all-chapters

# HTML only (faster)
python scripts/download_rcw_title_82.py --format html

# Test with limited sections per chapter
python scripts/download_rcw_title_82.py --limit 10
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir` | Output directory path | `knowledge_base/wa_tax_law/rcw/title_82` |
| `--chapters` | Comma-separated chapters | Priority chapters (82.04, 82.08, 82.12, 82.14, 82.32) |
| `--all-chapters` | Download ALL 48 chapters | False |
| `--format` | Download format: `html`, `pdf`, `both` | `both` |
| `--limit` | Limit sections per chapter (testing) | No limit |
| `--rate-limit` | Seconds between downloads | 2.0 |

### Priority Chapters

| Chapter | Title | Sections | Relevance |
|---------|-------|----------|-----------|
| **82.08** | Retail sales tax | ~200 | ⭐⭐⭐ Critical (sales tax law) |
| **82.12** | Use tax | ~100 | ⭐⭐⭐ Critical (use tax law) |
| **82.04** | Business and occupation tax | ~350 | ⭐⭐ Important (B&O tax) |
| **82.14** | Local retail sales and use taxes | ~50 | ⭐⭐ Important |
| **82.32** | Excise tax—administrative provisions | ~150 | ⭐⭐ Important (admin rules) |

### Output Structure

```
knowledge_base/wa_tax_law/rcw/title_82/
├── chapter_82_04_business_occupation_tax/
│   ├── 82_04_010_definitions.html
│   ├── 82_04_010_definitions.pdf
│   ├── 82_04_010_definitions.json
│   ├── 82_04_020_...
│   └── ...
├── chapter_82_08_retail_sales_tax/
│   └── ...
└── chapter_82_12_use_tax/
    └── ...
```

### Expected Results

- **Priority chapters**: ~500 sections
- **All chapters**: ~4,800 sections
- **Download time**: ~17-20 hours for priority (with 2sec rate limit)
- **Storage**: ~300 MB

---

## Recommended Workflow

### Step 1: Download Documents (Priority Order)

```bash
# 1. Tax Decisions (highest priority, most relevant for refund analysis)
python scripts/download_tax_decisions.py --years 2022,2023,2024,2025

# 2. WAC Chapter 458-20 (administrative rules for exemptions)
python scripts/download_wac_title_458.py --chapters 458-20

# 3. RCW Priority Chapters (statutory foundation)
python scripts/download_rcw_title_82.py --chapters 82.08,82.12
```

### Step 2: Verify Downloads

```bash
# Check directory structure
ls -lh knowledge_base/wa_tax_law/tax_decisions/2025/
ls -lh knowledge_base/wa_tax_law/wac/title_458/chapter_458_20*/
ls -lh knowledge_base/wa_tax_law/rcw/title_82/chapter_82_08*/
```

### Step 3: Ingest with Existing Pipeline

```bash
# Export metadata for review
python core/ingest_documents.py \
    --type tax_law \
    --folder knowledge_base/wa_tax_law \
    --export-metadata outputs/WA_Tax_Law.xlsx

# Review in Excel, then import
python core/ingest_documents.py \
    --import-metadata outputs/WA_Tax_Law.xlsx --yes
```

---

## Troubleshooting

### Problem: Scraper finds 0 documents

**Solution**: Check your internet connection and try again. The website may be temporarily down.

### Problem: PDFs fail to download (PDF authentication errors)

**Solution**: Use HTML format instead:
```bash
python scripts/download_wac_title_458.py --format html
python scripts/download_rcw_title_82.py --format html
```

### Problem: Rate limiting / connection timeouts

**Solution**: Increase rate limit:
```bash
python scripts/download_tax_decisions.py --rate-limit 3.0
```

### Problem: Scraper interrupted mid-download

**Solution**: Just run it again! All scrapers skip already-downloaded files automatically.

---

## Rate Limiting & Etiquette

All scrapers implement respectful rate limiting:
- **Tax Decisions**: 1 second between downloads
- **WAC/RCW**: 2 seconds between downloads
- **User-Agent**: Clear identification as research bot
- **Retry logic**: Exponential backoff on errors

These are **public legal documents** with no robots.txt restrictions, but we still respect server resources.

---

## File Formats

### HTML Files
- Well-structured, semantic HTML
- Easier to parse than PDFs
- Preserves hyperlinks to related sections
- Recommended for ingestion

### PDF Files
- Official format for archival
- May have authentication issues (WAC/RCW)
- Useful for citation verification

### JSON Metadata
- Contains citation, date, summary, URL
- Used by ingestion pipeline
- Helps AI understand document context

---

## Next Steps

After downloading:

1. **Review downloads**: Check that files look correct
2. **Run ingestion pipeline**: Use `core/ingest_documents.py`
3. **Review metadata in Excel**: Edit AI suggestions before importing
4. **Import to Supabase**: Load into knowledge base with embeddings
5. **Test RAG chatbot**: Query with real questions

---

## Maintenance

### Updating Documents

Run scrapers periodically to get new content:
- **Tax Decisions**: Monthly (active updates)
- **WAC**: Quarterly (regulatory changes)
- **RCW**: Annually (legislative changes)

Scrapers automatically skip existing files, so you can safely re-run them.

### Storage Management

Expected storage per document type:
- Tax Decisions: ~500 MB (755 PDFs)
- WAC Chapter 458-20: ~100 MB (270 sections)
- RCW Priority Chapters: ~300 MB (500 sections)
- **Total**: ~1 GB for complete collection

---

## Support

If you encounter issues:
1. Check this guide first
2. Verify internet connection
3. Test with `--limit 5` flag
4. Check GitHub issues: https://github.com/jjsupreme7/refundengine/issues
