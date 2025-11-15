# Quick Reference Guide

Fast lookup for common commands and workflows.

## 📋 Common Commands

### Setup (One-Time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Deploy schemas (use current schema files from schema/ folder)
psql -h db.xxx.supabase.co -U postgres << EOF
\i database/schema/schema_knowledge_base.sql
\i database/schema/schema_vendor_learning.sql
EOF

# Or in Supabase SQL Editor:
# Copy/paste each .sql file and run
# Note: schema_knowledge_base.sql includes search RPC functions
```

### Ingest Knowledge Base

```bash
# Tax law documents
python scripts/8_ingest_knowledge_base.py tax_law \
    "knowledge_base/tax_law/RCW_82.08.02565.pdf" \
    --citation "RCW 82.08.02565" \
    --law-category "exemption"

# Vendor documents
python scripts/8_ingest_knowledge_base.py vendor_background \
    "knowledge_base/vendors/Nokia_Profile.pdf" \
    --vendor-name "Nokia" \
    --vendor-category "manufacturer" \
    --doc-category "company_profile"

# Batch: entire folder
python scripts/8_ingest_knowledge_base.py tax_law \
    "knowledge_base/tax_law/" \
    --citation "RCW 82.08" \
    --law-category "exemption"
```

### Run Analysis

```bash
# Basic analysis
python scripts/6_analyze_refunds.py "input.xlsx"

# Save to database (recommended)
python scripts/6_analyze_refunds.py "input.xlsx" --save-db

# Custom output path
python scripts/6_analyze_refunds.py "input.xlsx" \
    --output "results_Q1_2024.xlsx" \
    --save-db

# Custom docs folder
python scripts/6_analyze_refunds.py "input.xlsx" \
    --docs-folder "my_invoices" \
    --save-db
```

### Import Corrections

```bash
# Import reviews
python scripts/7_import_corrections.py "input_analyzed.xlsx"

# With reviewer name
python scripts/7_import_corrections.py "input_analyzed.xlsx" \
    --reviewer "john.doe@company.com"

# Dry run (preview only)
python scripts/7_import_corrections.py "input_analyzed.xlsx" \
    --dry-run
```

---

## 📊 Excel Column Reference

### Input Columns (Required)

| Column | Example | Notes |
|--------|---------|-------|
| Row_ID | 1, 2, 3... | Unique identifier |
| Vendor | Nokia | Vendor name |
| Invoice_Number | INV-2024-001 | Invoice # |
| PO Number | 490293453 | Purchase order # |
| Date | 2024-08-18 | Transaction date |
| Inv_1_File | invoice.pdf | Invoice PDF filename |
| PO_1_File | po.pdf | PO PDF filename |
| Amount | 8000 | Line item amount |
| Tax | 800 | Tax paid |

### AI Output Columns (Auto-Generated)

| Column | Description |
|--------|-------------|
| AI_Product_Desc | Product extracted from invoice |
| AI_Product_Type | Category (Hardware, Software, etc.) |
| AI_Refund_Eligible | True/False |
| AI_Refund_Basis | Legal reasoning |
| AI_Citation | RCW/WAC reference |
| AI_Confidence | 0-100% |
| AI_Estimated_Refund | Dollar amount |
| AI_Explanation | Detailed reasoning |

### Review Columns (You Fill)

| Column | Values | Required? |
|--------|--------|-----------|
| Review_Status | Approved / Needs Correction / Rejected | **YES** |
| Corrected_Product_Desc | Text | If AI wrong |
| Corrected_Product_Type | Text | If AI wrong |
| Corrected_Refund_Basis | Text | If AI wrong |
| Corrected_Citation | RCW/WAC | If AI wrong |
| Corrected_Estimated_Refund | Number | If AI wrong |
| Reviewer_Notes | Text | **Recommended** |

---

## 🗄️ Database Quick Queries

### View Knowledge Base Stats

```sql
-- Overall stats
SELECT * FROM knowledge_base_stats;

-- Tax law documents
SELECT * FROM tax_law_documents_summary;

-- Vendor documents
SELECT * FROM vendor_documents_summary;
```

### Check Analysis Results

```sql
-- Recent analyses
SELECT row_id, vendor_name, ai_product_desc, ai_estimated_refund, analysis_status
FROM analysis_results
ORDER BY created_at DESC
LIMIT 10;

-- Pending review
SELECT COUNT(*) FROM analysis_results
WHERE analysis_status = 'pending_review';
```

### View Corrections

```sql
-- Recent corrections
SELECT row_id, review_status, corrected_product_type, reviewer_notes
FROM analysis_reviews
ORDER BY reviewed_at DESC
LIMIT 10;

-- Correction stats
SELECT review_status, COUNT(*)
FROM analysis_reviews
GROUP BY review_status;
```

### Vendor Learning

```sql
-- What system learned
SELECT vendor_name, product_description, product_type, learning_source
FROM vendor_products
ORDER BY created_at DESC;

-- Patterns created
SELECT vendor_name, product_keyword, correct_product_type, times_confirmed
FROM vendor_product_patterns
WHERE is_active = true
ORDER BY times_confirmed DESC;
```

### Audit Trail

```sql
-- Recent changes
SELECT event_type, field_name, old_value, new_value, changed_by
FROM audit_trail
ORDER BY created_at DESC
LIMIT 20;

-- Corrections by user
SELECT changed_by, COUNT(*) as corrections
FROM audit_trail
WHERE event_type = 'human_correction'
GROUP BY changed_by
ORDER BY corrections DESC;
```

---

## 🔧 Troubleshooting

### Error: "Function search_tax_law does not exist"

**Solution:**
```bash
psql -h db.xxx.supabase.co -U postgres -f database/schema/schema_knowledge_base.sql
```

### Error: "Table analysis_results does not exist"

**Solution:**
```bash
psql -h db.xxx.supabase.co -U postgres -f database/schema/schema_vendor_learning.sql
```

### Error: "No text extracted from PDF"

**Causes:**
- Scanned PDF (no OCR)
- Encrypted PDF
- Corrupted file

**Solutions:**
- Use OCR tool to convert
- Check PDF can be opened
- Re-download file

### Error: "No analysis found for Row X"

**Cause:** Analysis wasn't saved to database

**Solution:** Run analysis with `--save-db` flag:
```bash
python scripts/6_analyze_refunds.py input.xlsx --save-db
```

### Low Confidence (<50%)

**Causes:**
- Insufficient legal documents
- Ambiguous product description
- Novel scenario

**Actions:**
1. Review AI_Explanation
2. Add more tax law documents
3. Add vendor background docs
4. Provide correction to teach system

### Files Not Found

**Check:**
```bash
# Verify PDFs exist
ls client_docs/invoice.pdf

# Check Excel references correct filenames
# Column Inv_1_File should match actual filename
```

---

## 📈 Performance Tips

### Speed Up Analysis

1. **Use --save-db** - Enables future optimizations
2. **Keep PDFs organized** - Faster file access
3. **Batch process** - Don't analyze one row at a time
4. **Close Excel** - While running scripts

### Reduce Costs

1. **Review before re-running** - Don't re-analyze same data
2. **Use corrections** - System learns, fewer mistakes
3. **Ingest once** - Knowledge base rarely changes
4. **Batch reviews** - Import corrections together

### Improve Accuracy

1. **Add vendor docs** - More context = better decisions
2. **Provide detailed notes** - Helps system learn
3. **Review corrections** - Verify they make sense
4. **Update tax law** - Keep knowledge base current

---

## 🎯 Best Practices

### Before Analysis

- ✅ PDFs in correct folder
- ✅ Excel columns match required format
- ✅ Row_ID is unique
- ✅ Knowledge base is up to date

### During Review

- ✅ Always add Reviewer_Notes for corrections
- ✅ Review AI_Explanation before correcting
- ✅ Be consistent in terminology
- ✅ Correct all fields if one is wrong

### After Import

- ✅ Verify corrections were imported
- ✅ Check audit_trail for changes
- ✅ Review vendor_products for new learnings
- ✅ Test system on similar rows

---

## 📞 Quick Help

| Issue | Document |
|-------|----------|
| Understanding the workflow | EXCEL_WORKFLOW_GUIDE.md |
| Knowledge base setup | KNOWLEDGE_BASE_GUIDE.md |
| System architecture | SYSTEM_ARCHITECTURE.md |
| This reference | QUICK_REFERENCE.md (you are here) |

---

## 🔑 Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="eyJ..."  # Service role key

# Optional
export DOCS_FOLDER="client_docs"  # Default folder for PDFs
```

Add to `.env` file:
```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
```

---

## 📝 File Locations

```
/Users/jacoballen/Desktop/refund-engine/
├── database/
│   ├── schema/
│   │   ├── schema_knowledge_base.sql    # Knowledge base tables & RPC functions
│   │   └── schema_vendor_learning.sql   # Learning system tables
│   └── archive/
│       └── old_schema/                  # Deprecated schema files (archived)
│
├── scripts/
│   ├── 6_analyze_refunds.py             # Main analysis script
│   ├── 7_import_corrections.py          # Import reviews
│   └── 8_ingest_knowledge_base.py       # Ingest documents
│
├── docs/
│   ├── EXCEL_WORKFLOW_GUIDE.md          # Excel workflow guide
│   ├── KNOWLEDGE_BASE_GUIDE.md          # Knowledge base guide
│   ├── SYSTEM_ARCHITECTURE.md           # Architecture docs
│   └── QUICK_REFERENCE.md               # This file
│
├── knowledge_base/
│   ├── tax_law/                         # RCW/WAC PDFs
│   └── vendors/                         # Vendor background PDFs
│
└── client_docs/                         # Invoice & PO PDFs
```

---

**Last Updated:** 2025-11-13 (Updated schema references to current files)
