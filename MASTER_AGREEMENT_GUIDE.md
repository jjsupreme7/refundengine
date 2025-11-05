# Master Agreement Linking Guide

## 🔗 Overview

The system now supports a **complete 4-level document hierarchy**! This guide explains how master agreements fit into the document linking system.

```
Master Agreement
    ↓
    ├─→ Statement of Work (SOW)
    │      ↓
    │      └─→ Invoice(s)
    │
    └─→ Purchase Order (PO)
           ↓
           └─→ Invoice(s)
```

## 📊 The 4-Level Hierarchy

### **Level 1: Master Agreement (Top)**
- **What**: Overarching agreement establishing overall terms
- **Contains**: General terms, pricing structure, overall relationship framework
- **Duration**: Usually multi-year
- **Example**: "Microsoft Master Service Agreement 2024-2027"

### **Level 2: SOW or PO (Middle)**
- **Statement of Work (SOW)**:
  - Specific project or engagement under the master agreement
  - References the master agreement
  - Describes deliverables, timeline, costs for a specific project
  - Example: "Cloud Migration Project SOW - Q4 2024"

- **Purchase Order (PO)**:
  - Specific purchase authorization
  - May reference master agreement or SOW
  - Lists items/services to be ordered
  - Example: "PO-12345 for consulting hours"

### **Level 3: Invoice (Bottom)**
- **What**: Bill for work performed
- **References**: PO number (usually), project/SOW name
- **Links to**: Both PO and SOW (when applicable)
- **Example**: "Invoice INV-789 for November consulting"

## 🎯 How Master Agreement Linking Works

### **Automatic Linking Methods**

#### **1. Exact Reference Match (100% Confidence)**
When a SOW explicitly references a master agreement:

```
SOW Document contains:
"This work is performed under Master Agreement MSA-2024-001"

System finds:
Master Agreement with agreement_number = "MSA-2024-001"

Result: ✅ Linked with 100% confidence
```

#### **2. AI Semantic Matching (70-100% Confidence)**
When SOW doesn't have explicit reference, AI analyzes:
- **Vendor name match**: "Microsoft Corporation" vs "Microsoft Corp"
- **Date alignment**: SOW dated after MA effective date
- **Scope description**: Does SOW work fall under MA scope?
- **Agreement title similarity**: Keywords in both documents

```
SOW: "Cloud Services Consulting - Microsoft - Oct 2024"
MA: "Microsoft Cloud Services Master Agreement - Jan 2024"

AI Analysis:
- Vendor match: 100%
- Date alignment: ✓ (SOW after MA)
- Scope overlap: "Cloud Services" appears in both

Result: ✅ Linked with 85% confidence
```

## 🚀 Using the System

### **End-to-End Workflow**

```bash
# 1. Drop all documents in uploads folder
# - Master agreements
# - SOWs
# - POs
# - Invoices

# 2. Run the full pipeline (includes linking)
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/

# This automatically:
# ✅ Classifies all documents (AI reads content, determines type)
# ✅ Links invoices to POs (by PO number)
# ✅ Links invoices to SOWs (by vendor, dates, descriptions)
# ✅ Links SOWs to master agreements (by reference or AI matching)
# ✅ Generates Excel report showing full hierarchy
```

### **Manual Linking Only**

```bash
# If you already ingested but want to (re)link:
python scripts/link_documents.py --client_id 1

# Re-link everything (clears old links first):
python scripts/link_documents.py --client_id 1 --relink

# View existing relationships:
python scripts/link_documents.py --client_id 1 --view
```

## 📋 Best Practices

### **1. Master Agreement Document Clarity**

**What AI needs to find in your MA:**
- Agreement number/ID (e.g., "MSA-2024-001")
- Agreement title (e.g., "Microsoft Master Service Agreement")
- Vendor name (consistent across all docs)
- Effective date and expiration date
- Scope description

**Example Good MA:**
```
MASTER SERVICE AGREEMENT

Agreement Number: MSA-2024-001
Title: Cloud Services Master Agreement
Parties: Your Company and Microsoft Corporation
Effective: January 1, 2024
Expires: December 31, 2026

Scope: This agreement covers all cloud consulting, migration,
and support services to be performed by Microsoft...
```

### **2. SOW References to Master Agreement**

**BEST - Explicit Reference:**
```
This Statement of Work is executed under
Master Agreement MSA-2024-001 dated January 1, 2024.
```

**GOOD - Implicit Reference:**
```
Services Agreement
Under the Cloud Services Master Agreement
Vendor: Microsoft Corporation
```

**OKAY - AI Will Try to Match:**
```
Cloud Migration SOW
Microsoft Corporation
Date: October 2024
```

### **3. Filename Organization**

While AI **doesn't require** specific filenames (it reads content), clear names help YOU track documents:

**Recommended Structure:**
```
uploads/
  ├─ Microsoft_MSA_2024-2026.pdf                    (Master Agreement)
  ├─ Microsoft_CloudMigration_SOW_Q42024.pdf        (SOW under MA)
  ├─ Microsoft_PO_12345_20241020.pdf                (PO)
  └─ Microsoft_Invoice_INV789_20241105.pdf          (Invoice)
```

**Also Works (AI reads content):**
```
uploads/
  ├─ scan001.pdf    (MA - AI will detect from content)
  ├─ scan002.pdf    (SOW - AI will detect from content)
  ├─ scan003.pdf    (PO - AI will detect from content)
  └─ scan004.pdf    (Invoice - AI will detect from content)
```

### **4. Vendor Name Consistency**

Use consistent vendor names across all documents for better matching:

✅ **Consistent:**
```
Master Agreement: "Microsoft Corporation"
SOW: "Microsoft Corporation"
Invoice: "Microsoft Corporation"
```

⚠️ **Inconsistent (harder to match):**
```
Master Agreement: "Microsoft Corp"
SOW: "MSFT"
Invoice: "Microsoft Inc."
```

## 📊 Understanding Confidence Scores

### **Master Agreement → SOW Linking**

| Confidence | Meaning | How It Happens |
|------------|---------|----------------|
| **100%** | Perfect Match | SOW explicitly references MA number/title |
| **90-99%** | Very Strong | Exact vendor, dates align, scope overlap |
| **80-89%** | Strong | Vendor match, dates reasonable, some scope match |
| **70-79%** | Moderate | Vendor similar, dates loosely align |
| **<70%** | Too Weak | Not linked - manual review needed |

**Note:** Master agreement linking has a **higher threshold (70%)** than SOW-invoice linking (60%) because MA relationships are more critical.

## 📈 Viewing the Hierarchy

### **In Excel Reports**

The "Document Relationships" sheet shows:

```
Master Agreement          | SOW/PO                    | Invoice        | Relationship Type      | Confidence
-------------------------|---------------------------|----------------|------------------------|------------------
Microsoft_MSA_2024.pdf   | CloudMigration_SOW.pdf   | INV-789.pdf    | MA → SOW → Invoice    | 100% (MA-SOW), 85% (SOW-Inv)
Microsoft_MSA_2024.pdf   | AzureConsulting_SOW.pdf  | INV-790.pdf    | MA → SOW → Invoice    | 95% (MA-SOW), 90% (SOW-Inv)
No MA                    | WebDev_SOW.pdf           | INV-791.pdf    | SOW → Invoice         | 75%
N/A                      | Hardware_PO_12345.pdf    | INV-792.pdf    | PO → Invoice          | 100%
```

### **Via Command Line**

```bash
python scripts/link_documents.py --client_id 1 --view
```

Output:
```
📋 SOW UNDER MASTER AGREEMENT
   (2 relationships)

  CloudMigration_SOW.pdf
    └─→ Microsoft_MSA_2024.pdf
        Confidence: 100%
        Reference: Reference: MSA-2024-001

  AzureConsulting_SOW.pdf
    └─→ Microsoft_MSA_2024.pdf
        Confidence: 95%
        Reference: Matching vendor (Microsoft) and date range

📋 INVOICE BILLS SOW
   (3 relationships)

  Invoice_INV789.pdf
    └─→ CloudMigration_SOW.pdf
        Confidence: 85%
        Reference: Matching vendor and project description

  Invoice_INV790.pdf
    └─→ AzureConsulting_SOW.pdf
        Confidence: 90%
        Reference: PO reference and vendor match
```

## 🔧 Troubleshooting

### **"SOW not linked to MA but should be"**

**Possible Causes:**
1. **No MA document uploaded**
   - Upload MA to `client_documents/uploads/`
   - Run ingestion: `python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1`

2. **Vendor name mismatch**
   - Check vendor names in both documents
   - SOW: "Microsoft Corp" vs MA: "Microsoft Corporation"
   - Small variations are okay, but major differences (like "MSFT") may fail

3. **Low AI confidence (<70%)**
   - Run `--view` to see confidence score
   - If 65-69%, consider lowering threshold in `link_documents.py` line ~419
   - If <65%, documents may genuinely not match

4. **No explicit reference and scope unclear**
   - Add MA reference to SOW if possible
   - Ensure MA scope description is clear

**Solutions:**

```bash
# Check what MAs exist
python scripts/link_documents.py --client_id 1 --view

# Re-run linking
python scripts/link_documents.py --client_id 1 --relink

# Manually verify in database if needed
sqlite3 database/refund_engine.db
SELECT * FROM master_agreements;
SELECT * FROM statements_of_work;
```

### **"MA linked to wrong SOW"**

**Rare but possible causes:**
- Multiple MAs with same vendor
- SOW dates/scope ambiguous

**Solution:**
1. Make MA titles more specific
2. Add explicit MA references to SOWs
3. Check confidence scores - should be 80%+ for correct matches

### **"How do I know if linking worked?"**

**Three ways to verify:**

1. **Run with --view flag:**
```bash
python scripts/link_documents.py --client_id 1 --view
```

2. **Check Excel report:**
```bash
python scripts/generate_client_report.py --client_id 1
# Open: outputs/reports/[ClientName]_Refund_Report_[Date].xlsx
# Go to: "Document Relationships" sheet
```

3. **Query database directly:**
```bash
sqlite3 database/refund_engine.db
SELECT relationship_type, COUNT(*)
FROM document_relationships
GROUP BY relationship_type;
```

## 💡 Advanced: Understanding the Data Model

### **Database Schema**

```sql
-- Master Agreements table
CREATE TABLE master_agreements (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    agreement_number TEXT,        -- e.g., "MSA-2024-001"
    agreement_title TEXT,          -- e.g., "Cloud Services Master Agreement"
    vendor_name TEXT,              -- e.g., "Microsoft Corporation"
    effective_date DATE,           -- When MA starts
    expiration_date DATE,          -- When MA ends
    total_contract_value DECIMAL,  -- Total $ value
    scope_description TEXT         -- What MA covers
);

-- SOWs reference MAs
CREATE TABLE statements_of_work (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    sow_title TEXT,
    vendor_name TEXT,
    master_agreement_reference TEXT,  -- NEW! e.g., "MSA-2024-001"
    service_description TEXT
);

-- Relationships table
CREATE TABLE document_relationships (
    source_document_id INTEGER,    -- SOW document
    target_document_id INTEGER,    -- MA document
    relationship_type TEXT,        -- "sow_under_master_agreement"
    confidence_score INTEGER,      -- 70-100
    matched_reference TEXT,        -- What matched (reference or AI reasoning)
    matching_method TEXT           -- "agreement_reference_match" or "ai_semantic_match"
);
```

### **Relationship Types**

| Type | Direction | Example |
|------|-----------|---------|
| `invoice_references_po` | Invoice → PO | Invoice #789 → PO-12345 |
| `invoice_bills_sow` | Invoice → SOW | Invoice #789 → Cloud Migration SOW |
| `sow_under_master_agreement` | SOW → MA | Cloud Migration SOW → Microsoft MSA 2024 |

## 🎯 Quick Reference

```bash
# Full pipeline (recommended)
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/

# Manual steps
python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1
python scripts/link_documents.py --client_id 1
python scripts/generate_client_report.py --client_id 1

# View relationships
python scripts/link_documents.py --client_id 1 --view

# Re-link everything
python scripts/link_documents.py --client_id 1 --relink
```

## ✨ Benefits of 4-Level Hierarchy

1. **Complete Audit Trail**: See exactly which invoices trace back to which master agreements
2. **Contract Compliance**: Verify all work is authorized under proper agreements
3. **Spend Analysis**: Track spending per master agreement over time
4. **Relationship Mapping**: Understand vendor relationship structure
5. **Risk Management**: Identify work without proper MA coverage

## 📚 Related Documentation

- **DOCUMENT_LINKING_GUIDE.md** - Original 3-level linking (Invoice → PO/SOW)
- **WORKFLOW.md** - Complete system workflow
- **README.md** - Full system documentation
- **QUICKSTART.md** - 5-minute setup guide

---

**Questions?** The system handles master agreements automatically - just upload them with your other documents! 🚀
