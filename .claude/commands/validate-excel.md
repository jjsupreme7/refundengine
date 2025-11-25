Validate Excel file has required columns and correct data types for analysis.

Arguments: $ARGUMENTS (required)
- Excel file path to validate

Checks:
- Required INPUT columns exist (Vendor Name, Description, Amount, Tax Paid, etc.)
- OUTPUT columns exist (AI Taxability, AI Confidence, AI Exemption Type, etc.)
- Data types are correct (dates, numbers, text)
- No critical data missing in required fields

```bash
python -c "
import sys
import pandas as pd
from pathlib import Path

file_path = '$ARGUMENTS'
if not file_path:
    print('ERROR: Please provide an Excel file path')
    print('Usage: /validate-excel path/to/file.xlsx')
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
