# Getting Started Checklist

Step-by-step checklist to get your refund analysis system up and running.

## ✅ Phase 1: Initial Setup (15-30 minutes)

### Database Setup

- [ ] **Have Supabase account**
  - Sign up at https://supabase.com if needed
  - Create new project
  - Note your project URL and keys

- [ ] **Set environment variables**
  ```bash
  export OPENAI_API_KEY="sk-..."
  export SUPABASE_URL="https://xxx.supabase.co"
  export SUPABASE_KEY="eyJ..."
  ```
  Or create `.env` file with these values

- [ ] **Install Python dependencies**
  ```bash
  pip install -r requirements.txt
  ```
  Expected packages: openai, supabase, pandas, PyPDF2, openpyxl

- [ ] **Deploy database schemas**

  **Option A: psql command line**
  ```bash
  psql -h db.xxx.supabase.co -U postgres << EOF
  \i database/schema_knowledge_base.sql
  \i database/schema_vendor_learning.sql
  EOF
  ```

  **Option B: Supabase Dashboard**
  1. Go to SQL Editor in Supabase
  2. Copy contents of `schema_knowledge_base.sql`
  3. Paste and Run
  4. Repeat for `schema_vendor_learning.sql`

- [ ] **Verify tables created**
  ```sql
  SELECT * FROM knowledge_base_stats;
  ```
  Should return empty table (no errors)

---

## ✅ Phase 2: Knowledge Base Setup (30-60 minutes)

### Organize Your Documents

- [ ] **Create folder structure**
  ```bash
  mkdir -p knowledge_base/tax_law/exemptions
  mkdir -p knowledge_base/tax_law/rates
  mkdir -p knowledge_base/vendors
  mkdir -p client_docs
  ```

- [ ] **Collect tax law documents**
  - Download Washington State RCW/WAC PDFs
  - Recommended: RCW 82.08, RCW 82.04, relevant WACs
  - Place in `knowledge_base/tax_law/`

- [ ] **Collect vendor documents** (optional but recommended)
  - Company profiles
  - Product catalogs
  - Industry information
  - Place in `knowledge_base/vendors/[VendorName]/`

### Ingest Tax Law

- [ ] **Ingest first tax law document**
  ```bash
  python scripts/8_ingest_knowledge_base.py tax_law \
      "knowledge_base/tax_law/RCW_82.08.02565.pdf" \
      --citation "RCW 82.08.02565" \
      --law-category "exemption" \
      --title "Manufacturing Machinery Exemption"
  ```

- [ ] **Verify ingestion**
  ```sql
  SELECT * FROM tax_law_documents_summary;
  ```
  Should show 1 document with chunks

- [ ] **Ingest remaining tax law documents**
  Repeat for each PDF, or batch process:
  ```bash
  python scripts/8_ingest_knowledge_base.py tax_law \
      "knowledge_base/tax_law/" \
      --citation "RCW 82.08" \
      --law-category "exemption"
  ```

### Ingest Vendor Background (Optional)

- [ ] **Ingest vendor documents**
  ```bash
  python scripts/8_ingest_knowledge_base.py vendor_background \
      "knowledge_base/vendors/Nokia/Nokia_Profile.pdf" \
      --vendor-name "Nokia" \
      --vendor-category "manufacturer" \
      --doc-category "company_profile"
  ```

- [ ] **Verify vendor ingestion**
  ```sql
  SELECT * FROM vendor_documents_summary;
  ```

---

## ✅ Phase 3: First Analysis (10-20 minutes)

### Prepare Test Data

- [ ] **Collect sample invoices**
  - Gather 5-10 invoice PDFs
  - Place in `client_docs/`
  - Name clearly (e.g., `nokia_inv_001.pdf`)

- [ ] **Collect corresponding POs** (if available)
  - Place in `client_docs/`

- [ ] **Create Excel file**

  Create `test_input.xlsx` with these columns:

  | Row_ID | Vendor | Invoice_Number | PO Number | Date | Inv_1_File | PO_1_File | Amount | Tax |
  |--------|--------|----------------|-----------|------|------------|-----------|--------|-----|
  | 1 | Nokia | INV-001 | PO-12345 | 2024-01-15 | nokia_inv_001.pdf | nokia_po_001.pdf | 10000 | 1000 |
  | 2 | Ericsson | INV-002 | PO-12346 | 2024-01-20 | ericsson_inv_002.pdf | ericsson_po_002.pdf | 5000 | 500 |

- [ ] **Verify file paths**
  ```bash
  ls client_docs/nokia_inv_001.pdf
  ls client_docs/ericsson_inv_002.pdf
  # Should list files without errors
  ```

### Run First Analysis

- [ ] **Run analysis script**
  ```bash
  python scripts/6_analyze_refunds.py "test_input.xlsx" --save-db
  ```

- [ ] **Check output Excel**
  - File: `test_input_analyzed.xlsx`
  - Should have AI columns filled in
  - Review AI_Product_Desc, AI_Refund_Basis, AI_Estimated_Refund

- [ ] **Verify database records**
  ```sql
  SELECT COUNT(*) FROM analysis_results;
  ```
  Should match number of rows in Excel

---

## ✅ Phase 4: Review & Correction (15-30 minutes)

### Review AI Analysis

- [ ] **Open `test_input_analyzed.xlsx` in Excel**

- [ ] **For each row, fill in:**
  - **Review_Status**: Approved / Needs Correction / Rejected
  - **Corrected_*** columns: Only if AI got it wrong
  - **Reviewer_Notes**: Your reasoning (recommended)

Example:
```
Row 1:
  AI_Product_Desc: "5G Radio Equipment"
  AI_Product_Type: "Manufacturing Equipment"
  AI_Estimated_Refund: $1000

  Your review:
  Review_Status: "Needs Correction"
  Corrected_Product_Type: "Telecommunications Hardware"
  Corrected_Estimated_Refund: $0
  Reviewer_Notes: "Networking equipment, not manufacturing machinery"
```

- [ ] **Save Excel file** (keep same name or rename to `test_input_reviewed.xlsx`)

### Import Corrections

- [ ] **Import your reviews**
  ```bash
  python scripts/7_import_corrections.py "test_input_analyzed.xlsx" \
      --reviewer "your.name@company.com"
  ```

- [ ] **Check import summary**
  Should show:
  - Approved: X
  - Corrected: Y
  - Rejected: Z
  - Products learned: Y
  - Patterns learned: Y

- [ ] **Verify learning in database**
  ```sql
  SELECT * FROM vendor_products;
  SELECT * FROM vendor_product_patterns;
  SELECT * FROM audit_trail ORDER BY created_at DESC LIMIT 10;
  ```

---

## ✅ Phase 5: Verification (10 minutes)

### Test Learning

- [ ] **Create second test file**
  - Use same vendors as first test
  - Similar products
  - Save as `test_input_2.xlsx`

- [ ] **Run analysis again**
  ```bash
  python scripts/6_analyze_refunds.py "test_input_2.xlsx" --save-db
  ```

- [ ] **Check if AI learned**
  - Open `test_input_2_analyzed.xlsx`
  - For vendors/products you corrected before:
    - AI_Product_Type should match your correction
    - AI_Confidence should be higher
    - AI_Explanation should reference learning

- [ ] **Verify system is working**
  - [ ] AI extracts products correctly
  - [ ] Tax law search returns relevant results
  - [ ] Refund calculations make sense
  - [ ] Corrections are stored
  - [ ] System learns from corrections

---

## ✅ Phase 6: Production Ready (Optional)

### Scale Up

- [ ] **Ingest all tax law documents**
  - All relevant RCW sections
  - All relevant WAC sections
  - Tax bulletins, advisories

- [ ] **Ingest vendor backgrounds for major vendors**
  - Top 10-20 vendors by transaction volume
  - Vendors with complex products

- [ ] **Process historical data**
  - Gather all invoices from past quarters
  - Create comprehensive Excel
  - Run analysis
  - Review and correct
  - Build up learning database

### Optimize

- [ ] **Review performance**
  ```sql
  -- Check chunk distribution
  SELECT document_type, COUNT(*)
  FROM knowledge_documents
  GROUP BY document_type;

  -- Check learning stats
  SELECT vendor_name, COUNT(*) as products
  FROM vendor_products
  GROUP BY vendor_name
  ORDER BY products DESC;
  ```

- [ ] **Fine-tune confidence thresholds**
  - Determine acceptable confidence levels
  - Set rules for auto-approval (>90%?)
  - Flag low confidence for manual review

- [ ] **Document your patterns**
  - List common vendor/product combinations
  - Document refund eligibility rules you've learned
  - Create internal knowledge base

---

## 🎉 You're Done!

### What You Should Have Now

✅ Database with dual knowledge base (tax law + vendor background)
✅ AI analysis pipeline that reads invoices and determines refunds
✅ Excel-based review workflow
✅ Self-improving system that learns from your corrections
✅ Audit trail of all decisions

### Next Steps

1. **Process more data** - The more you analyze, the smarter it gets
2. **Review learning** - Periodically check what system has learned
3. **Update knowledge base** - Add new tax laws, vendor info as needed
4. **Monitor accuracy** - Track how often AI is correct vs needs correction

---

## 📊 Success Metrics

Track these to measure system performance:

```sql
-- Approval rate (AI accuracy)
SELECT
    review_status,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analysis_reviews) as percentage
FROM analysis_reviews
GROUP BY review_status;

-- Average confidence over time
SELECT
    DATE(created_at) as date,
    AVG(ai_confidence) as avg_confidence
FROM analysis_results
GROUP BY DATE(created_at)
ORDER BY date;

-- Learning growth
SELECT
    DATE(created_at) as date,
    COUNT(*) as patterns_learned
FROM vendor_product_patterns
GROUP BY DATE(created_at)
ORDER BY date;
```

**Goals:**
- Approval rate: >70% after first month
- Average confidence: >80% after building knowledge base
- Learning growth: Steady increase in patterns

---

## 🆘 Need Help?

### Stuck on a Step?

**Check:**
1. Error messages in terminal
2. Supabase logs in dashboard
3. Verification queries in checklist
4. Relevant documentation in `docs/`

**Common Issues:**
- Database connection → Check SUPABASE_URL and SUPABASE_KEY
- PDF not found → Verify file paths match Excel columns
- Low confidence → Need more knowledge base documents
- Import fails → Ensure --save-db was used during analysis

### Documentation

- **Full workflow:** `docs/EXCEL_WORKFLOW_GUIDE.md`
- **Knowledge base:** `docs/KNOWLEDGE_BASE_GUIDE.md`
- **Architecture:** `docs/SYSTEM_ARCHITECTURE.md`
- **Quick reference:** `docs/QUICK_REFERENCE.md`
- **This checklist:** `docs/GETTING_STARTED_CHECKLIST.md`

---

**Estimated Total Setup Time:** 2-3 hours (including document collection)

**Good luck! 🚀**
