# Refund Engine - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Deploy Excel Tracking Schema (One-Time Setup)

**Option A: Supabase Dashboard** (Recommended)
```
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor"
4. Click "New Query"
5. Copy/paste: database/schema/migration_excel_file_tracking.sql
6. Click "Run"
```

**Option B: Command Line** (If you have psql installed)
```bash
./scripts/deploy_excel_tracking_schema.sh
```

### Step 2: Test with Fictional Data

```bash
# Test the Excel file watcher
python core/excel_file_watcher.py --file test_data/Refund_Claim_Sheet_Test.xlsx

# You should see:
# ✅ Changes detected
# ✅ 12 rows identified as new
# ✅ Processing complete
```

### Step 3: Verify Vendor Data

```bash
# Check that 30 vendors were ingested
python -c "from core.database import get_supabase_client; \
           s = get_supabase_client(); \
           r = s.table('knowledge_documents').select('vendor_name').eq('document_type', 'vendor_background').execute(); \
           print(f'Vendors: {len(r.data)}')"

# Should output: Vendors: 30
```

### Step 4: Review Generated Test Documents

Open these files to see what was created:
```bash
# View test invoices
open test_data/invoices/0001.pdf  # Microsoft invoice
open test_data/invoices/0003.pdf  # Dell server (shipped to Oregon)
open test_data/invoices/0004.pdf  # Deloitte consulting

# View test purchase orders
open test_data/purchase_orders/PO_49001_MICROSOFT.pdf

# View master claim sheet
open test_data/Refund_Claim_Sheet_Test.xlsx
```

---

## 📋 Key Files to Know

### Documentation
- `REFUND_ENGINE_SUMMARY.md` - Complete system overview (READ THIS FIRST)
- `docs/CLAIM_SHEET_SPECIFICATION.md` - Excel column specifications
- `QUICK_START_GUIDE.md` - This file

### Core Analysis Code
- `analysis/analyze_refunds.py` - Main refund analyzer
- `analysis/fast_batch_analyzer.py` - For large batches (10K+ rows)
- `core/excel_file_watcher.py` - Auto-detect Excel changes

### Data Management
- `scripts/ingest_vendor_background.py` - Ingest vendor metadata
- `scripts/generate_test_documents.py` - Create test data
- `core/law_version_handler.py` - Old law vs new law

### Database Schemas
- `database/schema/migration_excel_file_tracking.sql` - Excel tracking
- `database/schema/migration_vendor_metadata.sql` - Vendor metadata
- `database/migrations/migration_003_analysis_tables.sql` - Analysis results

---

## 🎯 Common Tasks

### Task: Process a New Claim Sheet

```bash
# 1. Place Excel file in claim_sheets/
cp /path/to/client_claim_sheet.xlsx claim_sheets/

# 2. Run file watcher to detect rows
python core/excel_file_watcher.py --file claim_sheets/client_claim_sheet.xlsx

# 3. Integrate with refund analyzer (TODO: you'll build this)
# python analysis/analyze_refunds.py --file claim_sheets/client_claim_sheet.xlsx
```

### Task: Add New Vendors

```bash
# 1. Add vendors to Excel or JSON file
# 2. Run ingestion script
python scripts/ingest_vendor_background.py
```

### Task: Check Processing Status

```python
from core.database import get_supabase_client

supabase = get_supabase_client()

# View file processing status
result = supabase.table("v_excel_file_status").select("*").execute()
print(result.data)

# View unprocessed rows
result = supabase.rpc("get_unprocessed_rows", {
    "file_path_param": "claim_sheets/client_claim_sheet.xlsx"
}).execute()
print(f"Unprocessed rows: {len(result.data)}")
```

### Task: Generate More Test Data

```bash
# Edit test scenarios in scripts/generate_test_documents.py
# Then regenerate
python scripts/generate_test_documents.py
```

---

## ⚠️ Important Rules

### 1. Law Version Selection
- **Historical invoices (pre-Oct 1, 2025)**: Use OLD LAW ONLY
- **New invoices (Oct 1, 2025+)**: Use NEW LAW
- Why? Tax treatment changed on October 1, 2025 for 8 service categories

### 2. Decision Rules
- **Items < $20,000**: `Final_Decision = "Add to Claim - Refund Sample"`
- **Items >= $20,000**: Must specify exact `Tax_Category`

### 3. File Naming
- Invoices: Simple numbers (e.g., `0001.pdf`, `0002.pdf`)
- POs: Format `PO_[number]_[VENDOR].pdf` (e.g., `PO_49038_MICROSOFT.pdf`)
- Multiple files: Comma-separated in Excel cell

### 4. Tax Categories (Controlled Vocabulary)
Only use these values:
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

### 5. Refund Basis (Controlled Vocabulary)
- MPU (Multiple Points of Use)
- Non-Taxable
- Out of State - Services
- Out of State - Shipment
- Partial Out-of-State Services
- Partial Out-of-State Shipment
- Resale
- Wrong Rate

---

## 🔍 Troubleshooting

### Problem: Excel file watcher shows no changes

**Solution**: Check if file was already processed
```python
from core.excel_file_watcher import ExcelFileWatcher

watcher = ExcelFileWatcher()
is_modified, previous = watcher.is_file_modified("path/to/file.xlsx")

if not is_modified:
    print(f"Last processed: {previous['last_processed']}")
    print("No changes since then")
```

### Problem: Vendor not found in database

**Solution**: Add vendor to background file and re-ingest
```bash
# 1. Add vendor to outputs/Vendor_Background.xlsx
# 2. Re-run ingestion
python scripts/ingest_vendor_background.py
```

### Problem: Database tables don't exist

**Solution**: Deploy the schema
```bash
# Use Supabase Dashboard SQL Editor to run:
# database/schema/migration_excel_file_tracking.sql
```

### Problem: PDF files not found

**Solution**: Check file paths and names
```bash
# Files should be in:
# test_data/invoices/0001.pdf
# test_data/purchase_orders/PO_49001_MICROSOFT.pdf

# Verify:
ls test_data/invoices/
ls test_data/purchase_orders/
```

---

## 📊 Testing Checklist

- [ ] Excel tracking schema deployed (check Supabase Dashboard)
- [ ] 30 vendors in database (run verification query)
- [ ] 12 test invoices generated (check test_data/invoices/)
- [ ] 8 test POs generated (check test_data/purchase_orders/)
- [ ] Test claim sheet exists (test_data/Refund_Claim_Sheet_Test.xlsx)
- [ ] File watcher detects 12 new rows (run test command)
- [ ] Old law vs new law understood (read REFUND_ENGINE_SUMMARY.md)

---

## 🎓 Next Steps (Your Integration Tasks)

### 1. Build Complete Workflow Script

Create `analysis/refund_workflow.py`:
```python
from core.excel_file_watcher import ExcelFileWatcher
from analysis.analyze_refunds import analyze_row

def process_claim_sheet(file_path):
    watcher = ExcelFileWatcher()

    def process_row(row_index, row_data):
        # Your logic here:
        # 1. Extract invoice PDF
        # 2. Query tax law (OLD LAW)
        # 3. Determine refund eligibility
        # 4. Update Excel with results
        return True

    return watcher.process_excel_file(file_path, process_row)
```

### 2. Connect to Invoice Extraction

Integrate `analysis/invoice_lookup.py` to:
- Match invoice files to Excel rows
- Extract line item text from PDFs
- Match purchase orders

### 3. Connect to Tax Law RAG

Use `core/enhanced_rag.py` to:
- Query knowledge base with OLD LAW filter
- Get relevant RCW/WAC citations
- Determine exemptions and refund basis

### 4. Connect to Vendor Metadata

Query vendor background to:
- Predict likely tax treatment
- Identify common refund scenarios
- Improve confidence scores

### 5. Update Excel with Results

Write AI analysis back to claim sheet:
- Final_Decision
- Tax_Category
- Refund_Basis
- Estimated_Refund
- Legal_Citation
- AI_Confidence
- Analysis_Notes

### 6. Set Up Continuous Monitoring

```bash
# Create cron job to check for Excel updates
# Add to crontab -e:
0 * * * * cd /path/to/refund-engine && python core/excel_file_watcher.py --watch claim_sheets/
```

---

## 📞 Support

- Full system overview: `REFUND_ENGINE_SUMMARY.md`
- Excel specification: `docs/CLAIM_SHEET_SPECIFICATION.md`
- Code documentation: Inline comments in Python files
- Database schema: `database/schema/*.sql` files

---

**You're all set! Start with the Testing Checklist above, then move to integration tasks.**
