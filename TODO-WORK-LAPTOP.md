# 🚨 TO-DO ON WORK LAPTOP

## Import Historical Data to Supabase

**What:** Load historical refund data into the database so the AI learns from past analyses

**When:** Next time you're on your work laptop

**Steps:**

1. **Navigate to project:**
   ```bash
   cd /path/to/refund-engine
   ```

2. **Find your historical Excel file** (likely named):
   - Master Refunds.xlsx
   - Historical Refunds.xlsx
   - Or any Excel with past refund analyses

3. **Run dry-run first** (to preview what will be imported):
   ```bash
   python scripts/import_historical_knowledge.py --file "path/to/your/file.xlsx" --dry-run
   ```

4. **Review the output** - it will show what data it found

5. **Actually import** (if dry-run looks good):
   ```bash
   python scripts/import_historical_knowledge.py --file "path/to/your/file.xlsx"
   ```

6. **Verify import worked:**
   - Check the output for success messages
   - Should see counts of vendors and patterns imported

## What This Does:

- Extracts vendor patterns from your historical data
- Extracts product keyword patterns
- Loads them into Supabase
- Makes future AI analyses smarter (higher confidence for known vendors)
- Adds 6 historical columns to Excel output

## Status:

- ✅ Supabase schema deployed (tables created)
- ✅ Import script ready
- ❌ **Need to run import on work laptop**

---

**After import:** System will automatically use historical data for all future analyses.
