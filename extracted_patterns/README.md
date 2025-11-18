# Historical Pattern Data

This folder contains extracted historical patterns from 116,310 analyzed tax records (2020 Denodo data).

## Files

- **vendor_patterns.json** - 294 vendors with historical refund success rates
- **keyword_patterns.json** - 0 keyword patterns (description column not usable in this dataset)
- **citation_patterns.json** - 9 refund basis citation patterns

## Data Summary

### Top Vendors (100% Success Rate)
- ALLNET LABS LLC (12 cases)
- COMPETITIVE MEDIA REPORTING LLC (12 cases)
- FIREEYE INC (10 cases)
- KRONOS INCORPORATED (8 cases)
- And 290 more vendors...

### Citation Patterns
- 9 different refund bases identified from historical data

## How to Import

### On Your Personal Laptop (where you have .env credentials):

1. **Copy this folder** to your personal laptop

2. **Make sure .env file exists** with Supabase credentials:
   ```bash
   SUPABASE_URL=https://bvrvzjqscrthfldyfqyo.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-key-here
   SUPABASE_DB_PASSWORD=your-password-here
   ```

3. **Deploy database schema** (if not already done):
   ```bash
   bash scripts/deploy_historical_knowledge_schema.sh
   ```

4. **Import the patterns**:
   ```bash
   python scripts/import_patterns_from_json.py --dir extracted_patterns
   ```

5. **Test it works**:
   ```bash
   python analysis/analyze_refunds.py --input test.xlsx --output results.xlsx
   ```

The analysis will now include:
- Historical vendor match data
- Success rate predictions
- 6 new columns in Excel output with historical context

## What This Enables

Once imported, the refund analysis AI will:
- Recognize 294 vendors with known success rates
- Boost confidence from ~65% → ~95% for known vendors
- Pre-populate refund basis suggestions
- Show historical precedent in Excel output

## Next Steps

After importing this data, consider:
1. Extract patterns from other completed Excel files (2018, 2021, 2022, 2023)
2. Merge all patterns for comprehensive coverage
3. Regular updates as new decisions are made

---

Generated: 2025-11-18
Source: 2020 Records in Denodo not in Master_8-28-23_COMPLETED.xlsx
