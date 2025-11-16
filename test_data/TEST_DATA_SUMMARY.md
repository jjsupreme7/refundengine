# Comprehensive Test Data Summary

## What Was Created

✅ **Master Excel File**: `Master_Claim_Sheet_Comprehensive.xlsx`
- **31 rows** (transaction line items)
- **12 invoices** (various formats)
- **5 purchase orders** (various formats)
- **5 vendors** across different scenarios
- **27 Sales Tax rows** + **4 Use Tax rows**

## Excel Structure

### INPUT Columns (You Fill Out):
1. `Vendor_ID` - Internal vendor ID
2. `Vendor_Name` - Vendor name
3. `Invoice_Number` - Invoice number (same for itemized rows)
4. `Purchase_Order_Number` - PO number
5. `Purchase_Order_File_Name` - **Comma-separated** if multiple POs (e.g., "PO1.pdf, PO2.pdf")
6. `Total_Amount` - Line item amount
7. `Tax_Amount` - Tax charged/self-assessed on this line
8. `Tax_Remitted` - Tax vendor remitted (>0 = Sales Tax, =0 = Use Tax)
9. `Tax_Rate_Charged` - Tax rate (e.g., "10.5%")
10. `Tax_Type` - **"Sales Tax" or "Use Tax"** (you specify)
11. `Invoice_File_Name_1` - Vendor invoice filename
12. `Invoice_File_Name_2` - Internal invoice filename
13. `Line_Item_Description` - Description of this line item

### OUTPUT Columns (AI Fills Out):
14. `Analysis_Notes` - AI analysis notes
15. `Final_Decision` - Add to claim or not
16. `Tax_Category` - Category from controlled vocabulary
17. `Additional_Info` - Additional info from controlled vocabulary
18. `Refund_Basis` - Refund reason from controlled vocabulary
19. `Estimated_Refund` - Calculated refund amount
20. `Legal_Citation` - WAC/RCW citations
21. `AI_Confidence` - 0-100% confidence score

## Hierarchical Structure Examples

### Example 1: One Invoice → Multiple Line Items
**Invoice**: MS-INV-2024-0451 (Microsoft)
- Row 1: Custom API Development - $25,000 (no tax) ✅ Exempt
- Row 2: Microsoft 365 Licenses - $15,000 + $1,575 tax ❌ Taxed
- Row 3: Support Services - $8,000 (no tax) ✅ Exempt

**Same invoice number**, **same invoice file**, **different line items**

### Example 2: One PO → Multiple Invoices → Multiple Line Items
**PO**: PO-2024-001 (Microsoft)
  ↓
- Invoice 1: MS-INV-2024-0451 → 3 line items
- Invoice 2: MS-INV-2024-0628 → 5 line items
- Invoice 3: MS-INV-2024-0892 → 2 line items

**Total: 10 Excel rows** from **1 PO**

### Example 3: Multiple POs for One Invoice
**Invoice**: ORA-2024-INV-44521 (Oracle)
- Purchase_Order_File_Name: `"PO_2024_005_Oracle_Master.pdf, PO_2024_005_Oracle_Amendment_1.pdf"`

**Comma-separated** list of PO files

## Test Scenarios Covered

### Scenario 1: Microsoft (Software/Services Mix)
- **PO**: PO-2024-001
- **Invoices**: 3 (PDF, Excel formats)
- **Line Items**: 10 total
- **Tests**:
  - Custom software exemption
  - Licenses (taxable)
  - Support services (exempt)
  - Hosting (exempt)
  - Professional services with **odd dollar amount** ($5,525 = hidden tax!)
  - Hardware (taxable)
  - Mixed itemized invoices

### Scenario 2: BuildRight Construction (Retainage Issue)
- **PO**: PO-2024-002
- **Invoices**: 3 (all PDF)
- **Line Items**: 3 total
- **Tests**:
  - **Construction retainage** - Tax charged on full $100K PO upfront
  - Progress payment #1: $80K paid, but $10.5K tax (on full $100K!) ❌ WRONG
  - Progress payment #2: $15K additional work, no tax
  - Retainage release: $20K (should get refund on $20K × 10.5% = $2,100)
  - **Refund Potential**: $2,100

### Scenario 3: Salesforce (Use Tax - Out-of-State Vendor)
- **PO**: PO-2024-003 (email format)
- **Invoices**: 2 (PDF, JPG image)
- **Line Items**: 4 total
- **Tax Type**: **Use Tax** (self-assessed)
- **Tests**:
  - Remote services from CA (you self-assessed use tax)
  - Custom development (should be exempt - refund opportunity)
  - Training delivered remotely (exempt)
  - Hardware shipped from CA (correctly self-assessed use tax)
  - **Refund Potential**: ~$5,985 on services

### Scenario 4: Deloitte (Professional Services - Hidden Tax)
- **PO**: PO-2024-004
- **Invoices**: 2 (PDF, Excel)
- **Line Items**: 3 total
- **Tests**:
  - **Odd dollar amounts**: $55,250 and $22,100 (indicate hidden tax!)
  - $55,250 = $50,000 + 10.5% tax = hidden tax on exempt professional services
  - $22,100 = $20,000 + 10.5% tax = hidden tax on tax advisory
  - Training (correctly no tax)
  - **Refund Potential**: ~$7,350

### Scenario 5: Oracle (Complex Bundled Deal - 7+ Line Items)
- **PO**: PO-2024-005 (Master + Amendment - **2 PO files comma-separated**)
- **Invoices**: 2 (PDF, PNG image)
- **Line Items**: 11 total
- **Tests**:
  - Custom development (exempt)
  - Licenses (taxable)
  - Cloud hosting (exempt)
  - Hardware (taxable)
  - Installation (taxable - should be exempt if professional service)
  - Professional services (exempt)
  - Maintenance (exempt)
  - Testing (exempt)
  - Training (exempt)
  - Printed materials (taxable - correct)
  - **Complex itemization** with 7+ items on single invoice

## File Formats Included

### Invoices (12 total):
- **PDFs**: 8 invoices
  - MS_INV_2024_0451.pdf
  - MS_INV_2024_0892.pdf
  - BRC_2024_1501.pdf (Construction)
  - BRC_2024_1623.pdf
  - BRC_2024_1844.pdf
  - SF_2024_88451.pdf (Salesforce)
  - DLT_2024_CC_9821.pdf (Deloitte)
  - ORA_2024_INV_44521.pdf (Oracle)

- **Excel**: 2 invoices
  - MS_INV_2024_0628.xlsx (Microsoft)
  - DLT_2024_CC_9955.xlsx (Deloitte)

- **Images**: 2 invoices
  - SF_2024_90123.jpg (Salesforce - JPG)
  - ORA_2024_INV_45789.png (Oracle - PNG)

### Purchase Orders (5 total):
- **PDFs**: 4 POs
  - PO_2024_001_Microsoft.pdf
  - PO_2024_002_BuildRight_Construction.pdf
  - PO_2024_004_Deloitte.pdf
  - PO_2024_005_Oracle_Master.pdf
  - PO_2024_005_Oracle_Amendment_1.pdf (Oracle has 2 POs)

- **Email**: 1 PO
  - PO_2024_003_Salesforce_Email.pdf (email screenshot/export)

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Rows | 31 |
| Unique Invoices | 12 |
| Unique POs | 5 |
| Sales Tax Rows | 27 |
| Use Tax Rows | 4 |
| PDF Invoices | 8 |
| Excel Invoices | 2 |
| Image Invoices | 2 |
| Average Line Items per Invoice | 2.6 |
| Most Itemized Invoice | ORA-2024-INV-44521 (7 items) |
| Total Tax Charged | $23,127.50 |
| Estimated Refund Potential | ~$15,435 |

## Key Test Cases to Validate

### 1. ✅ Hierarchical Structure Recognition
- System must handle same Invoice_Number appearing in multiple rows
- System must link all rows to same invoice PDF
- System must aggregate results per invoice

### 2. ✅ Multiple PO Handling
- System must parse comma-separated PO filenames
- Oracle invoice references 2 POs: "PO_2024_005_Oracle_Master.pdf, PO_2024_005_Oracle_Amendment_1.pdf"

### 3. ✅ Sales Tax vs Use Tax Classification
- Tax_Type column pre-filled by user
- System uses this for RAG query optimization
- Different analysis logic for each type

### 4. ✅ Anomaly Detection
- **Odd Dollar Amounts**: Deloitte invoices ($55,250, $22,100)
- **Construction Retainage**: BuildRight first invoice
- **Use Tax on Services**: Salesforce implementation services (should be exempt)

### 5. ✅ Various File Formats
- PDF OCR
- Excel cell reading
- Image OCR (JPG, PNG)
- Email parsing

### 6. ✅ Confidence Thresholds
- High-dollar amounts should reduce confidence (require review)
- In-state vendors (Microsoft, Oracle) should boost confidence when they charge tax
- Out-of-state vendors (Salesforce, Deloitte) with tax should reduce confidence

## Next Steps

1. **Generate Actual Invoice/PO PDFs, Excel, and Images**
   - Create realistic-looking documents matching the data
   - Include line items, tax breakdowns, vendor logos
   - Various layouts to test OCR robustness

2. **Run Analysis Pipeline**
   - Process all 31 rows
   - Populate OUTPUT columns
   - Test confidence scoring
   - Validate anomaly detection

3. **Load into Dashboard**
   - Import analyzed data
   - Show Review Queue
   - Test human override workflow
   - Validate learning system

4. **Create Claim Packets**
   - Split into Sales Tax vs Use Tax sheets
   - Generate PDF claim packets
   - Test with sample submission

## Questions for User

1. Should I now generate the actual PDF/Excel/Image files for these invoices and POs?
2. Do you want me to run the analysis pipeline to populate the OUTPUT columns?
3. Any additional test scenarios you want included?
4. Is the hierarchical structure clear and correct?

---

**Created**: 2025-11-15
**File**: `test_data/Master_Claim_Sheet_Comprehensive.xlsx`
**Script**: `scripts/create_comprehensive_test_data.py`
