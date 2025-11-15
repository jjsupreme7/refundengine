# Excel-Based Refund Analysis Workflow

Complete guide for analyzing tax refunds with AI + human review using Excel.

## Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│ Upload      │ ───> │ AI Analyzes  │ ───> │ You Review  │ ───> │ System       │
│ Excel       │      │ Each Row     │      │ in Excel    │      │ Learns       │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
     Input              Extract from           Approve/Fix          Updates KB
                       Invoice PDFs              Corrections
```

## Step-by-Step Guide

### Step 1: Prepare Your Input Excel

Your Excel should have these columns:

| Column | Required | Description |
|--------|----------|-------------|
| Row_ID | Yes | Unique identifier for each line item |
| Vendor | Yes | Vendor name (e.g., "Nokia", "Ericsson") |
| Invoice_Number | Yes | Invoice number |
| PO Number | Yes | Purchase order number |
| Date | Yes | Transaction date |
| Inv_1_File | Yes | Invoice PDF filename |
| PO_1_File | Yes | PO PDF filename |
| Amount | Yes | Line item amount (before tax) |
| Tax | Yes | Tax paid on this line item |
| Notes | No | Any notes |

**Example:**

| Row_ID | Vendor | Invoice_Number | PO Number | Date | Inv_1_File | PO_1_File | Amount | Tax |
|--------|--------|----------------|-----------|------|------------|-----------|--------|-----|
| 1 | Nokia | INV-2024-001 | 490293453 | 2024-08-18 | nokia-inv-001.pdf | nokia-po-001.pdf | 8000 | 800 |
| 2 | Nokia | INV-2024-001 | 490293453 | 2024-08-18 | nokia-inv-001.pdf | nokia-po-001.pdf | 5000 | 500 |

**Important Notes:**
- Rows 1 and 2 have same invoice/PO but different amounts → They're different line items
- Each row will be analyzed separately
- PDFs must exist in the `client_docs/` folder

### Step 2: Run AI Analysis

```bash
# Basic usage
python scripts/6_analyze_refunds.py "path/to/your/input.xlsx"

# Specify output location
python scripts/6_analyze_refunds.py "input.xlsx" --output "output.xlsx"

# Save to database for tracking
python scripts/6_analyze_refunds.py "input.xlsx" --save-db

# Custom docs folder
python scripts/6_analyze_refunds.py "input.xlsx" --docs-folder "my_docs"
```

**What happens:**
1. Script reads each row
2. Opens the invoice PDF (e.g., `nokia-inv-001.pdf`)
3. Uses AI to find the line item matching the amount ($8000 or $5000)
4. Extracts product description from that line item
5. Queries legal knowledge base (vector search)
6. Analyzes if tax refund is eligible
7. Outputs Excel with AI analysis columns

### Step 3: Review the AI Analysis

The output Excel will have **new columns** added:

#### AI Analysis Columns (Read-Only)

| Column | Description |
|--------|-------------|
| AI_Product_Desc | Product description extracted from invoice |
| AI_Product_Type | Product category (e.g., "Hardware", "Services") |
| AI_Product_Details | Additional details (SKU, model, etc.) |
| AI_Refund_Eligible | True/False - Is refund eligible? |
| AI_Refund_Basis | Legal basis (e.g., "Manufacturing exemption") |
| AI_Exemption_Type | Type of exemption |
| AI_Citation | RCW/WAC citation |
| AI_Confidence | 0-100% confidence score |
| AI_Refund_Percentage | Percentage of tax refundable |
| AI_Estimated_Refund | Dollar amount |
| AI_Explanation | Detailed reasoning |
| AI_Key_Factors | Key decision factors |

#### Human Review Columns (You Fill These In)

| Column | Your Action | Values |
|--------|-------------|--------|
| Review_Status | **REQUIRED** | `Approved`, `Needs Correction`, or `Rejected` |
| Corrected_Product_Desc | Fix if AI got description wrong | Text |
| Corrected_Product_Type | Fix if AI got category wrong | Text |
| Corrected_Refund_Basis | Fix if AI got legal basis wrong | Text |
| Corrected_Citation | Fix if AI got citation wrong | RCW/WAC |
| Corrected_Estimated_Refund | Fix if AI got amount wrong | Number |
| Reviewer_Notes | **RECOMMENDED** | Your reasoning/comments |

**Example Review:**

| Row | AI_Product_Desc | AI_Product_Type | AI_Refund | Review_Status | Corrected_Product_Type | Reviewer_Notes |
|-----|-----------------|-----------------|-----------|---------------|----------------------|----------------|
| 1 | 5G Radio Equipment | Manufacturing Equipment | $800 | Needs Correction | Telecommunications Hardware | This is networking gear, not manufacturing machinery |
| 2 | Installation Services | Professional Services | $0 | Approved | | Correct - services are taxable |

### Step 4: Import Your Corrections

Once you've reviewed and corrected the Excel:

```bash
# Import corrections
python scripts/7_import_corrections.py "path/to/reviewed.xlsx"

# Specify your name/email
python scripts/7_import_corrections.py "reviewed.xlsx" --reviewer "your.email@company.com"

# Preview without saving (dry run)
python scripts/7_import_corrections.py "reviewed.xlsx" --dry-run
```

**What happens:**
1. Script reads your review status and corrections
2. Saves reviews to database (`analysis_reviews` table)
3. **Learns from your corrections:**
   - Stores Nokia → "5G Radio Equipment" → "Telecommunications Hardware"
   - Creates pattern for future analysis
   - Updates vendor knowledge base
4. Next time AI sees similar product from Nokia, it will use your correction!

### Step 5: System Gets Smarter

The system learns from every correction you make:

**Example Learning:**

```
First analysis:
  Nokia "5G Radio Equipment" → AI guesses "Manufacturing Equipment"
  You correct to: "Telecommunications Hardware"

Second analysis (weeks later):
  Nokia "5G Radio Equipment Model XYZ" → AI remembers → "Telecommunications Hardware"
  Confidence: 95% (learned from you!)
```

**Learning is stored in:**
- `vendor_products` - Product catalog per vendor
- `vendor_product_patterns` - Patterns for matching
- `audit_trail` - Complete history of AI vs Human decisions

---

## Complete Example Workflow

### Input Excel

```
Row_ID: 7
Vendor: Nokia
Invoice: INV-2024-007
PO: 49029342342
Amount: 8000
Tax: 800
Inv_1_File: inv-54567.pdf
PO_1_File: PO_568203921_Nokia.pdf
```

### After AI Analysis (Step 2)

```
AI_Product_Desc: "5G NR Radio Unit Model AAHF"
AI_Product_Type: "Manufacturing Equipment"
AI_Refund_Basis: "Manufacturing machinery & equipment exemption"
AI_Citation: "RCW 82.08.02565"
AI_Confidence: 78%
AI_Estimated_Refund: $800
AI_Explanation: "Radio equipment used in manufacturing telecommunications products may qualify..."
```

### Your Review (Step 3)

```
Review_Status: "Needs Correction"
Corrected_Product_Type: "Telecommunications Network Equipment"
Corrected_Refund_Basis: "Not eligible - networking equipment doesn't qualify for manufacturing exemption"
Corrected_Estimated_Refund: $0
Reviewer_Notes: "This is infrastructure equipment for telecom network, not manufacturing machinery. Used for signal transmission, not production of goods."
```

### After Import (Step 4)

```
✓ Review saved to database
✓ Learned: Nokia → 5G NR Radio → Telecommunications Network Equipment
✓ Pattern created: "5G" + "Radio" → No manufacturing exemption
✓ Future analyses will apply this learning
```

---

## Database Schema

### Tables Created

1. **analysis_results** - AI analysis for each row
2. **analysis_reviews** - Your reviews and corrections
3. **vendor_products** - Learned product catalog
4. **vendor_product_patterns** - Pattern matching rules
5. **audit_trail** - Complete change history

### To Deploy Schema

```bash
# Run migrations on Supabase (use current schema files)
psql -h your-db-host -U postgres -d postgres -f database/schema/schema_vendor_learning.sql
psql -h your-db-host -U postgres -d postgres -f database/schema/schema_knowledge_base.sql
```

Or use Supabase dashboard SQL editor:
1. Copy contents of `database/schema/schema_vendor_learning.sql`
2. Paste into SQL Editor
3. Run
4. Repeat for `database/schema/schema_knowledge_base.sql`

**Note**: The knowledge base schema includes the search RPC functions:
- `search_tax_law()` - Search tax law documents
- `search_vendor_background()` - Search vendor documents
- `search_knowledge_base()` - Combined search

---

## Tips & Best Practices

### When to Approve vs Correct

**Approve when:**
- ✅ Product description is accurate
- ✅ Refund decision is correct
- ✅ Citation/legal basis is appropriate
- ✅ You agree with AI reasoning

**Correct when:**
- ❌ Product is misidentified
- ❌ Wrong product category
- ❌ Incorrect refund eligibility
- ❌ Wrong legal citation
- ❌ Refund amount is wrong

**Reject when:**
- ❌ Analysis is completely wrong
- ❌ Can't determine from documents
- ❌ Need more information

### Always Add Reviewer Notes

Good notes help the system learn:

**Bad note:** "Wrong"

**Good note:** "This is networking infrastructure, not manufacturing equipment. Used for signal transmission in telecom network, not production of goods. RCW 82.08.02565 doesn't apply."

### Batch Processing

For large Excel files:

```bash
# Process in chunks
python scripts/6_analyze_refunds.py large_file.xlsx --save-db

# Review in Excel (can do offline)

# Import when ready
python scripts/7_import_corrections.py large_file_analyzed.xlsx
```

### Version Control

Keep track of your files:

```
input.xlsx                    # Original
input_analyzed.xlsx           # After AI analysis
input_analyzed_reviewed.xlsx  # After your review
```

---

## Troubleshooting

### "No analysis found for Row X"
- Make sure you ran analysis with `--save-db` flag
- Check that Row_ID matches between files

### "Error: Missing required columns"
- Ensure Excel has all required columns
- Check column names match exactly (case-sensitive)

### "AI extracted wrong product"
- Invoice PDF might have poor OCR quality
- Multiple items with same amount → AI confused
- Add clarification in Reviewer_Notes

### Low AI Confidence (<50%)
- Insufficient legal knowledge in database
- Ambiguous product description
- Novel/unusual scenario
- **Review carefully and provide correction**

---

## Next Steps

1. ✅ Run schema migrations to create database tables
2. ✅ Upload legal documents to knowledge base
3. ✅ Prepare your first Excel file
4. ✅ Run analysis script
5. ✅ Review in Excel
6. ✅ Import corrections
7. ✅ Watch system get smarter!

---

## Support

For issues or questions:
- Check logs in console output
- Verify PDFs exist in `client_docs/` folder
- Ensure Supabase connection is configured
- Review database schema is deployed
