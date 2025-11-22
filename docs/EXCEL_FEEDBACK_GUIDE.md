# Excel Analysis Feedback System Guide

> **Note:** This guide covers the Excel invoice/PO analysis feedback system. For RAG chatbot feedback, see [CHATBOT_FEEDBACK_GUIDE.md](CHATBOT_FEEDBACK_GUIDE.md).

## Overview

This system captures human corrections and explanations during the review of AI-analyzed invoices and purchase orders. When analysts review and correct AI decisions, the system automatically extracts patterns and improves future analysis accuracy.

The Excel feedback system is separate from the chatbot feedback system. It focuses on learning vendor-specific patterns, product classifications, and refund determination rules through human-in-the-loop corrections.

## Core Principles

1. **Human-in-the-Loop**: AI flags uncertainty (< 90% confidence), humans make final decisions
2. **Explanation Required**: Every human override must include reasoning
3. **Pattern Extraction**: System automatically learns from corrections
4. **Confidence Adjustment**: Learned patterns boost/reduce future confidence scores
5. **Audit Trail**: All decisions and corrections logged for compliance

## Architecture

### Components

1. **Database Schema**
   - `analysis_results`: Stores AI analysis of each invoice line item
   - `analysis_reviews`: Human corrections and review decisions (the feedback table)
   - `vendor_products`: Learning database of known vendor products
   - `vendor_product_patterns`: Patterns learned from corrections
   - `learned_patterns`: Generalized decision patterns extracted from reviews
   - `pattern_applications`: Tracks when and how patterns are applied
   - `audit_trail`: Complete change history for compliance

2. **Review Queue UI** ([dashboard/pages/3_Review_Queue.py](../dashboard/pages/3_Review_Queue.py))
   - Table of flagged transactions with < 90% confidence
   - Detail panel showing AI's initial determination and rationale
   - Override form for human corrections
   - Similar cases indicator
   - Pattern learning feedback

3. **Analytics Dashboard** ([dashboard/pages/6_Analytics.py](../dashboard/pages/6_Analytics.py))
   - Total items analyzed
   - AI confidence distribution
   - Most corrected fields
   - Refund breakdown by exemption type
   - Vendor patterns learned
   - Product types cataloged

4. **Excel Processing** ([analysis/excel_processors.py](../analysis/excel_processors.py))
   - Processes uploaded Excel files
   - Applies learned patterns during analysis
   - Flags low-confidence items for review

5. **Excel Manager** ([dashboard/pages/7_Excel_Manager.py](../dashboard/pages/7_Excel_Manager.py))
   - Upload and version control of Excel files
   - Track processing status
   - View analysis results

## How It Works

### Step 1: Excel Upload & AI Analysis

1. **Upload Invoice/PO Excel File**
   - User uploads Excel file through Excel Manager
   - System extracts line items (description, amount, vendor, etc.)

2. **AI Analysis with Learned Patterns**
   - Base AI analyzes each line item
   - Applies learned patterns from previous corrections
   - Adjusts confidence scores based on pattern matches
   - Flags items with < 90% confidence for human review

### Step 2: Human Review & Correction

When reviewing flagged transactions, analysts see:

**AI's Determination:**
- Product description
- Product type
- Refund basis (exemption reason)
- Citation (legal reference)
- Refund percentage
- Estimated refund amount
- Confidence score
- Rationale (why AI made this decision)

**Review Actions:**
1. **Accept**: AI determination is correct
2. **Correct**: Override one or more fields with correct values
3. **Reject**: Item should not be in claim

**Required for Corrections:**
- **Corrected values** (which fields were wrong)
- **Explanation** (why AI was wrong) - REQUIRED
- **Pattern hint** (optional: what pattern to learn)
- **Apply to similar** (optional: apply this correction to similar items)

### Step 3: Pattern Extraction & Learning

When a correction is submitted:

1. **Save Review**: Correction saved to `analysis_reviews` table
2. **Extract Pattern**: System analyzes the explanation and correction to identify learnable patterns
3. **Update Vendor Knowledge**: Corrected product info added to `vendor_products` table
4. **Create/Update Patterns**: New patterns added to `learned_patterns` table
5. **Find Similar Cases**: If "apply to similar" is checked, find and update similar unreviewed items
6. **Log Audit Trail**: All changes recorded for compliance

### Step 4: Apply Learned Patterns

Future analyses automatically apply learned patterns:
- Vendor-specific patterns (e.g., "Microsoft professional services are always custom software development")
- Category-based rules (e.g., "Professional services with odd dollar amounts likely have hidden tax")
- Keyword triggers (e.g., "hosting" + "cloud" → digital goods exemption)
- Anomaly responses (e.g., construction retainage on first invoice)

## Database Schema

### analysis_results Table
```sql
- id: UUID (primary key)
- invoice_id: TEXT
- line_number: INTEGER
- vendor_name: TEXT
- product_description: TEXT
- amount: DECIMAL
- ai_product_type: TEXT
- ai_refund_basis: TEXT
- ai_citation: TEXT
- ai_refund_percentage: DECIMAL
- ai_estimated_refund: DECIMAL
- ai_confidence: FLOAT
- ai_rationale: TEXT
- final_decision: TEXT (approved/needs_review/corrected)
- created_at: TIMESTAMP
```

### analysis_reviews Table (Feedback Table)
```sql
- id: UUID (primary key)
- analysis_id: UUID (references analysis_results)
- invoice_id: TEXT
- vendor_name: TEXT

-- Original AI Determination
- ai_taxability: TEXT
- ai_tax_category: TEXT
- ai_refund_basis: TEXT
- ai_confidence: FLOAT
- ai_rationale: TEXT

-- Human Correction
- human_taxability: TEXT
- human_tax_category: TEXT
- human_refund_basis: TEXT
- human_explanation: TEXT (REQUIRED)
- correction_type: TEXT (accept/override_taxability/override_category/override_basis)

-- Corrected Values
- corrected_product_desc: TEXT
- corrected_product_type: TEXT
- corrected_refund_basis: TEXT
- corrected_citation: TEXT
- corrected_refund_percentage: DECIMAL
- corrected_estimated_refund: DECIMAL
- fields_corrected: TEXT[]

-- Learning Metadata
- pattern_extracted: BOOLEAN
- pattern_id: UUID (references learned_patterns)
- similar_case_refs: UUID[]
- apply_to_similar: BOOLEAN

-- Audit Trail
- reviewed_by: TEXT (analyst username)
- reviewed_at: TIMESTAMP
- review_duration_seconds: INTEGER
```

### learned_patterns Table
```sql
- id: UUID (primary key)
- pattern_type: TEXT (vendor_specific/category_rule/keyword_trigger/anomaly_response)
- pattern_name: TEXT
- description: TEXT

-- Pattern Definition
- trigger_conditions: JSONB (what triggers this pattern)
- confidence_adjustment: FLOAT (boost/reduce confidence)
- override_determination: TEXT (optional: force specific determination)

-- Learning Source
- learned_from_review_ids: UUID[]
- learned_from_count: INTEGER
- first_learned_at: TIMESTAMP
- last_reinforced_at: TIMESTAMP

-- Application Stats
- times_applied: INTEGER
- times_correct: INTEGER
- times_incorrect: INTEGER
- accuracy_rate: FLOAT (auto-calculated)

-- Status
- is_active: BOOLEAN
- requires_validation: BOOLEAN (new patterns need approval)
- validated_by: TEXT
- validated_at: TIMESTAMP
```

### vendor_products Table
```sql
- id: UUID (primary key)
- vendor_name: TEXT
- product_description: TEXT
- product_type: TEXT
- refund_basis: TEXT
- citation: TEXT
- refund_percentage: DECIMAL
- confidence_score: FLOAT
- times_seen: INTEGER
- last_seen: TIMESTAMP
- learning_source: TEXT (ai/human_correction/pattern)
```

### vendor_product_patterns Table
```sql
- id: UUID (primary key)
- vendor_name: TEXT
- description_pattern: TEXT (regex or keywords)
- product_type: TEXT
- refund_basis: TEXT
- citation: TEXT
- confidence_boost: FLOAT
- times_matched: INTEGER
- times_correct: INTEGER
- accuracy_rate: FLOAT
- created_from_reviews: UUID[]
```

### pattern_applications Table
```sql
- id: UUID (primary key)
- pattern_id: UUID (references learned_patterns)
- analysis_id: UUID (references analysis_results)
- invoice_id: TEXT
- applied_at: TIMESTAMP
- confidence_before: FLOAT
- confidence_after: FLOAT
- determination_before: TEXT
- determination_after: TEXT
- was_correct: BOOLEAN (NULL until reviewed)
- reviewed_by: TEXT
- reviewed_at: TIMESTAMP
```

## Pattern Types and Examples

### 1. Vendor-Specific Patterns

**Example**: Microsoft always provides custom software development

```json
{
  "pattern_type": "vendor_specific",
  "pattern_name": "microsoft_custom_software",
  "trigger_conditions": {
    "vendor_name": "Microsoft Corporation",
    "keywords_in_description": ["development", "custom", "configuration"]
  },
  "confidence_adjustment": +15,
  "override_determination": null
}
```

**Learning Event**: Human corrected 3 Microsoft invoices from "taxable" to "exempt - custom software"

### 2. Category-Based Rules

**Example**: Professional services + odd dollar amount = hidden tax

```json
{
  "pattern_type": "category_rule",
  "pattern_name": "professional_services_hidden_tax",
  "trigger_conditions": {
    "tax_category": "Services",
    "additional_info": "Professional",
    "anomaly_detected": "odd_dollar_amount"
  },
  "confidence_adjustment": +25,
  "override_determination": "Add to Claim - Non-Taxable Services"
}
```

### 3. Keyword Triggers

**Example**: "Hosting" keyword → likely exempt under digital goods

```json
{
  "pattern_type": "keyword_trigger",
  "pattern_name": "hosting_digital_goods_exempt",
  "trigger_conditions": {
    "keywords_in_description": ["hosting", "cloud", "infrastructure"],
    "tax_type": "sales_tax",
    "invoice_date_before": "2025-10-01"
  },
  "confidence_adjustment": +20,
  "override_determination": "Exempt - Digital Goods"
}
```

### 4. Anomaly Response Patterns

**Example**: Construction retainage on first invoice

```json
{
  "pattern_type": "anomaly_response",
  "pattern_name": "construction_retainage_first_invoice",
  "trigger_conditions": {
    "anomaly_detected": "construction_retainage_issue",
    "is_first_invoice_on_po": true,
    "vendor_industry": "Construction"
  },
  "confidence_adjustment": +30,
  "override_determination": "Add to Claim - Tax Timing Error"
}
```

## Setup Instructions

### 1. Deploy Database Schema

```bash
# Set your database password
export SUPABASE_DB_PASSWORD='your-password'

# Deploy analysis tables and feedback schema
bash scripts/deploy_analysis_schema.sh

# Deploy vendor learning schema
bash scripts/deploy_vendor_learning_schema.sh
```

This creates all necessary tables, indexes, triggers, and functions.

### 2. Verify Schema Deployment

Check that the following tables exist:
- `analysis_results`
- `analysis_reviews`
- `vendor_products`
- `vendor_product_patterns`
- `learned_patterns`
- `pattern_applications`
- `audit_trail`

### 3. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Navigate to:
- **Review Queue**: `/3_Review_Queue` (port 5001/pages/3)
- **Analytics**: `/6_Analytics` (port 5001/pages/6)
- **Excel Manager**: `/7_Excel_Manager` (port 5001/pages/7)

## Usage Guide

### For Analysts (Reviewers)

#### Reviewing Flagged Transactions

1. **Open Review Queue**
   - Navigate to Review Queue page
   - See table of all transactions flagged for review (< 90% confidence)

2. **Select Transaction to Review**
   - Click on a row to view details
   - Review AI's determination and rationale

3. **Make Decision**

   **If AI is Correct:**
   - Click "Accept"
   - Review is saved, confidence increases for similar patterns

   **If AI Needs Correction:**
   - Click "Correct"
   - Fill in corrected values for any incorrect fields:
     - Product description
     - Product type
     - Refund basis
     - Citation
     - Refund percentage
     - Estimated refund
   - **REQUIRED**: Explain why AI was wrong
     - Example: "AI missed that this is custom software development, which is exempt under WAC 458-20-15502(3)(a)"
   - Optional: Check "Apply this pattern to similar transactions"
   - Submit correction

4. **Review Similar Cases** (if available)
   - System shows similar past cases
   - Click to view how similar transactions were handled
   - Ensures consistency in decisions

5. **Track Learning Progress**
   - See indicator: "AI has learned X patterns from your reviews"
   - View patterns extracted from your corrections

#### Best Practices for Reviewers

1. **Provide Clear Explanations**
   - Be specific about why AI was wrong
   - Mention key facts AI missed
   - Reference legal citations when applicable
   - Good: "This is custom software development (exempt per WAC 458-20-15502), not prewritten software"
   - Bad: "Wrong category"

2. **Use Pattern Hints**
   - If you notice a recurring issue, mention it
   - Example: "This vendor always provides custom development services"
   - Helps system learn faster

3. **Check Similar Cases**
   - Review similar past cases before deciding
   - Maintain consistency in rulings
   - Learn from previous analyst decisions

4. **Verify Pattern Suggestions**
   - When system suggests "Apply to similar", review similar cases first
   - Ensure pattern is truly applicable
   - Prevents overgeneralization

### For Administrators

#### Managing Learned Patterns

1. **Review Pending Patterns**
   - Navigate to Pattern Library (if implemented)
   - See patterns awaiting validation
   - Review trigger conditions and impact

2. **Validate Patterns**
   ```sql
   -- Approve a pattern
   UPDATE learned_patterns
   SET requires_validation = false,
       validated_by = 'admin_name',
       validated_at = NOW(),
       is_active = true
   WHERE id = '<pattern_id>';
   ```

3. **Deactivate Low-Performing Patterns**
   ```sql
   -- Deactivate patterns with < 60% accuracy after 10+ applications
   UPDATE learned_patterns
   SET is_active = false,
       deactivation_reason = 'Low accuracy rate'
   WHERE accuracy_rate < 0.6 AND times_applied > 10;
   ```

4. **Monitor Pattern Performance**
   - Check accuracy_rate for all active patterns
   - Target: > 80% accuracy
   - Investigate patterns with < 60% accuracy

#### Managing Vendor Knowledge

1. **Review Vendor Products Database**
   ```sql
   -- See all learned products for a vendor
   SELECT * FROM vendor_products
   WHERE vendor_name = 'Microsoft Corporation'
   ORDER BY confidence_score DESC;
   ```

2. **Manually Add Vendor Products**
   ```sql
   -- Add known vendor product
   INSERT INTO vendor_products (
       vendor_name,
       product_description,
       product_type,
       refund_basis,
       citation,
       refund_percentage,
       confidence_score,
       learning_source
   ) VALUES (
       'Acme Corp',
       'Professional Services - Custom Development',
       'Custom Software',
       'Exempt - Custom Software Development',
       'WAC 458-20-15502(3)(a)',
       100.0,
       0.95,
       'manual_entry'
   );
   ```

## Analytics & Monitoring

### Key Metrics to Track

The analytics dashboard ([dashboard/pages/6_Analytics.py](../dashboard/pages/6_Analytics.py)) provides:

1. **Analysis Volume**
   - Total items analyzed
   - Items requiring review
   - Items auto-approved

2. **AI Confidence Distribution**
   - Breakdown by confidence ranges
   - Trend over time (should improve)

3. **Most Corrected Fields**
   - Which fields get corrected most often
   - Identifies areas where AI needs improvement

4. **Review Efficiency**
   - Average review time per item
   - Reviews completed per analyst
   - % of reviews requiring override

5. **Learning Progress**
   - Total patterns learned
   - Active patterns
   - Average pattern accuracy
   - Patterns learned this month

6. **Vendor Knowledge**
   - Vendors with learned patterns
   - Products cataloged
   - Coverage by vendor

7. **Refund Analysis**
   - Breakdown by exemption type
   - Total estimated refunds
   - Confidence in refund calculations

### Target Metrics

**After 100 Reviews:**
- At least 15 patterns learned
- Average pattern accuracy > 75%
- Override rate < 30%

**After 500 Reviews:**
- At least 50 patterns learned
- Average pattern accuracy > 85%
- Override rate < 20%
- Auto-approval rate > 60%

**After 1000 Reviews:**
- At least 100 patterns learned
- Average pattern accuracy > 90%
- Override rate < 15%
- Auto-approval rate > 70%

## API Reference

### Analysis with Learning

```python
def analyze_invoice_with_learning(invoice_data: Dict) -> Dict:
    """
    Analyze invoice using base AI + learned patterns.
    """
    # Base AI analysis
    base_result = analyze_invoice_enhanced(invoice_data)

    # Apply learned patterns
    applicable_patterns = find_applicable_patterns(invoice_data)

    adjusted_confidence = base_result['confidence']
    pattern_notes = []

    for pattern in applicable_patterns:
        # Adjust confidence based on learned pattern
        adjusted_confidence += pattern['confidence_adjustment']

        # Override determination if pattern says so
        if pattern.get('override_determination'):
            base_result['final_decision'] = pattern['override_determination']

        pattern_notes.append(
            f"Pattern '{pattern['pattern_name']}' applied "
            f"(+{pattern['confidence_adjustment']} confidence)"
        )

        # Log pattern application
        log_pattern_application(pattern['id'], base_result['analysis_id'])

    # Cap confidence at 100
    adjusted_confidence = min(100, max(0, adjusted_confidence))

    base_result['confidence'] = adjusted_confidence
    base_result['patterns_applied'] = pattern_notes

    return base_result
```

### Handle Review Submission

```python
def handle_human_review(review_data: Dict) -> Dict:
    """
    Capture human review and extract patterns.
    """
    # Save review to database
    review_id = save_analysis_review(review_data)

    # Extract pattern if correction made
    if review_data['correction_type'] in ['override_taxability', 'override_category']:
        pattern = extract_pattern_from_correction(review_data)

        if pattern:
            # Save learned pattern
            pattern_id = save_learned_pattern(pattern)

            # Link pattern to this review
            update_review(review_id, {
                'pattern_id': pattern_id,
                'pattern_extracted': True
            })

            # If "apply to similar" checked, find similar cases
            if review_data.get('apply_to_similar'):
                similar_cases = find_similar_unreviewed_cases(review_data)
                apply_pattern_to_similar(pattern_id, similar_cases)

    return {
        'review_id': review_id,
        'pattern_extracted': pattern is not None
    }
```

### Find Similar Cases

```python
def find_similar_unreviewed_cases(reference_review: Dict) -> List[Dict]:
    """
    Find transactions similar to the one just reviewed.
    """
    similar = []

    # Similarity criteria
    criteria = [
        ('vendor_name', 1.0),          # Exact vendor match = very similar
        ('tax_category', 0.8),         # Same category = similar
        ('tax_amount_range', 0.5),     # Similar $ amount = moderately similar
        ('description_keywords', 0.7), # Shared keywords = similar
        ('tax_type', 0.6),             # Sales vs use tax
    ]

    # Query unreviewed transactions
    unreviewed = get_unreviewed_transactions()

    for transaction in unreviewed:
        similarity_score = calculate_similarity(
            reference_review,
            transaction,
            criteria
        )

        if similarity_score > 0.7:  # 70% similarity threshold
            similar.append({
                'transaction_id': transaction['id'],
                'similarity_score': similarity_score,
                'match_reasons': get_match_reasons(reference_review, transaction)
            })

    # Sort by similarity
    similar.sort(key=lambda x: x['similarity_score'], reverse=True)

    return similar[:10]  # Top 10 most similar
```

## Best Practices

### For Review Quality

1. **Always Provide Context in Explanations**
   - Mention specific legal citations
   - Explain what fact pattern triggers the exemption
   - Note vendor-specific considerations

2. **Review Similar Cases First**
   - Check if similar transactions were previously reviewed
   - Maintain consistency with past decisions
   - Learn from other analysts' reasoning

3. **Use Pattern Application Judiciously**
   - Only check "Apply to similar" when you're confident
   - Review the similar cases list before applying
   - Verify the pattern is broadly applicable

4. **Track Your Accuracy**
   - Monitor how often your reviews need re-review
   - Check if patterns learned from your reviews perform well
   - Adjust review thoroughness accordingly

### For System Performance

1. **Regular Pattern Audits**
   - Review pattern library weekly
   - Deactivate underperforming patterns
   - Validate pending patterns promptly

2. **Monitor Key Metrics**
   - AI confidence vs. accuracy correlation
   - Override rate trend (should decrease)
   - Pattern accuracy rates (should be > 80%)
   - Review velocity (reviews per day)

3. **Quality Control**
   - Spot-check auto-approved items
   - Review high-value items even if high confidence
   - Validate critical patterns manually

4. **Continuous Learning**
   - Share insights from reviews with team
   - Document edge cases and unusual patterns
   - Refine pattern extraction algorithms based on results

## Troubleshooting

### Patterns Not Being Extracted

**Problem:** Reviews are submitted but no patterns are learned.

**Solutions:**
1. Check that explanations are provided (required for pattern extraction)
2. Verify pattern extraction algorithm is running
3. Review database logs for errors
4. Ensure OpenAI API key is configured (if using AI for pattern extraction)

### Low Pattern Accuracy

**Problem:** Learned patterns have low accuracy rates (< 60%).

**Solutions:**
1. Review pattern trigger conditions - may be too broad
2. Check if patterns are being applied to wrong contexts
3. Deactivate low-performing patterns
4. Collect more reviews to refine patterns
5. Adjust confidence_adjustment values (may be too aggressive)

### Similar Cases Not Found

**Problem:** "Apply to similar" doesn't find similar transactions.

**Solutions:**
1. Check similarity algorithm thresholds (may be too strict)
2. Verify sufficient transactions in the database
3. Review similarity criteria weights
4. Ensure vendor names are normalized (e.g., "Microsoft" vs "Microsoft Corporation")

### High Override Rate Not Decreasing

**Problem:** Override rate stays high even after many reviews.

**Solutions:**
1. Check if patterns are being applied (review pattern_applications table)
2. Verify patterns are active and validated
3. Review pattern accuracy rates - may need refinement
4. Consider if new transaction types are appearing (requiring new patterns)
5. Check if base AI needs retraining

## Future Enhancements

Potential additions to the system:

1. **Pattern Library UI**
   - Visual interface for managing patterns
   - Batch pattern validation
   - Pattern performance analytics

2. **Automated Pattern Suggestions**
   - AI suggests patterns based on review clusters
   - Analysts approve/reject suggestions
   - Faster pattern creation

3. **Advanced Similarity Detection**
   - Semantic similarity using embeddings
   - Better cross-vendor pattern matching
   - Industry-based pattern grouping

4. **Review Collaboration**
   - Flag items for second opinion
   - Team discussion threads on complex items
   - Consensus-based pattern creation

5. **Confidence Calibration**
   - Adjust AI confidence based on actual accuracy
   - Per-category confidence calibration
   - Time-based confidence decay

## Conclusion

This Excel analysis feedback system creates a continuous improvement cycle:
- AI analyzes invoices with learned patterns
- Analysts review and correct low-confidence items
- System extracts patterns from corrections
- Future analyses automatically apply learned patterns
- Analysis accuracy improves over time
- Fewer items require manual review

Over time, the system becomes increasingly accurate at identifying refund opportunities, learning your organization's specific vendor relationships and product classifications, creating a truly intelligent and adaptive tax refund analysis engine.
