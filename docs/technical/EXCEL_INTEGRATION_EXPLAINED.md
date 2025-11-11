# Excel Integration Workflow - Detailed Explanation

## Overview

The Excel integration is the **heart** of your refund analysis workflow. It connects your master Excel sheet (with invoice line items) to the AI-powered analysis engine, matching documents by filename and filling in analysis results.

---

## Your Test Refund Sheet Structure

### Input Columns (You Fill These)
```
| Vendor Name | Invoice # | PO # | Date | Inv 1 | Inv 2 | File Path | PO File Name |
|-------------|-----------|------|------|-------|-------|-----------|--------------|
| Ericsson    | INV-001   | PO-A | 1/15 | inv1  | inv2  | ericsson-001.pdf | po-a.pdf |
| Ericsson    | INV-001   | PO-A | 1/15 | inv1  | inv2  | ericsson-001.pdf | po-a.pdf |
| Nokia       | INV-002   | PO-B | 2/20 | inv1  |       | nokia-002.pdf    | po-b.pdf |
```

### Output Columns (AI Fills These)
```
| Product Description | Background | Type | Additional Info | Refund Basis | Citation | Location | Explanation |
|---------------------|------------|------|-----------------|--------------|----------|----------|-------------|
| Cloud hosting       | AWS svc    | SaaS | Multi-state     | Digital svc  | RCW...   | WA       | Exempt...   |
| Software license    | License    | SW   | Single          | Prof service | WAC...   | WA       | Eligible... |
| Consulting          | Prof svc   | Svc  | On-site         | Human effort | RCW...   | WA       | Refund...   |
```

---

## Key Understanding: Multiple Rows = Same Invoice

**Critical Point**: When you have **multiple line items** from the same invoice, you repeat the invoice information on each row:

```
Row 1: Ericsson | INV-001 | ericsson-001.pdf | [Line Item 1: Cloud hosting]
Row 2: Ericsson | INV-001 | ericsson-001.pdf | [Line Item 2: Software license]
Row 3: Ericsson | INV-001 | ericsson-001.pdf | [Line Item 3: Consulting]
```

**The script will**:
1. Recognize rows 1-3 share the same `ericsson-001.pdf`
2. Process the invoice PDF **once** (not three times)
3. Extract all line items from the invoice
4. Match each extracted line item to the appropriate Excel row
5. Fill in analysis for each row independently

---

## The Complete Workflow (Step-by-Step)

### **BEFORE Running the Script**

#### Step 1: Prepare Your Excel Sheet

```excel
Test Refund Sheet.xlsx:
- Fill in columns: Vendor Name, Invoice #, Date, File Path
- Leave analysis columns blank
- For multiple line items from same invoice, repeat the invoice info
```

#### Step 2: Organize Your Invoice Files

```
Place invoice PDFs in:
~/Desktop/refund-engine/client_documents/invoices/

Files:
- ericsson-001.pdf
- nokia-002.pdf
- zones-003.pdf
```

**Important**: The `File Path` column in your Excel should match these filenames exactly.

---

### **RUNNING the Script**

```bash
python scripts/3_analyze_from_excel.py \
  --excel ~/Desktop/"Test Refund Sheet.xlsx" \
  --invoice-folder ~/Desktop/refund-engine/client_documents/invoices/ \
  --output ~/Desktop/refund-engine/outputs/analyzed_sheets/"Test Refund Sheet - Analyzed.xlsx"
```

---

### **WHAT HAPPENS (Behind the Scenes)**

#### Phase 1: Load Excel & Match Documents

```python
# 1. Read Excel file
df = pd.read_excel("Test Refund Sheet.xlsx")

# 2. Group rows by filename (since same invoice = multiple rows)
grouped = df.groupby('File Path')

# Result:
# - ericsson-001.pdf → 3 rows (rows 1, 2, 3)
# - nokia-002.pdf → 1 row (row 4)
# - zones-003.pdf → 2 rows (rows 5, 6)
```

#### Phase 2: Process Each Invoice (One Time Per File)

For each unique filename (e.g., `ericsson-001.pdf`):

**Step A: Match Invoice File**
```python
invoice_path = find_invoice_file("ericsson-001.pdf", invoice_folder)
# Result: ~/Desktop/refund-engine/client_documents/invoices/ericsson-001.pdf
```

**Step B: Extract Invoice Data (GPT-4 Vision)**
```python
# Send PDF to GPT-4 Vision
extracted_data = extract_invoice_with_ai(invoice_path)

# Result:
{
  "vendor_name": "Ericsson",
  "invoice_number": "INV-001",
  "invoice_date": "2024-01-15",
  "line_items": [
    {
      "line_number": 1,
      "description": "AWS Cloud Hosting Services",
      "amount": 10000.00,
      "tax": 800.00
    },
    {
      "line_number": 2,
      "description": "Software License - Annual Subscription",
      "amount": 5000.00,
      "tax": 400.00
    },
    {
      "line_number": 3,
      "description": "Professional Consulting Services (40 hrs)",
      "amount": 10000.00,
      "tax": 800.00
    }
  ]
}
```

**Step C: Store Invoice in Supabase**
```python
# Store invoice header
invoice_id = store_invoice(extracted_data)

# Store each line item
for item in extracted_data['line_items']:
    line_item_id = store_line_item(invoice_id, item)
```

#### Phase 3: Analyze Each Line Item (RAG + AI)

For each line item:

**Step A: RAG Search Legal Knowledge Base**
```python
# Create search query
query = f"Washington sales tax {item['description']} taxability"

# Generate embedding
query_embedding = openai.embeddings.create(input=query).data[0].embedding

# Search Supabase (vector similarity)
relevant_laws = supabase.rpc('match_documents', {
    'query_embedding': query_embedding,
    'match_count': 5
})

# Result: Top 5 relevant legal document chunks
# Example:
# 1. WAC 458-20-15502 (Page 3): "Digital automated services..."
# 2. RCW 82.04.050 (Page 2): "Services primarily requiring human effort..."
# 3. Det. No. 17-0083 (Page 5): "Cloud hosting exemption criteria..."
```

**Step B: AI Analysis**
```python
# Send to GPT-4/Claude for analysis
analysis = analyze_with_ai(
    line_item=item,
    legal_context=relevant_laws
)

# Result:
{
    "product_description": "AWS Cloud Hosting Services",
    "background": "Cloud infrastructure service, multi-state deployment",
    "type": "SaaS",
    "additional_info": "Delivered electronically, automated platform",
    "refund_basis": "Digital automated service exemption",
    "citation": "RCW 82.04.050, WAC 458-20-15502",
    "location": "Washington (multi-location service)",
    "explanation": "This service qualifies as a digital automated service which is exempt from sales tax under RCW 82.04.050. The service is delivered electronically and does not primarily require human effort. Sales tax of $800 should not have been charged. Eligible for refund.",
    "confidence_score": 87,
    "estimated_refund": 800.00
}
```

**Step C: Store Analysis in Supabase**
```python
store_refund_analysis(
    line_item_id=line_item_id,
    analysis=analysis
)
```

#### Phase 4: Match Results Back to Excel Rows

```python
# For ericsson-001.pdf (3 rows in Excel)
# We extracted 3 line items
# Match each line item to its corresponding row

row_1_data = {
    "Product Description": "AWS Cloud Hosting Services",
    "Background": "Cloud infrastructure service...",
    "Type": "SaaS",
    "Additional Info": "Delivered electronically...",
    "Refund Basis": "Digital automated service exemption",
    "Citation": "RCW 82.04.050, WAC 458-20-15502",
    "Location": "Washington",
    "Explanation": "This service qualifies..."
}

row_2_data = {
    "Product Description": "Software License - Annual Subscription",
    # ... etc
}

row_3_data = {
    "Product Description": "Professional Consulting Services",
    # ... etc
}

# Update Excel dataframe
df.loc[row_1_index, output_columns] = row_1_data
df.loc[row_2_index, output_columns] = row_2_data
df.loc[row_3_index, output_columns] = row_3_data
```

#### Phase 5: Export Updated Excel

```python
# Write to output file
df.to_excel("Test Refund Sheet - Analyzed.xlsx", index=False)
```

---

## The Output Excel File

### What You Get

```
Test Refund Sheet - Analyzed.xlsx

Same structure as input, but now analysis columns are filled:

| Vendor | Invoice# | File Path        | Product Description | Refund Basis | Citation | Explanation |
|--------|----------|------------------|---------------------|--------------|----------|-------------|
| Ericsson| INV-001 | ericsson-001.pdf | AWS Cloud Hosting  | Digital svc  | RCW...  | Eligible... |
| Ericsson| INV-001 | ericsson-001.pdf | Software License   | Digital svc  | WAC...  | Eligible... |
| Ericsson| INV-001 | ericsson-001.pdf | Consulting         | Human effort | RCW...  | Eligible... |
| Nokia  | INV-002 | nokia-002.pdf    | Equipment          | Manufacturing| RCW...  | Not elig... |
```

---

## Key Features & Intelligence

### 1. **Automatic Document Matching**
- Reads `File Path` column
- Finds corresponding PDF in invoice folder
- Handles missing files gracefully (logs warning, continues)

### 2. **Smart Line Item Extraction**
- Uses GPT-4 Vision to "see" the invoice
- Extracts all line items with amounts and tax
- Handles various invoice formats automatically

### 3. **Deduplication**
- Same filename on multiple rows = process invoice once
- Stores invoice once in database
- Matches extracted items to Excel rows

### 4. **Intelligent RAG Search**
- Each line item gets personalized legal search
- "Cloud hosting" → finds digital services laws
- "Consulting" → finds primarily human effort laws
- "Equipment" → finds manufacturing exemptions

### 5. **Context-Aware Analysis**
- AI analyzes based on:
  - Product description
  - Retrieved legal documents
  - Transaction details (amount, location, etc.)
  - Historical patterns (if available)

### 6. **Confidence Scoring**
- Each analysis includes confidence score (0-100)
- High confidence (>80): Strong refund case
- Medium confidence (60-80): Needs review
- Low confidence (<60): Manual investigation required

---

## Example: Full Lifecycle of One Row

### Input Row (You Provide)
```
Vendor: Ericsson
Invoice #: INV-001
File Path: ericsson-001.pdf
[Rest blank]
```

### Processing Steps

1. **Find PDF**: `~/Desktop/refund-engine/client_documents/invoices/ericsson-001.pdf` ✓
2. **Extract with AI**: "This invoice has 3 line items..."
3. **Match to Row**: This row is line item #1
4. **RAG Search**: "AWS Cloud Hosting Services" → Find relevant laws
5. **AI Analysis**: "This is a digital automated service..."
6. **Generate Result**: Populate all output columns

### Output Row (AI Fills)
```
Vendor: Ericsson
Invoice #: INV-001
File Path: ericsson-001.pdf
Product Description: AWS Cloud Hosting Services - Multi-region deployment
Background: Cloud infrastructure service providing compute, storage, and networking
Type: SaaS / Cloud Service
Additional Info: Delivered electronically, automated platform, no human intervention
Refund Basis: Digital automated service exempt from sales tax
Citation: RCW 82.04.050 (digital services), WAC 458-20-15502 (cloud services)
Location: Washington (service accessed from WA, multi-state infrastructure)
Explanation: This cloud hosting service qualifies as a "digital automated service" under RCW 82.04.050. The service is delivered electronically through an automated platform and does not primarily require human effort in its provision. Under Washington law, such services are exempt from sales tax. The $800 in sales tax charged on this $10,000 service should not have been applied. Client is eligible for a full refund of the improperly charged tax. Confidence: 92%. Documentation: Invoice shows clear digital service delivery.
```

---

## Error Handling & Edge Cases

### Case 1: Invoice PDF Not Found
```python
# Excel row has: File Path = "missing-invoice.pdf"
# File doesn't exist in invoice folder

Action:
- Log warning: "⚠️ Invoice not found: missing-invoice.pdf"
- Mark row: "ERROR: Invoice file not found"
- Continue processing other rows
```

### Case 2: Can't Extract Data from PDF
```python
# PDF is corrupted, scanned image with poor quality, etc.

Action:
- Try OCR fallback (pytesseract)
- If still fails, log error
- Mark row: "ERROR: Could not extract invoice data"
- Store partial information if any
```

### Case 3: Low Confidence Analysis
```python
# AI analysis returns confidence < 60%

Action:
- Still populate all columns
- Add note in "Additional Info": "⚠️ Low confidence (55%) - requires manual review"
- Flag for human review
```

### Case 4: Multiple Line Items, But Excel Has Wrong Count
```python
# Invoice has 5 line items
# Excel only has 3 rows for this invoice

Action:
- Match the 3 rows to first 3 line items
- Log warning: "Invoice has 5 items but only 3 rows in Excel"
- Store all 5 in database for reference
```

---

## Database Storage (Behind the Scenes)

While filling Excel, everything is also stored in Supabase:

```sql
-- Invoice header stored
invoices table:
  - vendor_name, invoice_number, total_amount, etc.

-- Each line item stored
invoice_line_items table:
  - invoice_id (FK), description, amount, tax, etc.

-- Analysis for each line item
refund_analysis table:
  - line_item_id (FK)
  - potentially_eligible (bool)
  - confidence_score (int)
  - estimated_refund_amount (decimal)
  - refund_calculation_method (text)
  - explanation (text)
  - legal_citations (text)
```

**Why store in database**:
1. **Audit trail**: Every analysis is logged
2. **Reusability**: Can re-export to Excel anytime
3. **Query capability**: Can filter/search/analyze across all invoices
4. **Learning**: System can learn from patterns over time
5. **Reporting**: Generate summary reports

---

## Advanced Features (Future)

### Pattern Learning
```python
# After processing 100 invoices, system learns:
"Vendor 'Ericsson' + Product contains 'cloud' → 95% eligible for digital service exemption"

# Next time: Higher confidence, faster analysis
```

### Bulk Operations
```python
# Process entire Excel sheet overnight
# 10,000 rows × 100 unique invoices → 8 hours
# Wake up to complete analysis
```

### Delta Updates
```python
# Only analyze NEW rows since last run
# Excel with 1000 rows, only 50 new → Process 50 only
```

---

## Summary: What You Need to Know

### Before Running Script:
1. ✅ Fill Excel with invoice info and file paths
2. ✅ Put invoice PDFs in `client_documents/invoices/`
3. ✅ Ingest 20-30 legal docs (one-time setup)

### Run Script:
```bash
python scripts/3_analyze_from_excel.py --excel "Test Refund Sheet.xlsx"
```

### After Script:
1. ✅ Review output Excel with filled analysis columns
2. ✅ Check rows with low confidence manually
3. ✅ Make any edits/adjustments needed
4. ✅ Use for client proposals or DOR filing

### Key Points:
- **Same filename on multiple rows** = Multiple line items from one invoice ✓
- **AI matches each line item to correct row** ✓
- **All analysis stored in Supabase + Excel** ✓
- **Can re-run or update anytime** ✓

---

## Questions?

This system transforms:
- **FROM**: Blank Excel rows with just invoice filenames
- **TO**: Complete refund analysis with legal citations and explanations

The magic happens through:
1. **OCR/Vision AI** (extract invoice data)
2. **RAG Search** (find relevant laws)
3. **Analysis AI** (determine eligibility)
4. **Smart Matching** (link everything together)

All automatically, while you review and approve the results.
