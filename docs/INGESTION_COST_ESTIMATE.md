# WA Tax Law Full Ingestion - Cost & Limit Analysis

## 📊 Your Data

**Location:** `/Users/jacoballen/Desktop/WA Tax Law`

- **Total PDFs:** 783 documents
- **Total Size:** 170 MB
- **Average PDF Size:** ~217 KB each
- **Estimated Pages:** ~3,900 pages total (assuming 5 pages avg per PDF)

**Already Ingested:**
- ✅ 2 documents fully chunked (WAC 458-20-15502, WAC 458-20-15503)
- ✅ 227 chunks with embeddings
- ✅ 4 documents in database (2 others partially ingested)

**Remaining:** 779 PDFs to process

---

## 💰 COST ESTIMATE

### **Processing Costs:**

| Step | Service | Unit Cost | Quantity | Total Cost |
|------|---------|-----------|----------|------------|
| 1. PDF Text Extraction | pdfplumber (local) | FREE | 779 PDFs | **$0** |
| 2. AI Metadata Extraction | OpenAI GPT-4 | $0.05/doc | 779 docs | **$39** |
| 3. Text Chunking | Local processing | FREE | ~15,500 chunks | **$0** |
| 4. Generate Embeddings | OpenAI ada-002 | $0.0001/chunk | 15,500 chunks | **$1.55** |
| 5. Store in Supabase | Supabase storage | FREE tier | 170 MB | **$0** |

### **TOTAL ESTIMATED COST: ~$40.55**

**Breakdown:**
- GPT-4 for metadata: $39.00
- Embeddings: $1.55
- Everything else: FREE

---

## 📈 API RATE LIMITS & PLAN CHECKS

### **OpenAI Limits (Your Account)**

Need to check your OpenAI tier. Let me estimate based on typical limits:

**Tier 1 (Default - $5+ spent):**
- GPT-4: 500 requests/day, 10,000 tokens/min
- Embeddings: 3,000 requests/day, 1,000,000 tokens/min

**Your ingestion needs:**
- GPT-4: 779 requests (metadata) → **2 days** at 500/day
- Embeddings: 15,500 requests → **6 batches** at 3k/day (same day)

**Tier 2 (Paid $50+):**
- GPT-4: 5,000 requests/day
- Embeddings: 5,000 requests/day
- **Can finish in 1 day** ✅

---

### **Anthropic Claude Limits (Your Account)**

**Current Plan:** Unknown (need to check)

**Typical limits:**
- Free tier: 50 requests/day
- Paid tier 1: 1,000 requests/day
- Paid tier 2: 10,000 requests/day

**Your usage today:**
- Tokens used: 92k / 200k (46%)
- **Safe to continue** ✅

**Note:** Ingestion only uses OpenAI, not Claude. Claude is for web search in Script 4.

---

### **Supabase Limits (Your Account)**

**Free Tier Limits:**
- Database size: 500 MB
- Bandwidth: 2 GB/month
- Rows: Unlimited
- API requests: Unlimited

**Your current usage:**
- Documents: 6 rows
- Chunks: 227 rows
- Total DB size: ~5 MB

**After full ingestion:**
- Documents: ~785 rows (tiny)
- Chunks: ~15,700 rows (still tiny)
- Estimated DB size: ~100-150 MB (text + vectors)
- **Well within 500 MB free tier** ✅

**Vector storage estimate:**
- 15,700 chunks × 1536 dimensions × 4 bytes = ~96 MB for vectors
- Plus ~50 MB for text
- Total: ~150 MB / 500 MB limit = **30% usage** ✅

---

## ⚠️ RECOMMENDATIONS

### **Option 1: STAGED INGESTION (Recommended)**

**Why:** Safer, allows you to validate quality, manage costs

**Plan:**
1. **Week 1:** Ingest 50 most relevant documents
   - Cost: ~$2.60
   - Time: ~2 hours
   - Test RAG quality with chatbot

2. **Week 2:** Add 100 more documents
   - Cost: ~$5.10
   - Running total: ~$7.70
   - Evaluate if you need more

3. **Week 3:** Add remaining if needed
   - Cost: remaining ~$33
   - Total: ~$40

**Benefits:**
- ✅ Spread costs over time
- ✅ Test quality before committing
- ✅ Stay under daily API limits
- ✅ Can stop if you have enough coverage

---

### **Option 2: BATCH INGESTION (Faster)**

Process 50-100 documents per batch:

```bash
# Batch 1 (50 docs)
python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --limit 50 \
  --export-metadata outputs/Batch_1_Metadata.xlsx

# Review, approve, ingest
# Wait 1 hour (rate limits)

# Batch 2 (next 50)
# etc.
```

**Total time:** 4-6 hours spread over 2 days
**Cost:** ~$40

---

### **Option 3: SELECTIVE INGESTION (Smart)**

Don't ingest everything! Prioritize:

1. **WAC documents** (Washington Administrative Code) - ~150 docs
2. **RCW documents** (Revised Code of Washington) - ~100 docs
3. **Recent determinations** (case law) - ~50 docs
4. **Industry guides** (software, SaaS, etc.) - ~20 docs

**Total:** ~320 documents instead of 783
**Cost:** ~$16 instead of $40
**Quality:** Likely better (less noise)

---

## 🎯 MY RECOMMENDATION

### **Start with TOP 100 Documents**

Let me help you identify the most relevant 100 documents first:

```bash
# Find all WAC and RCW files (highest priority)
find "WA Tax Law" -name "WAC*.pdf" -o -name "RCW*.pdf"

# Find software/SaaS related
find "WA Tax Law" -name "*software*" -o -name "*SaaS*" -o -name "*digital*"

# Find exemption guides
find "WA Tax Law" -name "*exemption*" -o -name "*refund*"
```

**Process these 100 first:**
- Cost: ~$5.10
- Time: 2-3 hours
- Chunks: ~2,000

**Then test RAG quality** with chatbot before deciding whether to ingest more.

---

## 📋 SAFETY CHECKS BEFORE STARTING

Let me run these checks:

1. ✅ **Check OpenAI API limits**
2. ✅ **Check Supabase storage available**
3. ✅ **Estimate API costs accurately**
4. ✅ **Test with 5 documents first**
5. ✅ **Monitor costs in real-time**

---

## 🚀 PROPOSED NEXT STEPS

**RIGHT NOW:**

1. I'll find the top 100 most relevant PDFs
2. Export metadata for review (~5 min)
3. You approve which ones to ingest
4. We ingest in batches of 20-30 (rate limit friendly)
5. Total cost: ~$5-10 for 100 docs
6. Build chatbot to test quality

**Sound good?**

Want me to proceed with finding the top 100 most relevant documents?
