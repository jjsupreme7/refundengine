# Work Laptop Quick Start

**5-Minute Setup Guide**

---

## What You Need

1. ✅ Python 3.12+ installed
2. ✅ Git installed
3. ✅ Your Supabase credentials (from MacBook or Supabase dashboard)

---

## Setup (One Time)

### Step 1: Clone the Repository

```bash
# Open Terminal (Mac) or Command Prompt (Windows)
cd ~/Documents  # or wherever you want the project

git clone https://github.com/jjsupreme7/refundengine.git
cd refundengine
```

### Step 2: Run Setup Script

**Mac/Linux:**
```bash
./setup_work_laptop.sh
```

**Windows:**
```cmd
setup_work_laptop.bat
```

This installs everything automatically!

### Step 3: Add Your Credentials

Edit the `.env` file that was created:

```bash
# Mac:
nano .env

# Windows:
notepad .env
```

Replace with your actual values:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_DB_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

### Step 4: Test Connection

```bash
# Activate virtual environment first
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Test connection
python scripts/utils/check_supabase_tables.py
```

You should see: ✅ Connected to Supabase

---

## Daily Usage

### Add Client Invoices

Just drop PDFs into the folder:
```
client_documents/
├── invoices/
│   └── your_client_invoices.pdf
└── purchase_orders/
    └── your_client_pos.pdf
```

### Run Analysis

```bash
python analysis/analyze_refunds.py \
  --input client_documents/master_data/transactions.xlsx \
  --docs-folder client_documents \
  --output outputs/analysis/results.xlsx
```

### Query Knowledge Base

```bash
python chatbot/chat_rag.py
```

Ask questions like:
- "What is the MPU exemption?"
- "Are SaaS services taxable in Washington?"
- "What exemptions apply to telecom equipment?"

---

## Get Latest Code Updates

When your MacBook pushes new code:

```bash
git pull
```

That's it! Knowledge base is already in the cloud (Supabase).

---

## What's Where

| What | Where | Synced? |
|------|-------|---------|
| Code | GitHub | ✅ Auto sync |
| Knowledge Base | Supabase | ✅ Auto sync |
| Client Invoices | Local only | ❌ Your work laptop only |
| .env credentials | Local only | ❌ Never synced |

---

## Help

- 📖 Full guide: `docs/MULTI_COMPUTER_SETUP.md`
- 🔐 Security info: `docs/CLOUD_STORAGE_SECURITY.md`
- 📚 Knowledge base sync: `docs/KNOWLEDGE_BASE_SYNC.md`

---

## Common Commands

```bash
# Activate environment
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows

# Check Supabase connection
python scripts/utils/check_supabase_tables.py

# Run tests
pytest tests/

# Get latest code
git pull

# Query knowledge base
python chatbot/chat_rag.py
```

---

**That's it! Your work laptop is now set up and can access the shared knowledge base while keeping client data local and secure.**
