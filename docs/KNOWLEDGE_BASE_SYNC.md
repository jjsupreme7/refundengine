# Knowledge Base Sync Guide

How to access your knowledge base (PDFs, vendor data) from any computer.

## 🎯 Quick Summary

Your RAG system has **three layers**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Supabase Database (ALWAYS ACCESSIBLE) ✅              │
│  ├─ Embeddings (vector search)                                  │
│  ├─ Chunks (processed text)                                     │
│  └─ Metadata (vendors, citations)                               │
│                                                                  │
│  Layer 2: Supabase Storage (BACKUP & SYNC) 🔄                  │
│  ├─ Original PDFs                                               │
│  ├─ Excel files                                                 │
│  └─ Accessible from anywhere                                    │
│                                                                  │
│  Layer 3: Local Files (DEVELOPMENT ONLY) 💻                     │
│  └─ knowledge_base/ folder                                      │
└─────────────────────────────────────────────────────────────────┘
```

## ✅ What Already Works

**Your RAG queries work from ANY computer because:**
- Embeddings are in Supabase (cloud database)
- Chunks are in Supabase
- No local files needed for queries!

**The only time you need local PDFs:**
- Initial ingestion (first time adding documents)
- Re-ingesting documents (if you update them)

---

## 📤 Step 1: Upload Your Knowledge Base (One Time)

On your **current computer** (where you have the PDFs):

```bash
# Upload all PDFs and Excel files to Supabase Storage
python scripts/upload_knowledge_base_to_storage.py
```

This will:
- ✅ Create a private `knowledge-base` bucket in Supabase
- ✅ Upload all files from `knowledge_base/` directory
- ✅ Make them accessible from any computer

**What gets uploaded:**
- `knowledge_base/states/washington/legal_documents/*.pdf`
- `knowledge_base/vendors/*.pdf`
- `knowledge_base/taxonomy/*.xlsx`
- Any other PDFs or Excel files

---

## 📥 Step 2: Download on New Computer (When Needed)

On a **new computer**:

```bash
# List what's available
python scripts/download_knowledge_base_from_storage.py --list-only

# Download everything
python scripts/download_knowledge_base_from_storage.py
```

This downloads all files to the local `knowledge_base/` directory.

---

## 🚀 Using the System on a New Computer

### Scenario A: Just Running Queries (Most Common)
**No download needed!** Your RAG works immediately because:

```bash
# Clone the repo
git clone https://github.com/jjsupreme7/refundengine.git
cd refundengine

# Set up environment
cp .env.example .env
# Add your SUPABASE_URL and SUPABASE_KEY

# Install dependencies
pip install -r requirements.txt

# Start querying immediately! 🎉
python chatbot/chat_rag.py
```

The system queries Supabase database embeddings - **no local files needed**.

### Scenario B: Re-Ingesting Documents
**Download needed only if re-ingesting:**

```bash
# Download PDFs first
python scripts/download_knowledge_base_from_storage.py

# Then re-ingest
python scripts/8_ingest_knowledge_base.py tax_law "knowledge_base/states/washington/..."
```

---

## 🔐 Security

### What's Safe to Commit to GitHub
✅ Code (already committed)
✅ Schema files (already committed)
✅ Empty folder structure (already committed)

### What's NEVER in GitHub (for security)
❌ PDFs with client data (in .gitignore)
❌ Vendor Excel sheets (in .gitignore)
❌ Your .env file (in .gitignore)

### Where Sensitive Data Lives
- **Supabase Database**: Encrypted, access-controlled
- **Supabase Storage**: Private bucket, requires authentication
- **Local only**: Your laptop (when downloaded)

---

## 📊 Your Current Knowledge Base

Check what you have:

```bash
# See what's in Supabase Storage
python scripts/download_knowledge_base_from_storage.py --list-only

# See what's in your local folder
ls -R knowledge_base/

# See what's in Supabase Database
python scripts/utils/check_supabase_tables.py
```

---

## 🆘 Common Scenarios

### "I'm on a new computer and queries aren't working"
**Solution:** Check your `.env` file - you need `SUPABASE_URL` and `SUPABASE_KEY`

### "I need to add new PDFs"
**Steps:**
1. Add PDFs to local `knowledge_base/` folder
2. Run ingestion script to process them
3. Run upload script to back them up to Supabase Storage

### "I want to update vendor metadata"
**Steps:**
1. Download current Excel file (or use local)
2. Update the Excel file
3. Re-run vendor ingestion script
4. Upload updated file to Supabase Storage

### "I accidentally deleted local PDFs"
**Solution:** Run the download script - they're backed up in Supabase Storage!

---

## 💾 Storage Costs

**Supabase Free Tier:**
- Database: 500MB (embeddings/chunks)
- Storage: 1GB (PDFs)
- More than enough for your use case!

**Current usage:**
- Your `knowledge_base/` is ~5MB
- Well within free tier limits

---

## 🎓 Best Practices

1. **Upload PDFs to Supabase Storage** ← Do this first!
2. **Keep .env file secure** (never commit)
3. **Run ingestion once per document** (embeddings persist in Supabase)
4. **Query from anywhere** (works immediately with just .env)
5. **Re-download PDFs only if re-ingesting** (rare)

---

## 🔄 Workflow Summary

### First Time Setup (Your Current Computer)
```bash
# 1. Process documents into database
python scripts/8_ingest_knowledge_base.py ...

# 2. Upload originals to cloud storage (NEW!)
python scripts/upload_knowledge_base_to_storage.py
```

### New Computer Setup
```bash
# 1. Clone repo
git clone ...

# 2. Set up .env
# (Add Supabase credentials)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start using immediately!
python chatbot/chat_rag.py
# (Queries work right away - no download needed)
```

### When You Need PDFs on New Computer
```bash
# Only if re-ingesting or viewing originals
python scripts/download_knowledge_base_from_storage.py
```

---

## ✨ The Magic

Your RAG system is **already cloud-native**:
- ✅ Embeddings in Supabase → queries work from anywhere
- ✅ Original PDFs in Supabase Storage → backup/sync
- ✅ No local files needed for daily use
- ✅ Secure and scalable

**You can now work on this project from ANY computer with just your .env file!**
