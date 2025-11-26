# Batch Research All Vendors

Runs AI research on all vendors that haven't been researched yet. This is the batch version of `/18-research-vendor` - use it to build out the vendor knowledge base.

## What It Does

1. Queries vendor_products table for vendors with `researched = false`
2. For each vendor, uses AI to research and classify
3. Updates database with findings
4. Skips already-researched vendors (safe to re-run)

## How It Fits In The System

```
[465 vendors from client data]
        |
        v
    /19-research-vendors
        |
        +--> Batch 1: Vendors 1-30
        |    +--> MICROSOFT → researched
        |    +--> AMAZON → researched
        |    +--> ...
        |
        +--> Batch 2: Vendors 31-60
        |    +--> ...
        |
        v (30-60 minutes later)
    [All vendors enriched with tax classification]
        |
        v
    /04-analyze has full vendor context
```

## Arguments

$ARGUMENTS (optional)
- `--batch-size N` - How many per batch (default: 30)
- `--start-from N` - Resume from specific index
- `--dry-run` - Preview without making changes

## Examples

```bash
/19-research-vendors                      # Research all unresearched (typical)
/19-research-vendors --batch-size 50      # Larger batches
/19-research-vendors --start-from 100     # Resume from vendor #100
/19-research-vendors --dry-run            # Preview what would be researched
```

## Success Looks Like

```
Finding unresearched vendors...
Found 287 vendors needing research

Starting batch research...

Batch 1/10 (vendors 1-30):
  ✓ MICROSOFT CORPORATION → Technology / Digital Products
  ✓ AMAZON WEB SERVICES → Cloud Services / Digital Products
  ✓ HOME DEPOT → Retail / Building Materials
  ...
  Batch complete. 30 vendors processed.

Batch 2/10 (vendors 31-60):
  ✓ GRAINGER → Industrial Supply / M&E
  ...

[Progress continues...]

Research complete.
  Total processed: 287
  Successful: 284
  Errors: 3 (see errors.log)
  Time elapsed: 47 minutes
```

## Runtime

- ~30 seconds per vendor (API calls + processing)
- 100 vendors ≈ 50 minutes
- 500 vendors ≈ 4 hours
- Can be stopped and resumed with `--start-from`

## Rate Limiting

OpenAI API has rate limits. The script:
- Automatically pauses between batches
- Retries on rate limit errors
- Saves progress so you can resume

## When To Run

- Initial setup (research all client vendors)
- After importing new vendor list
- Periodically to catch new vendors

```bash
python scripts/ai_training/research_all_vendors.py --resume $ARGUMENTS
```
