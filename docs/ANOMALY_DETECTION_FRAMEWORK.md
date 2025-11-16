# Tax Refund Anomaly Detection Framework

## 🎯 Executive Summary

Based on research into Washington State tax audit patterns, sales tax compliance issues, and expert tax analysis, we've identified **15 critical anomaly detectors** that will flag invoices requiring human review.

**Confidence Threshold**: Any invoice with AI confidence < 90% gets flagged for human review.

---

## 🚩 The 15 Anomaly Detectors

### Category 1: Amount & Calculation Anomalies

#### 1. **Odd Dollar Amount Detector** (Your Original Insight)
**Pattern**: Round-number services with odd-cent totals suggest hidden tax

**Logic**:
```python
def detect_odd_amount_on_exempt_service(invoice):
    """
    Flag if:
    - Category is typically exempt (professional services, consulting)
    - Amount has odd cents (not .00, .25, .50, .75)
    - Vendor is in-state WA (should know better)

    Example: $5,525.00 on "Consulting Services" = $5,000 + 10.5% tax
    """
    has_odd_cents = (invoice.amount * 100) % 100 not in [0, 25, 50, 75]
    is_exempt_category = invoice.category in ['professional services', 'consulting',
                                                'custom software development']
    is_instate = invoice.vendor_state == 'WA'

    if has_odd_cents and is_exempt_category and is_instate:
        return {
            'flag': True,
            'severity': 'HIGH',
            'reason': 'Odd dollar amount on exempt category from in-state vendor',
            'suspicion': 'Tax may have been incorrectly added to exempt service',
            'implied_base': round(invoice.amount / 1.105, 2),
            'implied_tax': round(invoice.amount - (invoice.amount / 1.105), 2)
        }
```

**Confidence Impact**: -20 points

---

#### 2. **Tax Rate Mismatch Detector**
**Pattern**: Inconsistent tax rates vs. location and date

**Research Finding**: Wrong tax rates are a common refund basis

**Logic**:
```python
def detect_wrong_tax_rate(invoice, expected_rate_by_location):
    """
    Flag if:
    - Tax rate doesn't match location + date combination
    - Rate is from wrong jurisdiction
    - Using old rate after rate change

    Example:
    - Invoice from Seattle in 2024
    - Expected rate: 10.5%
    - Actual rate: 9.5% (old rate from 2020)
    """
    actual_rate = invoice.tax_amount / invoice.pretax_amount
    expected_rate = expected_rate_by_location[invoice.location][invoice.date]

    tolerance = 0.001  # 0.1% tolerance

    if abs(actual_rate - expected_rate) > tolerance:
        return {
            'flag': True,
            'severity': 'MEDIUM',
            'reason': f'Tax rate {actual_rate:.3%} doesn\'t match expected {expected_rate:.3%}',
            'refund_basis': 'Wrong Rate',
            'potential_refund': abs(invoice.tax_amount - (invoice.pretax_amount * expected_rate))
        }
```

**Confidence Impact**: -15 points

---

#### 3. **Round Number Tax Detector**
**Pattern**: Tax amounts that are suspiciously round

**Research Finding**: Estimated or improperly calculated tax

**Logic**:
```python
def detect_round_tax_amount(invoice):
    """
    Flag if:
    - Tax amount is exactly $100, $500, $1000, etc.
    - Suggests tax was estimated, not calculated

    Example: $10,000 invoice with exactly $1,000 tax (too round)
    """
    if invoice.tax_amount % 100 == 0 and invoice.tax_amount >= 100:
        calculated_tax = invoice.pretax_amount * 0.105
        discrepancy = abs(invoice.tax_amount - calculated_tax)

        if discrepancy > 10:  # More than $10 off
            return {
                'flag': True,
                'severity': 'MEDIUM',
                'reason': f'Tax amount ${invoice.tax_amount} is suspiciously round',
                'calculated_tax': calculated_tax,
                'discrepancy': discrepancy
            }
```

**Confidence Impact**: -10 points

---

### Category 2: Construction & Retainage Anomalies

#### 4. **Construction Retainage Tax Tracker** (Your Original Insight)
**Pattern**: Multi-invoice construction projects with incorrect tax allocation

**Research Finding**: WA law requires tax on full contract price upfront, not on each progress payment

**Logic**:
```python
def detect_construction_retainage_issue(invoice, po, all_po_invoices):
    """
    Flag if:
    - Construction industry
    - Multiple invoices for same PO
    - Tax charged doesn't align with retainage rules

    WA Rule: Tax charged on FULL contract price, not per progress payment
    """
    if invoice.vendor_industry != 'construction':
        return None

    # Get all invoices for this PO
    invoices = get_all_invoices_for_po(po.number)

    if len(invoices) <= 1:
        return None  # Only one invoice, no retainage issue

    # Calculate total billed vs PO amount
    total_billed = sum(inv.pretax_amount for inv in invoices)
    po_amount = po.total_amount
    percent_complete = (total_billed / po_amount) * 100

    # Expected: Tax on full PO charged upfront
    expected_total_tax = po_amount * tax_rate

    # Actual: Sum of all tax charged across invoices
    actual_total_tax = sum(inv.tax_amount for inv in invoices)

    discrepancy = actual_total_tax - expected_total_tax

    if abs(discrepancy) > 100:  # More than $100 difference
        return {
            'flag': True,
            'severity': 'HIGH',
            'reason': 'Construction retainage tax allocation issue',
            'po_number': po.number,
            'po_amount': po_amount,
            'percent_complete': f'{percent_complete:.1f}%',
            'invoices_in_po': len(invoices),
            'expected_total_tax': expected_total_tax,
            'actual_total_tax': actual_total_tax,
            'discrepancy': discrepancy,
            'refund_potential': max(0, discrepancy),
            'recommendation': 'Review entire PO invoice series for retainage tax treatment'
        }
```

**Confidence Impact**: -25 points (complex issue)

---

#### 5. **Progress Payment Percentage Anomaly**
**Pattern**: Unusual completion percentages

**Logic**:
```python
def detect_unusual_progress_percentage(invoice, po, all_invoices):
    """
    Flag if:
    - Completion percentage is unusual (>100%, <0%, weird increments)
    - Suggests data entry error or fraud
    """
    total_billed = sum(inv.pretax_amount for inv in all_invoices)
    percent_complete = (total_billed / po.total_amount) * 100

    if percent_complete > 105:  # Over-billing
        return {
            'flag': True,
            'severity': 'CRITICAL',
            'reason': f'Progress payments exceed PO amount ({percent_complete:.1f}%)',
            'total_po': po.total_amount,
            'total_billed': total_billed,
            'over_billing': total_billed - po.total_amount
        }
```

**Confidence Impact**: -30 points

---

### Category 3: Vendor & Pattern Anomalies

#### 6. **In-State Vendor Credibility Indicator** (Your Original Insight)
**Pattern**: WA vendors know WA tax law better than out-of-state

**Logic**:
```python
def assess_vendor_credibility(vendor, invoice):
    """
    Confidence boost/reduction based on vendor location

    In-state WA vendor:
    - If they charge tax → HIGH confidence it's taxable
    - If they don't charge tax → HIGH confidence it's exempt

    Out-of-state vendor:
    - Less reliable, flag for verification
    """
    if vendor.state == 'WA':
        if invoice.tax_amount > 0:
            return {
                'confidence_boost': +15,
                'note': 'In-state vendor charged tax - likely correct',
                'trust_level': 'HIGH'
            }
        else:
            return {
                'confidence_boost': +15,
                'note': 'In-state vendor didn\'t charge tax - likely exempt',
                'trust_level': 'HIGH'
            }
    else:
        # Out-of-state vendor
        return {
            'flag': True,
            'severity': 'LOW',
            'confidence_boost': -10,
            'note': 'Out-of-state vendor - verify WA tax law application',
            'trust_level': 'MEDIUM',
            'recommendation': 'Cross-check with WA tax requirements'
        }
```

---

#### 7. **Vendor Pattern Consistency Checker**
**Pattern**: Vendor behavior inconsistent with history

**Research Finding**: Fluctuations in vendor tax patterns are audit triggers

**Logic**:
```python
def detect_vendor_pattern_deviation(invoice, vendor_history):
    """
    Flag if:
    - This vendor usually charges tax, but didn't this time
    - OR vendor usually doesn't charge tax, but did this time
    - Suggests error or special circumstance
    """
    # Get vendor's historical tax pattern
    historical_invoices = get_vendor_invoices(invoice.vendor_id, limit=20)

    tax_charge_rate = sum(1 for inv in historical_invoices if inv.tax_amount > 0) / len(historical_invoices)

    # Vendor usually charges tax (>80% of time)
    if tax_charge_rate > 0.8 and invoice.tax_amount == 0:
        return {
            'flag': True,
            'severity': 'MEDIUM',
            'reason': f'Vendor typically charges tax ({tax_charge_rate:.0%} of time) but didn\'t on this invoice',
            'recommendation': 'Verify if this is correctly exempt or if tax was omitted'
        }

    # Vendor usually doesn't charge tax (<20% of time)
    if tax_charge_rate < 0.2 and invoice.tax_amount > 0:
        return {
            'flag': True,
            'severity': 'MEDIUM',
            'reason': f'Vendor rarely charges tax ({tax_charge_rate:.0%} of time) but did on this invoice',
            'recommendation': 'Verify if this is correctly taxable or if tax was added in error'
        }
```

**Confidence Impact**: -15 points

---

### Category 4: Sales vs. Use Tax Classification

#### 8. **Sales vs. Use Tax Misclassification Detector**
**Pattern**: Transaction classified as wrong tax type

**Research Finding**: Use tax applies when sales tax wasn't collected; they're mutually exclusive

**Logic**:
```python
def detect_sales_vs_use_tax_error(invoice):
    """
    Flag if:
    - Transaction shows BOTH sales tax and use tax (impossible)
    - Use tax charged but vendor is in-state (should be sales tax)
    - Sales tax charged but no nexus (should be use tax)

    Key Rule: Goods are subject to either sales OR use tax, but not both
    """
    # Check for double taxation
    if invoice.sales_tax_amount > 0 and invoice.use_tax_amount > 0:
        return {
            'flag': True,
            'severity': 'CRITICAL',
            'reason': 'Both sales tax and use tax charged - mutually exclusive',
            'refund_basis': 'Duplicate Tax',
            'potential_refund': min(invoice.sales_tax_amount, invoice.use_tax_amount)
        }

    # Use tax charged by in-state vendor (wrong)
    if invoice.use_tax_amount > 0 and invoice.vendor_state == 'WA':
        return {
            'flag': True,
            'severity': 'HIGH',
            'reason': 'Use tax charged by in-state vendor - should be sales tax',
            'recommendation': 'Reclassify as sales tax or investigate'
        }
```

**Confidence Impact**: -20 points

---

#### 9. **Out-of-State Purchase Use Tax Checker**
**Pattern**: Out-of-state purchases should trigger use tax

**Research Finding**: Purchases from states with no/low sales tax require WA use tax

**Logic**:
```python
def detect_missing_use_tax(invoice):
    """
    Flag if:
    - Purchased from Oregon (no sales tax) or low-tax state
    - No sales tax charged
    - No use tax self-assessed
    - Used in Washington

    Example: Buy from Oregon, use in WA → Owe WA use tax
    """
    if invoice.vendor_state == 'OR' and invoice.tax_amount == 0:
        return {
            'flag': True,
            'severity': 'HIGH',
            'reason': 'Purchase from Oregon with no tax - WA use tax may be owed',
            'potential_use_tax': invoice.amount * 0.105,
            'note': 'Oregon has no sales tax; WA use tax applies to goods used in WA'
        }
```

**Confidence Impact**: -15 points

---

### Category 5: Exemption & Documentation Anomalies

#### 10. **High Exempt Sales Ratio Detector**
**Pattern**: Unusually high percentage of exempt sales

**Research Finding**: Top audit trigger - states scrutinize high exempt percentages

**Logic**:
```python
def detect_abnormal_exempt_ratio(vendor, period_invoices):
    """
    Flag if:
    - Vendor has >50% exempt sales (unusual for most businesses)
    - Exempt ratio much higher than industry average
    - Suggests missing exemption certificates or errors
    """
    total_invoices = len(period_invoices)
    exempt_invoices = sum(1 for inv in period_invoices if inv.tax_amount == 0)
    exempt_ratio = exempt_invoices / total_invoices

    industry_avg = get_industry_exempt_ratio(vendor.industry)

    if exempt_ratio > 0.5 or exempt_ratio > (industry_avg * 1.5):
        return {
            'flag': True,
            'severity': 'MEDIUM',
            'reason': f'High exempt sales ratio ({exempt_ratio:.0%}) vs industry avg ({industry_avg:.0%})',
            'vendor_exempt_ratio': f'{exempt_ratio:.0%}',
            'industry_average': f'{industry_avg:.0%}',
            'recommendation': 'Verify exemption certificates on file'
        }
```

**Confidence Impact**: -10 points

---

#### 11. **Lump Sum vs. Separately Stated Detector**
**Pattern**: Taxable and non-taxable items bundled without separation

**Research Finding**: If lump sum includes taxable + non-taxable, entire amount is taxable unless separately stated

**Logic**:
```python
def detect_lump_sum_taxability_issue(invoice):
    """
    Flag if:
    - Invoice has single line item with mixed goods/services
    - No itemization between taxable and non-taxable components
    - Entire amount may be incorrectly taxed

    Example: "$10,000 - Equipment + Installation + Training"
    - Equipment: Taxable
    - Installation: Depends
    - Training: Non-taxable
    → Must be separately stated to exclude training from tax
    """
    # Check for bundled line items
    bundled_keywords = ['and', '+', 'including', 'with', 'plus']

    if any(keyword in invoice.description.lower() for keyword in bundled_keywords):
        # Check if there's only one line item
        if invoice.line_item_count == 1:
            return {
                'flag': True,
                'severity': 'MEDIUM',
                'reason': 'Bundled goods/services not separately stated',
                'description': invoice.description,
                'rule': 'Entire lump sum is taxable unless components are separately stated',
                'recommendation': 'Request itemized invoice to exclude non-taxable components'
            }
```

**Confidence Impact**: -15 points

---

### Category 6: Temporal & Frequency Anomalies

#### 12. **Never Reported Use Tax Detector**
**Pattern**: Company never reports use tax

**Research Finding**: Major audit red flag - unrealistic for any company to have zero use tax

**Logic**:
```python
def detect_zero_use_tax_pattern(company, period='year'):
    """
    Flag if:
    - Company has NEVER reported use tax
    - With proliferation of internet sales, impossible to have zero use tax
    """
    use_tax_invoices = get_use_tax_invoices(company.id, period)

    if len(use_tax_invoices) == 0:
        return {
            'flag': True,
            'severity': 'HIGH',
            'reason': 'Company has never reported use tax - major audit red flag',
            'note': 'With internet sales proliferation, zero use tax is unrealistic',
            'recommendation': 'Review out-of-state purchases for unreported use tax'
        }
```

**Confidence Impact**: -20 points (at company level)

---

#### 13. **Revenue Fluctuation Detector**
**Pattern**: Unusual spikes or drops in revenue/tax

**Research Finding**: For non-seasonal businesses, states expect normalized revenue patterns

**Logic**:
```python
def detect_revenue_fluctuation(vendor, current_invoice, historical_avg):
    """
    Flag if:
    - Non-seasonal business with >50% revenue spike or drop
    - Suggests data entry error, fraud, or special circumstance
    """
    if vendor.is_seasonal:
        return None  # Skip for seasonal businesses

    current_amount = current_invoice.amount
    avg_amount = historical_avg

    percent_change = abs((current_amount - avg_amount) / avg_amount)

    if percent_change > 0.5:  # 50% change
        return {
            'flag': True,
            'severity': 'MEDIUM',
            'reason': f'Revenue fluctuation of {percent_change:.0%} from average',
            'current_invoice': current_amount,
            'historical_average': avg_amount,
            'recommendation': 'Verify if this is a legitimate large order or data error'
        }
```

**Confidence Impact**: -10 points

---

### Category 7: Documentation & Consistency Anomalies

#### 14. **Missing Documentation Pattern**
**Pattern**: Missing supporting documents (PO, contracts, exemption certificates)

**Logic**:
```python
def detect_missing_documentation(invoice):
    """
    Flag if:
    - Large amount (>$20K) with no PO
    - Exempt claim with no exemption certificate
    - Out-of-state shipment with no delivery proof
    """
    flags = []

    # Large purchase without PO
    if invoice.amount > 20000 and not invoice.po_number:
        flags.append({
            'severity': 'MEDIUM',
            'reason': f'Invoice over $20K with no PO number',
            'recommendation': 'Obtain PO for audit trail'
        })

    # Exempt sale without certificate
    if invoice.tax_amount == 0 and invoice.amount > 5000:
        flags.append({
            'severity': 'HIGH',
            'reason': 'Exempt sale over $5K - verify exemption certificate on file',
            'recommendation': 'Obtain exemption certificate or resale certificate'
        })

    # Out-of-state claim without proof
    if invoice.claimed_exempt_basis == 'Out of State - Shipment':
        if not invoice.has_delivery_documentation:
            flags.append({
                'severity': 'HIGH',
                'reason': 'Out-of-state exemption claimed without delivery proof',
                'recommendation': 'Obtain shipping documents showing out-of-state delivery'
            })

    return flags if flags else None
```

**Confidence Impact**: -15 points per missing document

---

#### 15. **Stair-Stepping Refund Request Pattern**
**Pattern**: Progressive refund requests to find threshold

**Research Finding**: Fraudsters file progressively larger refunds to find audit threshold

**Logic**:
```python
def detect_stair_stepping_pattern(company_refund_history):
    """
    Flag if:
    - Multiple refund requests with increasing amounts
    - Suggests testing audit thresholds

    Example: $5K → $10K → $15K → $20K refund requests
    """
    if len(company_refund_history) < 3:
        return None

    amounts = [r.amount for r in sorted(company_refund_history, key=lambda x: x.date)]

    # Check if consistently increasing
    is_increasing = all(amounts[i] < amounts[i+1] for i in range(len(amounts)-1))

    if is_increasing:
        return {
            'flag': True,
            'severity': 'CRITICAL',
            'reason': 'Stair-stepping refund pattern detected - potential fraud indicator',
            'refund_amounts': amounts,
            'recommendation': 'Flag for senior review and enhanced documentation'
        }
```

**Confidence Impact**: -40 points (fraud indicator)

---

## 📊 Anomaly Severity & Confidence Scoring

### Severity Levels
- **CRITICAL** (-30 to -40 confidence): Fraud indicators, impossible scenarios
- **HIGH** (-20 to -25 confidence): Likely errors, construction issues, major red flags
- **MEDIUM** (-10 to -15 confidence): Inconsistencies, missing docs, vendor deviations
- **LOW** (-5 to -10 confidence): Minor flags, informational

### Confidence Scoring Formula

```python
def calculate_final_confidence(base_confidence, anomaly_flags):
    """
    Start with AI base confidence
    Apply all anomaly penalties
    Cap at 0-100 range
    """
    final_confidence = base_confidence

    for flag in anomaly_flags:
        final_confidence += flag.confidence_impact  # Negative value

    # Apply positive adjustments
    for boost in positive_indicators:
        final_confidence += boost.confidence_impact  # Positive value

    # Cap at 0-100
    return max(0, min(100, final_confidence))
```

### Review Threshold

```python
CONFIDENCE_THRESHOLDS = {
    'auto_accept': 90,      # >= 90% → Auto-accept
    'human_review': 90,     # < 90% → Flag for review
    'senior_review': 70,    # < 70% → Requires senior analyst
    'reject': 50            # < 50% → Auto-reject, needs investigation
}
```

---

## 🎓 How Anomalies Feed Learning

When analyst reviews a flagged invoice:

1. **Analyst confirms anomaly was correct**:
   - Strengthen anomaly detector weight
   - Add to pattern database
   - Increase future confidence impact

2. **Analyst says anomaly was false positive**:
   - Reduce anomaly detector weight
   - Add exception to pattern database
   - Decrease future confidence impact

3. **Analyst teaches new pattern**:
   - Create new anomaly detector
   - Extract generalized rule
   - Apply to similar cases

---

## Summary

These 15 detectors capture:
- Your expert insights (odd amounts, construction retainage, in-state vendors)
- Research-backed patterns (high exempt ratios, use tax, fluctuations)
- Washington-specific rules (retainage, sales vs use tax)
- Fraud indicators (stair-stepping, lump sums)

**Result**: Intelligent flagging system that gets smarter with every human review.
