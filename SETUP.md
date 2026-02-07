# Setup Guide: Washington State Tax Refund Engine

Get the system running on a new machine.

---

## Prerequisites

### Required
- **Python 3.8+** (3.10+ recommended)
- **Supabase Account** (free tier works)
- **OpenAI API Key** (GPT-4o access required)

### Optional
- **Docker** (for containerized deployment)
- **Redis** (for async processing - can skip for basic use)
- **Tesseract OCR** (recommended for scanned/image-only invoice PDFs)

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/refund-engine.git
cd refund-engine
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**What Gets Installed**:
- `openai` - GPT-4o, GPT-4 Vision
- `supabase` - Database client
- `pandas` - Excel processing  
- `pdfplumber` - PDF extraction
- `pytesseract` + `pypdfium2` - OCR fallback for scanned PDFs
- `streamlit` - Dashboard
- `pytest` - Testing

### 4. Install Tesseract Binary (Recommended)

`pytesseract` requires the `tesseract` system binary.

macOS (Homebrew):
```bash
brew install tesseract
```

Verify:
```bash
tesseract --version
```

---

## Environment Configuration

### 1. Create .env File

```bash
cp .env.example .env
```

### 2. Get API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to `.env`: `OPENAI_API_KEY=sk-...`

---

## New Pipeline CLI

The rebuilt workflow is config-driven via `config/datasets.yaml`.

List datasets:
```bash
venv/bin/python scripts/refund_cli.py list-datasets
```

Run preflight checks:
```bash
venv/bin/python scripts/refund_cli.py preflight --dataset use_tax_2024
```

Dry-run analysis (no API calls/writes):
```bash
venv/bin/python scripts/refund_cli.py analyze --dataset use_tax_2024 --limit 5 --dry-run
```

Run real OpenAI analysis and write updates:
```bash
venv/bin/python scripts/refund_cli.py analyze --dataset use_tax_2024 --limit 5 --model gpt-5.2-pro
```

Validate output workbook:
```bash
venv/bin/python scripts/refund_cli.py validate --dataset use_tax_2024
```

Run the local web app:
```bash
venv/bin/streamlit run apps/refund_webapp.py
```

#### Supabase Credentials
1. Go to https://supabase.com/dashboard
2. Create new project (or use existing)
3. Go to Project Settings → API
4. Copy:
   - **URL**: `SUPABASE_URL=https://...supabase.co`
   - **Service Role Key**: `SUPABASE_SERVICE_ROLE_KEY=eyJ...` (NOT anon key!)

### 3. Complete .env File

```bash
# Required
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...

# Optional (for development)
DEBUG=false
LOG_LEVEL=INFO
```

**IMPORTANT**: Use **Service Role Key**, not anon key (needed for database admin operations)

---

## Database Setup

### 1. Access Supabase SQL Editor

1. Go to https://supabase.com/dashboard/project/YOUR_PROJECT/sql
2. Click "New Query"

### 2. Run Schema Migrations (In Order)

#### Step 1: Knowledge Base Tables
```bash
cat database/schema/schema_knowledge_base.sql
```
Copy output → Paste in SQL Editor → Run

**What This Creates**:
- `knowledge_documents` - Document registry
- `tax_law_chunks` - WA tax law (chunked for RAG)
- `vendor_background_chunks` - Vendor info
- `search_tax_law()` - RPC function for vector search
- `search_vendor_background()` - RPC function for vendor search

#### Step 2: Vendor Learning Tables
```bash
cat database/schema/schema_vendor_learning.sql
```
Copy → Paste → Run

**What This Creates**:
- `vendor_products` - Vendor → Product mappings
- `refund_citations` - Refund basis → Legal citations
- `keyword_patterns` - Product keywords by category

#### Step 3: Excel Versioning Tables
```bash
cat database/schema/migration_excel_versioning.sql
```
Copy → Paste → Run

**What This Creates**:
- `excel_file_tracking` - File metadata
- `excel_file_versions` - Version history
- `excel_cell_changes` - Cell-level change tracking

#### Step 4: Projects Table
```bash
cat database/schema/migration_projects.sql
```
Copy → Paste → Run

**What This Creates**:
- `projects` - Multi-project organization
- `v_project_summaries` - Summary view

#### Step 5: Analysis Results Tables
```bash
cat database/schema/schema_simple.sql
```
Copy → Paste → Run

**What This Creates**:
- `analysis_results` - AI analysis output
- `analysis_reviews` - Human corrections
- `analysis_feedback` - Learning data

### 3. Verify Tables Created

```sql
-- Run this in SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Expected Tables** (should see ~15-20):
- projects
- knowledge_documents
- tax_law_chunks
- vendor_background_chunks
- vendor_products
- refund_citations
- keyword_patterns
- excel_file_tracking
- excel_file_versions
- excel_cell_changes
- analysis_results
- analysis_reviews
- analysis_feedback

### 4. Enable pgvector Extension

```sql
-- Run in SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

**Why Needed**: For vector similarity search (RAG)

---

## Knowledge Base Setup

You have 2 options:

### Option A: Download from Supabase Storage (Recommended)

**If someone already ingested docs and uploaded to storage**:

```bash
python scripts/knowledge_base/download_from_storage.py
```

**What This Does**:
- Downloads all documents from Supabase Storage
- Saves to local `knowledge_base/` folder
- Downloads embeddings from database
- **~5 minutes for full knowledge base**

### Option B: Ingest Local Documents (First Time Setup)

**If you're setting up from scratch**:

#### 1. Add WA Tax Law PDFs

Place PDF files in:
```
knowledge_base/states/washington/legal_documents/
```

**Where to Get Documents**:
- Washington State Legislature: https://leg.wa.gov/
- DOR Website: https://dor.wa.gov/
- Essential Documents:
  - RCW 82.04 (B&O Tax)
  - RCW 82.08 (Retail Sales Tax)
  - RCW 82.12 (Use Tax)
  - WAC 458-20-15502 (MPU Rule)

#### 2. Run Ingestion

```bash
python scripts/knowledge_base/ingest_legal_docs.py \
    --folder knowledge_base/states/washington/legal_documents/
```

**What This Does**:
- Chunks PDFs into 1000-character segments
- Generates embeddings (text-embedding-3-small)
- Stores in `tax_law_chunks` table
- **~10-15 minutes for 50 documents**

#### 3. (Optional) Add Vendor Background Docs

```bash
python scripts/knowledge_base/ingest_vendor_docs.py \
    --folder knowledge_base/vendors/
```

**Examples**:
- `Microsoft_Company_Overview.pdf`
- `Salesforce_Product_Catalog.pdf`
- (Helps AI understand vendor context)

---

## Verification

### Test Database Connection

```bash
python core/database.py
```

**Expected Output**:
```
Testing Supabase connection...
=============================================================
[1/4] Creating client...
✓ Client created successfully

[2/4] Checking client info...
✓ Connected: True

[3/4] Testing database query...
✓ Query successful! Found X documents

[4/4] Testing singleton behavior...
✓ Singleton working: True (should be True)
```

### Run Full Verification Script

```bash
python scripts/utils/verify_schema.py
```

**What It Checks**:
- Database tables exist
- RPC functions work
- Knowledge base has documents
- Vector search functional

**Expected Output**:
```
✅ knowledge_documents: 45 documents
✅ tax_law_chunks: 2,847 chunks
✅ search_tax_law() function: Working
✅ pgvector extension: Enabled
```

### Run Test Analysis (10 Rows)

```bash
# Create test Excel or use provided sample
python analysis/fast_batch_analyzer.py \
    --excel test_data/sample_invoices.xlsx \
    --state washington \
    --limit 10
```

**Expected Output**:
```
🚀 FAST BATCH REFUND ANALYZER
=====================================================================
Excel: test_data/sample_invoices.xlsx
State: WASHINGTON

📂 Loading Excel...
✓ Analyzing 10 rows

📄 Extracting invoices...
Extracting: 100%|██████████| 5/5 [00:15<00:00]

🔍 Matching line items...
✓ Matched 8/10 rows

🤖 AI Analysis (Batch Processing)...
Batch 1/1: 100%|██████████| 1/1 [00:08<00:00]

✅ Analysis complete!
Output: test_data/sample_invoices_analyzed.xlsx
```

---

## Optional: Docker Setup

### 1. Install Docker

- **Mac**: https://docs.docker.com/desktop/install/mac-install/
- **Windows**: https://docs.docker.com/desktop/install/windows-install/
- **Linux**: https://docs.docker.com/engine/install/

### 2. Build Image

```bash
docker-compose build
```

### 3. Start Services

```bash
docker-compose up -d
```

**What Gets Started**:
- Redis (caching)
- Celery workers (async processing)
- Flower (monitoring UI at http://localhost:5555)

### 4. Run Analysis in Docker

```bash
docker-compose run app python analysis/fast_batch_analyzer.py \
    --excel Master_Refunds.xlsx \
    --state washington
```

---

## File Structure After Setup

```
refund-engine/
├── .env                              # Your API keys (NEVER COMMIT)
├── venv/                             # Python virtual environment
├── knowledge_base/
│   └── states/washington/
│       └── legal_documents/          # Your WA tax law PDFs
├── client_documents/
│   └── invoices/                     # Your invoice PDFs go here
├── test_data/
│   └── sample_invoices.xlsx          # Test data
└── outputs/                          # Analysis results
```

---

## Troubleshooting Setup

### "ModuleNotFoundError: No module named 'openai'"
**Fix**: Activate virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "ValueError: SUPABASE_URL not set"
**Fix**: Check `.env` file exists and has correct values
```bash
cat .env  # Verify content
```

### "Could not find the table 'tax_law_chunks'"
**Fix**: Run database migrations
```bash
# Run schema_knowledge_base.sql in Supabase SQL Editor
```

### "No embeddings model found"
**Fix**: Verify OpenAI API key has GPT-4 access
```bash
python scripts/openai_smoke_test.py --model gpt-5.2

# If you need to inspect available models:
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### "Permission denied: 'client_documents/invoices/'"
**Fix**: Create directories
```bash
mkdir -p client_documents/invoices
mkdir -p outputs
```

### Supabase RPC function errors
**Fix**: Make sure you used **Service Role Key**, not anon key
```bash
# Check .env
grep SUPABASE_SERVICE_ROLE_KEY .env  # Should be ~300+ characters
```

---

## Multi-Computer Setup

### Sync Knowledge Base Across Machines

**Machine 1 (Primary)**:
```bash
# Ingest documents
python scripts/knowledge_base/ingest_legal_docs.py --folder knowledge_base/states/washington/legal_documents/

# Upload to Supabase Storage
python scripts/knowledge_base/upload_to_storage.py
```

**Machine 2 (Secondary)**:
```bash
# Download from Supabase Storage
python scripts/knowledge_base/download_from_storage.py
```

**Why**: Avoids re-ingesting 50+ PDFs (saves 15 min + API costs)

### Share Projects

Projects are already in Supabase (stored in `projects` table), so all machines see the same projects automatically.

---

## Performance Tuning (Optional)

### Increase Batch Size (Faster, More Expensive)
Edit `analysis/fast_batch_analyzer.py`:
```python
BATCH_SIZE = 50  # Default: 20, Max: 100
```

### Adjust Cache TTL
Edit `scripts/utils/smart_cache.py`:
```python
INVOICE_CACHE_DAYS = 60  # Default: 30
RAG_CACHE_DAYS = 14      # Default: 7
```

### Increase Concurrent Workers (Docker)
Edit `docker-compose.yml`:
```yaml
command: celery -A tasks worker --concurrency=20  # Default: 10
```

---

## Next Steps After Setup

1. **Read PROJECT_OVERVIEW.md** - Understand the system architecture
2. **Read WORKFLOWS.md** - Learn day-to-day usage
3. **Run first analysis** - Process a real Excel file
4. **Review results** - Correct AI mistakes
5. **Import corrections** - Teach the system

---

## Getting Help

### Quick Reference
- **Command not working?** Check module README: `analysis/README.md`, `scripts/README.md`
- **Database issues?** See `database/README.md`
- **Dashboard not loading?** See `dashboard/README.md`

### Common Issues
- Can't find files → Check `client_documents/invoices/` folder
- Low confidence → Need more tax law documents
- Slow performance → Enable caching, increase batch size
- API errors → Check `.env` has correct keys

---

**Setup Complete!** You're ready to analyze invoices.

**Last Updated**: 2025-11-23
