# Project Overview: Washington State Tax Refund Engine

**THE** comprehensive guide to understanding this system.

---

## What Is This?

An AI-powered system that **analyzes invoices to identify Washington State sales/use tax refund opportunities**. It combines:
- **GPT-4 Vision** for invoice extraction
- **Enhanced RAG** (Retrieval-Augmented Generation) for legal research
- **Human-in-the-loop learning** to improve accuracy over time
- **Excel versioning** with intelligent change tracking

**Target Users**: Tax consultants, businesses with significant WA tax liability

---

## Core Concepts

### 1. Multi-Point Use (MPU)
Washington State tax law: Digital services are taxed based on **where they're used**, not where the company is located.

**Example**:
- 100 Microsoft 365 licenses, $10,000/month, $1,050 tax paid
- 85 employees work outside Washington
- **Refund**: 85% × $1,050 = **$892.50/month**
- **Legal Basis**: WAC 458-20-15502

### 2. Enhanced RAG (Legal Research)
Searches Washington tax law (RCW/WAC documents) using:
- **Vector embeddings** - semantic similarity search
- **AI reranking** - reorders results for relevance
- **Corrective RAG** - verifies answers against source documents

**Process**:
```
User Query → Generate Embedding → Search pgvector → Rerank Results → Extract Citations
```

### 3. Vendor Learning System
Learns from your corrections to build **product patterns**:
- "Microsoft → Office 365 → DAS (Digital Automated Services)"
- "Deloitte → Consulting → Services (Non-taxable)"
- Stored in `vendor_products` table
- Applied automatically on future analyses

### 4. Excel Versioning
Tracks **which rows changed** to avoid re-analyzing entire files:
- **File hash** - detects if Excel changed
- **Row hash** - identifies which specific rows changed
- **Cell-level tracking** - shows what changed (column, old→new value)
- **INPUT vs OUTPUT columns** - only re-analyze when INPUT data changes

---

## System Architecture

### Data Flow
```
┌──────────────┐
│ Excel Upload │ (Vendor, Invoice #, Tax Amount, PDF files)
└──────┬───────┘
       │
       ▼
┌────────────────────┐
│ Change Detection   │ (ExcelFileWatcher - only process changed rows)
└────────┬───────────┘
         │
         ▼
┌─────────────────────┐
│ Invoice Extraction  │ (GPT-4 Vision - extract line items from PDFs)
└─────────┬───────────┘
          │ (Cached 30 days)
          ▼
┌──────────────────────┐
│ Vendor Lookup        │ (Check vendor_products table for known patterns)
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────┐
│ Enhanced RAG Search     │ (Search WA tax law using pgvector embeddings)
└─────────┬───────────────┘
          │ (Cached 7 days)
          ▼
┌──────────────────────────┐
│ AI Batch Analysis        │ (GPT-4o analyzes 20 items/call)
└──────────┬───────────────┘
           │
           ▼
┌────────────────────────┐
│ Excel Results Output   │ (Analysis, refund estimate, citations)
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Human Review           │ (Approve/correct in Excel)
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Import Corrections     │ (System learns vendor patterns)
└────────────────────────┘
```

### Tech Stack
- **AI Models**:
  - GPT-4o (analysis)
  - GPT-4 Vision (invoice extraction)
  - text-embedding-3-small (RAG embeddings)
- **Database**: Supabase (PostgreSQL + pgvector)
- **Caching**: SmartCache (30-day invoice cache, 7-day RAG cache)
- **UIs**:
  - Dashboard (Streamlit) - Workflow management
  - Chatbot (Streamlit) - Legal Q&A
- **Language**: Python 3.8+

---

## Project Structure

```
refund-engine/
├── analysis/                     # Core analysis modules
│   ├── fast_batch_analyzer.py   # MAIN ANALYZER (start here)
│   ├── excel_processors.py      # Parse Excel files
│   ├── invoice_lookup.py        # Extract from PDFs
│   ├── import_corrections.py    # Learn from corrections
│   └── matchers.py              # Vendor/keyword matching
│
├── core/                         # Shared infrastructure
│   ├── database.py              # Supabase client (singleton)
│   ├── enhanced_rag.py          # Legal research engine
│   ├── excel_versioning.py      # File upload & version tracking
│   ├── excel_file_watcher.py    # Row-level change detection
│   └── excel_column_definitions.py  # INPUT vs OUTPUT columns
│
├── database/                     # Schema & migrations
│   └── schema/
│       ├── schema_knowledge_base.sql      # Tax law & vendor docs
│       ├── migration_excel_versioning.sql # Excel tracking
│       ├── migration_projects.sql         # Multi-project support
│       └── schema_vendor_learning.sql     # Vendor patterns
│
├── scripts/                      # Utility scripts
│   ├── knowledge_base/          # Ingest tax law PDFs
│   ├── data_management/         # Excel utilities
│   └── utils/                   # Smart cache, verification
│
├── dashboard/                    # Streamlit UI (Workflow Management)
│   ├── Dashboard.py             # Main dashboard
│   └── pages/                   # Projects, Documents, Review Queue, Claims, Analytics
│
├── chatbot/                      # Streamlit UI (Legal Q&A)
│   ├── rag_ui_with_feedback.py  # Chat interface
│   └── feedback_analytics.py    # Feedback analytics
│
├── knowledge_base/              # Source documents
│   ├── states/washington/       # WA tax law PDFs
│   └── vendors/                 # Vendor background docs
│
└── client_documents/            # Your data
    └── invoices/                # Invoice PDFs go here
```

---

## Database Schema Overview

### Knowledge Base Tables
**Purpose**: Store and search tax law + vendor documentation

| Table | Purpose | Size |
|-------|---------|------|
| `knowledge_documents` | Master doc registry | ~50 docs |
| `tax_law_chunks` | WA tax law (chunked for RAG) | ~3,000 chunks |
| `vendor_background_chunks` | Vendor info (for context) | ~500 chunks |

**RPC Functions**:
- `search_tax_law(query_embedding, threshold, count)` → Similar law chunks
- `search_vendor_background(query_embedding, threshold, count)` → Vendor context

### Vendor Learning Tables
**Purpose**: Learn patterns from your corrections

| Table | Purpose | Example Data |
|-------|---------|--------------|
| `vendor_products` | Vendor → Product mappings | "Microsoft → Office 365 → DAS" |
| `refund_citations` | Refund basis → Legal citations | "MPU → WAC 458-20-15502" |
| `keyword_patterns` | Product keywords by category | "SaaS: ['cloud', 'subscription']" |

### Excel Versioning Tables
**Purpose**: Track file changes & versions

| Table | Purpose |
|-------|---------|
| `projects` | Organize by tax type/year |
| `excel_file_tracking` | File metadata & current version |
| `excel_file_versions` | Version history (last 10 auto-saved) |
| `excel_cell_changes` | Cell-level change tracking |

### Analysis Results Tables
**Purpose**: Store AI analysis & human review

| Table | Purpose |
|-------|---------|
| `analysis_results` | AI analysis output |
| `analysis_reviews` | Human corrections |
| `analysis_feedback` | Learning data |

---

## Main Workflows

### 1. Analysis Workflow (Day-to-Day)

**Command**:
```bash
python analysis/fast_batch_analyzer.py \
    --excel "Master_Refunds.xlsx" \
    --state washington
```

**What Happens**:
1. Loads Excel, checks which rows changed (via file/row hashes)
2. Skips already-analyzed rows
3. Extracts line items from new invoice PDFs (GPT-4 Vision)
4. Searches WA tax law (Enhanced RAG)
5. Analyzes 20 items/batch (GPT-4o)
6. Writes results to Excel (Product_Type, Refund_Basis, Estimated_Refund, etc.)
7. Updates tracking DB (marks rows as processed)

**Input Columns** (you provide):
- Vendor_Name
- Invoice_Number
- Tax_Amount
- Invoice_File_Name_1
- Invoice_File_Name_2 (optional)

**Output Columns** (AI fills):
- Analysis_Notes
- Final_Decision
- Tax_Category
- Refund_Basis
- Estimated_Refund
- Legal_Citation
- AI_Confidence

### 2. Review & Corrections Workflow

**Steps**:
1. Open analyzed Excel file
2. Review AI analysis (focus on high confidence >80% first)
3. Correct mistakes (change Tax_Category, Estimated_Refund, etc.)
4. Import corrections:
```bash
python analysis/import_corrections.py "Master_Refunds.xlsx"
```
5. System learns vendor patterns (stored in `vendor_products`)
6. Future analyses benefit from learned patterns

### 3. Knowledge Base Management

**Add WA Tax Law Documents**:
```bash
python scripts/knowledge_base/ingest_legal_docs.py \
    --folder knowledge_base/states/washington/legal_documents/
```

**Add Vendor Background Docs**:
```bash
python scripts/knowledge_base/ingest_vendor_docs.py \
    --folder knowledge_base/vendors/
```

**Sync Across Machines**:
1. Download from Supabase Storage: `python scripts/knowledge_base/download_from_storage.py`
2. Or upload local: `python scripts/knowledge_base/upload_to_storage.py`

### 4. Excel Versioning Workflow

**Upload New Version**:
```python
from core.excel_versioning import ExcelVersionManager

manager = ExcelVersionManager()
file_id = manager.upload_file(
    file_path="Master_Refunds.xlsx",
    project_id="<project-uuid>",
    user_email="analyst@company.com"
)
```

**Create New Version** (after making changes):
```python
version_id = manager.create_version(
    file_id=file_id,
    file_path="Master_Refunds_updated.xlsx",
    user_email="analyst@company.com",
    change_summary="Updated 45 refund amounts"
)
```

**View Changes**:
```python
diff = manager.get_version_diff(file_id, version_1=1, version_2=2)
print(f"Cells changed: {len(diff['cells_changed'])}")
```

**How It Works**:
- **Auto-saves last 10 versions** (rolling window)
- **Snapshots** - manual permanent save points ("Final - ready for filing")
- **Cell-level tracking** - see exactly what changed (row, column, old→new)
- **Per-project** - each project has separate version history

---

## Key Features

### 1. Intelligent Change Detection

**Problem**: Re-analyzing 10,000 rows takes hours and costs money
**Solution**: Only analyze rows where **INPUT columns** changed

**INPUT Columns** (trigger re-analysis):
- Invoice_File_Name_1/2 (new invoice added)
- Tax_Amount (amount changed)
- Vendor_Name
- Purchase_Order_Number

**OUTPUT Columns** (feedback only, skip re-analysis):
- Analysis_Notes (you corrected AI's analysis)
- Tax_Category (you fixed categorization)
- Estimated_Refund (you adjusted amount)

**How It Works**:
```python
# Check excel_cell_changes table
changes = supabase.table('excel_cell_changes')\
    .select('row_index, column_name')\
    .eq('file_id', file_id)\
    .execute()

# Filter to INPUT column changes only
from core.excel_column_definitions import is_input_column

rows_to_reanalyze = set()
for change in changes.data:
    if is_input_column(change['column_name']):
        rows_to_reanalyze.add(change['row_index'])
```

### 2. Multi-Project Support

**Use Case**: Organize different Excel files by tax type, year, client

**Examples**:
- "WA Sales Tax 2024"
- "WA Use Tax 2024"
- "WA Sales Tax 2025" (NEW LAW post Oct 1, 2025)

**Setup**:
```sql
INSERT INTO projects (name, tax_type, tax_year) VALUES
('WA Sales Tax 2024', 'sales_tax', 2024),
('WA Use Tax 2024', 'use_tax', 2024);
```

**Benefits**:
- Separate version tracking per project
- Separate snapshots
- No mixing between sales/use tax

### 3. Smart Caching

**Saves Time & Money**:
- **Invoice extraction** - 30-day cache (80%+ hit rate after first run)
- **Vendor lookups** - Instant (database table, no API calls)
- **RAG searches** - 7-day cache (100% hit rate for repeat categories)

**Cost Savings** (per 100 invoices):
- Without cache: ~$5.00 (100 extractions + 100 RAG searches)
- With cache: ~$1.08 (20 extractions + cached RAG)
- **79% cost reduction**

### 4. Dashboard (Streamlit) - Workflow Management

**Purpose**: Manage the refund analysis workflow

**Pages**:
- **Home** - System overview, quick stats
- **Projects** - Manage tax claim projects
- **Documents** - Browse knowledge base (tax law, vendor docs)
- **Review Queue** - Review AI analysis, approve/reject
- **Claims** - Generate refund claim summaries
- **Analytics** - Refund trends, vendor patterns
- **Excel Manager** - Upload files, view versions, compare changes

**Start Dashboard**:
```bash
streamlit run dashboard/Dashboard.py
# Opens at: http://localhost:8501
```

**Use Case**: Day-to-day refund analysis (upload Excel, review results, generate claims)

---

### 5. Chatbot (Streamlit) - Legal Q&A

**Purpose**: Ask questions about Washington State tax law

**Features**:
- **Interactive Chat** - "What is the MPU rule?", "How is SaaS taxed?"
- **Enhanced RAG** - Searches WA tax law documents
- **Legal Citations** - Returns exact RCW/WAC references
- **Feedback System** - Thumbs up/down to improve answers
- **Learning** - Gets smarter from your feedback

**Start Chatbot**:
```bash
streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503
# Opens at: http://localhost:8503
```

**Use Case**: Legal research, understanding tax law concepts, training team members

**Example Questions**:
- "What is the multi-point use rule?"
- "Are consulting services taxable in Washington?"
- "How do I allocate tax for digital services used in multiple states?"
- "What exemptions exist for manufacturing equipment?"

**Note**: This is separate from the Dashboard - you run them independently for different purposes

---

## Common Scenarios

### Scenario 1: First-Time Analysis (1,000 Invoices)

**Steps**:
1. Put invoice PDFs in `client_documents/invoices/`
2. Create Excel with vendor names, invoice numbers, amounts
3. Run analyzer:
```bash
python analysis/fast_batch_analyzer.py --excel Master.xlsx --state washington
```
4. Wait ~15-20 minutes (invoice extraction + analysis)
5. Review results in Excel
6. Correct 10-20% of items (teach the system)
7. Import corrections: `python analysis/import_corrections.py Master.xlsx`

**Outcome**: System learned vendor patterns, next batch will be more accurate

### Scenario 2: Adding New Invoices (50 More)

**Steps**:
1. Add 50 new rows to Excel (new vendors, new invoices)
2. Run analyzer again:
```bash
python analysis/fast_batch_analyzer.py --excel Master.xlsx --state washington
```
3. System detects 50 new rows (via row hash)
4. Skips 1,000 already-analyzed rows
5. Only processes 50 new rows (~2 minutes)

**Time Saved**: 95% faster (2 min vs 20 min)

### Scenario 3: Correcting AI Mistakes

**Steps**:
1. Open analyzed Excel
2. Find row where AI miscategorized (e.g., said "SaaS" should be "Services")
3. Change `Tax_Category` from "DAS" → "Services"
4. Change `Estimated_Refund` from "$5,000" → "$10,000" (100% refund)
5. Add note in `Corrected_Notes`: "This is consulting, not software"
6. Re-upload Excel (creates new version)
7. System detects OUTPUT column changes only
8. **Skips re-analysis** (it's just feedback, not new data)

**What Happens**: Correction stored, but row not re-analyzed (saving time)

### Scenario 4: Adding Purchase Order File (New Data)

**Steps**:
1. You get PO file that wasn't available before
2. Add filename to `Purchase_Order_File_Name` column (was blank)
3. Re-upload Excel
4. System detects **INPUT column change**
5. **Re-analyzes that row** (new data available!)

**Why**: INPUT column changed = new information = needs re-analysis

---

## Where to Find More

### Quick Reference
- **Setup Guide**: See `SETUP.md` (installation, database setup, verification)
- **Daily Usage**: See `WORKFLOWS.md` (analysis, review, knowledge base)
- **Module Details**: Each folder has README.md with specific info

### Module READMEs
- `analysis/README.md` - Analysis modules (fast_batch_analyzer, matchers, etc.)
- `core/README.md` - Core infrastructure (database, RAG, versioning)
- `scripts/README.md` - Utility scripts (knowledge base, data management)
- `dashboard/README.md` - Dashboard usage (workflow management UI)
- `chatbot/README.md` - Chatbot usage (legal Q&A UI)
- `database/README.md` - Database schema details

### Key Files to Understand
1. **analysis/fast_batch_analyzer.py** - Start here, the main analyzer
2. **core/enhanced_rag.py** - How legal research works
3. **core/excel_versioning.py** - How versioning works
4. **core/excel_column_definitions.py** - INPUT vs OUTPUT columns
5. **database/schema/schema_knowledge_base.sql** - Database structure

---

## Performance & Costs

### Speed
- **First 1,000 invoices**: ~15-20 minutes
- **Adding 50 new invoices**: ~2 minutes (change detection works!)
- **Re-running (all cached)**: ~1 minute

### Cost (OpenAI API)
- **Invoice extraction**: $0.003/invoice (first time), $0/invoice (cached)
- **RAG search**: $0.002/search (first time), $0/search (cached)
- **AI analysis**: $0.004/item (batch of 20)
- **Total for 100 invoices**: ~$1.08 (with caching)

### Accuracy
- **Out of box**: 70-75% correct
- **After 100 corrections**: 85-90% correct (vendor learning kicks in)
- **After 500 corrections**: 92-95% correct (mature system)

---

## Legal Concepts Quick Reference

### Multi-Point Use (MPU)
**RCW**: WAC 458-20-15502
**Rule**: Digital services taxed where used, not where sold
**Example**: 100 users, 85 outside WA → 85% refund

### Primarily Human Effort
**RCW**: RCW 82.04.050(6)
**Rule**: Services requiring human expertise NOT taxable
**Example**: Consulting, professional services → 100% refund

### Digital Automated Services (DAS)
**Rule**: Cloud/SaaS taxable in WA
**BUT**: MPU allocation applies if multi-state
**Example**: Salesforce, AWS, Azure → 70-90% refund (depending on user locations)

### Out-of-State Shipment
**Rule**: Tangible goods shipped out of WA → NOT taxable
**Example**: Hardware shipped to Oregon office → 100% refund

---

## Troubleshooting

### "No changes detected - all rows already analyzed"
- **Cause**: File hash unchanged OR all row hashes unchanged
- **Fix**: Use `--limit 10` to force re-analysis for testing

### "Could not find invoice file"
- **Cause**: PDF not in `client_documents/invoices/`
- **Fix**: Move PDFs to correct folder, check Excel `Invoice_File_Name_1` column

### "No legal documents found"
- **Cause**: Knowledge base not ingested
- **Fix**: Run `python scripts/knowledge_base/ingest_legal_docs.py`

### Low confidence scores (<60%)
- **Cause**: Ambiguous product description OR missing legal docs
- **Fix**: Review `Explanation` column, add more tax law PDFs if needed

### "Table 'projects' does not exist"
- **Cause**: Projects table not created
- **Fix**: Run `database/schema/migration_projects.sql` in Supabase SQL Editor

---

## Next Steps After Reading This

1. **Setup**: Read `SETUP.md` → get system running
2. **First Analysis**: Read `WORKFLOWS.md` → learn day-to-day usage
3. **Dive Deeper**: Check module READMEs in folders you're working in
4. **Extend**: Review code in `analysis/fast_batch_analyzer.py` to understand flow

---

**Last Updated**: 2025-11-23
**System Version**: v2.0 (Enhanced RAG + Excel Versioning + Multi-Project)
