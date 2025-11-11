# Washington State Tax Law Scraper

Automated web scraper that ingests Washington State tax laws directly from official sources into a SQLite database, with manual approval workflow before ingesting into Supabase for RAG system integration.

## Data Sources

1. **RCW Title 82** - Excise Taxes (PDF Archive: lawfilesext.leg.wa.gov)
   - Business & Occupation Tax (82.04)
   - Retail Sales Tax (82.08)
   - Use Tax (82.12)
   - Local Taxes (82.14)
   - Administration (82.32)
   - **Status**: ✅ Complete (1,128 sections scraped)

2. **WAC Title 458** - DOR Regulations (Coming soon)

3. **DOR Tax Determinations** (Coming soon)

## Installation

```bash
cd tax_scraper
pip install -r requirements.txt
```

Dependencies:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `PyPDF2` - PDF text extraction
- `pandas` - Excel export/import
- `openpyxl` - Excel file handling
- `supabase` - Supabase client

## Complete Workflow

The scraper follows a 3-step workflow with manual approval:

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Scrape PDFs from Official Sources                  │
│  Command: python scraper_pdf.py                             │
│  Output: tax_laws.db (SQLite with 1,128 RCW sections)       │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Export to Excel for Manual Review                  │
│  Command: python export_to_excel.py                         │
│  Output: exports/rcw_sections_review_YYYYMMDD_HHMMSS.xlsx   │
│                                                              │
│  📋 YOU MANUALLY REVIEW IN EXCEL:                            │
│  - Mark 'approved' with 'APPROVED' or 'YES' to import       │
│  - Add notes in 'notes' column if needed                    │
│  - Fill in 'reviewed_by' and 'review_date'                  │
│  - Save the file                                             │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Import Approved Sections to Supabase               │
│  Command: python import_to_supabase.py                      │
│  Output: Approved rows inserted into knowledge_base table   │
└─────────────────────────────────────────────────────────────┘
```

## Usage Guide

### Step 1: Scrape RCW PDFs

```bash
python scraper_pdf.py
```

This will:
- Download RCW Title 82 PDFs from lawfilesext.leg.wa.gov
- Extract text using PyPDF2
- Store in `tax_laws.db` SQLite database
- Save raw PDFs to `raw_files/pdfs/` for verification
- Log progress to `logs/` directory
- Takes ~25-30 minutes for all 1,128 sections

### Step 2: Export to Excel for Review

```bash
python export_to_excel.py
```

This will:
- Read all scraped sections from `tax_laws.db`
- Create Excel file in `exports/` directory with timestamp
- Include approval columns: `approved`, `notes`, `reviewed_by`, `review_date`
- Add `text_preview` column (first 200 chars) for quick review
- Freeze header row for easy scrolling

**Your Manual Review Process:**
1. Open the generated Excel file in `exports/rcw_sections_review_YYYYMMDD_HHMMSS.xlsx`
2. Review each section's `citation`, `title`, and `text_preview`
3. Mark `approved` column with **"APPROVED"** or **"YES"** for sections you want to import to Supabase
   - Accepted values: `APPROVED`, `approved`, `YES`, `yes`, `Y` (case-insensitive)
4. Leave blank or mark "NO" for sections to skip
5. Optionally add notes in the `notes` column
6. Fill in `reviewed_by` (your name) and `review_date` (today's date)
7. **Save the file**

### Step 3: Import Approved Sections to Supabase

First, set your Supabase credentials as environment variables:

```bash
# Windows (Command Prompt)
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_SERVICE_KEY=your-service-key

# Windows (PowerShell)
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_SERVICE_KEY="your-service-key"

# Linux/Mac
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_KEY=your-service-key
```

Then run the import:

```bash
python import_to_supabase.py
```

This will:
- Read the most recent Excel file from `exports/`
- Filter for rows where `approved` = "APPROVED" or "YES" (case-insensitive)
- Insert approved sections into Supabase `knowledge_base` table
- Use upsert logic (updates existing, inserts new)
- Log summary: inserted, updated, failed counts
- Verify import by counting total RCW documents in Supabase

## Database Schema

### SQLite: rcw_sections (Intermediate Storage)
```sql
CREATE TABLE rcw_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation TEXT UNIQUE NOT NULL,          -- e.g., "RCW 82.08.020"
    title TEXT,                             -- Section title
    chapter TEXT,                           -- Chapter number
    section TEXT,                           -- Section number
    full_text TEXT NOT NULL,                -- Complete PDF text
    effective_date TEXT,                    -- When law took effect
    url TEXT,                               -- Source PDF URL
    pdf_path TEXT,                          -- Local PDF archive path
    embedding BLOB,                         -- Reserved for future RAG vectors
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Supabase: knowledge_base (Final Storage)
```sql
-- Assumed schema based on import script
{
    id: uuid,
    source_type: text,                      -- 'rcw', 'wac', 'dor'
    citation: text,                         -- Unique citation
    title: text,                            -- Section title
    content: text,                          -- Full text
    metadata: jsonb,                        -- Nested metadata object
    uploaded_at: timestamp,
    embedding: vector(1536)                 -- For RAG retrieval
}
```

**Metadata JSONB structure:**
```json
{
  "chapter": "08",
  "section": "020",
  "effective_date": "2023 c 123 § 1",
  "source_url": "https://...",
  "pdf_path": "raw_files/pdfs/rcw_82_08_020.pdf",
  "reviewed_by": "Jacob Allen",
  "review_date": "2025-01-10",
  "review_notes": "Critical for sales tax calculations",
  "scraped_at": "2025-01-10T15:30:00"
}
```

## Features

- **PDF-Based Extraction**: Robust text extraction from official PDF archives
- **Rate Limiting**: 1 second delay between requests (respectful scraping)
- **Error Handling**: Automatic retry with 3 attempts and 5-second delays
- **Upsert Logic**: Re-running scraper updates existing sections safely
- **Logging**: Detailed logs with timestamps to `logs/` directory
- **Raw File Storage**: Saves original PDFs to `raw_files/pdfs/` for verification
- **Manual Approval Workflow**: Excel-based review before Supabase import
- **Resumability**: Tracks progress in `scraping_progress` table
- **Security**: Parameterized SQL queries, no hardcoded credentials

## File Structure

```
tax_scraper/
├── scraper_pdf.py              # Main scraper (Step 1)
├── export_to_excel.py          # Export for review (Step 2)
├── import_to_supabase.py       # Import approved sections (Step 3)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── tax_laws.db                 # SQLite intermediate storage
├── logs/                       # Scraping logs
├── raw_files/
│   └── pdfs/                   # Downloaded PDFs (1,128 files)
└── exports/                    # Excel review files
    └── rcw_sections_review_YYYYMMDD_HHMMSS.xlsx
```

## Troubleshooting

**Issue**: `pip install` fails on Windows with "lxml build error"
- **Solution**: Use built-in `html.parser` (already configured in code)

**Issue**: Import script says "No approved sections found"
- **Solution**: Make sure you marked the `approved` column with "APPROVED" or "YES" in Excel (case-insensitive)

**Issue**: Supabase import fails with "Missing credentials"
- **Solution**: Set `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` environment variables

**Issue**: Excel file too large to open
- **Solution**: 1,128 rows is manageable. Use Excel's filter feature to review chapter by chapter

## Next Steps

After completing RCW Title 82 ingestion:
1. **Build WAC Title 458 scraper** (administrative regulations)
2. **Build DOR Tax Determinations scraper** (tax decision PDFs)
3. **Generate embeddings** for RAG retrieval using OpenAI/Anthropic
4. **Integrate with RefundEngine** for tax law Q&A

## Security Best Practices

- ✅ Uses parameterized SQL queries (no SQL injection risk)
- ✅ No hardcoded credentials (uses environment variables)
- ✅ Rate limiting prevents DoS classification
- ✅ Path traversal protection via `pathlib.Path`
- ✅ Request timeouts prevent indefinite hangs
- ✅ Retry logic with exponential backoff

## License & Usage

This scraper accesses public Washington State legal documents for authorized use in tax compliance software. Be respectful of government servers by maintaining rate limits.
