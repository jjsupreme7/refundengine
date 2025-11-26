# Import Analyst Corrections

Imports human-reviewed corrections from an Excel file to improve the AI's future performance. This is how the system learns from analyst feedback.

## The Learning Loop

```
[AI analyzes invoices]
        |
        v
[Analyst reviews, corrects mistakes]
        |
        v
    /17-import-corrections
        |
        v
[System learns patterns]
        |
        v
[AI makes fewer mistakes next time]
```

## What It Imports

When an analyst reviews AI output and makes corrections:

| AI Said | Analyst Corrected | System Learns |
|---------|-------------------|---------------|
| Taxable | Exempt (M&E) | "This vendor's products are M&E exempt" |
| 60% confidence | 95% confidence | "Similar transactions are clear-cut" |
| Wrong citation | Correct WAC | "Use WAC 458-20-13601 for this category" |

## How It Fits In The System

```
[Master_Refunds_Reviewed.xlsx]
    |
    | Contains:
    | - Original AI columns
    | - Analyst override columns
    | - Final decision columns
    |
    v
/17-import-corrections
    |
    +--> Extract corrections where Analyst != AI
    |
    +--> Update vendor_patterns table
    |
    +--> Update refund_basis_patterns table
    |
    v
[Next analysis run uses learned patterns]
```

## Arguments

$ARGUMENTS (required)
- Excel file path with reviewed data
- `--reviewer <name>` - Who reviewed (for audit trail)

## Examples

```bash
/17-import-corrections "Master_Refunds_Reviewed.xlsx"
/17-import-corrections "Master_Refunds_Reviewed.xlsx" --reviewer "john_smith"
```

## Success Looks Like

```
Loading Master_Refunds_Reviewed.xlsx...
Found 1,247 rows

Analyzing corrections...
  - 1,180 rows: AI correct (no changes)
  - 52 rows: Analyst corrected taxability
  - 15 rows: Analyst corrected exemption type

Importing 67 corrections...
  ✓ Updated vendor pattern: MICROSOFT CORP → Digital Products Exempt
  ✓ Updated vendor pattern: GRAINGER → M&E Exempt
  ✓ Added refund basis: "Manufacturing consumables" → WAC 458-20-13601
  ...

Import complete. 67 corrections learned.
```

## Required Excel Columns

The reviewed file should have:
- Original AI OUTPUT columns (AI Taxability, AI Exemption Type, etc.)
- Analyst columns (Final Taxability, Final Exemption Type, etc.)
- Or override indicators showing where analyst disagreed

## When To Use

- After analyst completes review of a batch
- Periodically to incorporate accumulated feedback
- Before reprocessing similar transaction types

```bash
python analysis/import_corrections.py --excel $ARGUMENTS
```
