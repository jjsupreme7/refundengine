# Local Environment Setup Guide

This guide will help you set up the Refund Engine on your local machine.

## Prerequisites

- Python 3.10 or higher (you have 3.12.7 ✅)
- PostgreSQL client (psql) for database operations
- Git (for version control)
- OpenAI API account
- Supabase account

---

## Quick Setup (Automated)

Run the setup script:

```bash
bash setup_local_env.sh
```

This will:
1. Create `.env` file from template
2. Set up Python virtual environment
3. Install all dependencies
4. Create necessary directories
5. Optionally deploy database schema

---

## Manual Setup (Step by Step)

### 1. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
nano .env
```

Required values:

| Variable | Where to Get It |
|----------|----------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `SUPABASE_URL` | Supabase Dashboard → Project Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Project Settings → API |
| `SUPABASE_DB_HOST` | Supabase Dashboard → Database Settings (format: `db.xxxxx.supabase.co`) |
| `SUPABASE_DB_PASSWORD` | Supabase Dashboard → Database Settings |

### 2. Python Virtual Environment

Create and activate virtual environment:

```bash
# Create venv
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

Your terminal should now show `(venv)` prefix.

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- `openai` - GPT-4o Vision and embeddings
- `supabase` - Vector database client
- `pandas` - Excel processing
- `pdfplumber` - PDF extraction
- `anthropic` - Optional Claude support
- And more...

### 4. Create Directory Structure

```bash
mkdir -p client_documents/invoices
mkdir -p knowledge_base/states/washington/legal_documents
mkdir -p knowledge_base/vendors
mkdir -p knowledge_base/taxonomy
mkdir -p output
```

### 5. Deploy Database Schema

Deploy to Supabase:

```bash
# Using the deployment script
bash scripts/0_deploy_schema.sh

# OR manually using psql
source .env
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
  -h $SUPABASE_DB_HOST \
  -U $SUPABASE_DB_USER \
  -d $SUPABASE_DB_NAME \
  -f database/schema_knowledge_base.sql

PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
  -h $SUPABASE_DB_HOST \
  -U $SUPABASE_DB_USER \
  -d $SUPABASE_DB_NAME \
  -f database/schema_vendor_learning.sql
```

### 6. Verify Installation

Test the RAG system:

```bash
python3 scripts/test_rag.py --mode stats
```

You should see database connection and stats (even if empty).

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'openai'`

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: `psql: command not found`

**Solution (macOS):**
```bash
# Install PostgreSQL client
brew install postgresql
```

**Solution (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql-client
```

### Issue: Database connection fails

**Solution:**
1. Check `.env` credentials are correct
2. Verify Supabase project is active
3. Check IP allowlist in Supabase (allow all: `0.0.0.0/0`)
4. Test connection:
```bash
source .env
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
  -h $SUPABASE_DB_HOST \
  -U $SUPABASE_DB_USER \
  -d $SUPABASE_DB_NAME \
  -c "SELECT version();"
```

### Issue: `pdftotext` command not found (when processing PDFs)

**Solution (macOS):**
```bash
brew install poppler
```

**Solution (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

---

## Directory Structure

After setup, your project should look like:

```
refund-engine/
├── .env                                   # Your credentials (DO NOT COMMIT)
├── .env.example                           # Template for .env
├── requirements.txt                       # Python dependencies
├── setup_local_env.sh                     # Automated setup script
│
├── venv/                                  # Virtual environment (created by setup)
│
├── client_documents/
│   └── invoices/                          # Place invoice PDFs here
│
├── knowledge_base/
│   ├── states/washington/
│   │   ├── legal_documents/               # WA tax law PDFs (WAC, RCW, WTD)
│   │   └── tax_rules.json                 # WA tax logic
│   ├── vendors/                           # Vendor background PDFs
│   └── taxonomy/
│       └── product_types.json             # Product classification rules
│
├── database/
│   ├── schema_knowledge_base.sql          # Knowledge base schema
│   └── schema_vendor_learning.sql         # Vendor learning schema
│
├── scripts/
│   ├── 0_deploy_schema.sh                 # Deploy database
│   ├── 6_analyze_refunds.py               # Main analyzer
│   ├── 7_import_corrections.py            # Import corrections
│   ├── 8_ingest_knowledge_base.py         # Ingest documents
│   └── test_rag.py                        # Test RAG system
│
├── docs/                                  # Documentation
└── output/                                # Analysis results (created by scripts)
```

---

## Next Steps

### 1. Ingest Tax Law Documents

Add WA tax law PDFs to `knowledge_base/states/washington/legal_documents/`, then:

```bash
python3 scripts/8_ingest_knowledge_base.py tax_law \
    "knowledge_base/states/washington/legal_documents/" \
    --citation "RCW 82.08" \
    --law-category "exemption"
```

### 2. Test RAG System

```bash
# Interactive mode
python3 scripts/test_rag.py

# In the prompt, try:
stats
tax software as a service
tax multi-point use
```

### 3. Add Sample Invoices

Place invoice PDFs in `client_documents/invoices/`

### 4. Create Excel Input

Create an Excel file with columns:
- `Row_ID`
- `Vendor`
- `Invoice_Number`
- `PO Number`
- `Date`
- `Amount`
- `Tax`
- `Inv_1_File` (filename of PDF in `client_documents/invoices/`)
- `PO_1_File` (optional)

### 5. Run Analysis

```bash
python3 scripts/6_analyze_refunds.py "your-file.xlsx" --save-db
```

### 6. Review Results

Open the generated `your-file_analyzed.xlsx` and review AI suggestions.

### 7. Import Corrections

After reviewing:

```bash
python3 scripts/7_import_corrections.py "your-file_analyzed.xlsx" --reviewer "your.email@company.com"
```

---

## Environment Variables Reference

### Required

```bash
# OpenAI
OPENAI_API_KEY=sk-...                      # For GPT-4o Vision + embeddings

# Supabase
SUPABASE_URL=https://xxx.supabase.co       # From API settings
SUPABASE_SERVICE_ROLE_KEY=eyJh...          # From API settings (service_role key)

# Database (for psql commands)
SUPABASE_DB_HOST=db.xxx.supabase.co        # From Database settings
SUPABASE_DB_USER=postgres                  # Usually 'postgres'
SUPABASE_DB_PASSWORD=your-password         # From Database settings
SUPABASE_DB_NAME=postgres                  # Usually 'postgres'
SUPABASE_DB_PORT=5432                      # Usually 5432
```

### Optional

```bash
# Anthropic (if using Claude instead of GPT)
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Development Workflow

### Daily Workflow

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Pull latest changes
git pull

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. Work on your tasks...

# 5. Deactivate when done
deactivate
```

### Adding New Dependencies

```bash
# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Commit changes
git add requirements.txt
git commit -m "Add package-name dependency"
```

---

## Performance Tips

### 1. Enable Caching

The system automatically caches:
- Invoice extractions (30 days)
- RAG searches (7 days)
- Vendor lookups (instant)

Caches are stored in `.cache/` directory.

### 2. Batch Processing

For large datasets, use batching:

```bash
python3 scripts/6_analyze_refunds.py "large-file.xlsx" --batch-size 20
```

### 3. Test Mode

Test with first 10 rows:

```bash
python3 scripts/6_analyze_refunds.py "file.xlsx" --limit 10
```

---

## Backup & Version Control

### What to Commit

✅ **DO commit:**
- Code changes
- Schema updates
- Documentation
- `requirements.txt`
- `.env.example`

❌ **DO NOT commit:**
- `.env` (contains secrets!)
- `venv/` (virtual environment)
- `.cache/` (cache files)
- `output/` (analysis results)
- `client_documents/` (sensitive invoices)

### .gitignore

Make sure your `.gitignore` includes:

```
.env
venv/
.cache/
output/
client_documents/
*.pyc
__pycache__/
```

---

## Support & Documentation

- **README.md** - Project overview
- **QUICKSTART.md** - Quick start guide
- **docs/EXCEL_WORKFLOW_GUIDE.md** - Excel workflow details
- **docs/KNOWLEDGE_BASE_GUIDE.md** - Knowledge base management

---

## Security Best Practices

1. **Never commit `.env`** - Contains API keys and passwords
2. **Use service_role key carefully** - Has full database access
3. **Rotate keys regularly** - Generate new API keys periodically
4. **Restrict Supabase IP allowlist** - Only allow your IPs in production
5. **Review permissions** - Ensure database RLS policies are correct

---

## Troubleshooting Checklist

- [ ] Virtual environment activated? (`source venv/bin/activate`)
- [ ] Dependencies installed? (`pip install -r requirements.txt`)
- [ ] `.env` file exists and configured?
- [ ] Supabase project active?
- [ ] Database schema deployed?
- [ ] PostgreSQL client installed? (`psql --version`)
- [ ] Invoice PDFs in correct folder?
- [ ] Excel file has required columns?

---

**You're all set! Start with:**

```bash
bash setup_local_env.sh
```

Or follow the manual steps above. Happy refund hunting! 💰
