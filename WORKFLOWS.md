# Workflows Guide: Day-to-Day Usage

How to actually USE the refund engine.

---

## Table of Contents

1. [Analysis Workflow](#analysis-workflow) - Process invoices
2. [Review & Corrections](#review--corrections) - Improve accuracy
3. [Knowledge Base Management](#knowledge-base-management) - Add tax law docs
4. [Excel Versioning](#excel-versioning) - Track changes
5. [Dashboard Usage](#dashboard-usage) - Web UI
6. [Common Scenarios](#common-scenarios) - Real examples

---

## Analysis Workflow

### The Main Command

```bash
python analysis/fast_batch_analyzer.py \
    --excel "Master_Refunds.xlsx" \
    --state washington
```

**What It Does**:
1. Checks which rows changed (skips already-analyzed)
2. Extracts line items from new invoices (GPT-4 Vision)
3. Searches WA tax law (Enhanced RAG)
4. Analyzes items in batches (GPT-4o)
5. Writes results to Excel
6. Updates tracking database

---

### Step-by-Step: First Analysis

#### 1. Prepare Your Excel File

**Required Columns** (you fill):
| Column | Description | Example |
|--------|-------------|---------|
| Vendor_Name | Vendor name | Microsoft Corporation |
| Invoice_Number | Invoice ID | INV-2024-001 |
| Total_Amount | Total invoice | 10000.00 |
| Tax_Amount | Tax paid | 1050.00 |
| Invoice_File_Name_1 | Vendor invoice PDF | microsoft_jan.pdf |
| Invoice_File_Name_2 | Internal invoice (optional) | microsoft_jan_internal.pdf |

**Optional Columns**:
- Purchase_Order_Number
- Tax_Rate_Charged (as %)
- Line_Item_Description

#### 2. Add Invoice PDFs

```bash
# Put your PDFs here
cp ~/Downloads/*.pdf client_documents/invoices/
```

**File Naming**: Match Excel `Invoice_File_Name_1` column exactly
- Excel says: `microsoft_jan.pdf`
- File must be: `client_documents/invoices/microsoft_jan.pdf`

#### 3. Run Analyzer

```bash
python analysis/fast_batch_analyzer.py \
    --excel "Master_Refunds.xlsx" \
    --state washington
```

**Progress Output**:
```
🚀 FAST BATCH REFUND ANALYZER
=====================================================================
Excel: Master_Refunds.xlsx
State: WASHINGTON
=====================================================================

📂 Loading Excel...
✓ Analyzing 250 rows

🔍 Checking for changes...
✓ Found 250 changed/new rows out of 250 total

📄 Extracting invoices...
Extracting: 100%|███████████████| 45/45 [01:15<00:00]

🔍 Matching line items...
✓ Matched 220/250 rows (88%)
⚠️  Skipped 30 rows (no invoice file or match failed)

🤖 AI Analysis (Batch Processing)...
Batch 1/11: 100%|████████████████| 11/11 [02:30<00:00]

✅ Analysis complete!
Output: Master_Refunds_analyzed.xlsx
```

**Time**: ~5-10 minutes for 250 rows (first run)

#### 4. Check Results

Open `Master_Refunds_analyzed.xlsx`:

**New Columns Added** (AI filled):
- **Analysis_Notes** - Summary of findings
- **Final_Decision** - Add to Claim / No Refund / Needs Review
- **Tax_Category** - DAS, Services, Hardware, etc.
- **Refund_Basis** - MPU, Non-Taxable, Exemption, etc.
- **Estimated_Refund** - Dollar amount
- **Legal_Citation** - WAC 458-20-15502, etc.
- **AI_Confidence** - 0-100%

---

### Step-by-Step: Subsequent Analyses (Changed Rows Only)

#### Scenario: You Add 50 New Invoices

**Before**:
- Excel has 250 rows (already analyzed)
- You add 50 new rows (rows 251-300)

**Run Same Command**:
```bash
python analysis/fast_batch_analyzer.py \
    --excel "Master_Refunds.xlsx" \
    --state washington
```

**What Happens**:
```
📂 Loading Excel...
✓ 300 total rows

🔍 Checking for changes...
✓ Found 50 changed/new rows out of 300 total
  Skipping 250 already-analyzed rows

📄 Extracting invoices...
Extracting: 100%|████| 10/10 [00:15<00:00]  # Only 10 new invoices

🤖 AI Analysis...
Batch 1/3: 100%|████| 3/3 [00:35<00:00]    # Only 3 batches

✅ Analysis complete!
```

**Time**: ~2 minutes (vs 10 minutes for full re-analysis)

**Why Faster**:
- Skipped 250 rows (row hash unchanged)
- 40 invoices already cached (from before)
- RAG searches cached

---

### Understanding Change Detection

#### INPUT Column Changes → Re-analyze Row
```
You change: Invoice_File_Name_2 from blank → "invoice_internal.pdf"
System: "New data available, re-analyzing row"
```

#### OUTPUT Column Changes → Skip Re-analysis
```
You change: Tax_Category from "DAS" → "Services"
System: "Just feedback, skipping re-analysis"
```

**How to Force Re-analysis** (for testing):
```bash
python analysis/fast_batch_analyzer.py \
    --excel "Master_Refunds.xlsx" \
    --state washington \
    --limit 10  # Force first 10 rows
```

---

## Review & Corrections

### Why Review?

**AI Accuracy**:
- Out of box: ~70-75%
- After corrections: ~85-95%

**Focus Areas**:
1. High confidence (>80%) - Likely correct, quick review
2. Medium confidence (60-80%) - Verify assumptions
3. Low confidence (<60%) - Manual research needed

---

### Review Workflow

#### 1. Filter by Confidence

**Excel**:
1. Open analyzed file
2. Sort by `AI_Confidence` (high to low)
3. Start with >80% (quick wins)

**Dashboard** (easier):
```bash
streamlit run dashboard/Home.py
```
Navigate to "Review Queue" → Filter by confidence

#### 2. Review Each Row

**Check**:
- ✅ Product categorization correct? (DAS vs Services)
- ✅ Refund basis makes sense? (MPU vs Non-Taxable)
- ✅ Estimated refund reasonable? (Not >100% of tax)
- ✅ Legal citation accurate?

**Common Mistakes AI Makes**:
- Categorizes consulting as SaaS (should be Services)
- Applies MPU when product is single-location
- Misreads line item description
- Cites wrong WAC section

#### 3. Make Corrections (In Excel)

**If AI is wrong**:
1. Change `Tax_Category` to correct value
2. Change `Refund_Basis` if needed
3. Update `Estimated_Refund`
4. Add note in `Corrected_Notes` column explaining WHY

**Example**:
```
Row 45:
AI Said: Tax_Category = "DAS" (Digital Automated Services)
You Change: Tax_Category = "Services" (Professional Services)
Corrected_Notes: "This is consulting, not software - requires human expertise"
```

#### 4. Import Corrections

```bash
python analysis/import_corrections.py "Master_Refunds_analyzed.xlsx"
```

**What This Does**:
1. Reads your corrections
2. Stores in `analysis_reviews` table
3. Updates `vendor_products` table (system learns!)
4. Updates `keyword_patterns` table

**Output**:
```
📥 Importing Corrections from Excel
=====================================================================

📊 Found 15 corrections

Analyzing patterns...
  ✓ Microsoft → Office 365 → DAS (confidence: 95%)
  ✓ Deloitte → Consulting → Services (confidence: 100%)
  ✓ Salesforce → Sales Cloud → DAS (confidence: 90%)

💾 Storing to database...
  ✓ 15 reviews stored
  ✓ 3 vendor patterns updated
  ✓ 12 keyword patterns added

🎓 System Learning Summary:
  - 3 new vendor-product mappings
  - 12 new product keywords learned
  - Next analysis will be more accurate!
```

---

### Learning System Explained

**Before Corrections**:
```
Row: Vendor = "Microsoft", Description = "Office 365"
AI: (searches RAG, unsure) → "DAS" (70% confidence)
```

**After You Correct**:
```
System stores: Microsoft → Office 365 → DAS (confirmed)
```

**Next Time**:
```
Row: Vendor = "Microsoft", Description = "Office 365 E5"
AI: (checks vendor_products table) → "DAS" (95% confidence)
```

**Impact**: Accuracy improves from 70% → 95% for similar items

---

## Knowledge Base Management

### When to Add Documents

**Add Tax Law Docs When**:
- Low confidence scores on specific categories
- New tax law published (e.g., ESSB 5814 in Oct 2025)
- Expanding to new product types

**Add Vendor Docs When**:
- Analyzing new vendor for first time
- Need context about vendor's products
- Vendor has complex product catalog

---

### Add Tax Law Documents

#### 1. Get PDFs

**Sources**:
- WA Legislature: https://leg.wa.gov/
- DOR Website: https://dor.wa.gov/
- Tax Ruling Database (WTD)

**Essential Docs**:
- RCW 82.04 (B&O Tax)
- RCW 82.08 (Retail Sales Tax)
- RCW 82.12 (Use Tax)
- WAC 458-20-15502 (MPU Rule)
- ESSB 5814 (2025 New Law)

#### 2. Place in Folder

```bash
cp ~/Downloads/WAC_458-20-15502.pdf \
   knowledge_base/states/washington/legal_documents/
```

#### 3. Ingest

```bash
python scripts/knowledge_base/ingest_legal_docs.py \
    --folder knowledge_base/states/washington/legal_documents/
```

**What It Does**:
- Chunks PDF (1000 chars/chunk, 200 char overlap)
- Generates embeddings (text-embedding-3-small)
- Stores in `tax_law_chunks` table
- ~30 seconds per document

**Output**:
```
📚 Ingesting Legal Documents
=====================================================================

Found 5 new PDFs

Processing: WAC_458-20-15502.pdf
  ✓ Extracted 45 pages
  ✓ Created 67 chunks
  ✓ Generated embeddings
  ✓ Stored in database

...

✅ Ingestion Complete!
  Total: 5 documents
  Chunks: 342
  Time: 2m 15s
```

---

### Add Vendor Background Documents

**Purpose**: Help AI understand vendor context

**Example**:
```
Vendor: Salesforce
Background Doc: Salesforce_Product_Catalog.pdf
Helps AI: Understand Sales Cloud vs Service Cloud vs Marketing Cloud
```

#### Steps:

```bash
# 1. Add PDF
cp ~/Downloads/Salesforce_Catalog.pdf knowledge_base/vendors/

# 2. Ingest
python scripts/knowledge_base/ingest_vendor_docs.py \
    --folder knowledge_base/vendors/
```

---

### Sync Knowledge Base Across Machines

**Problem**: You have 3 computers, don't want to re-ingest 50 PDFs on each

**Solution**: Upload/Download from Supabase Storage

#### Upload (Machine 1):
```bash
python scripts/knowledge_base/upload_to_storage.py
```

#### Download (Machine 2):
```bash
python scripts/knowledge_base/download_from_storage.py
```

**Benefits**:
- Saves 15+ minutes of ingestion time
- Saves OpenAI API costs (~$5 for embeddings)
- Consistent knowledge base across machines

---

## Excel Versioning

### Why Version Control?

**Problems Solved**:
- "Which version is latest?"
- "What changed since yesterday?"
- "Can I undo that mistake?"

**Solution**: Automatic versioning with cell-level change tracking

---

### Upload File to Versioning System

```python
from core.excel_versioning import ExcelVersionManager

manager = ExcelVersionManager()

# Upload new file
file_id = manager.upload_file(
    file_path="Master_Refunds.xlsx",
    project_id="<uuid>",  # From projects table
    user_email="analyst@company.com"
)
```

**What Happens**:
- Uploads to Supabase Storage
- Creates record in `excel_file_tracking`
- Creates version 1 in `excel_file_versions`
- Calculates file hash

---

### Create New Version (After Changes)

```python
# You made changes to Excel locally
# Now create version 2

version_id = manager.create_version(
    file_id=file_id,
    file_path="Master_Refunds_updated.xlsx",
    user_email="analyst@company.com",
    change_summary="Corrected 45 tax categories"
)
```

**What Happens**:
- Compares with version 1 (cell by cell)
- Stores changes in `excel_cell_changes` table
- Creates version 2 in `excel_file_versions`
- Updates `current_version` to 2

**Auto-Saves**: Last 10 versions automatically
**Snapshots**: Create permanent save points manually

---

### View Changes Between Versions

```python
# Compare version 1 vs 2
diff = manager.get_version_diff(file_id, version_1=1, version_2=2)

print(f"Rows added: {diff['rows_added']}")
print(f"Rows modified: {diff['rows_modified']}")
print(f"Cells changed: {len(diff['cells_changed'])}")

# See specific changes
for change in diff['cells_changed']:
    print(f"Row {change['row_index']}, Column {change['column']}")
    print(f"  Old: {change['old_value']}")
    print(f"  New: {change['new_value']}")
```

**Output**:
```
Row 23, Column Tax_Category
  Old: DAS
  New: Services

Row 45, Column Estimated_Refund
  Old: 5000
  New: 8500
```

---

### Create Manual Snapshot

**When**: Important milestones
- "First 2,500 rows complete"
- "Ready for partner review"
- "Final - ready for filing"

**How**: (via dashboard or directly)
```python
manager.create_snapshot(
    file_id=file_id,
    snapshot_name="Final - Ready for Filing",
    user_email="analyst@company.com"
)
```

**Benefit**: Snapshot never auto-deleted (permanent)

---

## Dashboard Usage

### Start Dashboard

```bash
streamlit run dashboard/Home.py
```

Open browser: http://localhost:8501

---

### Dashboard Pages

#### 1. Home
- System overview
- Quick stats (total refunds, top vendors)
- Recent activity

#### 2. Projects
- Create new project ("WA Sales Tax 2024")
- View all projects
- See files per project
- Processing status

#### 3. Documents
- Browse knowledge base (tax law, vendor docs)
- Search documents
- View document details
- Upload new documents

#### 4. Review Queue
- **Filter** by confidence (>80%, 60-80%, <60%)
- **Filter** by decision (Add to Claim, Needs Review)
- **Sort** by refund amount (high to low)
- **Approve/Reject** items
- **Add notes** for team

#### 5. Claims
- Generate refund claim summary
- Group by refund basis (MPU, Non-Taxable, etc.)
- Export to PDF
- Legal citations included

#### 6. Analytics
- **Refund Trends**: By month, by vendor, by category
- **Vendor Patterns**: Most common refund bases per vendor
- **AI Performance**: Accuracy over time
- **Keyword Patterns**: What keywords correlate with refunds

#### 7. Excel Manager
- **Upload** files
- **View** version history
- **Compare** versions (GitHub-style diff)
- **Download** any version
- **Restore** previous version

---

### Review Queue Workflow

**Dashboard Steps**:
1. Go to "Review Queue" page
2. Filter: Confidence > 80%
3. Sort: Estimated_Refund (high to low)
4. Review top 20 items
5. Approve correct ones (click ✓)
6. Flag incorrect ones (click ✗)
7. Add notes for flagged items
8. Export corrections to Excel
9. Import: `python analysis/import_corrections.py`

---

## Common Scenarios

### Scenario 1: Monthly Invoice Processing

**Timeline**: 1st of each month

**Steps**:
1. Get invoice data from accounting system
2. Export to Excel (vendor, invoice #, amounts)
3. Download invoice PDFs to `client_documents/invoices/`
4. Run analyzer:
```bash
python analysis/fast_batch_analyzer.py --excel "Invoices_March_2024.xlsx" --state washington
```
5. Review in dashboard (focus on >80% confidence)
6. Correct mistakes
7. Import corrections
8. Generate claim summary (dashboard → Claims)

**Time**: ~30 minutes for 300 invoices

---

### Scenario 2: Backlog Processing (1,000+ Invoices)

**Strategy**: Process in batches

**Steps**:
1. Split into 5 files (200 invoices each)
2. Process File 1:
```bash
python analysis/fast_batch_analyzer.py --excel "Batch_1.xlsx" --state washington
```
3. Review & correct Batch 1
4. Import corrections:
```bash
python analysis/import_corrections.py "Batch_1_analyzed.xlsx"
```
5. Process File 2 (system now smarter from Batch 1 corrections)
6. Repeat for Files 3-5

**Time**: ~4-5 hours total (including review)

**Why Batches**: System learns from early corrections, improves accuracy on later batches

---

### Scenario 3: Quarterly Review with Partner

**Timeline**: End of quarter

**Steps**:
1. Create snapshot in dashboard: "Q1 2024 - Pre-Partner Review"
2. Export claim summary (dashboard → Claims → PDF)
3. Send to partner for review
4. Partner sends back comments
5. Make corrections in Excel
6. Re-upload (creates new version)
7. Create snapshot: "Q1 2024 - Post-Partner Review"
8. Export final claim summary
9. Submit to Department of Revenue

**Versioning Benefit**: Can compare pre/post partner review to see exactly what changed

---

### Scenario 4: New Tax Law (ESSB 5814)

**When**: October 1, 2025 (new law effective)

**Steps**:
1. Download new law PDF
2. Place in `knowledge_base/states/washington/legal_documents/ESSB_5814.pdf`
3. Ingest:
```bash
python scripts/knowledge_base/ingest_legal_docs.py --folder knowledge_base/states/washington/legal_documents/
```
4. Create new project: "WA Sales Tax 2025 (NEW LAW)"
5. Process 2025 invoices under new project
6. System automatically uses new law for RAG searches

**Benefit**: 2024 claims use old law, 2025 claims use new law (separate projects)

---

### Scenario 5: Adding Purchase Order File (New Data)

**Before**:
```
Row 45: Invoice_File_Name_1 = "invoice.pdf"
        Purchase_Order_File_Name = (blank)
        Estimated_Refund = $5,000 (based on invoice only)
```

**After You Get PO**:
1. Add PO PDF to `client_documents/invoices/PO-5001.pdf`
2. Update Excel: `Purchase_Order_File_Name = "PO-5001.pdf"`
3. Re-upload Excel
4. Run analyzer again:
```bash
python analysis/fast_batch_analyzer.py --excel "Master_Refunds.xlsx" --state washington
```

**What Happens**:
- System detects INPUT column change (Purchase_Order_File_Name)
- Re-analyzes row 45 with new PO data
- New estimate: $8,500 (PO shows multi-state usage!)

**Key Point**: INPUT column changes trigger re-analysis, OUTPUT changes don't

---

## Best Practices

### 1. Review High-Confidence First
- >80%: Quick review (5-10 min for 100 items)
- 60-80%: Verify assumptions (20-30 min)
- <60%: Deep research (1-2 hours)

### 2. Provide Detailed Correction Notes
**Bad**: "Wrong"
**Good**: "This is consulting (human expertise), not SaaS - cite RCW 82.04.050(6)"

**Why**: System learns better from detailed explanations

### 3. Create Snapshots at Milestones
- "First 1,000 rows complete"
- "Pre-partner review"
- "Post-partner review"
- "Final submitted to DOR"

### 4. Batch Process Large Files
- Don't try to analyze 10,000 rows at once
- Split into 500-row batches
- System learns from early batches, improves on later ones

### 5. Update Knowledge Base Regularly
- Add new WTD rulings as published
- Add new WAC sections when updated
- Add vendor docs for new vendors

---

## Quick Reference Commands

```bash
# Main analysis
python analysis/fast_batch_analyzer.py --excel FILE.xlsx --state washington

# Test mode (first 10 rows)
python analysis/fast_batch_analyzer.py --excel FILE.xlsx --state washington --limit 10

# Import corrections
python analysis/import_corrections.py FILE_analyzed.xlsx

# Ingest tax law
python scripts/knowledge_base/ingest_legal_docs.py --folder knowledge_base/states/washington/legal_documents/

# Ingest vendor docs
python scripts/knowledge_base/ingest_vendor_docs.py --folder knowledge_base/vendors/

# Start dashboard
streamlit run dashboard/Home.py

# Verify setup
python scripts/utils/verify_schema.py
```

---

**Last Updated**: 2025-11-23
**Version**: v2.0
