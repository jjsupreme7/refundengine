# Refund Engine - Complete System Summary

## Executive Overview

Your Refund Engine is now fully configured with:
- ✅ Old Law vs New Law system confirmed and documented
- ✅ Invoice/Purchase analysis code identified and mapped
- ✅ 30 vendors ingested into Supabase with background metadata
- ✅ Excel claim sheet structure designed with all required columns
- ✅ Auto-detection system for Excel file updates created
- ✅ Fictional test invoices and purchase orders generated (12 test cases)

---

## 1. Old Law vs New Law System

### Confirmation for Refund Engine

**CRITICAL:** For analyzing historical invoices (pre-October 1, 2025), the system **MUST USE OLD LAW ONLY**.

### Why This Matters

The new law (ESSB 5814) became effective **October 1, 2025**. Since your refund engine analyzes historical invoices from BEFORE this date, you need to determine if tax was improperly charged under the OLD law.

### Key Implication for Refunds

If sales tax was charged on these services **before October 1, 2025**, that's a **REFUND OPPORTUNITY** because they were NOT taxable under old law:
- Information Technology Services
- Advertising Services
- Custom Website Development
- Custom Software Development
- Temporary Staffing Services
- Investigation/Security Services
- Live Presentations

**Example**: A company charged sales tax on "Custom Software Development" in August 2024. Under OLD LAW, this was NOT taxable. This creates a refund opportunity!

### System Files

- **Law Version Handler**: `core/law_version_handler.py`
- **Effective Date Script**: `scripts/set_default_effective_dates.py`
- **RAG UI Integration**: `chatbot/rag_ui_with_feedback.py`
- **Database Schema**: Effective dates stored in `knowledge_documents.effective_date`

---

## 2. Invoice and Purchase Analysis Code

### Primary Analysis Modules

#### Standard Refund Analyzer
**File**: `analysis/analyze_refunds.py`

Key functions:
- `analyze_refund_eligibility()` - Determines if refund is due
- `find_line_item_in_invoice()` - Locates line items in PDF text
- `check_vendor_learning()` - Uses historical vendor knowledge
- `save_to_database()` - Stores analysis results

#### Enhanced Refund Analyzer
**File**: `analysis/analyze_refunds_enhanced.py`

Enhancements:
- Corrective RAG (validates legal citations)
- Reranking (improves relevance)
- Query expansion (better tax terminology)
- Hybrid search (vector + keyword)

#### Fast Batch Analyzer
**File**: `analysis/fast_batch_analyzer.py`

For processing 10,000+ row Excel files:
- Smart caching (vendor DB, invoice extraction, RAG results)
- Batch AI analysis (20 items per call)
- GPT-4 Vision for invoice extraction
- Product categorization (SaaS, Services, Hardware, etc.)

### Excel File Processors

**File**: `analysis/excel_processors.py`

Contains two specialized processors:

1. **DenodoSalesTaxProcessor** - 109-column SAP extracts
2. **UseTaxProcessor** - 32-column research files

Both support:
- Auto-detection of file format
- Key field extraction
- Summary statistics
- Filtering for refund opportunities

### Database Tables

**Migration File**: `database/migrations/migration_003_analysis_tables.sql`

Key tables:
- `analysis_results` - AI analysis of each invoice line
- `analysis_reviews` - Human corrections and reviews
- `vendor_products` - Learning database of vendor products
- `vendor_product_patterns` - Pattern matching for recognition

---

## 3. Vendor Background Data Ingestion

### What Was Ingested

✅ **30 Vendors Total**
- 10 from `knowledge_base/vendors/vendor_database.json` (Microsoft, AWS, Salesforce, etc.)
- 20 from `outputs/Vendor_Background.xlsx` (Lucid, MongoDB, Citrix, etc.)

### Vendor Metadata Fields

Each vendor now has:
- `industry` - Industry classification
- `business_model` - B2B SaaS, Professional Services, etc.
- `primary_products` - Array of main products/services
- `typical_delivery` - Cloud-based, On-premise, etc.
- `tax_notes` - Common refund scenarios for this vendor type
- `confidence_score` - 0-100 (how reliable is this data)
- `data_source` - json, excel, ai_research, etc.

### How to Use

The refund analyzer can now query vendor metadata to:
- Predict likely tax treatment based on vendor
- Identify common refund scenarios
- Improve analysis confidence scores

### Ingestion Script

**File**: `scripts/ingest_vendor_background.py`

Usage:
```bash
python scripts/ingest_vendor_background.py
```

Results:
- ✅ 30 vendors ingested
- ✅ 0 errors
- All vendors stored in `knowledge_documents` table with `document_type='vendor_background'`

---

## 4. Excel Claim Sheet Structure

### Complete Specification

**Documentation**: `docs/CLAIM_SHEET_SPECIFICATION.md`

### Column Categories

#### 1. Identification Columns
- `Vendor_Number` - Unique vendor ID
- `Vendor_Name` - Vendor name
- `Invoice_Number` - Invoice number
- `PO_Number` - Purchase order number (optional)
- `Line_Item_Number` - Line item within invoice

#### 2. Financial Columns
- `Tax_Remitted` - Tax charged
- `Tax_Percentage_Charged` - Tax rate applied
- `Line_Item_Amount` - Pre-tax amount
- `Total_Amount` - Amount + tax

#### 3. Document File References
- `Invoice_Files` - PDF filename(s), comma-separated
- `PO_Files` - PO PDF filename(s), comma-separated

**Example**: `"0001.pdf"` or `"PO_49038_VENDOR.pdf, PO_49038_Amendment.pdf"`

#### 4. Analysis Output Columns (AUTO-POPULATED by AI)
- `Final_Decision` - "Add to Claim - Refund Sample" or specific tax category
- `Tax_Category` - See controlled vocabulary below
- `Additional_Info` - Subcategory/context
- `Refund_Basis` - Legal basis for refund
- `Estimated_Refund` - Dollar amount
- `Refund_Percentage` - Percent being refunded
- `Legal_Citation` - RCW/WAC references
- `AI_Confidence` - 0-100%
- `Analysis_Notes` - Detailed explanation
- `Review_Status` - Pending Review, Approved, Corrected, Rejected
- `Reviewed_By` - Human reviewer name
- `Review_Date` - Date of review

#### 5. Metadata Columns
- `Invoice_Date` - Date on invoice
- `Transaction_Date` - Transaction date
- `Cost_Center` - Business unit/location
- `GL_Account` - General ledger code
- `Product_Description` - Line item description

### Controlled Vocabularies

#### Tax Categories
For items >= $20,000:
- Custom Software
- DAS (Digitally Automated Service)
- DAS/License
- Digital Goods
- Hardware Support
- License
- Services
- Services/Tangible Goods
- Software Maintenance
- Software Support
- Tangible Goods

#### Additional Info Categories
- Advertising, Building Permit, Cleaning, Construction
- Credit Card Processing Fee, Data Processing
- Dining, Disposal, Food, Freight
- Help Desk, Hosting, Installation
- Internet Access, Janitorial, Landscaping
- Professional, Public Relations
- Software Development/Configuration
- Storage, Telecommunications, Testing
- Website Development, Website Hosting
- ...and more (see full spec)

#### Refund Basis Values
- `MPU` - Multiple Points of Use (multi-state, <10% WA)
- `Non-Taxable`
- `Non-Taxable - Services in Respect to Construction`
- `Out of State - Services`
- `Out of State - Shipment`
- `Partial Out-of-State Services`
- `Partial Out-of-State Shipment`
- `Resale`
- `Wrong Rate`

### Decision Rules

**Items < $20,000**: Final_Decision = `"Add to Claim - Refund Sample"`
- Auto-added without detailed categorization
- Still requires Legal Citation and Refund Basis

**Items >= $20,000**: Must specify exact Tax Category
- Requires detailed analysis
- Must have strong Legal Citation
- Requires AI_Confidence > 85%

---

## 5. Excel File Auto-Detection System

### System Components

#### File Watcher Class
**File**: `core/excel_file_watcher.py`

Key methods:
- `is_file_modified()` - Detects file-level changes via SHA256 hash
- `get_changed_rows()` - Detects row-level changes via MD5 hashes
- `process_excel_file()` - Main workflow
- `watch_directory()` - Monitor entire directory

#### Database Tracking Tables

**Schema File**: `database/schema/migration_excel_file_tracking.sql`

Tables:
1. **excel_file_tracking** - File-level metadata
   - `file_path`, `file_hash`, `last_modified`, `last_processed`
   - `row_count`, `processing_status`

2. **excel_row_tracking** - Row-level change detection
   - `file_path`, `row_index`, `row_hash`
   - `vendor_name`, `invoice_number`, `line_item_amount`
   - `processing_status`, `last_processed`

Helper functions:
- `get_unprocessed_rows(file_path)` - Get pending rows
- `mark_file_processed(file_path)` - Mark file complete
- `mark_row_processed(file_path, row_index)` - Mark row complete

Helper view:
- `v_excel_file_status` - Monitoring dashboard

### How It Works

1. **File Watch**: System monitors Excel file modification timestamp
2. **Hash Comparison**: Compares file hash to last known hash
3. **Row Detection**: If file changed, computes hash for each row
4. **Change Identification**: Compares row hashes to detect new/modified rows
5. **Incremental Processing**: Only processes changed rows
6. **Status Tracking**: Updates database with processing status

### Usage

```bash
# Process single file
python core/excel_file_watcher.py --file claim_sheets/Refund_Claim_Sheet_Test.xlsx

# Watch directory
python core/excel_file_watcher.py --watch claim_sheets/ --pattern "Refund_*.xlsx"
```

### Integration with Refund Analyzer

To integrate with your refund analysis:

```python
from core.excel_file_watcher import ExcelFileWatcher
from analysis.analyze_refunds import analyze_row

def process_row(row_index, row_data):
    """Process a single row with refund analyzer"""
    result = analyze_row(row_data)
    # Update Excel with results
    return result['success']

watcher = ExcelFileWatcher()
watcher.process_excel_file(
    "claim_sheets/Refund_Claim_Sheet.xlsx",
    processor_callback=process_row
)
```

### Deployment

To deploy the database schema:

**Option 1: Supabase Dashboard**
1. Go to SQL Editor in Supabase Dashboard
2. Paste contents of `database/schema/migration_excel_file_tracking.sql`
3. Click "Run"

**Option 2: Command Line** (requires psql)
```bash
chmod +x scripts/deploy_excel_tracking_schema.sh
./scripts/deploy_excel_tracking_schema.sh
```

---

## 6. Fictional Test Documents

### What Was Generated

✅ **12 Test Invoice/PO Pairs**
- 10 with refund opportunities
- 2 with no refund (properly taxed)

**Output Location**: `test_data/`
- `test_data/invoices/` - 12 PDFs (0001.pdf - 0012.pdf)
- `test_data/purchase_orders/` - 8 POs (PO_49001_MICROSOFT.pdf, etc.)
- `test_data/Refund_Claim_Sheet_Test.xlsx` - Master claim sheet

### Test Scenarios

#### Refund Opportunities

1. **Microsoft 365** ($9,000 @ 10.5% tax)
   - Category: DAS
   - Basis: MPU (multi-state usage)
   - Expected Refund: 100%

2. **Salesforce Sales Cloud** ($15,000)
   - Category: DAS
   - Basis: MPU
   - Expected Refund: 100%

3. **Dell Server** ($25,000)
   - Category: Tangible Goods
   - Basis: Out of State - Shipment (Oregon datacenter)
   - Expected Refund: 100%

4. **Deloitte Consulting** ($45,000)
   - Category: Services
   - Basis: Non-Taxable (professional services)
   - Expected Refund: 100%

5. **Adobe Creative Cloud** ($12,500)
   - Category: DAS
   - Basis: MPU
   - Expected Refund: 100%

6. **AWS EC2** ($8,500)
   - Category: DAS
   - Basis: Out of State - Services
   - Expected Refund: 100%

7. **Zoom Enterprise** ($18,000)
   - Category: DAS
   - Basis: MPU
   - Expected Refund: 100%

8-10. **Smaller Items** (< $20K)
   - Slack, Oracle, Workday
   - Auto "Add to Claim - Refund Sample"

#### No Refund Opportunities

11. **Staples Office Supplies** ($2,500)
    - Category: Tangible Goods
    - Basis: None
    - Expected Refund: 0% (properly taxed)

12. **Comcast Internet** ($850)
    - Category: Telecommunications
    - Basis: None
    - Expected Refund: 0% (properly taxed)

### Test Claim Sheet

**File**: `test_data/Refund_Claim_Sheet_Test.xlsx`

Contains all columns from specification:
- Identification columns (pre-filled)
- Financial columns (pre-filled)
- Document file references (pre-filled)
- Expected analysis results (for validation)
- Test notes explaining each scenario

### Generator Script

**File**: `scripts/generate_test_documents.py`

Usage:
```bash
python scripts/generate_test_documents.py
```

Features:
- Generates realistic invoice PDFs with line items
- Generates purchase order PDFs
- Creates master Excel claim sheet
- All documents dated pre-October 1, 2025 (old law period)

---

## Next Steps

### 1. Deploy Excel Tracking Schema

Choose one method:

**A. Supabase Dashboard** (Easiest)
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to SQL Editor
4. Open `database/schema/migration_excel_file_tracking.sql`
5. Copy/paste contents
6. Click "Run"

**B. Command Line** (If you have psql)
```bash
./scripts/deploy_excel_tracking_schema.sh
```

### 2. Test the System

```bash
# Test with fictional documents
python core/excel_file_watcher.py --file test_data/Refund_Claim_Sheet_Test.xlsx

# This will:
# - Detect all 12 rows as new
# - Track them in database
# - Show which rows need processing
```

### 3. Integrate with Refund Analyzer

Modify `analysis/analyze_refunds.py` to:
1. Accept Excel file as input
2. Use ExcelFileWatcher to detect changes
3. Process only new/modified rows
4. Update Excel with AI analysis results
5. Mark rows as processed in database

### 4. Build Complete Workflow

```python
# Pseudocode for complete workflow

from core.excel_file_watcher import ExcelFileWatcher
from analysis.analyze_refunds_enhanced import EnhancedRefundAnalyzer

def refund_workflow(claim_sheet_path):
    """Complete refund analysis workflow"""

    # Initialize
    watcher = ExcelFileWatcher()
    analyzer = EnhancedRefundAnalyzer()

    # Define row processor
    def process_row(row_index, row_data):
        # 1. Extract invoice PDF text
        invoice_text = extract_invoice(row_data['Invoice_Files'])

        # 2. Query vendor background (if available)
        vendor_metadata = get_vendor_metadata(row_data['Vendor_Name'])

        # 3. Query tax law knowledge base (OLD LAW only)
        tax_law_results = query_tax_law(
            invoice_text,
            law_version='old_law',
            transaction_date=row_data['Invoice_Date']
        )

        # 4. Analyze refund eligibility
        analysis = analyzer.analyze(
            invoice_text=invoice_text,
            vendor_metadata=vendor_metadata,
            tax_law_results=tax_law_results,
            amount=row_data['Line_Item_Amount'],
            tax_charged=row_data['Tax_Remitted']
        )

        # 5. Update Excel with results
        update_excel_row(
            file_path=claim_sheet_path,
            row_index=row_index,
            final_decision=analysis['final_decision'],
            tax_category=analysis['tax_category'],
            refund_basis=analysis['refund_basis'],
            estimated_refund=analysis['estimated_refund'],
            legal_citation=analysis['legal_citation'],
            ai_confidence=analysis['confidence'],
            analysis_notes=analysis['notes']
        )

        return True

    # Process file
    result = watcher.process_excel_file(
        claim_sheet_path,
        processor_callback=process_row
    )

    return result

# Run workflow
refund_workflow('claim_sheets/Refund_Claim_Sheet_Client.xlsx')
```

### 5. Set Up Monitoring

Create a cron job or file watcher daemon to automatically process changes:

```bash
# Check for Excel updates every hour
0 * * * * cd /path/to/refund-engine && python core/excel_file_watcher.py --watch claim_sheets/
```

---

## File Structure

```
/refund-engine/
├── analysis/
│   ├── analyze_refunds.py              # Standard refund analyzer
│   ├── analyze_refunds_enhanced.py     # Enhanced with advanced RAG
│   ├── fast_batch_analyzer.py          # Batch processor
│   ├── excel_processors.py             # Excel file parsing
│   ├── invoice_lookup.py               # Invoice extraction
│   └── invoice_pattern_learning.py     # Learning system
├── core/
│   ├── database.py                     # Supabase client
│   ├── enhanced_rag.py                 # Tax law knowledge base
│   ├── excel_file_watcher.py           # NEW - Auto-detection
│   └── law_version_handler.py          # Old law vs new law
├── database/
│   ├── migrations/
│   │   └── migration_003_analysis_tables.sql
│   └── schema/
│       ├── schema_knowledge_base.sql
│       ├── migration_vendor_metadata.sql
│       └── migration_excel_file_tracking.sql  # NEW
├── scripts/
│   ├── ingest_vendor_background.py     # NEW - Vendor ingestion
│   ├── generate_test_documents.py      # NEW - Test data generator
│   ├── deploy_excel_tracking_schema.sh # NEW - Deploy tracking
│   └── set_default_effective_dates.py  # Law version dates
├── docs/
│   └── CLAIM_SHEET_SPECIFICATION.md    # NEW - Complete spec
├── test_data/                          # NEW
│   ├── invoices/
│   │   ├── 0001.pdf
│   │   ├── 0002.pdf
│   │   └── ... (12 total)
│   ├── purchase_orders/
│   │   ├── PO_49001_MICROSOFT.pdf
│   │   └── ... (8 total)
│   └── Refund_Claim_Sheet_Test.xlsx
└── REFUND_ENGINE_SUMMARY.md            # NEW - This file
```

---

## Questions Answered

### Q1: "I think for my RAG system, we have this old law vs new law thing set up. I'm sure you can confirm that."

✅ **CONFIRMED**. The old law vs new law system is fully set up in:
- `core/law_version_handler.py` - Main handler
- `chatbot/rag_ui_with_feedback.py` - User interface
- Database: `effective_date` field tracks which law version applies
- ESSB 5814 effective date: October 1, 2025

### Q2: "For the invoice and purchase analysis (refund engine), I'm not sure which code that is. Maybe you can point me towards it once you find it."

✅ **FOUND**. Invoice/purchase analysis code is in:
- `analysis/analyze_refunds.py` - Main analyzer (lines 1-436)
- `analysis/fast_batch_analyzer.py` - Batch processing
- `analysis/excel_processors.py` - Excel file parsing
- `analysis/invoice_lookup.py` - Invoice extraction and matching

### Q3: "We're not going to be applying the new law to this refund engine because all the invoices and purchase orders we're going to be analyzing at least for the foreseeable future will be all prior to this new law change, which was October 1st, 2025."

✅ **CORRECT APPROACH**. For historical invoices (pre-Oct 1, 2025):
- Use OLD LAW only
- Determine if tax was improperly charged under old law
- If services like "IT Services" or "Custom Software" were taxed before Oct 1, 2025, that's a REFUND OPPORTUNITY (they weren't taxable under old law)

### Q4: "There's gonna be a claim sheet from Excel... with vendor number, invoice number, PO number, tax remitted, tax percentage charged, file name..."

✅ **DESIGNED**. Complete Excel structure documented in:
- `docs/CLAIM_SHEET_SPECIFICATION.md` - Full specification
- All required columns defined with data types
- Controlled vocabularies for Tax Category, Additional Info, Refund Basis
- Decision rules for items <$20K vs >=$20K

### Q5: "I want there to be some system set up where if I make updates to an Excel file, it's automatically detected in that master Excel file."

✅ **BUILT**. Auto-detection system created:
- `core/excel_file_watcher.py` - File watcher class
- `database/schema/migration_excel_file_tracking.sql` - Tracking schema
- File-level change detection (SHA256 hash)
- Row-level change detection (MD5 hash per row)
- Incremental processing (only new/modified rows)

### Q6: "I mentioned, so I'll be, for this whole refund engine, there's gonna be a... And I'm not sure, but I thought we had a vendor background data file. I know we haven't ingested that into Supabase, but I think I want to go ahead and do that."

✅ **INGESTED**. 30 vendors now in Supabase:
- 10 from `knowledge_base/vendors/vendor_database.json`
- 20 from `outputs/Vendor_Background.xlsx`
- All vendors have industry, business model, products, tax notes
- Script: `scripts/ingest_vendor_background.py`
- 0 errors, all successful

### Q7: "Let's create some fictional invoices and purchase orders. Let's do that."

✅ **CREATED**. 12 test scenarios generated:
- 12 invoice PDFs with realistic formatting
- 8 purchase order PDFs
- Master claim sheet with all required columns
- 10 refund opportunities + 2 properly taxed items
- Script: `scripts/generate_test_documents.py`
- Output: `test_data/` directory

---

## Summary

Your Refund Engine now has:
1. ✅ Clear understanding of old law vs new law (use OLD LAW for historical invoices)
2. ✅ Mapped invoice/purchase analysis code locations
3. ✅ 30 vendors with background metadata ingested
4. ✅ Complete Excel claim sheet specification with controlled vocabularies
5. ✅ Auto-detection system for Excel file updates (needs database deployment)
6. ✅ 12 fictional test documents for system validation

**Ready to deploy and test!**
