# Run Invoice Analysis

This is the CORE command of the entire system. It takes an Excel file of invoices/transactions and analyzes each row to determine tax exemption eligibility using AI + RAG against Washington state tax law.

## What It Does (The Business Logic)

1. **Reads Excel file** with invoice data (vendor, description, amount, tax paid)
2. **For each row**, the system:
   - Looks up vendor in the knowledge base (what do they sell?)
   - Searches tax law documents (RCW 82, WAC 458) for exemption rules
   - Uses AI to determine: Is this taxable? What exemption applies? What's the legal basis?
3. **Writes results** back to OUTPUT columns in the Excel file
4. **Skips unchanged rows** using hash-based change detection (smart caching)

## How It Fits In The System

```
[Excel File]
    |
    v
/04-analyze
    |
    +--> [Vendor Lookup] --> vendor_products table in Supabase
    |
    +--> [RAG Search] --> tax_law_chunks table (RCW/WAC embeddings)
    |
    +--> [AI Analysis] --> OpenAI API
    |
    v
[Excel File with AI OUTPUT columns populated]
```

## The Columns

**INPUT (you provide):**
- Vendor Name, Description, Invoice Amount, Tax Amount, Invoice Date, GL Account

**OUTPUT (AI fills in):**
- AI Taxability (Taxable/Exempt/Review)
- AI Confidence (0-100%)
- AI Exemption Type (e.g., "Manufacturing M&E")
- AI Refund Basis (legal citation)
- AI Citations (WAC/RCW references)

## Arguments

$ARGUMENTS (required: Excel file path)
- `--limit N` → Only analyze first N rows (for testing)
- `--dry-run` → Preview without writing to file
- `--force-reanalyze` → Ignore cache, re-analyze everything

## Examples

```bash
/04-analyze test_data/Master_Claim_Sheet.xlsx                    # Full analysis
/04-analyze "Master Refunds.xlsx" --limit 10                     # Test with 10 rows
/04-analyze "Master Refunds.xlsx" --dry-run                      # Preview only
/04-analyze "Master Refunds.xlsx" --force-reanalyze              # Ignore cache
```

## Success Looks Like

```
Loading Excel file: Master_Claim_Sheet.xlsx
Found 1,247 rows, 892 need analysis (355 unchanged)
Processing batch 1/45...
  Row 1: MICROSOFT CORP - "Azure Services" → Exempt (Digital Products) - 94% confidence
  Row 2: HOME DEPOT - "Lumber" → Taxable - 98% confidence
  ...
Analysis complete. Updated 892 rows.
Output saved to: Master_Claim_Sheet_analyzed.xlsx
```

## Common Failures

- "Cannot connect to Supabase" → Check `.env` has correct `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- "OpenAI rate limit" → Wait a few minutes, or reduce batch size
- "Column not found" → Run `/13-validate-excel` to check file format
- Slow performance → First run is slow (building caches). Subsequent runs faster.

## Prerequisites

- Docker services running (`/01-docker-up`)
- Valid `.env` with API keys
- Excel file with required INPUT columns

```bash
python analysis/fast_batch_analyzer.py --excel $ARGUMENTS --state washington
```
