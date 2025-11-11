# Multi-Computer Setup Guide

Setup guide for using the refund engine across multiple computers.

---

## Architecture: Shared Knowledge Base, Local Client Data

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR SETUP                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MACBOOK (Development)                     WORK LAPTOP (Production)│
│  ┌──────────────────────────┐            ┌──────────────────────┐│
│  │ • Code development       │            │ • Client analysis    ││
│  │ • Testing                │            │ • Invoice processing ││
│  │ • No client docs         │            │ • Actual client docs ││
│  └──────────────────────────┘            └──────────────────────┘│
│            │                                       │              │
│            │         SHARED (Cloud)                │              │
│            └───────────┬───────────────────────────┘              │
│                        │                                          │
│                ┌───────▼────────┐                                │
│                │   SUPABASE     │                                │
│                ├────────────────┤                                │
│                │ • Database     │                                │
│                │ • Embeddings   │                                │
│                │ • Knowledge    │                                │
│                │   Base PDFs    │                                │
│                └────────────────┘                                │
│                                                                  │
│  MacBook: client_documents/ (empty or test data)                │
│  Work Laptop: client_documents/ (REAL client invoices/POs)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### ONE-TIME: MacBook Setup (Already Done ✅)

Your MacBook is already configured:
- ✅ Code repository
- ✅ Supabase connection
- ✅ Knowledge base uploaded to Supabase Storage
- ✅ Tests passing

---

### WORK LAPTOP: Initial Setup

#### Step 1: Install Prerequisites

**Windows:**
```powershell
# Install Python 3.12
# Download from: https://www.python.org/downloads/

# Install Git
# Download from: https://git-scm.com/download/win

# Verify installations
python --version  # Should be 3.12.x
git --version
```

**Mac:**
```bash
# Install Homebrew (if not already)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
brew install python@3.12

# Git is pre-installed on Mac
git --version
```

---

#### Step 2: Clone Repository

```bash
# Navigate to where you want the project
cd ~/Documents  # or C:\Users\YourName\Documents on Windows

# Clone the repository
git clone https://github.com/jjsupreme7/refundengine.git
cd refundengine
```

---

#### Step 3: Create .env File

Create a file named `.env` in the project root:

```bash
# On Mac/Linux
nano .env

# On Windows
notepad .env
```

Add your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database (same as Supabase, but explicit connection string)
SUPABASE_DB_PASSWORD=your_db_password_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_key_here
```

**Where to find these values:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_KEY`
   - service_role key → `SUPABASE_SERVICE_ROLE_KEY`
5. Go to Settings → Database
   - Copy password → `SUPABASE_DB_PASSWORD`

---

#### Step 4: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

---

#### Step 5: Verify Connection

```bash
# Test Supabase connection
python scripts/utils/check_supabase_tables.py
```

You should see:
```
✓ Connected to Supabase
✓ Knowledge base available
✓ RAG system ready
```

---

### CLIENT DOCUMENTS: Work Laptop Only

#### Your `client_documents/` Folder Structure

On your **work laptop**, create this structure:

```
client_documents/
├── invoices/
│   ├── client_a_invoice_001.pdf
│   ├── client_a_invoice_002.pdf
│   └── ...
├── purchase_orders/
│   ├── client_a_po_001.pdf
│   ├── client_a_po_002.pdf
│   └── ...
└── master_data/
    └── client_master_list.xlsx  # Optional: vendor metadata
```

**Important:**
- ⚠️ These files stay LOCAL on work laptop
- ⚠️ Never commit to GitHub (already in .gitignore)
- ⚠️ Never upload to cloud storage
- ✅ Work laptop has the REAL client data
- ✅ MacBook has empty folders (or test/dummy data)

---

## Daily Workflow

### On MacBook (Development)

```bash
# Pull latest code
git pull

# Make changes to code
# ... edit files ...

# Test with dummy data (if needed)
# Put test PDFs in client_documents/ for testing only

# Commit and push code changes
git add .
git commit -m "Your changes"
git push
```

**MacBook is for:**
- ✅ Writing code
- ✅ Running tests
- ✅ Experimenting with features
- ❌ NOT for real client analysis

---

### On Work Laptop (Production)

```bash
# Pull latest code from MacBook
git pull

# Your client documents are already there locally

# Run analysis
python analysis/analyze_refunds.py \
  --input client_documents/master_data/transactions.xlsx \
  --docs-folder client_documents \
  --output outputs/analysis/client_a_analysis.xlsx

# Generate reports
# ... analysis runs ...

# DON'T commit client documents (they're in .gitignore)
# Only commit code changes if you made any
```

**Work Laptop is for:**
- ✅ Real client analysis
- ✅ Invoice processing
- ✅ Generating reports for clients
- ✅ Production work

---

## Knowledge Base Access (Both Computers)

Both computers can query the knowledge base because it's in Supabase:

```python
# This works on BOTH computers automatically
from core.enhanced_rag import EnhancedRAG

rag = EnhancedRAG()
results = rag.search("What is the MPU exemption for SaaS?")
# Queries Supabase → returns tax law chunks
```

**No downloads needed!** The knowledge base is already in the cloud.

---

## Adding New Client Documents

### On Work Laptop

1. **Receive invoices from client** (email, upload, etc.)

2. **Save to local folder:**
   ```
   client_documents/invoices/client_name_invoice_001.pdf
   ```

3. **Run analysis immediately:**
   ```bash
   python analysis/analyze_refunds.py --input ...
   ```

4. **That's it!** No syncing needed.

---

## Updating Knowledge Base (Rare)

If you add new tax law PDFs or vendor research:

### On MacBook (Where you add the PDF)

```bash
# 1. Add PDF to knowledge_base/
cp ~/Downloads/new_tax_law.pdf knowledge_base/states/washington/legal_documents/

# 2. Ingest into Supabase database
python scripts/8_ingest_knowledge_base.py tax_law \
  "knowledge_base/states/washington/legal_documents/new_tax_law.pdf" \
  --citation "RCW 82.08.123" \
  --title "New Tax Law Document"

# 3. Upload to Supabase Storage (backup)
python scripts/upload_knowledge_base_to_storage.py

# 4. Commit the ingestion metadata (not the PDF)
git add database/ docs/
git commit -m "Add new tax law document"
git push
```

### On Work Laptop (Automatic)

```bash
# Pull the code
git pull

# That's it! The knowledge base is already in Supabase
# Your work laptop can query it immediately, no downloads needed
```

---

## What Gets Synced vs. What Stays Local

### ✅ Synced via GitHub

- Python code (scripts, analysis logic)
- Documentation
- Configuration files (except .env)
- Tests
- Docker files
- Database schemas

### ☁️ Synced via Supabase

- Knowledge base embeddings (tax laws, vendor research)
- Database schema and structure
- Ingested document metadata

### 💾 Local Only (Never Synced)

- `.env` file (credentials)
- `client_documents/` (invoices, POs)
- `outputs/` (generated reports)
- `venv/` (Python virtual environment)

---

## Security Checklist

### ✅ Good Practices

- `.env` file is in `.gitignore` (credentials never committed)
- `client_documents/` is in `.gitignore` (client data never committed)
- Use strong passwords for Supabase
- Enable 2FA on GitHub account
- Keep work laptop encrypted (BitLocker/FileVault)

### ⚠️ Important Reminders

- Never commit `.env` file
- Never commit client PDFs
- Don't store credentials in code
- Don't share `.env` via email/Slack

---

## Troubleshooting

### "Can't connect to Supabase" on Work Laptop

**Check:**
```bash
# 1. Verify .env file exists
cat .env  # Mac/Linux
type .env  # Windows

# 2. Test connection
python scripts/utils/check_supabase_tables.py

# 3. Check internet connection
ping supabase.com
```

### "Knowledge base not found"

**Solution:**
```bash
# The knowledge base is already in Supabase from your MacBook
# You don't need to download anything!

# Just verify connection:
python scripts/utils/check_supabase_tables.py
```

### "Can't find client documents"

**Expected!** On MacBook, `client_documents/` should be mostly empty (or test data).

On work laptop, you manually add client PDFs to `client_documents/`.

---

## Quick Reference Commands

### MacBook (Development)

```bash
# Update code
git pull

# Make changes
# ... code ...

# Push changes
git add .
git commit -m "Description"
git push

# Update knowledge base (rare)
python scripts/upload_knowledge_base_to_storage.py
```

### Work Laptop (Production)

```bash
# Get latest code
git pull

# Run analysis (client docs already local)
python analysis/analyze_refunds.py --input ... --docs-folder client_documents

# Query knowledge base (automatic, uses Supabase)
python chatbot/chat_rag.py
```

---

## Summary

**What's shared between computers:**
- ✅ Code (via GitHub)
- ✅ Knowledge base (via Supabase)
- ✅ Database structure (via Supabase)

**What stays separate:**
- 💻 Client documents (local to work laptop)
- 🔐 .env credentials (you manually create on each computer)
- 📊 Generated reports (local to where you run analysis)

**The beauty of this setup:**
- Work laptop has client data, runs production analysis
- MacBook has clean development environment
- Both access same knowledge base (tax laws) automatically
- No sensitive data in GitHub
- Simple and secure!
