# Next Steps - Run on Personal Laptop

## What We Just Did

On your work laptop, we extracted historical patterns from 116,310 analyzed tax records and saved them to JSON files. These files are now in GitHub.

## What You Need to Do on Your Personal Laptop

### Step 1: Pull Latest Changes from GitHub

```bash
cd /path/to/refundengine
git pull
```

This will download:
- `extracted_patterns/` folder with 294 vendor patterns
- `scripts/import_patterns_from_json.py` - Import script
- All other integration code

### Step 2: Verify .env File Exists

Make sure your `.env` file has these variables:

```bash
# Check if .env exists
cat .env

# Should contain:
SUPABASE_URL=https://bvrvzjqscrthfldyfqyo.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-actual-key-here
SUPABASE_DB_HOST=aws-0-us-west-1.pooler.supabase.com
SUPABASE_DB_USER=postgres.bvrvzjqscrthfldyfqyo
SUPABASE_DB_PASSWORD=your-actual-password-here
SUPABASE_DB_NAME=postgres
SUPABASE_DB_PORT=6543
```

### Step 3: Deploy Database Schema (if not already done)

```bash
bash scripts/deploy_historical_knowledge_schema.sh
```

This creates:
- `keyword_patterns` table
- `refund_citations` table
- Adds `vendor_keywords[]` and `description_keywords[]` columns to `vendor_products`
- Creates GIN indexes for fast fuzzy matching

Expected output:
```
Historical Knowledge Schema Deployed Successfully!
Tables created/enhanced:
  - refund_citations (new)
  - keyword_patterns (new)
  - vendor_products (enhanced with vendor_keywords, description_keywords)
  - vendor_product_patterns (enhanced)
```

### Step 4: Import the Historical Patterns

```bash
python scripts/import_patterns_from_json.py --dir extracted_patterns
```

Expected output:
```
Connecting to Supabase...
✓ Connected successfully

======================================================================
IMPORTING HISTORICAL PATTERNS
======================================================================

Importing 294 vendor patterns...
  Imported: 294 new vendors
  Updated: 0 existing vendors

Importing 0 keyword patterns...
  (Skipped - no data)

Importing 9 citation patterns...
  Imported: 9 new citations
  Updated: 0 existing citations

======================================================================
IMPORT COMPLETE
======================================================================
Total records imported: 303
Total records updated: 0

Historical pattern learning is now active!
```

### Step 5: Test the System

Create a test file with a few vendor names from the historical data:

```bash
# Test with a sample invoice
python analysis/analyze_refunds.py \
  --input test_invoice.xlsx \
  --output test_results.xlsx
```

Look for these in the output:
- **Historical_Vendor_Match**: Should show "Exact" or "Fuzzy"
- **Historical_Vendor_Cases**: Number of historical cases
- **Historical_Vendor_Success_Rate**: Percentage like "100.0%"
- **Historical_Context_Summary**: Human-readable precedent

### Step 6: Verify Data in Supabase Dashboard

Go to your Supabase dashboard and run these queries:

```sql
-- Check vendor patterns imported
SELECT COUNT(*) FROM vendor_products WHERE historical_sample_count > 0;
-- Should return: 294

-- Check top vendors by success rate
SELECT vendor_name, historical_sample_count, historical_success_rate
FROM vendor_products
WHERE historical_success_rate >= 0.85
ORDER BY historical_success_rate DESC, historical_sample_count DESC
LIMIT 10;

-- Check keyword patterns
SELECT COUNT(*) FROM keyword_patterns;
-- Should return: 0 (2020 data didn't have good description column)

-- Check citation patterns
SELECT refund_basis, usage_count FROM refund_citations ORDER BY usage_count DESC;
-- Should return: 9 citation patterns
```

## What This Enables

Once imported, your refund analysis will:

✅ **Recognize 294 vendors** with historical refund precedent
✅ **Boost AI confidence** from ~65% → ~95% for known vendors
✅ **Fuzzy match vendor names** (e.g., "American Tower" matches "ATC TOWER SERVICES")
✅ **Pre-populate refund basis** suggestions from historical data
✅ **Show historical context** in 6 new Excel columns

## Example Output

### Before Historical Learning:
```
Analyzing invoice from FIREEYE INC...
AI Confidence: 65%
Citation: [searches knowledge base for 30 seconds]
```

### After Historical Learning:
```
Analyzing invoice from FIREEYE INC...

Historical Match Found:
- Vendor: FIREEYE INC (10 historical cases, 100% success rate)
- Typical Basis: Out-of-State Services

AI Confidence: 95% (boosted from historical precedent)
Citation: RCW 82.04.050 (pre-populated from pattern)
```

### Excel Output Columns Added:
1. **Historical_Vendor_Match**: "Exact"
2. **Historical_Vendor_Cases**: 10
3. **Historical_Vendor_Success_Rate**: "100.0%"
4. **Historical_Pattern_Match**: "Keyword Match"
5. **Historical_Pattern_Success_Rate**: "88.0%"
6. **Historical_Context_Summary**: "Historical precedent (exact match): Vendor 'FIREEYE INC' has 10 historical cases with 100% refund success rate. Typical basis: Out-of-State Services"

## Future Enhancements

### Extract More Historical Data

You can extract patterns from other completed files:

```bash
# On work laptop (no credentials needed):
python scripts/extract_patterns_to_json.py \
  --file "C:\Users\jacob\Desktop\Denodo&UseTax\2018 Records in Denodo not in Master_1-3-24_COMPLETED.xlsx" \
  --output-dir extracted_patterns_2018

# Transfer to personal laptop and import:
python scripts/import_patterns_from_json.py --dir extracted_patterns_2018
```

### Merge All Historical Data

To get comprehensive coverage, extract and import from:
- ✅ 2020 Records (DONE - 116K rows, 294 vendors)
- ⬜ 2018 Records (need xlrd package)
- ⬜ 2021 Records (93K rows, but vendor column is country code)
- ⬜ 2022 Records (127K rows, but vendor column is country code)
- ⬜ 2023 Records (need to check format)

## Troubleshooting

### Error: "No module named 'supabase'"
```bash
pip install supabase
```

### Error: "SUPABASE_DB_PASSWORD not set"
Check that `.env` file exists and contains credentials

### Error: "Table 'keyword_patterns' does not exist"
Run schema deployment script first:
```bash
bash scripts/deploy_historical_knowledge_schema.sh
```

### Import succeeds but no historical data showing
Check that historical_sample_count > 0:
```sql
SELECT COUNT(*) FROM vendor_products WHERE historical_sample_count > 0;
```

## Summary

**Work Laptop (DONE):**
- ✅ Extracted 294 vendor patterns from 116K analyzed records
- ✅ Created JSON export files
- ✅ Committed and pushed to GitHub

**Personal Laptop (TODO):**
1. Pull latest from GitHub
2. Deploy database schema (if needed)
3. Import JSON patterns to Supabase
4. Test with sample invoices
5. Verify historical columns appear in Excel output

**Total time to complete:** ~5 minutes

---

Generated: 2025-11-18
Commit: 5eece97
