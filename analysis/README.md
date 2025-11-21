# Analysis Modules

This folder contains the core analysis modules for processing tax refund data, analyzing invoices, and learning from corrections.

## Overview

The analysis system processes Excel files with invoice data, extracts information from PDF invoices, queries the knowledge base using enhanced RAG, and determines refund eligibility using AI. The system intelligently tracks which rows have been analyzed to avoid redundant processing.

## Current File Structure

```
analysis/
├── fast_batch_analyzer.py    # Main analyzer (EnhancedRAG + ExcelFileWatcher)
├── excel_processors.py        # Excel parsing and validation
├── invoice_lookup.py          # PDF invoice extraction
├── import_corrections.py      # Learning from human corrections
├── matchers.py                # Vendor and keyword pattern matching
└── README.md                  # This file
```

**Total: 5 modules** (consolidated from 8 for simplicity)

---

## Module Descriptions

### Core Analysis Engine

#### `fast_batch_analyzer.py`
**Purpose**: High-quality, efficient batch invoice analysis with intelligent change tracking

**Key Features**:
- **EnhancedRAG Integration**: Corrective RAG + AI reranking + query expansion for higher quality legal research
- **ExcelFileWatcher**: Database-backed row tracking using file/row hashes - only analyzes new or modified rows
- **Smart Caching**: Vendor DB, invoice extraction, RAG results cached for performance
- **Batch Processing**: Analyzes 20 items per API call for efficiency
- **State-Aware**: Configurable for different state tax laws

**What it does**:
1. Loads Excel file and checks which rows are new/changed (skips already-analyzed rows)
2. Extracts invoice data from PDFs using GPT-4 Vision (with caching)
3. Matches line items by dollar amount
4. Categorizes products (SaaS, Professional Services, Hardware, etc.)
5. Searches legal docs using EnhancedRAG (corrective RAG + reranking)
6. Batch analyzes 20 items at a time with GPT-4o
7. Outputs Excel with AI analysis columns
8. Updates tracking database for processed rows

**Usage**:
```bash
# Analyze only changed rows (production use)
python analysis/fast_batch_analyzer.py \
    --excel "Master Refunds.xlsx" --state washington

# Test mode (force re-analysis of first N rows)
python analysis/fast_batch_analyzer.py \
    --excel "Master Refunds.xlsx" --state washington --limit 10

# Custom output file
python analysis/fast_batch_analyzer.py \
    --excel input.xlsx --output results.xlsx
```

**How Change Tracking Works**:
- First run: Analyzes all rows, stores file hash + row hashes in database
- Subsequent runs: Compares file hash → if changed, checks row hashes → only processes new/modified rows
- Test mode (`--limit`): Bypasses tracking, forces re-analysis of first N rows

**Input**: Excel with columns (Vendor, Invoice_Number, Amount, Tax, Inv_1_File, etc.)
**Output**: Same Excel + Product_Desc, Product_Type, Refund_Basis, Citation, Confidence, Estimated_Refund, Explanation

---

### Supporting Modules

#### `excel_processors.py`
**Purpose**: Excel file parsing and validation utilities

**Contains**:
- `DenodoSalesTaxProcessor` - Processes 109-column SAP sales tax exports
- `UseTaxProcessor` - Processes 32-column use tax research files
- `auto_detect_file_type()` - Automatically detects Excel format based on columns

**Usage**: Imported by analysis scripts
```python
from analysis.excel_processors import auto_detect_file_type, DenodoSalesTaxProcessor

# Auto-detect format
processor = auto_detect_file_type("sales_tax.xlsx")
df = processor.load_file("sales_tax.xlsx")
```

---

#### `invoice_lookup.py`
**Purpose**: Extract line item details from invoice PDFs

**What it does**:
- Opens invoice PDF
- Finds line item matching specific dollar amount
- Extracts product description, SKU, details
- Handles multiple invoice formats (structured tables and text-based)

**Usage**: Called internally by fast_batch_analyzer.py
```python
from analysis.invoice_lookup import extract_line_item
desc = extract_line_item(pdf_path, amount=8000.00)
```

---

#### `matchers.py`
**Purpose**: Historical pattern matching for vendors and keywords

**Contains**:
- `VendorMatcher` - Fuzzy matching for vendor names using keyword overlap
- `KeywordMatcher` - Pattern matching for product descriptions

**What it does**:
- Matches vendor names (exact and fuzzy) to historical vendor_products database
- Extracts keywords from product descriptions and matches to keyword_patterns
- Returns historical success rates, typical refund basis, sample counts
- Provides human-readable context for AI analysis

**Usage**:
```python
from analysis.matchers import VendorMatcher, KeywordMatcher

# Match vendor
vendor_matcher = VendorMatcher()
match = vendor_matcher.get_best_match("American Tower Company")
# Returns: {'vendor_name': 'ATC TOWER SERVICES', 'match_type': 'fuzzy',
#           'historical_success_rate': 1.0, 'typical_refund_basis': 'Out-of-State Services'}

# Match product description
keyword_matcher = KeywordMatcher()
pattern = keyword_matcher.match_description("Tower construction services")
# Returns: {'keywords': ['tower', 'construction', 'services'], 'success_rate': 0.92,
#           'typical_basis': 'Out-of-State Services', 'sample_count': 15234}
```

**Matching Strategy**:
1. VendorMatcher: Exact match → Fuzzy match (keyword overlap) → No match
2. KeywordMatcher: Extract keywords → Find overlapping patterns → Return highest overlap

---

#### `import_corrections.py`
**Purpose**: Import human corrections and learn from them

**What it does**:
- Reads reviewed Excel with correction columns
- Stores reviews in `analysis_reviews` database table
- Creates/updates vendor product catalog in `vendor_products` table
- Generates keyword patterns in `keyword_patterns` table
- Logs all changes to audit trail

**Usage**:
```bash
python analysis/import_corrections.py reviewed.xlsx --reviewer email@company.com
```

**Input**: Excel with these human-filled columns:
- `Review_Status` - Approved/Needs Correction/Rejected (**required**)
- `Corrected_Product_Desc` - Fixed description (if wrong)
- `Corrected_Product_Type` - Fixed type (if wrong)
- `Corrected_Refund_Basis` - Fixed reasoning (if wrong)
- `Reviewer_Notes` - Your explanation (**recommended**)

**Output**: Updates database with learnings for future analyses

---

## How the System Works

### Complete Analysis Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Excel Input (Master Refunds.xlsx)                        │
│    - Vendor, Amount, Tax, Inv_1_File columns                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. fast_batch_analyzer.py                                   │
│    ├→ ExcelFileWatcher checks which rows are new/changed    │
│    ├→ Loads only changed rows (skips already-analyzed)      │
│    ├→ Extracts invoice PDFs with GPT-4 Vision (cached)      │
│    ├→ Matches line items by dollar amount                   │
│    ├→ Categorizes products (SaaS, Services, Hardware, etc.) │
│    ├→ EnhancedRAG searches legal docs (corrective RAG +     │
│    │  reranking + query expansion)                          │
│    ├→ Batch analyzes 20 items at a time with GPT-4o         │
│    ├→ Outputs Excel with AI analysis columns                │
│    └→ Updates tracking database for processed rows          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Excel Output (Master Refunds - Analyzed.xlsx)            │
│    + Product_Desc, Product_Type, Refund_Basis, Citation,    │
│      Confidence, Estimated_Refund, Explanation              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Human Review (You fill in Review_Status columns)         │
│    - Review_Status: Approved/Needs Correction/Rejected      │
│    - Corrected_* columns for any mistakes                   │
│    - Reviewer_Notes for your reasoning                      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. import_corrections.py                                    │
│    ├→ Reads review columns from Excel                       │
│    ├→ Stores in analysis_reviews table                      │
│    ├→ Updates vendor_products catalog (vendor patterns)     │
│    ├→ Updates keyword_patterns table (product patterns)     │
│    └→ Creates audit trail                                   │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Next Analysis (Improved!)                                │
│    ├→ VendorMatcher uses learned vendor patterns            │
│    ├→ KeywordMatcher uses learned product patterns          │
│    └→ AI gets better with each correction cycle!            │
└─────────────────────────────────────────────────────────────┘
```

### Smart Row Tracking Example

**First Run**:
```bash
python analysis/fast_batch_analyzer.py --excel "Master.xlsx"
# Processes all 10,000 rows
# Saves file hash + 10,000 row hashes to database
# Outputs: Master - Analyzed.xlsx
```

**Second Run** (no changes):
```bash
python analysis/fast_batch_analyzer.py --excel "Master.xlsx"
# ✓ No changes detected - all rows already analyzed!
# Exits immediately (saves time and API costs)
```

**Third Run** (added 50 new rows):
```bash
python analysis/fast_batch_analyzer.py --excel "Master.xlsx"
# ✓ Found 50 changed/new rows out of 10,050 total
# Skipping 10,000 already-analyzed rows
# Processes only the 50 new rows
# Updates tracking database
```

---

## Input/Output Formats

### Input Excel Format
Required columns:
- `Vendor` - Vendor name
- `Invoice_Number` - Invoice #
- `PO Number` - Purchase order #
- `Date` - Transaction date
- `Inv_1_File` - Invoice PDF filename (must exist in client_documents/invoices/)
- `Amount` - Line item amount (used for matching)
- `Tax` - Tax paid

### Output Excel Format
Input columns + these AI-generated columns:
- `Product_Desc` - Product description extracted from invoice
- `Product_Type` - Category (saas_subscription, professional_services, iaas_paas, software_license, tangible_personal_property, other)
- `Refund_Basis` - Legal reasoning (MPU, Non-taxable, OOS Services, No Refund)
- `Citation` - Legal citations (e.g., "WAC 458-20-15502, RCW 82.04.050")
- `Confidence` - AI confidence score (0-100%)
- `Estimated_Refund` - Dollar amount eligible for refund
- `Explanation` - Detailed explanation of the decision

### Review Excel Format (for import_corrections.py)
Output columns + these human-filled columns:
- `Review_Status` - Approved/Needs Correction/Rejected (**required**)
- `Corrected_Product_Desc` - Fixed description (if wrong)
- `Corrected_Product_Type` - Fixed type (if wrong)
- `Corrected_Refund_Basis` - Fixed reasoning (if wrong)
- `Reviewer_Notes` - Your explanation (**recommended**)

---

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-...           # For GPT-4o and embeddings
SUPABASE_URL=https://...        # Database connection
SUPABASE_SERVICE_ROLE_KEY=...  # Database auth
```

### Invoice Files Location
```
client_documents/invoices/
├── INV-001.pdf
├── INV-002.pdf
└── ...
```

The `Inv_1_File` column in Excel should match the filename exactly.

---

## Performance & Cost Optimization

### Fast Batch Analyzer Optimizations

**1. Smart Caching** (saves 70-80% API costs on repeated data):
- Invoice extraction cached by file path
- Vendor info cached by vendor name
- RAG results cached by category + state

**2. Intelligent Row Tracking** (only process what changed):
- File hash check: Instant detection if Excel unchanged
- Row hash check: Only process new/modified rows
- Database-backed: Survives across sessions

**3. Batch Processing** (reduces API calls by 20x):
- Analyzes 20 items per API call instead of 1
- Single prompt for entire batch
- Maintains quality while reducing costs

**4. EnhancedRAG** (better quality, similar cost):
- Corrective RAG validates citations
- AI reranking improves relevance
- Query expansion catches more scenarios
- Minimal additional API overhead

### Typical Performance

**10,000 row Excel file**:
- First run: ~30-45 minutes, ~$50-80 in API costs
- Second run (no changes): <5 seconds, $0
- Third run (50 new rows): ~3-5 minutes, ~$2-4
- Fourth run (500 corrections): ~15-20 minutes, ~$15-25

---

## Troubleshooting

### "No changes detected - all rows already analyzed!"
- This is normal! The system is working correctly.
- If you want to force re-analysis, use `--limit` flag for testing:
  ```bash
  python analysis/fast_batch_analyzer.py --excel file.xlsx --limit 100
  ```

### "No invoice file" or "Extraction failed"
- Check that invoice PDFs exist in `client_documents/invoices/`
- Verify `Inv_1_File` column matches exact filename
- PDFs must be text-based (not scanned images without OCR)

### "No line item match"
- Invoice amount in Excel doesn't match any line item in the PDF
- Try adjusting the matching threshold in invoice_lookup.py
- Verify Amount column is correct in Excel

### Low confidence scores (<50%)
- Insufficient knowledge base documents
- Ambiguous product descriptions
- Novel scenarios not seen before
- **Solution**: Add more legal documents to knowledge base, review and correct low-confidence items

### "Database connection failed"
- Check `.env` file has correct Supabase credentials
- Verify network connectivity
- Check that required tables exist: `excel_file_tracking`, `excel_row_tracking`, `vendor_products`, `keyword_patterns`

### EnhancedRAG import errors
- Ensure `core/enhanced_rag.py` exists
- Check that required dependencies are installed: `pip install openai supabase python-dotenv pandas tqdm pdfplumber`

---

## Database Schema

The analysis system uses these tables:

### `excel_file_tracking`
Tracks processed Excel files:
- `file_path` - Full path to Excel file
- `file_hash` - SHA256 hash of entire file
- `last_processed_at` - Timestamp
- `row_count` - Number of rows processed

### `excel_row_tracking`
Tracks individual rows:
- `file_path` - Full path to Excel file
- `row_index` - Row number in DataFrame
- `row_hash` - MD5 hash of row data
- `processed_at` - Timestamp
- `row_data` - JSONB snapshot of row

### `vendor_products`
Historical vendor patterns:
- `vendor_name` - Normalized vendor name (uppercase)
- `vendor_keywords` - Keywords extracted from name
- `description_keywords` - Typical product keywords
- `historical_success_rate` - % of refunds approved
- `typical_refund_basis` - Most common refund reason
- `historical_sample_count` - Number of historical cases

### `keyword_patterns`
Product description patterns:
- `keywords` - Array of keywords
- `success_rate` - % of refunds approved
- `typical_basis` - Most common refund reason
- `sample_count` - Number of matching cases

---

## Recent Changes (2025-11-20)

### Phase 1: Consolidation (8 files → 5 files)
- **Created**: `matchers.py` - Consolidated VendorMatcher + KeywordMatcher
- **Deleted**: `vendor_matcher.py`, `keyword_matcher.py` (merged into matchers.py)
- **Deleted**: `analyze_refunds_enhanced.py` (functionality moved to fast_batch_analyzer)
- **Deleted**: `invoice_pattern_learning.py` (orphaned code, not used)

### Phase 2: Enhancement (Quality Upgrade)
- **Upgraded**: `fast_batch_analyzer.py`
  - Integrated EnhancedRAG (corrective RAG + reranking + query expansion)
  - Added ExcelFileWatcher (intelligent row-level change tracking)
  - Updated documentation and usage examples

### Result
- 37.5% reduction in file count (simpler, easier to maintain)
- Higher quality analysis (EnhancedRAG)
- Intelligent change tracking (ExcelFileWatcher)
- Maintains batch processing speed
- Better documentation

---

## Related Documentation

- [Dev Log](../docs/active/DEV-LOG.md) - Recent development activity
- [Core Modules](../core/README.md) - EnhancedRAG, ExcelFileWatcher, database utilities
- [Scripts](../scripts/README.md) - Supporting scripts and deployment tools

---

**Last Updated**: 2025-11-20
