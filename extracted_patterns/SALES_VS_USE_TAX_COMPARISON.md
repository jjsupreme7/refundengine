# Sales Tax vs Use Tax Pattern Comparison

**Date**: November 22, 2025

This report compares patterns extracted from sales tax data (Denodo 2019-2023) and use tax data (Phase 3 2021).

## 1. Overall Statistics

| Metric | Sales Tax | Use Tax |
|--------|-----------|---------|
| **Total Vendors** | 1,033 | 524 |
| **Refund Basis Patterns** | 44 | 10 |
| **Keyword Categories** | 8 | 4 |
| **Vendor Overlap** | 147 vendors appear in BOTH |
| **Sales Tax Only Vendors** | 886 |
| **Use Tax Only Vendors** | 377 |

## 2. Data Sources

### Sales Tax Patterns
- **Source**: Denodo files 2019-2023 ("Records in Denodo not in Master")
- **Records**: 471,024 analyst-reviewed transactions
- **Vendors**: 1,033 unique vendors
- **File Type**: Historical sales tax refund decisions

### Use Tax Patterns
- **Source**: Phase_3_2021_Use Tax_10-17-25.xlsx, Sheet "2021"
- **Records**: 32,827 analyst-reviewed transactions
- **Vendors**: 524 unique vendors
- **File Type**: 2021 use tax analysis

## 3. Top Refund Bases Comparison

### Sales Tax Top 10

| Refund Basis | Count | Percentage |
|-------------|-------|------------|
| MPU | 8,405 | 34.5% |
| Non-taxable | 3,001 | 11.7% |
| Wrong rate | 2,210 | 2.8% |
| N/A - Reversed | 1,459 | 10.8% |
| Partial OOS services | 1,123 | 3.6% |
| OOS services | 716 | 1.2% |
| Partial OOS shipment | 416 | 1.1% |
| N - Out of State | 346 | 2.6% |
| N/A | 284 | 2.1% |
| OOS shipment | 155 | 0.6% |

### Use Tax Top 10

| Refund Basis | Count | Percentage |
|-------------|-------|------------|
| **Non-taxable - SIRC RISK** | 6,629 | 20.2% |
| **OOS services** | 5,433 | 16.6% |
| Wrong rate | 2,913 | 8.9% |
| OOS shipment | 1,347 | 4.1% |
| Non-taxable | 1,075 | 3.3% |
| MPU | 394 | 1.2% |
| Partial OOS shipment | 160 | 0.5% |
| Resale | 87 | 0.3% |
| Partial OOS services | 20 | 0.1% |
| OOS\Partial OOS | 4 | 0.0% |

## 4. Key Differences

### Most Significant Finding: MPU Usage

**Sales Tax:**
- MPU usage: 8,405 occurrences (34.5%)
- Vendors using MPU: 315
- **MPU is the #1 most common refund basis for sales tax**

**Use Tax:**
- MPU usage: 394 occurrences (1.2%)
- Vendors using MPU: 106
- **MPU is only #6 for use tax**

**Insight**: MPU is **21.3x more common** in sales tax than use tax. This makes sense because:
- MPU (Multi-Point Use) allocation is primarily a sales tax concept
- Use tax is typically assessed on specific purchases brought into the state
- Sales tax involves ongoing subscriptions/services that may be used across multiple states

### Use Tax Dominant Patterns

The top 2 use tax refund bases are:
1. **Non-taxable - SIRC RISK** (6,629 uses, 20.2%)
2. **OOS services** (5,433 uses, 16.6%)

These represent **36.8% of all use tax refunds**, indicating use tax refunds are heavily concentrated in:
- Services determined to be non-taxable (with SIRC risk considerations)
- Services delivered/performed out of state

### Sales Tax Specific Patterns (36 patterns)

Examples of refund bases ONLY found in sales tax data:
- Data Center Exemption?
- N - Nontaxable
- N-Hardware
- Discount
- Various state-specific markers (N - Not allocable, etc.)

### Use Tax Specific Patterns (2 patterns)

Refund bases ONLY found in use tax data:
- **Non-taxable - SIRC RISK** (6,629 uses) - Major use tax category
- OOS\Partial OOS (4 uses) - Rare hybrid classification

## 5. Vendor Overlap Analysis

**147 vendors** appear in both sales and use tax data, representing:
- 14.2% of sales tax vendors
- 28.1% of use tax vendors

### Top 10 Overlapping Vendors

| Vendor | Sales Tax Transactions | Use Tax Transactions | Total |
|--------|----------------------|-------------------|-------|
| MOREDIRECT INC | 422,326 | 96 | 422,422 |
| OFFICE DEPOT INC | 89,772 | 17 | 89,789 |
| COMSEARCH | 62,134 | 91 | 62,225 |
| HCL AMERICA INC | 60,905 | 3 | 60,908 |
| MC SIGN COMPANY | 36,201 | 250 | 36,451 |
| WIPRO LIMITED | 26,191 | 6 | 26,197 |
| ALLEN INDUSTRIES INC | 20,163 | 145 | 20,308 |
| ELOQUENT CORP | 14,322 | 707 | 15,029 |
| WALTON SIGNAGE LTD | 14,187 | 26 | 14,213 |
| ANIXTER INC | 11,588 | 2 | 11,590 |

**Observation**: Most high-volume vendors are primarily sales tax vendors with relatively small use tax transactions.

## 6. Implications for AI Analysis

### Current System Limitation

The AI analysis system currently processes ALL transactions without distinguishing between sales tax and use tax. This is problematic because:

1. **Different refund patterns**: MPU is common in sales tax but rare in use tax
2. **Different vendor behaviors**: Same vendor may have different refund bases for sales vs use tax
3. **Different exemption rules**: Sales tax and use tax have different legal frameworks
4. **Confidence scoring**: Using sales tax patterns for use tax analysis (or vice versa) will lower accuracy

### Recommended Enhancement

The pattern matching system should:
1. **Identify transaction tax type** (sales vs use) from source data
2. **Query appropriate pattern set** based on tax type
3. **Use tax-type-specific success rates** for confidence scoring
4. **Flag when a refund basis is common in one tax type but rare in another**

Example:
- If analyzing a use tax transaction suggesting MPU → flag as unusual (only 1.2% of use tax vs 34.5% of sales tax)
- If analyzing a use tax transaction suggesting "Non-taxable - SIRC RISK" → high confidence (20.2% of use tax)

## 7. Summary of Key Findings

1. ✅ **Sales tax has more vendors and refund basis diversity** (1,033 vendors, 44 bases vs 524 vendors, 10 bases)
2. ✅ **MPU dominates sales tax (34.5%) but is rare in use tax (1.2%)** - 21.3x difference
3. ✅ **Use tax is concentrated in two patterns**: "Non-taxable - SIRC RISK" (20.2%) and "OOS services" (16.6%)
4. ✅ **147 vendors appear in both tax types** - representing 28.1% of use tax vendors
5. ✅ **Each tax type has unique patterns** - 36 sales-only bases, 2 use-only bases
6. ⚠️ **Current system doesn't distinguish between tax types** - may reduce analysis accuracy

## 8. Next Steps

Recommended actions:
1. Add `tax_type` field to all pattern files (sales_tax vs use_tax)
2. Update matcher classes to filter by tax_type
3. Enhance AI analysis to detect transaction tax type
4. Create separate confidence scoring for sales vs use tax
5. Extract patterns from additional use tax files (2016-2020, 2023-2024)

---

**Pattern Files Generated:**
- Sales Tax: `extracted_patterns/*.json`
- Use Tax: `extracted_patterns/use_tax/*.json`
