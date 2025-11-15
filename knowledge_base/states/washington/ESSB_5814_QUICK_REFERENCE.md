# ESSB 5814 Quick Reference Guide

## 🎯 What You Need to Know

**ESSB 5814** (Chapter 422, 2025 Laws) is the **largest tax expansion in Washington State history**, making 7-8 categories of business services subject to retail sales tax for the first time.

**Effective Date**: October 1, 2025

---

## 📋 Services Now Taxable (After Oct 1, 2025)

| Service Type | Before Oct 1, 2025 | After Oct 1, 2025 | Refund Impact |
|--------------|-------------------|-------------------|---------------|
| **Information Technology Services** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |
| **Advertising Services** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |
| **Custom Website Development** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |
| **Custom Software** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |
| **Temporary Staffing** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |
| **Investigation/Security Services** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |
| **Live Presentations** | Service B&O, no sales tax | Retailing B&O + sales tax | Sales tax charged before Oct 1 = REFUND |

---

## 🗓️ Critical Dates

- **May 20, 2025**: Bill signed into law
- **July 27, 2025**: Law effective (signing date + 68 days)
- **October 1, 2025**: Retail sales tax provisions take effect
- **March 31, 2026**: End of transition period for existing contracts
- **April 1, 2026**: All existing contracts must collect sales tax

---

## 🔄 Transition Rules for Existing Contracts

### Scenario 1: Paid Before October 1, 2025
- **Contract signed**: Before Oct 1, 2025
- **Payment received**: Before Oct 1, 2025
- **Services performed**: After Oct 1, 2025
- **Tax treatment**: **NO SALES TAX** (grandfathered)

### Scenario 2: Not Paid, Unchanged Contract
- **Contract signed**: Before Oct 1, 2025
- **Payment received**: After Oct 1, 2025
- **Contract terms**: Unchanged
- **Tax treatment**:
  - Through March 31, 2026: Old treatment (no sales tax)
  - After April 1, 2026: Must collect sales tax

### Scenario 3: Contract Altered After Oct 1
- **Contract signed**: Before Oct 1, 2025
- **Contract altered**: After Oct 1, 2025 (material changes)
- **Tax treatment**: **Immediate sales tax** at time of alteration

---

## 🎯 Refund Analysis Impact

### For Invoice Review

When analyzing invoices for refund eligibility, **DATE MATTERS**:

#### Before October 1, 2025
```
Invoice Date: September 15, 2025
Vendor: Acme IT Services
Line Item: "Network support and help desk" - $10,000
Sales Tax Charged: $1,000

ANALYSIS: ❌ INCORRECT - IT services not taxable before Oct 1, 2025
RECOMMENDATION: REFUND ELIGIBLE - $1,000
```

#### After October 1, 2025
```
Invoice Date: October 15, 2025
Vendor: Acme IT Services
Line Item: "Network support and help desk" - $10,000
Sales Tax Charged: $1,000

ANALYSIS: ✅ CORRECT - IT services taxable after Oct 1, 2025
RECOMMENDATION: NO REFUND - Properly taxed
```

#### Existing Contract (Transition Period)
```
Contract Date: August 1, 2025
Invoice Date: November 1, 2025
Service: Custom software development - $50,000
Sales Tax Charged: $0 (contract allows old treatment through March 2026)

ANALYSIS: ✅ CORRECT - Transition rules apply
RECOMMENDATION: NO ISSUE - Valid use of transition rules
```

---

## 🤖 RAG System Implementation

### Metadata Tags

When ingesting ESSB 5814 documents, use:
```json
{
  "document_type": "tax_law",
  "law_category": "essb_5814",
  "effective_date": "2025-10-01",
  "supersedes_date": "2025-09-30",
  "jurisdiction": "washington",
  "law_change": true,
  "topics": [
    "information_technology",
    "advertising",
    "custom_software",
    "website_development",
    "temporary_staffing",
    "security_services",
    "live_presentations"
  ]
}
```

### Query Handling Strategy

**User asks**: "Are IT services taxable in Washington?"

**RAG should**:
1. Retrieve both old law (pre-Oct 1) and new law (post-Oct 1) chunks
2. Generate comparative answer:

```
IT services tax treatment in Washington CHANGED on October 1, 2025:

BEFORE October 1, 2025:
- IT services were NOT retail sales
- Subject to Service & Other B&O tax only
- NO retail sales tax applied

AFTER October 1, 2025:
- IT services ARE retail sales (ESSB 5814)
- Subject to Retailing B&O tax
- Retail sales tax MUST be collected

If you have a specific date or transaction, please provide it for
accurate guidance.

Source: ESSB 5814 (Chapter 422, 2025 Laws)
```

### Temporal Filtering

Implement date-aware retrieval:

```python
def search_with_temporal_awareness(query, invoice_date=None):
    if invoice_date:
        if invoice_date < datetime(2025, 10, 1):
            # Search old law
            return rag.search(query, filters={'effective_before': '2025-10-01'})
        else:
            # Search new law
            return rag.search(query, filters={'effective_after': '2025-10-01'})
    else:
        # Return both and explain the change
        old_results = rag.search(query, filters={'effective_before': '2025-10-01'})
        new_results = rag.search(query, filters={'effective_after': '2025-10-01'})
        return comparative_answer(old_results, new_results)
```

---

## 📁 Document Locations

All ESSB 5814 documents are stored in:
```
knowledge_base/states/washington/essb_5814_oct_2025/
├── 01_ESSB_5814_Session_Law.pdf (197KB, 8 pages)
├── 02_Final_Bill_Report.pdf (12KB, 4 pages)
├── 03_KPMG_October_2025_Analysis.pdf (203KB)
├── 04_KPMG_May_2025_Analysis.pdf (171KB)
├── 05_Deloitte_Tax_Alert.pdf (156KB)
└── README.md (detailed documentation)
```

---

## ⚠️ Common Pitfalls

### Pitfall 1: Ignoring Transition Rules
❌ **Wrong**: "Invoice dated October 2025 with no sales tax = ERROR"
✅ **Right**: Check if existing contract with transition protection applies

### Pitfall 2: Applying New Law Retroactively
❌ **Wrong**: "IT services have always been taxable in WA"
✅ **Right**: "IT services became taxable October 1, 2025 under ESSB 5814"

### Pitfall 3: Missing Refund Opportunities
❌ **Wrong**: Ignoring pre-Oct 2025 invoices that charged sales tax
✅ **Right**: Flag all pre-Oct 2025 sales tax on newly taxable services as refund eligible

---

## 📞 Additional Resources

- **DOR Services Overview**: https://dor.wa.gov/taxes-rates/retail-sales-tax/services-newly-subject-retail-sales-tax
- **Legislative Bill Summary**: https://app.leg.wa.gov/billsummary/?BillNumber=5814&Year=2025
- **Full Session Law**: See `01_ESSB_5814_Session_Law.pdf` in this folder

---

## ✅ Checklist for Implementation

- [x] Download ESSB 5814 documents
- [x] Organize in knowledge_base folder
- [ ] Ingest documents into Supabase
- [ ] Add temporal metadata (effective_date fields)
- [ ] Update RAG queries to handle date-based filtering
- [ ] Test comparative answers (old law vs new law)
- [ ] Update invoice analysis logic for Oct 1, 2025 boundary
- [ ] Add transition rule checking for existing contracts

---

**Last Updated**: November 14, 2025
