# Validate Excel File Format

Checks that an Excel file has the correct columns and data types before running analysis. Use this BEFORE `/04-analyze` to catch format issues early.

## What It Checks

**Required INPUT columns** (you provide data):
- Vendor Name
- Description
- Invoice Amount
- Tax Amount
- Invoice Date

**Required OUTPUT columns** (AI fills in):
- AI Taxability
- AI Confidence
- AI Exemption Type
- AI Refund Basis
- AI Citations

## How It Fits In The System

```
[New Excel file from client]
        |
        v
    /13-validate-excel
        |
        +-- Missing columns? --> Fix file first
        |
        +-- All good? --> /04-analyze
```

Prevents wasted time running analysis on malformed files.

## Arguments

$ARGUMENTS (required)
- Path to Excel file to validate

## Examples

```bash
/13-validate-excel Master_Refunds.xlsx
/13-validate-excel "client_data/2024 Claims.xlsx"
```

## Success Looks Like

```
File: Master_Refunds.xlsx
Rows: 1,247
Columns: 18

=== INPUT Columns ===
  Vendor Name: ✓
  Description: ✓
  Invoice Amount: ✓
  Tax Amount: ✓
  Invoice Date: ✓

=== OUTPUT Columns ===
  AI Taxability: ✓
  AI Confidence: ✓
  AI Exemption Type: ✓
  AI Refund Basis: ✓
  AI Citations: ✓

=== All Columns ===
  1. Invoice Number
  2. Vendor Name
  3. Description
  ...
```

## Red Flags

- `Vendor Name: ✗ MISSING` → Add column or rename existing column
- `AI Taxability: ✗ MISSING` → Need to add OUTPUT columns to file
- `Rows: 0` → File is empty or wrong sheet selected

## Common Issues

- Column name slightly different (e.g., "Vendor" instead of "Vendor Name") → Validation uses fuzzy matching, but exact names are better
- OUTPUT columns missing → These can be created by analysis, but better to have them pre-defined
- Wrong file format → Must be .xlsx (not .xls or .csv)

## When To Run

- When you receive a new Excel file from a client
- Before running analysis on unfamiliar data
- When analysis fails with "column not found" error

```bash
python -c "
import sys
import pandas as pd
from pathlib import Path

file_path = '$ARGUMENTS'
if not file_path:
    print('ERROR: Please provide an Excel file path')
    print('Usage: /13-validate-excel path/to/file.xlsx')
    sys.exit(1)

if not Path(file_path).exists():
    print(f'ERROR: File not found: {file_path}')
    sys.exit(1)

df = pd.read_excel(file_path)
print(f'File: {file_path}')
print(f'Rows: {len(df)}')
print(f'Columns: {len(df.columns)}')
print()

# Required INPUT columns
input_cols = ['Vendor Name', 'Description', 'Invoice Amount', 'Tax Amount', 'Invoice Date']
# Required OUTPUT columns
output_cols = ['AI Taxability', 'AI Confidence', 'AI Exemption Type', 'AI Refund Basis', 'AI Citations']

print('=== INPUT Columns ===')
for col in input_cols:
    matches = [c for c in df.columns if col.lower() in c.lower()]
    status = '✓' if matches else '✗ MISSING'
    print(f'  {col}: {status}')

print()
print('=== OUTPUT Columns ===')
for col in output_cols:
    matches = [c for c in df.columns if col.lower() in c.lower()]
    status = '✓' if matches else '✗ MISSING'
    print(f'  {col}: {status}')

print()
print('=== All Columns ===')
for i, col in enumerate(df.columns, 1):
    print(f'  {i}. {col}')
"
```
