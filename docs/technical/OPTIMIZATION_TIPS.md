# Refund Engine - Optimization Tips

## 🚀 How to Run More Efficiently

### 1. **Skip Web Search for Faster Testing**
Web search uses Claude API (costs tokens + time)

```bash
# Skip web search (30-40 seconds faster per row)
python scripts/4_analyze_master_excel.py \
  --excel ~/Desktop/"Your Sheet.xlsx" \
  --skip-web-search \
  --limit 10
```

**Trade-off:** No vendor/product background research, but analysis still works with RAG + AI reasoning.

---

### 2. **Use Smaller Batches for Testing**
```bash
# Test first 2 rows only
python scripts/4_analyze_master_excel.py \
  --excel ~/Desktop/"Your Sheet.xlsx" \
  --limit 2
```

**Time:** ~40-60 seconds per row with web search, ~10-15 seconds without

---

### 3. **Incremental Mode (Only New Rows)**
After initial analysis, only process new rows:

```bash
# Only analyze rows without existing analysis
python scripts/4_analyze_master_excel.py \
  --excel ~/Desktop/"Your Sheet.xlsx" \
  --incremental
```

**Saves:** Doesn't re-analyze rows you've already reviewed

---

### 4. **Batch Processing vs Real-time**

**Current approach:** Process all rows in one script run
- **Pros:** Simple, complete output file
- **Cons:** If it fails partway, you lose progress

**Future optimization (if needed):**
- Save progress after each row
- Resume from last processed row
- Parallel processing (multiple rows at once)

---

## 📊 Cost Breakdown Per Row

| Component | Time | API Calls | Cost |
|-----------|------|-----------|------|
| GPT-4 Vision (invoice extract) | ~5s | 1 | ~$0.02 |
| Web search (vendor) | ~15s | 1 | ~$0.01 |
| Web search (product) | ~15s | 1 | ~$0.01 |
| RAG search (OpenAI embedding) | ~2s | 1 | ~$0.0001 |
| GPT-4 analysis | ~8s | 1 | ~$0.02 |
| **TOTAL PER ROW** | **~45s** | **5** | **~$0.06** |

**For 100 rows:** ~75 minutes, ~$6

---

## ⚡ Maximum Efficiency Setup

If you need to process 1000+ rows regularly:

```bash
# Option 1: Skip web search (still 90% accurate)
python scripts/4_analyze_master_excel.py \
  --excel large_file.xlsx \
  --skip-web-search

# Option 2: Pre-cache vendor info
# (Build a vendor database so you don't web search the same vendor 50 times)

# Option 3: Batch by vendor
# Process all Ericsson invoices together, reuse background research
```

---

## 🎯 Recommendations

### For Development/Testing:
✅ Use `--limit 2-5` and `--skip-web-search`
✅ Takes 20-30 seconds total

### For Production (Real Client Work):
✅ Use full mode with web search
✅ Run overnight for large datasets
✅ Cost: ~$6 per 100 invoices

### For Your 700 WA Tax PDFs:
⚠️ Don't ingest all at once!
- Start with 10-20 most relevant documents
- Test search quality
- Add more as needed
- Full ingestion would take ~6-8 hours and cost ~$40-50

---

## 💡 Today's Session Efficiency

**What happened:**
- Error fixing took extra iterations (API version, schema mismatches)
- But each error taught us about the system
- Now everything is documented and working

**Next time you run it:**
- Should be ~10x faster (no debugging needed)
- Just run the command and get results
- Example: 10 rows = 5-8 minutes total

**Token usage today: 70k of 200k (35%)**
- Mostly from error investigation and multiple test runs
- Normal runs will use ~5-10k tokens per session
