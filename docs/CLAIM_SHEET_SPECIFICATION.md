# Refund Engine Claim Sheet Specification

## Overview
The Claim Sheet is a master Excel file that tracks all invoices and purchase orders being analyzed for tax refund opportunities. Each row represents a line item from an invoice that needs analysis.

## File Naming Convention
- **Master File**: `Refund_Claim_Sheet_[ClientName]_[Date].xlsx`
- **Example**: `Refund_Claim_Sheet_Acme_Corp_2025-01-15.xlsx`

## Excel Column Structure

### 1. IDENTIFICATION COLUMNS

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Vendor_Number` | Text | Unique vendor identifier | `V-12345` |
| `Vendor_Name` | Text | Name of the vendor/supplier | `Microsoft Corporation` |
| `Invoice_Number` | Text | Invoice number | `INV-2024-0001` |
| `PO_Number` | Text | Purchase order number (may be blank) | `PO-49038` |
| `Line_Item_Number` | Integer | Line item number within invoice | `1`, `2`, `3` |

### 2. FINANCIAL COLUMNS

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Tax_Remitted` | Currency | Total tax charged on this line item | `$850.00` |
| `Tax_Percentage_Charged` | Percentage | Tax rate that was applied | `10.5%` |
| `Line_Item_Amount` | Currency | Pre-tax amount for this line item | `$8,095.24` |
| `Total_Amount` | Currency | Line item amount + tax | `$8,945.24` |

### 3. DOCUMENT FILE REFERENCES

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Invoice_Files` | Text (comma-separated) | PDF filename(s) for invoice | `0001.pdf` |
| `PO_Files` | Text (comma-separated) | PDF filename(s) for purchase orders | `PO_49038_ADVANTAGE_ENGINEERS.pdf, PO_49038_Amendment_1.pdf` |

**Important**: Multiple files should be separated by commas. The system will match filenames to documents in the upload folder.

### 4. ANALYSIS OUTPUT COLUMNS (AUTO-POPULATED)

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Final_Decision` | Text | Final refund decision | `Add to Claim - Refund Sample` or specific tax category |
| `Tax_Category` | Text | Classification of the tax issue | See Tax Category Values below |
| `Additional_Info` | Text | Subcategory or additional classification | See Additional Info Values below |
| `Refund_Basis` | Text | Legal basis for the refund | See Refund Basis Values below |
| `Estimated_Refund` | Currency | Calculated refund amount | `$850.00` |
| `Refund_Percentage` | Percentage | Percentage of tax being refunded | `100%` or `50%` |
| `Legal_Citation` | Text | RCW/WAC reference | `RCW 82.08.02565, WAC 458-20-15502` |
| `AI_Confidence` | Percentage | Confidence score of AI analysis | `92%` |
| `Analysis_Notes` | Text | Detailed explanation | `Digital automated service with MPU analysis showing <10% WA usage` |
| `Reviewed_By` | Text | Name of human reviewer | `John Smith` |
| `Review_Date` | Date | Date of human review | `2025-01-15` |
| `Review_Status` | Text | Status of review | `Pending Review`, `Approved`, `Corrected`, `Rejected` |

### 5. METADATA COLUMNS

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Invoice_Date` | Date | Date on the invoice | `2024-09-15` |
| `Transaction_Date` | Date | Date of the transaction | `2024-09-10` |
| `Cost_Center` | Text | Business unit or location | `CC-1234 - Seattle Office` |
| `GL_Account` | Text | General ledger account code | `5200-Software Licenses` |
| `Product_Description` | Text | Description from invoice line item | `Microsoft 365 Business Premium - Annual Subscription` |

---

## CONTROLLED VOCABULARY

### Tax Category Values
Used when `Final_Decision` involves a specific tax category (items > $20,000):

- `Custom Software`
- `DAS` (Digitally Automated Service)
- `DAS/License` (hybrid)
- `Digital Goods`
- `Hardware Support`
- `License`
- `Services`
- `Services/Tangible Goods` (mixed)
- `Software Maintenance`
- `Software Support`
- `Tangible Goods`

### Additional Info Values
Provides subcategory or context for the transaction:

- `Advertising`
- `Building Permit`
- `City Permit`
- `Cleaning`
- `Construction`
- `Credit Card Processing Fee`
- `Data Processing`
- `Decommissioning`
- `Dining`
- `Discount Codes`
- `Disposal`
- `Food`
- `Freight`
- `Gift Certificates`
- `Help Desk`
- `Hosting`
- `Inspection`
- `Installation`
- `Internet Access`
- `Janitorial`
- `Landscaping`
- `Membership Dues`
- `Moving Permit`
- `Postage`
- `Professional` (professional services)
- `Public Relations`
- `Recycling`
- `Repair`
- `Sign Installation`
- `Software Development/Configuration`
- `Storage`
- `Telecommunications`
- `Testing`
- `IT Reimbursement`
- `Warehousing`
- `Website Development`
- `Website Hosting`

### Refund Basis Values
Legal/tax reason for the refund claim:

- `MPU` (Multiple Points of Use - multi-state usage with <10% in WA)
- `Non-Taxable`
- `Non-Taxable - Services in Respect to Construction`
- `Non-Taxable/Out of State/Partial Out of State` (combined basis)
- `Out of State - Services`
- `Out of State - Shipment`
- `Partial Out-of-State Services`
- `Partial Out-of-State Shipment`
- `Resale`
- `Wrong Rate`

---

## Decision Rules

### Items < $20,000
**Decision**: `Add to Claim - Refund Sample`
- These are automatically added to the refund claim without detailed categorization
- Still require Legal Citation and Refund Basis

### Items >= $20,000
**Decision**: Must specify exact Tax Category (e.g., `DAS`, `Custom Software`, `Services`)
- Requires detailed analysis due to high dollar value
- Must have strong Legal Citation
- Requires higher AI Confidence (typically >85%)

---

## Workflow

### 1. Initial Upload
User uploads Excel file with columns 1-5 (Identification + Financial + Document Files) populated.

### 2. Document Matching
System matches `Invoice_Files` and `PO_Files` to actual PDFs in the upload folder:
- Files are matched by exact filename
- Multiple files per row are supported (comma-separated)
- Warning if files cannot be found

### 3. AI Analysis
For each row, the system:
1. Extracts line item text from invoice PDF
2. Queries tax law knowledge base (OLD LAW only for historical invoices)
3. Analyzes vendor background (if available)
4. Determines tax category, refund basis, and legal citation
5. Calculates estimated refund
6. Assigns confidence score

### 4. Human Review
Reviewer:
1. Reviews AI analysis in Analysis Output columns
2. Marks `Review_Status` as Approved/Corrected/Rejected
3. If Corrected, provides corrections in dedicated columns
4. Signs off with name and date

### 5. Learning Feedback Loop
Corrections feed back into the vendor learning system to improve future analyses.

---

## File Update Detection

The system monitors the master Excel file for changes:

### Auto-Detection Features
1. **File Watcher**: Monitors the Excel file for modifications
2. **Timestamp Tracking**: Stores last processed timestamp per file
3. **Row-Level Changes**: Detects which rows have been added/modified
4. **Incremental Processing**: Only processes new or changed rows

### Update Triggers
- New rows added to Excel
- Changes to document file references
- Manual correction of AI analysis
- Review status changes

### Implementation
Database table tracks:
- `file_path`: Path to Excel file
- `last_modified`: Timestamp of last file modification
- `last_processed`: Timestamp of last processing
- `row_hash`: Hash of each row to detect changes
- `processing_status`: Status of each row

---

## Example Row

| Column | Value |
|--------|-------|
| Vendor_Number | `V-10234` |
| Vendor_Name | `Microsoft Corporation` |
| Invoice_Number | `INV-2024-08-1234` |
| PO_Number | `PO-49038` |
| Line_Item_Number | `1` |
| Tax_Remitted | `$945.00` |
| Tax_Percentage_Charged | `10.5%` |
| Line_Item_Amount | `$9,000.00` |
| Total_Amount | `$9,945.00` |
| Invoice_Files | `0001.pdf` |
| PO_Files | `PO_49038_MICROSOFT.pdf` |
| **Final_Decision** | `Add to Claim - Refund Sample` |
| **Tax_Category** | `DAS` |
| **Additional_Info** | `Software Development/Configuration` |
| **Refund_Basis** | `MPU` |
| **Estimated_Refund** | `$945.00` |
| **Refund_Percentage** | `100%` |
| **Legal_Citation** | `WAC 458-20-15502` |
| **AI_Confidence** | `88%` |
| **Analysis_Notes** | `Microsoft 365 subscription is a digitally automated service. Client has employees in multiple states with less than 10% located in Washington, qualifying for MPU exemption.` |
| **Review_Status** | `Pending Review` |
| Invoice_Date | `2024-08-15` |
| Transaction_Date | `2024-08-01` |
| Product_Description | `Microsoft 365 Business Premium - Annual Subscription` |

---

## File Storage Structure

```
/refund-engine/
├── claim_sheets/
│   ├── Refund_Claim_Sheet_Acme_Corp_2025-01-15.xlsx  (Master file)
│   └── archive/
│       └── Refund_Claim_Sheet_Acme_Corp_2025-01-14.xlsx  (Previous versions)
├── uploads/
│   ├── invoices/
│   │   ├── 0001.pdf
│   │   ├── 0002.pdf
│   │   └── ...
│   └── purchase_orders/
│       ├── PO_49038_MICROSOFT.pdf
│       ├── PO_49039_SALESFORCE.pdf
│       └── ...
└── outputs/
    ├── Refund_Analysis_Results_2025-01-15.xlsx  (AI analysis output)
    └── Refund_Summary_Report_2025-01-15.pdf  (Summary report)
```

---

## Notes

1. **Old Law vs New Law**: For historical invoices (pre-October 1, 2025), the system MUST use OLD LAW only.
2. **File Matching**: The system will look for invoice/PO files in both `uploads/invoices/` and `uploads/purchase_orders/` folders.
3. **Multiple Files**: When multiple files exist for one line item (e.g., PO amendments), list all files separated by commas.
4. **Confidence Threshold**: Items with AI_Confidence < 70% should be flagged for mandatory human review.
5. **Vendor Learning**: The system learns from corrections and will improve accuracy for repeat vendors over time.
