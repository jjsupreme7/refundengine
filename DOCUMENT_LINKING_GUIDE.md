# Document Linking Guide

## 🔗 Overview

The system now **automatically links related documents** together! This helps you understand which invoices relate to which purchase orders, statements of work, and master agreements.

## 📋 What Gets Linked

### 1. **Invoice ↔ Purchase Order**
- **Method**: Exact PO number matching
- **How**: System reads PO number from invoice and finds matching PO document
- **Confidence**: 100% (exact match)
- **Example**: Invoice references "PO-12345" → Finds PO document with number "PO-12345"

### 2. **Invoice ↔ Statement of Work**
- **Method**: AI semantic matching
- **How**: AI analyzes vendor names, dates, and service descriptions
- **Confidence**: 60-100% (AI determines match quality)
- **Example**: Consulting invoice from Microsoft dated Nov 2024 → Matches to Microsoft SOW for "Cloud Migration Project" from Oct 2024

### 3. **Master Agreement Detection** (Future)
- Coming soon: Links invoices to master agreements
- Will detect agreement references in documents

## 🚀 How to Use

### **Automatic Linking (Recommended)**

The **full pipeline now includes linking automatically**:

```bash
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/
```

This will:
1. ✅ Ingest documents
2. ✅ **Link documents automatically** (NEW!)
3. ✅ Identify products
4. ✅ Analyze refunds
5. ✅ Generate reports with relationships shown

### **Manual Linking**

If you want to link documents separately:

```bash
# Link all documents for a client
python scripts/link_documents.py --client_id 1

# Re-link all documents (clears old links first)
python scripts/link_documents.py --client_id 1 --relink

# View existing relationships
python scripts/link_documents.py --client_id 1 --view
```

## 📊 Where to See Links

### **In Excel Reports**

Client reports now include a **"Document Relationships"** sheet showing:
- Which invoices link to which POs
- Which invoices link to which SOWs
- Confidence scores for each link
- Reference information (PO numbers, matching reasons)

Example:
```
Invoice         | Related To              | Type          | Reference      | Confidence
----------------|-------------------------|---------------|----------------|------------
INV-2024-001    | PO_12345.pdf           | Purchase Order| PO-12345       | 100%
INV-2024-001    | SOW_CloudMigration.pdf | SOW           | Vendor & dates | 85%
INV-2024-002    | PO_67890.pdf           | Purchase Order| PO-67890       | 100%
```

### **Via Command Line**

```bash
python scripts/link_documents.py --client_id 1 --view
```

Output:
```
📋 INVOICE REFERENCES PO
   (2 relationships)

  Microsoft_Invoice_789.pdf
    └─→ Microsoft_PO_456.pdf
        Confidence: 100%
        Reference: PO-456789

  AWS_Invoice_123.pdf
    └─→ AWS_PO_789.pdf
        Confidence: 100%
        Reference: PO-789123

📋 INVOICE BILLS SOW
   (1 relationship)

  Consulting_Invoice_001.pdf
    └─→ SOW_CloudMigration.pdf
        Confidence: 85%
        Reference: Matching vendor (Microsoft) and date range
```

## 🎯 Linking Logic

### **PO → Invoice Linking**

**Step 1**: Extract PO number from invoice
```
Invoice metadata extraction finds:
purchase_order_number: "PO-12345"
```

**Step 2**: Search for matching PO
```sql
SELECT * FROM purchase_orders
WHERE po_number = "PO-12345"
  OR po_number LIKE "%12345%"
```

**Step 3**: Create relationship
```
✅ 100% confidence (exact match)
```

### **SOW → Invoice Linking**

**Step 1**: Find potential SOWs
```sql
SELECT * FROM statements_of_work
WHERE vendor_name LIKE "%Microsoft%"
```

**Step 2**: AI analyzes each match
```
AI considers:
- Vendor name similarity
- Date proximity (invoice after SOW date?)
- Service description overlap
- Project/engagement names

Returns confidence: 0-100%
```

**Step 3**: Create high-confidence links
```
Only creates link if confidence ≥ 60%
✅ 85% confidence = strong match
⚠️  55% confidence = too low, skipped
```

## 💡 Best Practices

### **1. Clear Filenames Help (But Not Required)**

While AI doesn't need clear filenames for classification, they help YOU track relationships:

**Good**:
```
Microsoft_Invoice_INV789_20241105.pdf
Microsoft_PO_PO456_20241020.pdf
Microsoft_SOW_CloudMigration_20241015.pdf
```

**Also Works** (AI reads content):
```
scan_001.pdf  (invoice)
scan_002.pdf  (PO)
scan_003.pdf  (SOW)
```

### **2. Include PO Numbers on Invoices**

For automatic PO linking, invoices should reference the PO number:
- In invoice header: "Re: PO-12345"
- In invoice fields: "Purchase Order: PO-12345"
- Anywhere in the document

### **3. Consistent Vendor Names**

For better SOW matching, use consistent vendor names:
- ✅ "Microsoft Corporation" everywhere
- ❌ "Microsoft Corp", "MSFT", "Microsoft Inc." (harder to match)

### **4. Date Proximity**

Invoices should be dated after related SOWs:
- ✅ SOW: Oct 2024 → Invoice: Nov 2024 (good match)
- ⚠️ SOW: Nov 2024 → Invoice: Sep 2024 (confusing, lower confidence)

## 🔧 Troubleshooting

### **"No relationships found"**

**Cause**: Documents weren't linked yet

**Solution**:
```bash
python scripts/link_documents.py --client_id 1
```

### **"Invoice not linked to PO but should be"**

**Possible causes**:
1. PO number format doesn't match
   - Invoice says "PO-12345"
   - PO document says "12345" (missing "PO-")
   - System tries to match both, but verify

2. PO document not processed yet
   - Upload PO to `client_documents/uploads/`
   - Run ingestion again

**Solution**:
```bash
# Re-run linking with --relink flag
python scripts/link_documents.py --client_id 1 --relink
```

### **"Invoice not linked to SOW but should be"**

**Possible causes**:
1. **Low AI confidence** (<60%)
   - Vendor names very different
   - Date ranges don't align
   - Service descriptions don't overlap

2. **SOW not processed yet**
   - Upload SOW and run ingestion

**Solution**:
Check confidence with:
```bash
python scripts/link_documents.py --client_id 1 --view
```

If confidence is 50-59%, you might want to manually verify and adjust the confidence threshold in `link_documents.py`:

```python
# Line ~215 in link_documents.py
if confidence < 60:  # Change to 50 if needed
    print(f"  ⚠️  Low confidence match...")
```

### **"Incorrect SOW match"**

**Cause**: AI matched invoice to wrong SOW (rare)

**Solution**:
1. Check document descriptions - are they clear?
2. Re-run with `--relink` after improving document clarity
3. Manually verify relationships in database if needed

## 📈 Understanding Confidence Scores

### **100% - Perfect Match**
- PO numbers exactly match
- No ambiguity

### **85-99% - Very Strong Match**
- Vendor names match exactly
- Dates align well
- Service descriptions overlap significantly
- High confidence for reporting

### **70-84% - Strong Match**
- Vendor names match (minor variations)
- Dates align reasonably
- Some service description overlap
- Reliable for most purposes

### **60-69% - Moderate Match**
- Vendor match but with variations
- Dates align loosely
- Limited description overlap
- Worth including but review recommended

### **<60% - Too Weak**
- Not linked automatically
- Manual review needed if you think they should be linked

## 🗄️ Database Schema

Relationships are stored in the `document_relationships` table:

```sql
CREATE TABLE document_relationships (
    source_document_id   -- Invoice document ID
    target_document_id   -- PO or SOW document ID
    relationship_type    -- "invoice_references_po" or "invoice_bills_sow"
    confidence_score     -- 0-100
    matched_reference    -- PO number or matching reason
    matching_method      -- "po_number_match" or "ai_semantic_match"
);
```

## 🎯 Quick Reference

```bash
# Automatic linking (part of pipeline)
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/

# Manual linking
python scripts/link_documents.py --client_id 1

# Re-link everything
python scripts/link_documents.py --client_id 1 --relink

# View relationships
python scripts/link_documents.py --client_id 1 --view

# See in Excel report
# → Open: outputs/reports/[ClientName]_Refund_Report_[Date].xlsx
# → Go to: "Document Relationships" sheet
```

## ✨ Benefits

1. **Audit Trail**: See which invoices relate to which agreements
2. **Compliance**: Track PO authorization for all invoices
3. **Analysis**: Understand project billing patterns
4. **Verification**: Confirm invoices match approved scopes
5. **Reporting**: Show clients document relationships clearly

---

**Questions?** The linking happens automatically now - just run the pipeline! 🚀
