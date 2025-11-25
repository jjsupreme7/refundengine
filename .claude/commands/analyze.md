Run smart batch analysis on an Excel claim sheet. Only re-analyzes modified rows using database-backed change tracking.

Arguments: $ARGUMENTS
- Required: Excel file path (e.g., "test_data/Master_Claim_Sheet.xlsx")
- Optional flags: --limit N (test mode), --dry-run (preview only)

Examples:
- /analyze test_data/Master_Claim_Sheet.xlsx
- /analyze "Master Refunds.xlsx" --limit 10
- /analyze "Master Refunds.xlsx" --dry-run

```bash
python analysis/fast_batch_analyzer.py --excel $ARGUMENTS --state washington
```
