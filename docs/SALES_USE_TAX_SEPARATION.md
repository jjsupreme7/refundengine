# Sales Tax vs Use Tax Separation Architecture

## Overview

Per Washington State tax law, **sales tax** and **use tax** are mutually exclusive and require separate refund claims. This document defines the architecture for separating transactions into two distinct Excel master sheets and processing workflows.

## Key Differences

### Sales Tax
- Tax collected by **vendor** at point of sale
- Vendor remits to Washington DOR
- Common on: Software licenses, tangible goods, taxable services
- **Refund claim**: Filed by purchaser to recover overpaid sales tax
- **Documentation**: Vendor invoices showing tax charged

### Use Tax
- Tax **self-assessed** by purchaser on untaxed purchases
- Purchaser remits to Washington DOR
- Common on: Out-of-state purchases, remote services, unreported items
- **Refund claim**: Filed by purchaser to recover overpaid use tax
- **Documentation**: Purchase orders, internal accruals, use tax returns

## Two-Sheet Architecture

### Master Sheet 1: Sales Tax Refunds
**File**: `Master_Sales_Tax_Claim_Sheet.xlsx`

**Detection Criteria**:
- `Tax_Remitted` > 0 (vendor collected and remitted tax)
- Invoice shows tax charged by vendor
- Vendor is typically in-state (WA) or has nexus
- Tax appears on vendor invoice line items

**Typical Refund Scenarios**:
- Exempt software maintenance incorrectly taxed
- Professional services incorrectly taxed
- MPU exemption not applied
- Out-of-state services incorrectly taxed
- Custom software incorrectly taxed
- Resale items incorrectly taxed

**Refund Basis Values** (Sales Tax Specific):
- Non-Taxable Service
- MPU (Multiple Points of Use)
- Out of State - Services
- Custom Software
- Professional Services
- Resale
- Wrong Rate

### Master Sheet 2: Use Tax Refunds
**File**: `Master_Use_Tax_Claim_Sheet.xlsx`

**Detection Criteria**:
- `Tax_Remitted` = 0 OR blank (no vendor tax collected)
- Tax self-assessed by purchaser
- Appears on use tax returns
- Internal accrual or estimation

**Typical Refund Scenarios**:
- Self-assessed tax on exempt software
- Use tax accrued but item was non-taxable
- Out-of-state purchase incorrectly accrued
- Digital goods incorrectly self-assessed

**Refund Basis Values** (Use Tax Specific):
- Non-Taxable Service
- Out of State - Shipment
- Digital Goods Exempt
- Software Maintenance Exempt
- Professional Services

## Detection Logic

### Auto-Classification Algorithm

```python
def classify_tax_type(transaction: Dict) -> str:
    """
    Classify transaction as 'sales_tax' or 'use_tax' based on transaction data.

    Returns:
        'sales_tax': Vendor collected and remitted tax
        'use_tax': Purchaser self-assessed tax
        'NEEDS_REVIEW': Cannot determine automatically
    """

    tax_remitted = transaction.get('Tax_Remitted', 0)
    tax_amount = transaction.get('Tax_Amount', 0)
    invoice_file = transaction.get('Invoice_File_Name_1', '')

    # SALES TAX: Vendor collected tax
    if tax_remitted > 0 and tax_amount > 0:
        return 'sales_tax'

    # USE TAX: No vendor tax, but tax amount recorded (self-assessed)
    if tax_remitted == 0 and tax_amount > 0:
        return 'use_tax'

    # NO TAX: No tax at all
    if tax_amount == 0:
        return 'NEEDS_REVIEW'  # Should not be in refund claim

    # EDGE CASE: Tax amount but unclear who remitted
    if tax_amount > 0 and (tax_remitted is None or tax_remitted == ''):
        # Analyze invoice PDF for clues
        if invoice_file:
            # Check if invoice shows tax line item (sales tax indicator)
            return 'ANALYZE_INVOICE'
        return 'NEEDS_REVIEW'

    return 'NEEDS_REVIEW'
```

### Enhanced Detection with Vendor Metadata

```python
def classify_with_vendor_context(transaction: Dict, vendor_metadata: Dict) -> str:
    """
    Enhanced classification using vendor background data.
    """

    basic_classification = classify_tax_type(transaction)

    if basic_classification in ['sales_tax', 'use_tax']:
        return basic_classification

    # Use vendor metadata for edge cases
    vendor_state = vendor_metadata.get('state', '')
    vendor_has_nexus = vendor_metadata.get('has_wa_nexus', False)

    # In-state vendor with tax amount = likely sales tax
    if vendor_state == 'WA' and transaction.get('Tax_Amount', 0) > 0:
        return 'sales_tax'

    # Out-of-state vendor with no nexus + tax amount = likely use tax
    if vendor_state != 'WA' and not vendor_has_nexus and transaction.get('Tax_Amount', 0) > 0:
        return 'use_tax'

    return 'NEEDS_REVIEW'
```

## Excel Sheet Structure

Both sheets have **identical column structure**, but different values in certain fields:

### Common INPUT Columns (Same for Both)
- Vendor_ID
- Vendor_Name
- Invoice_Number
- Purchase_Order_Number
- Total_Amount
- Tax_Amount
- **Tax_Remitted** (KEY DIFFERENTIATOR: >0 for sales tax, =0 for use tax)
- Tax_Rate_Charged
- Invoice_File_Name_1
- Invoice_File_Name_2

### Common OUTPUT Columns (Same for Both)
- Analysis_Notes
- Final_Decision
- Tax_Category
- Additional_Info
- **Refund_Basis** (Different values per tax type - see above)
- Estimated_Refund
- Legal_Citation
- AI_Confidence

### Additional Column: Tax_Type
**New Column Added to Both Sheets**:
- `Tax_Type`: "Sales Tax" or "Use Tax"
- Populated during classification
- Used for validation and reporting

## Workflow Integration

### Step 1: Upload Combined Excel
User uploads single Excel file with all transactions (sales + use mixed together).

### Step 2: Auto-Classification
```python
from analysis.tax_type_classifier import classify_transactions

# Read uploaded Excel
df = pd.read_excel('uploads/All_Transactions.xlsx')

# Classify each row
df['Tax_Type'] = df.apply(classify_tax_type, axis=1)

# Flag rows needing review
needs_review = df[df['Tax_Type'] == 'NEEDS_REVIEW']
print(f"⚠️  {len(needs_review)} transactions need manual classification")

# Split into two dataframes
sales_tax_df = df[df['Tax_Type'] == 'sales_tax']
use_tax_df = df[df['Tax_Type'] == 'use_tax']

# Write to separate sheets
sales_tax_df.to_excel('test_data/Master_Sales_Tax_Claim_Sheet.xlsx', index=False)
use_tax_df.to_excel('test_data/Master_Use_Tax_Claim_Sheet.xlsx', index=False)
```

### Step 3: Separate Analysis Pipelines
Each sheet gets analyzed with tax-type-specific logic:

**Sales Tax Analysis**:
- Focus on vendor invoices (Invoice_File_Name_1)
- Check if vendor should have collected tax
- Validate tax rate against location
- Look for exempt service indicators

**Use Tax Analysis**:
- Focus on internal records (Invoice_File_Name_2)
- Check if item should have been self-assessed
- Validate against use tax return filings
- Look for out-of-state shipment documentation

### Step 4: Separate Refund Packets
Generate two distinct claim packets:
- `Sales_Tax_Refund_Claim_Packet.pdf`
- `Use_Tax_Refund_Claim_Packet.pdf`

Each packet has:
- Cover letter (tax-type specific language)
- Schedule of transactions
- Legal citations
- Supporting documentation

## Database Schema Updates

### New Table: `tax_type_classifications`
```sql
CREATE TABLE tax_type_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id TEXT NOT NULL,
    vendor_id TEXT,
    tax_type TEXT CHECK(tax_type IN ('sales_tax', 'use_tax', 'NEEDS_REVIEW')),
    classification_method TEXT, -- 'auto', 'vendor_metadata', 'manual', 'ai_analysis'
    confidence_score FLOAT,
    tax_amount DECIMAL(10, 2),
    tax_remitted DECIMAL(10, 2),
    classification_notes TEXT,
    classified_by TEXT, -- 'system', 'analyst_name'
    classified_at TIMESTAMP DEFAULT NOW(),

    -- Foreign keys
    invoice_file_name TEXT,
    purchase_order_number TEXT,

    UNIQUE(transaction_id)
);

CREATE INDEX idx_tax_type ON tax_type_classifications(tax_type);
CREATE INDEX idx_classification_method ON tax_type_classifications(classification_method);
```

### Updated `analysis_results` Table
```sql
ALTER TABLE analysis_results
ADD COLUMN tax_type TEXT CHECK(tax_type IN ('sales_tax', 'use_tax')),
ADD COLUMN refund_basis TEXT,
ADD COLUMN master_sheet_name TEXT; -- Which Excel sheet this result belongs to

CREATE INDEX idx_analysis_tax_type ON analysis_results(tax_type);
```

## Anomaly Detection Adjustments

### Sales Tax Specific Anomalies
1. **In-State Vendor Charged Tax on Exempt Service** (High severity)
2. **Wrong Tax Rate for Location** (Medium severity)
3. **Tax on Professional Services** (High severity)
4. **Tax on Custom Software** (High severity)

### Use Tax Specific Anomalies
1. **Self-Assessed Tax on Out-of-State Services** (Medium severity)
2. **Use Tax on Digital Goods Post-2009** (High severity)
3. **Duplicate Tax (Sales + Use on Same Item)** (Critical severity)
4. **Missing Use Tax Accrual** (Informational - not a refund)

### Shared Anomalies
1. Odd dollar amounts
2. Construction retainage
3. High exempt ratios
4. Missing documentation

## Confidence Scoring Adjustments

### Sales Tax Confidence Boosters
- In-state vendor with clear invoice: +10
- Tax line item visible on invoice: +15
- Vendor known to collect tax properly: +10

### Sales Tax Confidence Reducers
- Out-of-state vendor with no nexus: -20 (might be use tax)
- No tax line on invoice but Tax_Remitted > 0: -30 (data inconsistency)

### Use Tax Confidence Boosters
- Out-of-state vendor with no nexus: +15
- Internal accrual documentation: +10
- Use tax return reference: +20

### Use Tax Confidence Reducers
- In-state vendor: -30 (likely sales tax)
- Tax visible on vendor invoice: -40 (definitely sales tax)

## Dashboard UI Updates

### Two Separate Claim Builder Workflows
- **Sales Tax Claim Builder**: Select sales tax master sheet
- **Use Tax Claim Builder**: Select use tax master sheet

### Classification Review Queue
New UI section for `NEEDS_REVIEW` transactions:
- Display transaction details
- Show classification clues (Tax_Remitted, vendor state, etc.)
- Allow analyst to manually classify as Sales or Use
- Capture reasoning for learning system

### Analytics Separation
Power BI dashboards show:
- Sales tax refunds: $X
- Use tax refunds: $Y
- Total refunds: $X + $Y
- Classification accuracy: % auto-classified correctly

## Learning System Integration

### Pattern: "Sales tax vs use tax confusion"
**When human corrects**:
- Transaction initially classified as sales tax
- Human reviews and changes to use tax
- **System learns**: What clues were missed?

**Example**:
```json
{
  "correction_id": "CORR-2024-0042",
  "original_classification": "sales_tax",
  "corrected_classification": "use_tax",
  "transaction_data": {
    "vendor_state": "CA",
    "tax_remitted": 0,
    "tax_amount": 523.50,
    "invoice_shows_tax": false
  },
  "analyst_explanation": "No tax on invoice, Tax_Remitted = 0, this was self-assessed by purchaser",
  "extracted_pattern": "CA vendor + Tax_Remitted = 0 + Tax_Amount > 0 = use_tax",
  "confidence_adjustment": {
    "rule": "Out-of-state vendor with no invoice tax = use_tax",
    "boost": +20
  }
}
```

### Pattern: "Out-of-state vendor edge cases"
**Challenge**: Some out-of-state vendors have WA nexus and collect sales tax
**Solution**: Vendor metadata enrichment + learning

```python
# After human correction
if vendor_state != 'WA' and corrected_to == 'sales_tax':
    # Update vendor metadata
    update_vendor_metadata(vendor_id, {'has_wa_nexus': True})
    # Log pattern
    log_learning_pattern(
        pattern_type='vendor_nexus_discovery',
        vendor=vendor_name,
        note='Out-of-state vendor collects WA sales tax - has nexus'
    )
```

## Implementation Scripts

### Script 1: `scripts/split_excel_by_tax_type.py`
```python
#!/usr/bin/env python3
"""
Split a combined Excel sheet into separate Sales Tax and Use Tax sheets.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

def classify_tax_type(row: pd.Series) -> str:
    """Classify a single row as sales_tax, use_tax, or NEEDS_REVIEW."""
    tax_remitted = row.get('Tax_Remitted', 0)
    tax_amount = row.get('Tax_Amount', 0)

    if pd.isna(tax_remitted):
        tax_remitted = 0
    if pd.isna(tax_amount):
        tax_amount = 0

    if tax_remitted > 0 and tax_amount > 0:
        return 'sales_tax'
    elif tax_remitted == 0 and tax_amount > 0:
        return 'use_tax'
    else:
        return 'NEEDS_REVIEW'

def split_excel_by_tax_type(input_file: str, output_dir: str = 'test_data') -> Tuple[str, str, str]:
    """
    Split combined Excel into Sales Tax and Use Tax sheets.

    Returns:
        (sales_tax_file, use_tax_file, needs_review_file)
    """
    df = pd.read_excel(input_file)

    # Classify each row
    df['Tax_Type'] = df.apply(classify_tax_type, axis=1)

    # Split
    sales_df = df[df['Tax_Type'] == 'sales_tax'].copy()
    use_df = df[df['Tax_Type'] == 'use_tax'].copy()
    needs_review_df = df[df['Tax_Type'] == 'NEEDS_REVIEW'].copy()

    # Write to separate files
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    sales_file = output_path / 'Master_Sales_Tax_Claim_Sheet.xlsx'
    use_file = output_path / 'Master_Use_Tax_Claim_Sheet.xlsx'
    review_file = output_path / 'Needs_Manual_Classification.xlsx'

    sales_df.to_excel(sales_file, index=False)
    use_df.to_excel(use_file, index=False)
    needs_review_df.to_excel(review_file, index=False)

    print(f"✅ Sales Tax: {len(sales_df)} transactions → {sales_file}")
    print(f"✅ Use Tax: {len(use_df)} transactions → {use_file}")
    print(f"⚠️  Needs Review: {len(needs_review_df)} transactions → {review_file}")

    return str(sales_file), str(use_file), str(review_file)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python split_excel_by_tax_type.py <input_excel_file>")
        sys.exit(1)

    split_excel_by_tax_type(sys.argv[1])
```

### Script 2: `scripts/analyze_sales_tax_sheet.py`
```python
#!/usr/bin/env python3
"""
Analyze SALES TAX master sheet and populate OUTPUT columns.
"""

import pandas as pd
from analysis.analyze_refunds_enhanced import analyze_invoice_enhanced
from core.law_version_handler import LawVersion

def analyze_sales_tax_sheet(excel_file: str, output_file: str):
    """
    Analyze sales tax transactions and populate OUTPUT columns.
    """
    df = pd.read_excel(excel_file)

    for idx, row in df.iterrows():
        print(f"Analyzing sales tax transaction {idx + 1}/{len(df)}: {row['Invoice_Number']}")

        # Analyze with OLD LAW (pre-Oct 2025)
        result = analyze_invoice_enhanced(
            invoice_file=row['Invoice_File_Name_1'],
            vendor_name=row['Vendor_Name'],
            law_version=LawVersion.OLD,
            tax_type='sales_tax'  # NEW PARAMETER
        )

        # Populate OUTPUT columns
        df.at[idx, 'Analysis_Notes'] = result['analysis_notes']
        df.at[idx, 'Final_Decision'] = result['final_decision']
        df.at[idx, 'Tax_Category'] = result['tax_category']
        df.at[idx, 'Additional_Info'] = result['additional_info']
        df.at[idx, 'Refund_Basis'] = result['refund_basis']
        df.at[idx, 'Estimated_Refund'] = result['estimated_refund']
        df.at[idx, 'Legal_Citation'] = result['legal_citation']
        df.at[idx, 'AI_Confidence'] = result['confidence_score']

    # Write back to Excel
    df.to_excel(output_file, index=False)
    print(f"✅ Sales tax analysis complete: {output_file}")

if __name__ == '__main__':
    analyze_sales_tax_sheet(
        'test_data/Master_Sales_Tax_Claim_Sheet.xlsx',
        'test_data/Master_Sales_Tax_Claim_Sheet_ANALYZED.xlsx'
    )
```

### Script 3: `scripts/analyze_use_tax_sheet.py`
Similar to above but with `tax_type='use_tax'` parameter.

## File Organization

```
test_data/
├── Master_Sales_Tax_Claim_Sheet.xlsx         # Sales tax refunds
├── Master_Use_Tax_Claim_Sheet.xlsx           # Use tax refunds
├── Needs_Manual_Classification.xlsx          # Needs human review
├── Master_Sales_Tax_Claim_Sheet_ANALYZED.xlsx  # After AI analysis
├── Master_Use_Tax_Claim_Sheet_ANALYZED.xlsx    # After AI analysis
└── refund_packets/
    ├── Sales_Tax_Refund_Packet.pdf
    └── Use_Tax_Refund_Packet.pdf
```

## Key Takeaways

1. **Tax_Remitted is the key differentiator**: >0 = sales tax, =0 = use tax
2. **Two completely separate workflows** after classification
3. **Different anomaly patterns** for each tax type
4. **Different refund basis values** appropriate to each type
5. **Learning system must capture** classification corrections
6. **Vendor metadata** helps resolve edge cases (nexus, state)
7. **Manual classification queue** for unclear cases ensures accuracy

## Next Steps

1. Update `analysis/analyze_refunds_enhanced.py` to accept `tax_type` parameter
2. Create `scripts/split_excel_by_tax_type.py`
3. Update anomaly detection to use tax-type-specific rules
4. Create separate claim packet generators
5. Update dashboard UI with tax type filter
6. Test with mixed sales/use tax dataset
