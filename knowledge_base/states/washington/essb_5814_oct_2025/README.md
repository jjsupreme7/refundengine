# ESSB 5814 - Washington State Tax Law Changes (Effective October 1, 2025)

## Overview

This folder contains official documents and professional analysis regarding **Engrossed Substitute Senate Bill 5814** (Chapter 422, 2025 Laws), which significantly expanded Washington State's retail sales tax to include various business services effective October 1, 2025.

## What Changed

ESSB 5814 made the following services subject to retail sales tax and retailing B&O tax:

1. **Information Technology Services** - Help desk, network support, system administration
2. **Advertising Services** - Design, placement, campaign planning (digital and non-digital)
3. **Custom Website Development** - Design and development services
4. **Custom Software** - Sales and customization of software
5. **Temporary Staffing Services** - Short-term worker placement
6. **Investigation, Security, and Armored Car Services**
7. **Live Presentations** - Workshops, webinars with real-time interaction

## Key Dates

- **Signed into law**: May 20, 2025
- **Effective date**: October 1, 2025
- **Transition period for existing contracts**: Through March 31, 2026

## Documents in This Folder

### Official Legislative Documents

1. **01_ESSB_5814_Session_Law.pdf**
   - Official enrolled bill text (Chapter 422, 2025 Laws)
   - The actual statutory language
   - Source: Washington State Legislature

2. **02_Final_Bill_Report.pdf**
   - Legislative summary of the bill
   - Synopsis as enacted
   - Source: Washington State Legislature

### Professional Tax Analysis

3. **03_KPMG_October_2025_Analysis.pdf**
   - SALT Alert 2025-11 (October 16, 2025)
   - Analysis of DOR interim guidance on newly taxable services
   - Covers transition rules and compliance requirements
   - Source: KPMG

4. **04_KPMG_May_2025_Analysis.pdf**
   - SALT Alert (May 28, 2025)
   - Initial analysis when bill was signed into law
   - Overview of significant sales tax and B&O tax changes
   - Source: KPMG

5. **05_Deloitte_Tax_Alert.pdf**
   - Multistate Tax Alert (June 20, 2025)
   - Analysis of hardware training and custom website development
   - Source: Deloitte

## Transition Rules (Critical for Refund Analysis)

### Existing Contracts Signed Before October 1, 2025

**Scenario 1**: Contract price paid BEFORE October 1, 2025
- **Treatment**: No retail sales tax due (grandfathered)
- **Applies**: Even if services continue after October 1, 2025

**Scenario 2**: Contract price NOT paid, terms unchanged
- **Treatment**: Can continue old tax treatment through March 31, 2026
- **Starting April 1, 2026**: Must collect retail sales tax

**Scenario 3**: Contract altered after October 1, 2025
- **Treatment**: Immediately subject to retail sales tax
- **"Altered"**: Material or substantive changes to contract

## Impact on Refund Analysis

This law change creates a **temporal boundary** for tax treatment:

### Before October 1, 2025
- IT services: Service & Other B&O tax, no sales tax
- Advertising: Service & Other B&O tax, no sales tax
- Custom software: Service & Other B&O tax, no sales tax
- Custom web development: Service & Other B&O tax, no sales tax

### After October 1, 2025
- All above services: Retailing B&O tax + retail sales tax
- Rate: Combined state/local retail sales tax rate

### Refund Implications

**For invoices dated before October 1, 2025:**
- If sales tax was charged on IT services → **REFUND ELIGIBLE** (not taxable at that time)
- If sales tax was charged on advertising → **REFUND ELIGIBLE** (not taxable at that time)

**For invoices dated after October 1, 2025:**
- Sales tax on IT services → **CORRECT** (now taxable)
- Sales tax on advertising → **CORRECT** (now taxable)

**For existing contracts:**
- Check contract date and payment dates
- Apply transition rules above

## Related DOR Guidance (Not in This Folder - HTML Only)

The Washington Department of Revenue has published interim guidance statements:

- **Services Overview**: https://dor.wa.gov/taxes-rates/retail-sales-tax/services-newly-subject-retail-sales-tax
- **Contracts Prior to Oct 1**: https://dor.wa.gov/laws-rules/interim-guidance-statement-regarding-contracts-existing-prior-october-1-2025-and-changes-made-essb
- **IT Services**: https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-information-technology-services
- **Advertising**: https://dor.wa.gov/laws-rules/interim_guidance_statements/interim-guidance-statement-regarding-changes-made-essb-5814-advertising-services
- **Custom Website Development**: https://dor.wa.gov/laws-rules/interim-guidance-statement-regarding-changes-made-essb-5814-custom-website-development-services

## Ingestion Instructions

To add these documents to the RAG system:

```bash
# From project root
python core/ingest_documents.py \
  --input-folder knowledge_base/states/washington/essb_5814_oct_2025 \
  --document-type tax_law \
  --law-category essb_5814 \
  --effective-date 2025-10-01
```

## Metadata Tags for RAG

When ingesting, use these metadata tags:

- **document_type**: `tax_law`
- **law_category**: `essb_5814` or `law_change_2025`
- **effective_date**: `2025-10-01`
- **supersedes**: Prior treatment of these services
- **jurisdiction**: `washington`
- **topics**: `information_technology`, `advertising`, `custom_software`, `website_development`, `temporary_staffing`, `security_services`, `live_presentations`

## RAG Query Examples

Users should be able to ask:

- "Are IT services taxable in Washington?"
  - RAG should explain: **DEPENDS ON DATE** - No before Oct 1, 2025; Yes after

- "Was advertising taxable before October 2025?"
  - RAG should answer: **NO** - became taxable Oct 1, 2025 under ESSB 5814

- "I have an invoice from Microsoft for IT services dated September 2025 with sales tax. Is this correct?"
  - RAG should answer: **NO** - IT services were not taxable before Oct 1, 2025. Likely refund eligible.

## Document Information

- **Folder created**: November 14, 2025
- **Last updated**: November 14, 2025
- **Total documents**: 5 PDFs
- **Total size**: ~740 KB
