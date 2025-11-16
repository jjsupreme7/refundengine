# Learning System Architecture

## Overview

The learning system captures human corrections and explanations during the review process, extracts patterns, and improves AI decision-making over time. This document defines how the Google AI Studio dashboard integrates with active learning and feedback capture.

## Core Principles

1. **Human-in-the-Loop**: AI flags uncertainty (< 90% confidence), humans make final decisions
2. **Explanation Required**: Every human override must include reasoning
3. **Pattern Extraction**: System automatically learns from corrections
4. **Confidence Adjustment**: Learned patterns boost/reduce future confidence scores
5. **Audit Trail**: All decisions and corrections logged for compliance

## Dashboard Integration

### Review Page UI (from Taxdesk Dashboard)

**Current UI Components** (from `/Users/jacoballen/Desktop/taxdesk_dashboard/pages/ReviewPage.tsx`):

```typescript
// Exception Queue (Left Panel)
- Table of flagged transactions with < 90% confidence
- Columns: Description, Category, Taxability, Confidence
- Click to select line item for review

// Detail Panel (Right Panel)
- Parsed Text: Shows invoice description
- System Suggestion: AI's initial determination
- Model Rationale: AI's explanation (when requested)
- Model Thoughts: Internal reasoning chain
- Citations: Legal references used

// Actions Available
- Accept: Approve AI determination
- Override: Taxable / Override: Exempt (analyst only)
- Ask for Rationale: Get AI explanation
- Send to Client: Request client clarification
```

### Enhanced Review UI for Learning

**New Components to Add**:

```typescript
// ADDITION 1: Human Override Form (appears when Override clicked)
interface OverrideForm {
  new_taxability: Taxability;  // User's corrected determination
  new_tax_category?: string;   // Corrected category
  new_refund_basis?: string;   // Corrected refund reason
  explanation: string;          // REQUIRED: Why AI was wrong
  pattern_hint?: string;        // Optional: What pattern to learn
  similar_cases?: string[];     // Optional: Similar past cases
}

// ADDITION 2: Correction Feedback Panel
<div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
  <h4 className="font-semibold text-yellow-800">Provide Correction Explanation</h4>
  <p className="text-sm text-yellow-700 mb-2">
    Help the AI learn: Why was the initial determination incorrect?
  </p>
  <textarea
    className="w-full p-2 border rounded-md"
    placeholder="Example: AI missed that this is custom software development, which is exempt under WAC 458-20-15502(3)(a)"
    rows={3}
    required
  />
  <label className="block mt-2 text-sm text-yellow-700">
    <input type="checkbox" className="mr-2" />
    Apply this pattern to similar transactions automatically
  </label>
</div>

// ADDITION 3: Similar Cases Indicator
{similarCases.length > 0 && (
  <div className="bg-blue-50 p-3 rounded-md">
    <h5 className="font-medium text-blue-800">💡 Similar Past Cases Found</h5>
    <p className="text-sm text-blue-700 mt-1">
      {similarCases.length} similar transactions were previously reviewed.
    </p>
    <button className="text-sm text-blue-600 underline mt-2">
      View Similar Cases
    </button>
  </div>
)}

// ADDITION 4: Learning Progress Indicator
<div className="flex items-center text-xs text-gray-500 mt-4">
  <Icons icon="lightbulb" className="w-4 h-4 mr-1 text-yellow-500" />
  <span>AI has learned {learnedPatternCount} patterns from your reviews</span>
</div>
```

## Database Schema for Learning

### Table: `analysis_reviews`
```sql
CREATE TABLE analysis_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analysis_results(id),
    invoice_id TEXT NOT NULL,
    vendor_name TEXT,

    -- Original AI Determination
    ai_taxability TEXT,
    ai_tax_category TEXT,
    ai_refund_basis TEXT,
    ai_confidence FLOAT,
    ai_rationale TEXT,

    -- Human Correction
    human_taxability TEXT,
    human_tax_category TEXT,
    human_refund_basis TEXT,
    human_explanation TEXT NOT NULL,  -- REQUIRED
    correction_type TEXT,  -- 'accept', 'override_taxability', 'override_category', 'override_basis'

    -- Learning Metadata
    pattern_extracted BOOLEAN DEFAULT FALSE,
    pattern_id UUID REFERENCES learned_patterns(id),
    similar_case_refs UUID[],  -- Array of similar review IDs
    apply_to_similar BOOLEAN DEFAULT FALSE,

    -- Audit Trail
    reviewed_by TEXT NOT NULL,  -- analyst username
    reviewed_at TIMESTAMP DEFAULT NOW(),
    review_duration_seconds INTEGER,  -- How long review took

    -- Context
    invoice_amount DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    vendor_state TEXT,
    tax_type TEXT,  -- 'sales_tax' or 'use_tax'

    UNIQUE(analysis_id)
);

CREATE INDEX idx_reviews_correction_type ON analysis_reviews(correction_type);
CREATE INDEX idx_reviews_pattern_extracted ON analysis_reviews(pattern_extracted);
CREATE INDEX idx_reviews_vendor ON analysis_reviews(vendor_name);
```

### Table: `learned_patterns`
```sql
CREATE TABLE learned_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type TEXT NOT NULL,  -- 'vendor_specific', 'category_rule', 'keyword_trigger', 'anomaly_response'
    pattern_name TEXT NOT NULL,
    description TEXT,

    -- Pattern Definition
    trigger_conditions JSONB NOT NULL,  -- What triggers this pattern
    confidence_adjustment FLOAT,  -- How much to boost/reduce confidence
    override_determination TEXT,  -- Optional: Force a specific determination

    -- Learning Source
    learned_from_review_ids UUID[],  -- Which reviews taught this pattern
    learned_from_count INTEGER DEFAULT 1,
    first_learned_at TIMESTAMP DEFAULT NOW(),
    last_reinforced_at TIMESTAMP,

    -- Application Stats
    times_applied INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_incorrect INTEGER DEFAULT 0,
    accuracy_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN times_applied > 0
        THEN CAST(times_correct AS FLOAT) / times_applied
        ELSE NULL END
    ) STORED,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    requires_validation BOOLEAN DEFAULT TRUE,  -- New patterns need validation
    validated_by TEXT,
    validated_at TIMESTAMP,

    UNIQUE(pattern_name)
);

CREATE INDEX idx_patterns_type ON learned_patterns(pattern_type);
CREATE INDEX idx_patterns_active ON learned_patterns(is_active);
CREATE INDEX idx_patterns_accuracy ON learned_patterns(accuracy_rate DESC);
```

### Table: `pattern_applications`
```sql
CREATE TABLE pattern_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID REFERENCES learned_patterns(id),
    analysis_id UUID REFERENCES analysis_results(id),
    invoice_id TEXT NOT NULL,

    -- Application Details
    applied_at TIMESTAMP DEFAULT NOW(),
    confidence_before FLOAT,
    confidence_after FLOAT,
    determination_before TEXT,
    determination_after TEXT,

    -- Validation
    was_correct BOOLEAN,  -- NULL until human reviews
    reviewed_by TEXT,
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_pattern_apps_pattern ON pattern_applications(pattern_id);
CREATE INDEX idx_pattern_apps_correct ON pattern_applications(was_correct);
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
  "override_determination": null,
  "learned_from_review_ids": ["a1b2c3d4", "e5f6g7h8"]
}
```

**Learning Event**:
```python
# Human corrected 3 Microsoft invoices from "taxable" to "exempt - custom software"
# System extracts pattern:
learned_pattern = {
    'pattern_type': 'vendor_specific',
    'pattern_name': f'{vendor_name}_custom_software',
    'trigger_conditions': {
        'vendor_name': vendor_name,
        'keywords': extract_common_keywords(past_corrections)
    },
    'confidence_adjustment': +20,
    'learned_from_count': 3
}
```

### 2. Category-Based Rules

**Example**: "Professional services" + odd dollar amount = hidden tax
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
    "invoice_date_before": "2025-10-01"  // OLD LAW
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

## Learning Workflow

### Step 1: AI Analysis (Initial Pass)
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

        pattern_notes.append(f"Pattern '{pattern['pattern_name']}' applied (+{pattern['confidence_adjustment']} confidence)")

        # Log pattern application
        log_pattern_application(pattern['id'], base_result['analysis_id'])

    # Cap confidence at 100
    adjusted_confidence = min(100, max(0, adjusted_confidence))

    base_result['confidence'] = adjusted_confidence
    base_result['patterns_applied'] = pattern_notes

    return base_result
```

### Step 2: Human Review (for < 90% confidence)
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
            update_review(review_id, {'pattern_id': pattern_id, 'pattern_extracted': True})

            # If "apply to similar" checked, find similar cases
            if review_data.get('apply_to_similar'):
                similar_cases = find_similar_unreviewed_cases(review_data)
                apply_pattern_to_similar(pattern_id, similar_cases)

    return {'review_id': review_id, 'pattern_extracted': pattern is not None}
```

### Step 3: Pattern Extraction
```python
def extract_pattern_from_correction(review_data: Dict) -> Optional[Dict]:
    """
    Automatically extract a pattern from human correction.
    """
    explanation = review_data['human_explanation']

    # Parse explanation for key indicators
    keywords = extract_keywords(explanation)
    vendor = review_data['vendor_name']
    category = review_data['human_tax_category']

    # Determine pattern type
    if 'always' in explanation.lower() and vendor:
        pattern_type = 'vendor_specific'
        trigger_conditions = {
            'vendor_name': vendor,
            'keywords': keywords
        }
    elif any(word in explanation.lower() for word in ['category', 'type of service']):
        pattern_type = 'category_rule'
        trigger_conditions = {
            'tax_category': category,
            'keywords': keywords
        }
    elif keywords:
        pattern_type = 'keyword_trigger'
        trigger_conditions = {
            'keywords_in_description': keywords
        }
    else:
        return None  # No clear pattern

    # Calculate confidence adjustment based on AI's original error
    ai_confidence = review_data['ai_confidence']
    if ai_confidence < 50:
        adjustment = +30  # AI was very wrong, big adjustment
    elif ai_confidence < 70:
        adjustment = +20
    else:
        adjustment = +10  # AI was close, small adjustment

    return {
        'pattern_type': pattern_type,
        'pattern_name': generate_pattern_name(trigger_conditions),
        'description': explanation,
        'trigger_conditions': trigger_conditions,
        'confidence_adjustment': adjustment,
        'learned_from_review_ids': [review_data['review_id']],
        'requires_validation': True  # New patterns need analyst approval
    }
```

### Step 4: Pattern Validation
```python
def validate_learned_pattern(pattern_id: str, analyst: str) -> Dict:
    """
    Analyst reviews and approves/rejects learned pattern.
    """
    pattern = get_pattern_by_id(pattern_id)

    # Show analyst:
    # - Pattern definition
    # - Source reviews that taught it
    # - Similar cases it would apply to
    # - Estimated impact

    # Analyst chooses: Approve, Modify, Reject
    # If approved:
    update_pattern(pattern_id, {
        'requires_validation': False,
        'validated_by': analyst,
        'validated_at': datetime.now(),
        'is_active': True
    })

    return {'status': 'validated', 'pattern_id': pattern_id}
```

## Similar Case Detection

### Algorithm: Find Similar Transactions
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
        similarity_score = calculate_similarity(reference_review, transaction, criteria)

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

## Dashboard UI: Pattern Management Page

### New Page: Pattern Library (`/patterns`)

```typescript
const PatternsPage: React.FC = () => {
  const [patterns, setPatterns] = useState<LearnedPattern[]>([]);

  return (
    <div>
      <Header title="Pattern Library" subtitle="AI-learned decision patterns">
        <button className="btn-primary">Create Custom Pattern</button>
      </Header>

      <div className="pattern-stats">
        <StatCard label="Active Patterns" value={patterns.filter(p => p.is_active).length} />
        <StatCard label="Pending Validation" value={patterns.filter(p => p.requires_validation).length} />
        <StatCard label="Average Accuracy" value={`${calculateAvgAccuracy(patterns)}%`} />
      </div>

      <table className="pattern-table">
        <thead>
          <tr>
            <th>Pattern Name</th>
            <th>Type</th>
            <th>Learned From</th>
            <th>Times Applied</th>
            <th>Accuracy</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {patterns.map(pattern => (
            <tr key={pattern.id}>
              <td>{pattern.pattern_name}</td>
              <td><Badge>{pattern.pattern_type}</Badge></td>
              <td>{pattern.learned_from_count} reviews</td>
              <td>{pattern.times_applied}</td>
              <td>
                <AccuracyBadge
                  accuracy={pattern.accuracy_rate}
                  className={pattern.accuracy_rate > 0.8 ? 'text-green' : 'text-yellow'}
                />
              </td>
              <td>
                {pattern.requires_validation ? (
                  <Badge color="yellow">Pending Validation</Badge>
                ) : pattern.is_active ? (
                  <Badge color="green">Active</Badge>
                ) : (
                  <Badge color="gray">Inactive</Badge>
                )}
              </td>
              <td>
                <button onClick={() => viewPattern(pattern.id)}>View</button>
                {pattern.requires_validation && (
                  <button onClick={() => validatePattern(pattern.id)}>Validate</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

## Analytics Integration (Power BI)

### New Measures for Learning System

```dax
// Pattern Effectiveness
PatternAccuracyRate =
CALCULATE(
    DIVIDE(
        SUM(learned_patterns[times_correct]),
        SUM(learned_patterns[times_applied]),
        0
    )
)

// Review Efficiency
AvgReviewTime =
AVERAGE(analysis_reviews[review_duration_seconds]) / 60  // in minutes

// Learning Velocity
PatternsLearnedThisMonth =
CALCULATE(
    COUNTROWS(learned_patterns),
    DATESINPERIOD(learned_patterns[first_learned_at], TODAY(), -1, MONTH)
)

// Override Rate
OverrideRate =
DIVIDE(
    COUNTROWS(FILTER(analysis_reviews, analysis_reviews[correction_type] <> 'accept')),
    COUNTROWS(analysis_reviews),
    0
)

// AI Improvement Over Time
ConfidenceAccuracyCorrelation =
CORRELATIONX(
    analysis_reviews,
    analysis_reviews[ai_confidence],
    IF(analysis_reviews[correction_type] = 'accept', 1, 0)
)
```

### Power BI Dashboard: "Learning & Accuracy"

**Page Layout**:
1. **KPI Cards**:
   - Total Patterns Learned
   - Active Patterns
   - Average Pattern Accuracy
   - Reviews This Month

2. **Chart: Pattern Accuracy Over Time**:
   - Line chart showing accuracy rate by pattern creation date
   - Shows if newer patterns are more accurate (learning improving)

3. **Chart: Most Valuable Patterns**:
   - Bar chart of patterns by times_applied
   - Shows which patterns are most useful

4. **Chart: Review Velocity**:
   - Line chart of reviews completed per day/week
   - Shows analyst productivity

5. **Table: Patterns Needing Validation**:
   - List of `requires_validation = TRUE` patterns
   - Click to open validation modal

## API Endpoints for Learning System

### POST /api/reviews
```python
@app.post("/api/reviews")
async def create_review(review_data: ReviewSubmission):
    """
    Submit a human review and trigger pattern learning.
    """
    # Save review
    review_id = save_analysis_review(review_data)

    # Extract pattern if applicable
    pattern = extract_pattern_from_correction(review_data)
    if pattern:
        pattern_id = save_learned_pattern(pattern)
        # Return pattern for analyst to review
        return {
            'review_id': review_id,
            'pattern_extracted': True,
            'pattern': pattern,
            'pattern_id': pattern_id
        }

    return {'review_id': review_id, 'pattern_extracted': False}
```

### GET /api/reviews/{analysis_id}/similar
```python
@app.get("/api/reviews/{analysis_id}/similar")
async def get_similar_cases(analysis_id: str):
    """
    Find similar past reviews to help analyst.
    """
    current_review = get_review_by_analysis_id(analysis_id)
    similar = find_similar_reviewed_cases(current_review)

    return {
        'similar_cases': similar,
        'count': len(similar)
    }
```

### GET /api/patterns
```python
@app.get("/api/patterns")
async def list_patterns(
    pattern_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    requires_validation: Optional[bool] = None
):
    """
    List learned patterns with optional filters.
    """
    patterns = query_patterns(
        pattern_type=pattern_type,
        is_active=is_active,
        requires_validation=requires_validation
    )

    return {'patterns': patterns, 'count': len(patterns)}
```

### POST /api/patterns/{pattern_id}/validate
```python
@app.post("/api/patterns/{pattern_id}/validate")
async def validate_pattern(pattern_id: str, validation: PatternValidation):
    """
    Analyst approves/rejects a learned pattern.
    """
    if validation.action == 'approve':
        activate_pattern(pattern_id, validation.analyst)
        return {'status': 'approved', 'pattern_id': pattern_id}
    elif validation.action == 'modify':
        update_pattern(pattern_id, validation.modifications)
        activate_pattern(pattern_id, validation.analyst)
        return {'status': 'modified_and_approved'}
    else:  # reject
        deactivate_pattern(pattern_id)
        return {'status': 'rejected'}
```

### POST /api/patterns/apply-to-similar
```python
@app.post("/api/patterns/apply-to-similar")
async def apply_pattern_to_similar(request: ApplyPatternRequest):
    """
    Apply a learned pattern to similar unreviewed transactions.
    """
    pattern = get_pattern_by_id(request.pattern_id)
    similar_transactions = find_similar_unreviewed_cases(request.reference_review)

    results = []
    for transaction in similar_transactions:
        # Re-analyze with pattern applied
        updated_result = reanalyze_with_pattern(transaction, pattern)
        results.append({
            'transaction_id': transaction['id'],
            'confidence_before': transaction['confidence'],
            'confidence_after': updated_result['confidence'],
            'determination_changed': updated_result['final_decision'] != transaction['final_decision']
        })

    return {
        'pattern_applied_to': len(results),
        'results': results
    }
```

## Key Metrics to Track

1. **Learning Velocity**:
   - Patterns learned per week
   - Time from correction to pattern extraction

2. **Pattern Quality**:
   - Accuracy rate of learned patterns (should be > 80%)
   - False positive rate (pattern applied incorrectly)

3. **Review Efficiency**:
   - Average time per review
   - Reviews completed per analyst per day
   - % of reviews requiring override

4. **AI Improvement**:
   - Confidence accuracy correlation (higher confidence = more correct?)
   - Override rate trend (should decrease as AI learns)
   - % of transactions auto-approved (should increase)

5. **Coverage**:
   - % of vendors with specific patterns
   - % of categories with learned rules
   - Gap areas (categories with high override rate but no patterns)

## Success Criteria

**After 100 reviews**:
- At least 15 patterns learned
- Average pattern accuracy > 75%
- Override rate < 30%

**After 500 reviews**:
- At least 50 patterns learned
- Average pattern accuracy > 85%
- Override rate < 20%
- Auto-approval rate > 60%

**After 1000 reviews**:
- At least 100 patterns learned
- Average pattern accuracy > 90%
- Override rate < 15%
- Auto-approval rate > 70%

## Next Steps

1. Implement `analysis_reviews` table in Supabase
2. Implement `learned_patterns` table in Supabase
3. Update ReviewPage.tsx with override explanation form
4. Create Pattern Library page
5. Implement pattern extraction algorithm
6. Create similar case detection algorithm
7. Add learning metrics to Power BI dashboard
8. Test with sample corrections and validate pattern learning works
