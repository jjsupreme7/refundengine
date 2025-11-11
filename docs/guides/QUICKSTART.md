# Quick Start Guide

You're all set up! Here's how to use your RAG system:

## ✅ What's Ready

- ✅ Database schema deployed to Supabase
- ✅ 2 tax law documents ingested (WAC 458-20-15502, WAC 458-20-15503)
- ✅ Vector embeddings created
- ✅ RAG testing interface ready

---

## 🚀 Test the RAG System

### Interactive Mode (Recommended)

```bash
python3 scripts/test_rag.py
```

This opens an interactive search interface. Try these commands:

```
# Show what's in the knowledge base
stats

# Search tax law
tax computer software taxation

# Search with filters
tax digital products --category software --threshold 0.3

# Search with specific citation
tax cloud services --citation WAC-458-20-15503

# Quit
quit
```

### Command Line Mode

```bash
# Search tax law
python3 scripts/test_rag.py --mode tax --query "software as a service" --threshold 0.3

# Show stats
python3 scripts/test_rag.py --mode stats
```

---

## 📥 Ingest More Documents

### Tax Law Documents

```bash
python3 scripts/ingest_document.py tax_law \
    "knowledge_base/states/washington/legal_documents/WAC 458-20-19402.pdf" \
    --citation "WAC 458-20-19402" \
    --category "exemption" \
    --title "Nonprofit Organizations"
```

**Categories**: `exemption`, `rate`, `definition`, `software`, `general`

### Vendor Background Documents

First, add vendor PDFs to `knowledge_base/vendors/`, then:

```bash
python3 scripts/ingest_document.py vendor \
    "knowledge_base/vendors/Nokia_Profile.pdf" \
    --vendor "Nokia" \
    --vendor-category "manufacturer" \
    --doc-category "profile"
```

**Vendor Categories**: `manufacturer`, `distributor`, `service_provider`
**Doc Categories**: `profile`, `catalog`, `contract`, `general`

---

## 🔍 Example RAG Queries

### Tax Law Searches

```
# Software taxation
tax computer software cloud SaaS

# Digital products
tax digital goods streaming music

# Services
tax professional services consulting

# Exemptions
tax manufacturing exemption equipment

# Multi-point use
tax allocation multi-state
```

### Vendor Searches (once you ingest vendor docs)

```
vendor Nokia telecommunications equipment

vendor Ericsson 5G products --vendor Nokia

vendor Microsoft software licensing
```

---

## 📊 Check Your Knowledge Base

```bash
python3 scripts/test_rag.py --mode stats
```

Output:
```
Documents:
  Tax Law:            2
  Vendor Background:  0
  Total:              2

Chunks:
  Tax Law:            2
  Vendor Background:  0
  Total:              2

Tax Law Documents:
  • WAC 458-20-15502               | software        | 1 chunks
  • WAC 458-20-15503               | software        | 1 chunks
```

---

## 🎯 Understanding Results

When you search, you'll see:

```
[1] Similarity: 0.405 | Citation: WAC 458-20-15502 | Category: software
    WAC 458-20-15502   Taxation of computer software.   (1) What is
    computer software?  RCW 82.04.215 provides...
```

- **Similarity**: 0-1 score (higher = better match)
  - 0.7+: Excellent match
  - 0.5-0.7: Good match
  - 0.3-0.5: Relevant
  - <0.3: Weak match

- **Citation**: RCW/WAC reference
- **Category**: Document category for filtering

---

## ⚙️ Adjust Search Sensitivity

```bash
# More strict (only very relevant results)
tax software --threshold 0.7

# More lenient (include loosely related results)
tax software --threshold 0.2

# More results
tax software --count 10
```

---

## 🧪 Testing Metadata Filters

The RAG system supports filtering by metadata:

```
# Only software-related laws
tax SaaS --category software

# Specific citation
tax cloud --citation WAC-458-20-15503

# Specific vendor (when you have vendor docs)
vendor 5G equipment --vendor Nokia
```

---

## 📁 File Locations

```
refund-engine/
├── scripts/
│   ├── ingest_document.py      # Ingest PDFs into knowledge base
│   └── test_rag.py              # Test RAG with interactive interface
│
├── knowledge_base/
│   ├── states/washington/legal_documents/   # Your tax law PDFs
│   └── vendors/                             # Vendor PDFs (add here)
│
└── database/
    └── schema_simple.sql        # Database schema
```

---

## 🐛 Troubleshooting

**No results found:**
- Lower the threshold: `--threshold 0.2`
- Check spelling
- Try broader terms
- Run `stats` to verify documents are ingested

**Ingestion fails:**
- Check .env file has OPENAI_API_KEY and SUPABASE credentials
- Verify PDF path is correct
- Check PDF is not encrypted/corrupted

**Similarity scores seem low:**
- This is normal! Scores of 0.3-0.5 can still be very relevant
- Legal text is dense, so exact semantic matches are rare
- Focus on the content, not just the score

---

## 🎉 Next Steps

1. **Ingest more tax law documents**
   - Add all your WA tax law PDFs
   - Try different categories (exemption, rate, etc.)

2. **Test different queries**
   - Try industry-specific terms
   - Test with real refund scenarios

3. **Add vendor documents**
   - Create vendor profiles
   - Add product catalogs
   - Build vendor knowledge base

4. **Integrate into analysis pipeline**
   - Use RAG results in refund analysis
   - Combine tax law + vendor context

---

## 💡 Pro Tips

- **Use natural language**: "How is cloud software taxed?" works great
- **Combine filters**: `--category exemption --threshold 0.6`
- **Experiment with threshold**: Different queries need different sensitivity
- **Check stats often**: Know what's in your knowledge base

---

**You're ready to go! Start with:**

```bash
python3 scripts/test_rag.py
```

Then type: `stats` → `tax computer software` → explore!
