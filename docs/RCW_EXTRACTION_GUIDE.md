# RCW Title 82 PDF Extraction Guide

This guide explains how to extract and process PDFs from the Washington State RCW (Revised Code of Washington) Title 82 website.

## Problem: Site Blocks Automated Access

The WA Legislature website (`app.leg.wa.gov`) blocks automated HTTP requests with 403 errors, making direct scraping difficult.

## Solution Options

### Option 1: Manual Download (Recommended)

The most reliable method is to manually download or print-to-PDF from your browser:

1. **Visit the RCW Title 82 page:**
   ```
   https://app.leg.wa.gov/rcw/default.aspx?Cite=82
   ```

2. **For each chapter/section you need:**
   - Click on the chapter link (e.g., "Chapter 82.04 - Business and occupation tax")
   - Click on individual sections (e.g., "82.04.010")
   - Use your browser's "Print to PDF" feature (Cmd/Ctrl + P → Save as PDF)
   - Save to: `knowledge_base/states/washington/legal_documents/rcw/`

3. **Naming convention:**
   - Use format: `RCW_82-04-010.pdf` for section 82.04.010
   - This matches what our ingestion scripts expect

4. **Process the PDFs:**
   ```bash
   python scripts/ingest_documents.py \
     --type tax_law \
     --folder knowledge_base/states/washington/legal_documents/rcw \
     --export-metadata outputs/RCW_Title_82_Metadata.xlsx
   ```

### Option 2: Browser Automation with Selenium

For bulk extraction, use Selenium to automate a real browser:

1. **Install requirements:**
   ```bash
   pip install selenium webdriver-manager
   ```

2. **Run the Selenium script:**
   ```bash
   # Test with 2 chapters first
   python scripts/extract_rcw_pdfs_selenium.py --limit 2 --visible

   # Run full extraction (headless)
   python scripts/extract_rcw_pdfs_selenium.py
   ```

3. **Note:** This may still encounter limitations depending on the site structure.

### Option 3: HTML Content Extraction

Since RCW content is primarily HTML (not PDF), you can extract the HTML and convert it:

1. **Extract as text files:**
   ```bash
   # Test with 5 sections
   python scripts/extract_rcw_html_to_pdf.py --limit 5 --format text

   # Full extraction
   python scripts/extract_rcw_html_to_pdf.py --format text
   ```

2. **Extract as PDFs (requires reportlab):**
   ```bash
   pip install reportlab
   python scripts/extract_rcw_html_to_pdf.py --format pdf
   ```

### Option 4: Use wget/curl with Session

Sometimes using curl or wget with the right headers works:

```bash
# Create directory
mkdir -p knowledge_base/states/washington/legal_documents/rcw

# Download with curl (example for one section)
curl 'https://app.leg.wa.gov/rcw/default.aspx?cite=82.04.010' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9' \
  -o rcw_82_04_010.html

# Then convert HTML to PDF using browser or wkhtmltopdf
wkhtmltopdf rcw_82_04_010.html knowledge_base/states/washington/legal_documents/rcw/RCW_82-04-010.pdf
```

## Key RCW Title 82 Chapters

Focus on these tax-related chapters:

| Chapter | Topic |
|---------|-------|
| 82.04 | Business and occupation tax |
| 82.08 | Retail sales tax |
| 82.12 | Use tax |
| 82.14 | Local retail sales and use taxes |
| 82.16 | Public utility tax |
| 82.32 | Excise tax collection and reporting |

## After Extraction: Ingestion Workflow

Once you have PDFs (or text files) in the `rcw/` folder:

### Step 1: Export Metadata for Review
```bash
python scripts/ingest_documents.py \
  --type tax_law \
  --folder knowledge_base/states/washington/legal_documents/rcw \
  --export-metadata outputs/RCW_Title_82_Metadata.xlsx
```

This will:
- Analyze each PDF with AI
- Suggest metadata (citations, categories, topics)
- Export to Excel for your review

### Step 2: Review and Edit Excel
1. Open `outputs/RCW_Title_82_Metadata.xlsx`
2. Review AI suggestions
3. Edit metadata as needed
4. Set `Status` column to:
   - `Approved` - Ready to ingest
   - `Skip` - Don't ingest
   - `Review` - Need more review (won't be ingested)

### Step 3: Import and Ingest
```bash
python scripts/ingest_documents.py \
  --import-metadata outputs/RCW_Title_82_Metadata.xlsx
```

This will:
- Chunk documents intelligently
- Generate embeddings
- Store in Supabase
- Track in knowledge_documents table

## Scripts Reference

### 1. `extract_rcw_pdfs.py`
Basic HTTP scraper (blocked by 403, but kept for reference)

### 2. `extract_rcw_pdfs_selenium.py`
Browser automation with Selenium

### 3. `extract_rcw_html_to_pdf.py`
HTML content extractor that converts to text or PDF

### 4. `ingest_documents.py`
Main ingestion script (works with any PDFs)

## Troubleshooting

### "403 Forbidden" Error
- Site is blocking automated access
- Use manual download or Selenium

### "No PDF link found"
- RCW sections may not have direct PDF downloads
- Use browser's Print-to-PDF feature
- Or use the HTML extraction script

### Empty or Missing Content
- Some sections may be structured differently
- Verify HTML structure and adjust extraction logic
- Consider manual review for critical sections

## Best Practices

1. **Start small:** Test with `--limit 5` before full extraction
2. **Respect the server:** Use delays (`--delay 2.0`) between requests
3. **Verify content:** Spot-check a few extracted files before processing all
4. **Manual backup:** For critical sections, manually verify the content
5. **Track progress:** Keep notes on which chapters you've processed

## Contact

If you encounter issues or need help with extraction, refer to the main project documentation or check the scripts' help text:

```bash
python scripts/extract_rcw_html_to_pdf.py --help
python scripts/ingest_documents.py --help
```
