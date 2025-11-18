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
   # Check if .env exists
   ls -la .env

   # If not, create it with these credentials:
   cat > .env << 'EOF'
SUPABASE_URL=https://yzycrptfkxszeutvhuhm.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl6eWNycHRma3hzemV1dHZodWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzNzY3NjYsImV4cCI6MjA3Nzk1Mjc2Nn0.3qLB6dkuMZg77UmU9keACfO_U00i88iqmVAVlojgUts
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl6eWNycHRma3hzemV1dHZodWhtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjM3Njc2NiwiZXhwIjoyMDc3OTUyNzY2fQ.4tC4uy2mI2Ps66XBu8Q-_lahyHQA3eFD8zeDFqYjV0Y
SUPABASE_ACCESS_TOKEN=sbp_aedcc714d160a73484dcedc0bdc388eb9602e7f1
SUPABASE_DB_HOST=db.yzycrptfkxszeutvhuhm.supabase.co
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=Rawdog#456
SUPABASE_DB_NAME=postgres
SUPABASE_DB_PORT=5432
EOF
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
