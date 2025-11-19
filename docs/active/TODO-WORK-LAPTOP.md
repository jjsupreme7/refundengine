# 🚨 TO-DO ON WORK LAPTOP

## Import Historical Data to Supabase

**What:** Load historical refund data into the database so the AI learns from past analyses

**When:** Next time you're on your work laptop

**Steps:**

1. **Navigate to project:**
   ```bash
   cd /path/to/refund-engine
   git pull origin main
   ```

2. **Create .env file with Supabase credentials** (if not already there):
   ```bash
   # Copy the .env file from your personal laptop (DO NOT commit credentials to GitHub!)
   # Or manually create .env with the credentials from your password manager

   # The .env file should contain:
   # SUPABASE_URL=<your-url>
   # SUPABASE_ANON_KEY=<your-anon-key>
   # SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
   # SUPABASE_ACCESS_TOKEN=<your-access-token>
   # SUPABASE_DB_HOST=<your-db-host>
   # SUPABASE_DB_USER=postgres
   # SUPABASE_DB_PASSWORD=<your-db-password>
   # SUPABASE_DB_NAME=postgres
   # SUPABASE_DB_PORT=5432
   ```

3. **Find your historical Excel file** (likely named):
   - Master Refunds.xlsx
   - Historical Refunds.xlsx
   - Or any Excel with past refund analyses

4. **Run dry-run first** (to preview what will be imported):
   ```bash
   python scripts/import_historical_knowledge.py --file "path/to/your/file.xlsx" --dry-run
   ```

5. **Review the output** - it will show what data it found

6. **Actually import** (if dry-run looks good):
   ```bash
   python scripts/import_historical_knowledge.py --file "path/to/your/file.xlsx"
   ```

7. **Verify import worked:**
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
