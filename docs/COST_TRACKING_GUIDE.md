# 💰 Real-Time Cost Tracking - Setup Complete!

## ✅ What I Just Added

Your document ingestion script now has **real-time cost tracking** that will:

1. **Track every API call** (GPT-4 and embeddings)
2. **Show running totals** as you process documents
3. **Alert you at cost thresholds:**
   - ⚠️ $5.00
   - ⚠️ $10.00 ← **YOU WILL BE PROMPTED HERE**
   - ⚠️ $20.00
   - ⚠️ $30.00
   - ⚠️ $40.00

4. **Calculate projections** - "At this rate, 100 docs will cost $X"
5. **Save detailed logs** to `cost_logs/` folder
6. **Let you stop anytime** - When you hit $10, you can choose to continue or stop

---

## 🚀 How to Use It

### **Option 1: Process 10 Documents (Test)**

```bash
cd /Users/jacoballen/Desktop/refund-engine

python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --export-metadata outputs/Test_10_Docs.xlsx \
  --limit 10
```

**Expected cost:** ~$0.50
**Will show:** Real-time tracking as it processes

---

### **Option 2: Process 100 Documents**

```bash
python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --export-metadata outputs/Top_100_Docs.xlsx \
  --limit 100
```

**Expected cost:** ~$5.00
**What happens:**
- Processes documents
- At $5, shows alert but continues
- At end, shows full summary

---

### **Option 3: Process Until You Hit $10**

```bash
python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --export-metadata outputs/Batch_1.xlsx \
  --limit 200
```

**What happens:**
1. Starts processing
2. Shows progress: "Processed 50 docs... Cost: $2.50..."
3. At $5: Shows alert, continues
4. **At $10: STOPS and asks:**
   ```
   💰 COST ALERT: You've reached $10.00

   ⚠️  You've spent $10.00. Continue? [y/N]:
   ```
5. You choose:
   - Type `y` + Enter = Continue processing
   - Type `N` + Enter = Stop here

---

## 📊 What You'll See

### **During Processing:**

```
Analyzing PDFs: 45%|████▌     | 45/100 [02:15<02:45, 3.33it/s]
```

### **At $5 Threshold:**

```
======================================================================
💰 COST ALERT: You've reached $5.00
======================================================================

📊 COST SUMMARY - legal_doc_ingestion
======================================================================
⏱️  Time elapsed: 5m 23s
📄 Documents processed: 98
📦 Chunks created: 1,960

💰 API COSTS:
   GPT-4o:       $4.7520 (98 calls)
   Embeddings:   $0.2450 (1960 calls)

   🎯 TOTAL:      $5.00
======================================================================

📈 PROJECTION:
   Cost per document: $0.0510
   Estimated for 100 docs: $5.10
   Estimated for 783 docs: $39.93
======================================================================
```

### **At $10 (Will Prompt You):**

```
======================================================================
💰 COST ALERT: You've reached $10.00
======================================================================
[Same summary as above but with $10 total]

⚠️  You've spent $10.00. Continue? [y/N]:  _
```

You can type:
- `y` = Keep going
- `N` = Stop and save what you have so far

---

## 📁 Cost Logs

Every session creates a detailed JSON log:

**Location:** `cost_logs/legal_doc_ingestion_20250107_143022.json`

**Contains:**
```json
{
  "session_name": "legal_doc_ingestion",
  "start_time": "2025-01-07T14:30:22",
  "current_time": "2025-01-07T14:45:18",
  "costs": {
    "gpt-4o": 4.752,
    "embeddings": 0.245,
    "total": 5.00
  },
  "api_calls": {
    "gpt-4o": 98,
    "embeddings": 1960
  },
  "documents_processed": 98,
  "chunks_created": 1960
}
```

**Use this to:**
- Track spending across sessions
- Review what you've already processed
- Calculate ROI for clients

---

## 🎯 Recommended Workflow

### **Step 1: Test with 10 docs** (5-10 minutes)

```bash
python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --export-metadata outputs/Test_Batch.xlsx \
  --limit 10
```

**Cost:** ~$0.50
**Goal:** Verify everything works

---

### **Step 2: Process 100 docs** (30-40 minutes)

```bash
python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --export-metadata outputs/First_100.xlsx \
  --limit 100
```

**Cost:** ~$5.00
**Goal:** Build core knowledge base

---

### **Step 3: Review & Import**

1. Open `outputs/First_100.xlsx`
2. Review AI metadata
3. Mark status: Approved/Skip/Review
4. Import:

```bash
python scripts/2_ingest_legal_docs.py \
  --import-metadata outputs/First_100.xlsx
```

**This step uses embeddings** (cheaper):
- 100 docs × ~20 chunks = 2,000 embeddings
- Cost: ~$0.25
- **Total for 100 docs: $5.25**

---

### **Step 4: Test RAG Chatbot**

Build chatbot to test quality before processing more docs.

---

### **Step 5: Decide on More**

Based on RAG quality:
- Good enough? Stop at 100 docs
- Need more coverage? Process another 100-200
- Diminishing returns? You're done!

---

## 💡 Pro Tips

### **1. Process in Batches**

Don't try to do all 783 at once:
- Batch 1: 100 most relevant (WAC/RCW codes)
- Test chatbot quality
- Batch 2: 100 more if needed
- Repeat until satisfied

### **2. Use File Patterns**

Process specific types first:

```bash
# Only WAC codes
find "/Users/jacoballen/Desktop/WA Tax Law" -name "WAC*.pdf" | head -100 > wac_files.txt

# Only software/digital related
find "/Users/jacoballen/Desktop/WA Tax Law" -name "*software*" -o -name "*digital*"
```

### **3. Monitor Logs**

```bash
# See all sessions
ls -lh cost_logs/

# View latest session
cat cost_logs/legal_doc_ingestion_*.json | jq .
```

---

## 🛑 How to Stop at $10

**The script will automatically ask you** when you hit $10.

You'll see:
```
⚠️  You've spent $10.00. Continue? [y/N]:
```

Just press Enter (defaults to N) or type `N` to stop.

---

## ✅ You're All Set!

The cost tracker is now integrated into Script 2.

**Want to test it right now with 10 documents?**

Run this:
```bash
cd /Users/jacoballen/Desktop/refund-engine
python scripts/2_ingest_legal_docs.py \
  --folder "/Users/jacoballen/Desktop/WA Tax Law" \
  --export-metadata outputs/Cost_Test.xlsx \
  --limit 10
```

Cost: ~$0.50
Time: 5 minutes
Result: You'll see exactly how the cost tracking works!
