# Use Tax Pattern Data

This folder contains extracted patterns from **USE TAX refund analysis** data, separate from sales tax patterns.

## Current Statistics

**Last Updated**: November 22, 2025

- **Total Records Processed**: 32,827 analyst-reviewed use tax transactions
- **Vendors**: 524 unique vendors
- **Keyword Categories**: 4 taxonomies
- **Refund Basis Patterns**: 10 distinct patterns
- **Date Range**: 2021 use tax data

## Data Source

**Primary Source**: Phase_3_2021_Use Tax_10-17-25.xlsx
- **Sheet**: "2021"
- **Total rows**: 114,491
- **Analyst-reviewed rows**: 32,827 (28.7% with Final Decision)
- **Tax Type**: Use Tax only

## Files

### vendor_patterns.json
**524 vendors** with use tax-specific patterns including:
- Historical refund basis preferences for use tax
- Common tax categories
- Success rates based on analyst decisions
- Description keywords extracted from Description and Add'l Info columns
- **Marked with**: `"tax_type": "use_tax"`

**Sample Fields**: vendor_name, tax_type, historical_sample_count, historical_success_rate, typical_refund_basis, typical_final_decision, common_tax_categories, common_refund_bases, description_keywords

### keyword_patterns.json
Taxonomy of keywords organized into **4 categories**:
- **Tax categories**: Services, Tangible goods, License, Hardware, etc.
- **Refund basis terms**: Non-taxable - SIRC RISK, OOS services, Wrong rate, etc.
- **Final decisions**: Add to claim - REFUND SAMPLE, NO OPP, ADDED TO CLAIM
- **Description keywords**: Common words from transaction descriptions

### refund_basis_patterns.json
**10 refund basis patterns** with comprehensive vendor mappings:
- Usage statistics and percentages
- **ALL vendors** using each refund basis (complete lists)
- Vendor counts per pattern
- Final decision outcomes
- **Marked with**: `"tax_type": "use_tax"`

**Top 5 Use Tax Refund Bases**:
1. **Non-taxable - SIRC RISK**: 207 vendors, 6,629 uses (20.2%)
2. **OOS services**: 219 vendors, 5,433 uses (16.6%)
3. **Wrong rate**: 167 vendors, 2,913 uses (8.9%)
4. **OOS shipment**: 94 vendors, 1,347 uses (4.1%)
5. **Non-taxable**: 87 vendors, 1,075 uses (3.3%)

### extraction_stats.json
Statistics from the extraction process

## Key Differences from Sales Tax

### 1. MPU Usage

**Use Tax**: MPU appears in only 394 transactions (1.2%) from 106 vendors
**Sales Tax**: MPU appears in 8,405 transactions (34.5%) from 315 vendors

**Insight**: MPU is **21.3x less common** in use tax. This makes sense because:
- MPU (Multi-Point Use) allocation is primarily a sales tax concept for services/subscriptions
- Use tax is typically assessed on specific purchases brought into state
- Use tax doesn't usually involve ongoing multi-state service allocations

### 2. Dominant Patterns

**Use Tax Top 2 (36.8% of all refunds)**:
1. Non-taxable - SIRC RISK (20.2%)
2. OOS services (16.6%)

**Sales Tax Top 2 (46.2% of all refunds)**:
1. MPU (34.5%)
2. Non-taxable (11.7%)

**Insight**: Use tax refunds are concentrated in out-of-state services and non-taxable determinations, while sales tax refunds are dominated by MPU allocation.

### 3. Vendor Overlap

- **147 vendors** appear in both sales and use tax data
- **377 vendors** appear ONLY in use tax data
- **886 vendors** appear ONLY in sales tax data

## Quality Filtering

All patterns are filtered to remove junk data:
- ✓ No PDF filenames
- ✓ No pure numeric codes
- ✓ No invoice numbers
- ✓ Text-based patterns only

**Filtering Results**:
- 10 clean refund basis patterns extracted
- Focus on analyst-reviewed decisions (Final Decision populated)

## Comparison to Sales Tax

See [SALES_VS_USE_TAX_COMPARISON.md](../SALES_VS_USE_TAX_COMPARISON.md) for detailed analysis of differences between sales and use tax patterns.

## How This Data Is Used

These use tax patterns should be used separately from sales tax patterns when analyzing use tax transactions:

1. **Tax Type Detection**: System should identify if a transaction is sales tax or use tax
2. **Pattern Matching**: Query use_tax patterns for use tax transactions
3. **Confidence Scoring**: Use tax-type-specific success rates
4. **Refund Basis Validation**: Flag if a suggested basis is uncommon for the tax type

Example:
- If analyzing a **use tax** transaction and AI suggests "MPU" → Should flag as unusual (only 1.2% of use tax)
- If analyzing a **use tax** transaction and AI suggests "Non-taxable - SIRC RISK" → High confidence (20.2% of use tax)

## Future Enhancements

Additional use tax data available for extraction:
- Phase 2_Master Refunds_Use Tax Sample Items_2016_4-24-22.xlsx
- Phase 2_Master Refunds_Use Tax Sample Items_2017_11-13-22.xlsx
- Phase 2_Master Refunds_Use Tax Sample Items_2018_12-4-23.xlsx
- Phase 2_Master Refunds_Use Tax Sample Items_2019_5-1-24.xlsx
- Phase 2_Master Refunds_Use Tax Sample Items_2020_5-1-24.xlsx
- Phase_3_2023_Use Tax files
- Phase_3_2024_Use Tax files

---

**Total Coverage**: 32,827 use tax records | 524 vendors | 10 refund basis patterns | 2021 data

**Extraction Script**: `scripts/extract_patterns_from_use_tax.py`
