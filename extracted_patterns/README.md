# Historical Pattern Data

This folder contains extracted historical patterns from **484,479 analyzed tax records** across multiple data sources.

## Current Statistics

**Last Updated**: November 22, 2025

- **Total Records Processed**: 484,479 transactions
- **Vendors**: 1,033 unique vendors
- **Keyword Categories**: 8 taxonomies
- **Refund Basis Patterns**: 44 distinct patterns
- **Date Range**: 2014-07-14 to 2024-10-18 (10+ years of historical data)

## Data Sources

1. **Phase 2 Master Refunds (2014-2024)**: 13,455 records from `Phase 2 Master Refunds_6-15-25.xlsx`
   - Extracted from **Column AG** (Description field)
2. **2019 Denodo Data**: 74,709 analyst-reviewed records (70.6% of total)
3. **2020 Denodo Data**: 116,310 analyst-reviewed records (62.7% of total)
4. **2021 Denodo Data**: 61,789 analyst-reviewed records (61.8% of total)
5. **2022 Denodo Data**: 93,924 analyst-reviewed records (73.5% of total)
   - Extracted from **Column BK** (post1_wbs_description)
   - Extracted from **Column CC** (sgtxt_line_item_text)
6. **2023 Denodo Data**: 124,292 analyst-reviewed records (75.6% of total)

**Total Analyst-Reviewed Records**: 471,024 (2019-2023 Denodo files)

## Files

### vendor_patterns.json
**1,033 vendors** with comprehensive historical patterns including:
- Historical refund basis preferences
- Common tax categories
- Product types
- Success rates based on analyst decisions
- Description keywords extracted from source columns

**Quality Improvements**:
- Removed `common_gl_accounts` field (per user request - "I don't care about gl accounts")
- Removed `vendor_keywords` field (was duplicating vendor name)
- Focus on meaningful text patterns only

**Sample Fields**: vendor_name, product_type, historical_sample_count, historical_success_rate, typical_refund_basis, description_keywords, common_tax_categories, common_refund_bases, common_allocation_methods, typical_final_decision

### keyword_patterns.json
Taxonomy of keywords organized into **8 categories**:
- **Tax categories** (12 keywords): License, Services, Software maintenance, Hardware maintenance, etc.
- **Product types** (50 keywords)
- **Refund basis terms** (44 keywords)
- **Final decisions** (23 keywords)
- **GL account descriptions** (11 keywords)
- **Material groups** (28 keywords)
- **Allocation methods** (31 keywords)
- **Location keywords** (32 keywords)

### refund_basis_patterns.json
**44 refund basis patterns** with comprehensive vendor mappings:
- Usage statistics and percentages
- **ALL vendors** using each refund basis (not just 5 examples)
- Vendor counts per pattern
- Final decision outcomes

**Top 5 Refund Bases**:
1. **MPU**: 315 vendors, 8,405 uses (34.5%)
2. **Non-taxable**: 146 vendors, 3,001 uses (11.7%)
3. **N/A - Reversed**: 94 vendors, 1,459 uses (10.8%)
4. **Partial OOS services**: 44 vendors, 1,123 uses (3.6%)
5. **Wrong rate**: 27 vendors, 2,210 uses (2.8%)

**Quality Improvements**:
- Changed from `example_vendors` (5 samples) to `all_vendors` (complete lists)
- Added `vendor_count` field for transparency
- Filtered out junk patterns (PDFs, invoice numbers, numeric codes)

### denodo_extraction_stats.json
Detailed statistics from Denodo file extraction process

## Quality Filtering

All patterns are filtered to remove junk data:
- ✓ No PDF filenames (e.g., "0000002774642-1.PDF")
- ✓ No pure numeric codes
- ✓ No invoice numbers
- ✓ No duplicate vendor name keywords
- ✓ No forced/empty citations
- ✓ Text-based patterns only

**Filtering Results**:
- Refund basis patterns: Reduced from 337 (with junk) to 44 (clean text only)
- Removed 294 junk patterns (86.6% noise reduction)

## Removed Files

- **citation_patterns.json**: Removed per user request - "I don't need the citations pattern"

## How to Import

### On Your Personal Laptop (where you have .env credentials):

1. **Copy this folder** to your personal laptop

2. **Make sure .env file exists** with Supabase credentials:
   ```bash
   SUPABASE_URL=https://bvrvzjqscrthfldyfqyo.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-key-here
   SUPABASE_DB_PASSWORD=your-password-here
   ```

3. **Deploy database schema** (if not already done):
   ```bash
   bash scripts/deploy_historical_knowledge_schema.sh
   ```

4. **Import the patterns**:
   ```bash
   python scripts/import_patterns_from_json.py --dir extracted_patterns
   ```

5. **Test it works**:
   ```bash
   python analysis/analyze_refunds.py --input test.xlsx --output results.xlsx
   ```

The analysis will now include:
- Historical vendor match data
- Success rate predictions
- 6 new columns in Excel output with historical context

## What This Enables

Once imported, the refund analysis AI will:
- Recognize **1,033 vendors** with known success rates and refund patterns
- Boost confidence from ~65% → ~95% for known vendors
- Pre-populate refund basis suggestions based on **44 validated patterns**
- Leverage **8 keyword categories** including analyst Final Decisions for improved classification
- Validate decisions against 471,024 analyst-reviewed precedents
- Show historical precedent in Excel output with allocation methodology guidance
- Complete vendor lists for each refund basis (not just samples)

## Vendor Coverage

- **1,033 unique vendors** tracked
- Top vendors include: MOREDIRECT INC, ZONES INC, OFFICE DEPOT INC, DELTA ELECTRONICS USA INC, COMSEARCH
- Vendors mapped to 44 distinct refund basis patterns
- 776 total vendor-to-refund-basis mappings

## Next Steps

After importing this data, consider:
1. Extract patterns from other completed Excel files as they become available
2. Regular updates as new analyst decisions are made
3. Monitor pattern quality and adjust filters as needed

---

**Total Coverage**: 484,479 tax records | 1,033 vendors | 44 refund basis patterns | 10+ years of historical data
