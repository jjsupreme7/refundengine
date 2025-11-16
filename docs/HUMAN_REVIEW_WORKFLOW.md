# Human Review Workflow & Feedback Capture

## Overview

This document defines the detailed step-by-step workflow for human analysts reviewing AI-flagged transactions, capturing feedback, and triggering the learning system.

## Review Queue Prioritization

### Auto-Triage Rules

Transactions are automatically sorted into review queues based on confidence and risk:

| Queue | Confidence | Tax Amount | Priority | SLA |
|-------|-----------|------------|----------|-----|
| **Critical Review** | < 50% | > $10,000 | P1 | 24 hours |
| **High Priority** | 50-70% | > $5,000 | P2 | 3 days |
| **Standard Review** | 70-90% | Any | P3 | 1 week |
| **Low Priority** | 70-90% | < $1,000 | P4 | 2 weeks |
| **Auto-Approved** | ≥ 90% | Any | N/A | None (flagged for spot check only) |

### Queue Assignment Logic

```python
def assign_to_queue(transaction: Dict) -> str:
    """
    Assign transaction to appropriate review queue.
    """
    confidence = transaction['ai_confidence']
    tax_amount = transaction['tax_amount']

    # Auto-approve high confidence
    if confidence >= 90:
        return 'auto_approved'

    # Critical review for low confidence + high dollar
    if confidence < 50 and tax_amount > 10000:
        return 'critical_review'

    # High priority for medium confidence + significant dollar
    if confidence < 70 and tax_amount > 5000:
        return 'high_priority'

    # Standard review for medium confidence
    if confidence < 90 and tax_amount >= 1000:
        return 'standard_review'

    # Low priority for small dollar amounts
    return 'low_priority'
```

## Step-by-Step Review Process

### Step 1: Select Transaction from Queue

**Analyst Action**:
1. Navigate to Review Queue page (`/review`)
2. Queue displays transactions sorted by priority
3. Click on a transaction to open detail panel

**UI Display**:
```typescript
// Review Queue Table
<table>
  <thead>
    <tr>
      <th>Priority</th>
      <th>Vendor</th>
      <th>Description</th>
      <th>Tax Amount</th>
      <th>AI Determination</th>
      <th>Confidence</th>
      <th>Flags</th>
    </tr>
  </thead>
  <tbody>
    {exceptions.map(transaction => (
      <tr
        key={transaction.id}
        className={getPriorityClass(transaction.queue)}
        onClick={() => selectTransaction(transaction)}
      >
        <td><PriorityBadge priority={transaction.queue} /></td>
        <td>{transaction.vendor_name}</td>
        <td>{transaction.description}</td>
        <td>${transaction.tax_amount.toLocaleString()}</td>
        <td>{transaction.ai_determination}</td>
        <td>
          <ConfidenceBadge score={transaction.ai_confidence} />
        </td>
        <td>
          {transaction.anomalies.map(a => <AnomalyFlag key={a} type={a} />)}
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

### Step 2: Review AI Analysis

**Detail Panel Shows**:
1. **Parsed Text**: Invoice description extracted via OCR
2. **System Suggestion**: AI's determination (e.g., "Exempt - Custom Software")
3. **Confidence Score**: 0-100% with visual indicator
4. **Anomalies Detected**: List of red flags (e.g., "Odd dollar amount", "High tax rate")
5. **Tax Type**: Sales Tax or Use Tax
6. **Vendor Context**: Industry, state, past patterns

**Analyst Evaluates**:
- Does the description match the AI's interpretation?
- Are the anomalies valid concerns?
- Is the tax category correct?
- Is the refund basis appropriate?

### Step 3: Request AI Rationale (Optional)

**Analyst Action**: Click "Ask for Rationale" button

**System Response**:
```typescript
// AI Rationale Display
<div className="bg-gray-50 p-4 rounded-md">
  <h4 className="font-semibold">AI Rationale</h4>
  <p className="text-sm mt-2 italic">
    "{selectedLine.determination.rationale}"
  </p>

  <h5 className="font-semibold text-xs text-gray-500 mt-3">MODEL THOUGHTS</h5>
  <p className="text-xs text-gray-600 mt-1">
    {selectedLine.determination.modelThoughts}
  </p>

  <h5 className="font-semibold text-xs text-gray-500 mt-3">CITATIONS</h5>
  <ul className="text-xs text-gray-600 mt-1 list-disc list-inside">
    {selectedLine.determination.citations.map(cite => (
      <li key={cite}>{cite}</li>
    ))}
  </ul>
</div>
```

**API Call**:
```python
@app.post("/api/analysis/{analysis_id}/rationale")
async def get_rationale(analysis_id: str):
    """
    Generate detailed rationale for AI determination.
    """
    analysis = get_analysis_by_id(analysis_id)

    # Call enhanced RAG system
    rationale = generate_rationale(
        description=analysis['description'],
        determination=analysis['final_decision'],
        tax_category=analysis['tax_category'],
        law_version='OLD'
    )

    # Update analysis with rationale
    update_analysis(analysis_id, {'rationale': rationale})

    return rationale
```

### Step 4: Review Supporting Documents

**Analyst Action**: Click on invoice file name to view

**System Displays**:
- PDF viewer with highlighted text (OCR results)
- Side-by-side comparison: Original invoice | Parsed data
- Download button for local review

**Key Checks**:
- Does invoice match parsed description?
- Is tax clearly shown on invoice?
- Are there additional line items AI missed?
- Is vendor information correct?

### Step 5: Check Similar Past Cases

**System Automatically Shows**:
```typescript
// Similar Cases Panel
{similarCases.length > 0 && (
  <div className="bg-blue-50 p-4 rounded-md mt-4">
    <h4 className="font-semibold text-blue-800">
      <Icons icon="history" className="inline w-5 h-5 mr-2" />
      Similar Past Cases Found
    </h4>
    <p className="text-sm text-blue-700 mt-2">
      {similarCases.length} similar transactions were previously reviewed:
    </p>
    <ul className="mt-3 space-y-2">
      {similarCases.map(case => (
        <li key={case.id} className="bg-white p-2 rounded border border-blue-200">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium">{case.vendor_name}</p>
              <p className="text-xs text-gray-600">{case.description}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-blue-800">
                {case.human_determination}
              </p>
              <p className="text-xs text-gray-500">
                Similarity: {(case.similarity_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          <button
            onClick={() => viewCase(case.id)}
            className="text-xs text-blue-600 underline mt-1"
          >
            View Full Review
          </button>
        </li>
      ))}
    </ul>
  </div>
)}
```

**Analyst Benefits**:
- See how similar cases were resolved
- Maintain consistency in determinations
- Learn from past analyst decisions

### Step 6: Make Decision

Analyst has 5 options:

#### Option A: Accept AI Determination
**When to Use**: AI is correct, confidence just below 90% threshold

**Action**: Click "Accept" button

**System Behavior**:
```python
def handle_accept(analysis_id: str, analyst: str):
    """
    Analyst accepts AI determination.
    """
    # Update analysis status
    update_analysis(analysis_id, {
        'review_status': 'accepted',
        'reviewed_by': analyst,
        'reviewed_at': datetime.now()
    })

    # Create review record
    create_review({
        'analysis_id': analysis_id,
        'correction_type': 'accept',
        'reviewed_by': analyst
    })

    # No pattern learning needed
    return {'status': 'accepted'}
```

**UI Feedback**:
- Green checkmark appears
- Transaction removed from review queue
- Next transaction auto-selected

---

#### Option B: Override Taxability
**When to Use**: AI got the taxability wrong (e.g., said "Taxable" but should be "Exempt")

**Action**: Click "Override: Taxable" or "Override: Exempt" button

**System Shows Override Form**:
```typescript
// Override Form Modal
<Modal isOpen={isOverrideModalOpen} title="Override AI Determination">
  <form onSubmit={handleOverrideSubmit}>
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700">
        AI Suggested: <span className="font-semibold">{aiDetermination}</span>
      </label>
      <label className="block text-sm font-medium text-gray-700 mt-2">
        Your Determination:
      </label>
      <select
        name="human_taxability"
        required
        className="mt-1 block w-full border-gray-300 rounded-md"
      >
        <option value="taxable">Taxable</option>
        <option value="exempt">Exempt</option>
        <option value="partial">Partially Taxable</option>
        <option value="needs review">Needs Further Review</option>
      </select>
    </div>

    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700">
        Tax Category:
      </label>
      <select name="tax_category" required>
        <option value="">Select category...</option>
        <option value="Custom Software">Custom Software</option>
        <option value="DAS">Digital Automated Services</option>
        <option value="Services">Services</option>
        <option value="Professional Services">Professional Services</option>
        {/* ... all categories */}
      </select>
    </div>

    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700">
        Refund Basis:
      </label>
      <select name="refund_basis" required>
        <option value="">Select basis...</option>
        <option value="Non-Taxable">Non-Taxable</option>
        <option value="MPU">Multiple Points of Use</option>
        <option value="Out of State - Services">Out of State - Services</option>
        <option value="Custom Software Exemption">Custom Software Exemption</option>
        {/* ... all bases */}
      </select>
    </div>

    <div className="mb-4 bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <label className="block text-sm font-medium text-yellow-800 mb-2">
        Explanation (Required) *
      </label>
      <p className="text-xs text-yellow-700 mb-2">
        Help the AI learn: Why was the initial determination incorrect?
      </p>
      <textarea
        name="explanation"
        required
        rows={4}
        className="w-full border-gray-300 rounded-md"
        placeholder="Example: AI categorized this as 'Software License' but invoice clearly shows 'custom development services' which are exempt under WAC 458-20-15502(3)(a). Vendor is providing custom coding, not prewritten software."
      />
    </div>

    <div className="mb-4">
      <label className="flex items-center">
        <input
          type="checkbox"
          name="apply_to_similar"
          className="mr-2"
        />
        <span className="text-sm text-gray-700">
          Apply this pattern to similar transactions automatically
        </span>
      </label>
    </div>

    <div className="flex justify-end space-x-2">
      <button
        type="button"
        onClick={() => setIsOverrideModalOpen(false)}
        className="px-4 py-2 border border-gray-300 rounded-md"
      >
        Cancel
      </button>
      <button
        type="submit"
        className="px-4 py-2 bg-blue-600 text-white rounded-md"
      >
        Submit Override
      </button>
    </div>
  </form>
</Modal>
```

**Backend Processing**:
```python
@app.post("/api/reviews/override")
async def handle_override(override_data: OverrideSubmission):
    """
    Process analyst override and trigger pattern learning.
    """
    # Save review
    review_id = create_review({
        'analysis_id': override_data.analysis_id,
        'ai_taxability': override_data.ai_taxability,
        'ai_tax_category': override_data.ai_tax_category,
        'ai_confidence': override_data.ai_confidence,
        'human_taxability': override_data.human_taxability,
        'human_tax_category': override_data.human_tax_category,
        'human_refund_basis': override_data.human_refund_basis,
        'human_explanation': override_data.explanation,
        'correction_type': 'override_taxability',
        'reviewed_by': override_data.analyst,
        'apply_to_similar': override_data.apply_to_similar
    })

    # Extract pattern from explanation
    pattern = extract_pattern_from_correction({
        'review_id': review_id,
        'vendor_name': override_data.vendor_name,
        'human_tax_category': override_data.human_tax_category,
        'human_explanation': override_data.explanation,
        'ai_confidence': override_data.ai_confidence
    })

    pattern_id = None
    if pattern:
        # Save learned pattern
        pattern_id = save_learned_pattern(pattern)

        # Link to review
        update_review(review_id, {
            'pattern_extracted': True,
            'pattern_id': pattern_id
        })

        # Find similar cases if requested
        if override_data.apply_to_similar:
            similar_cases = find_similar_unreviewed_cases(override_data)
            applied_count = apply_pattern_to_similar(pattern_id, similar_cases)

            return {
                'review_id': review_id,
                'pattern_extracted': True,
                'pattern_id': pattern_id,
                'applied_to_similar': applied_count
            }

    # Update original analysis
    update_analysis(override_data.analysis_id, {
        'final_decision': override_data.human_taxability,
        'tax_category': override_data.human_tax_category,
        'refund_basis': override_data.human_refund_basis,
        'review_status': 'overridden',
        'reviewed_by': override_data.analyst
    })

    return {
        'review_id': review_id,
        'pattern_extracted': pattern is not None,
        'pattern_id': pattern_id
    }
```

---

#### Option C: Send to Client
**When to Use**: Unclear determination, need client clarification

**Action**: Click "Send to Client" button

**System Shows Email Template**:
```typescript
// Client Question Modal
<Modal isOpen={isClientQuestionOpen} title="Send Question to Client">
  <form onSubmit={handleSendToClient}>
    <div className="mb-4 bg-gray-50 p-3 rounded">
      <h4 className="font-semibold text-sm">Transaction Summary</h4>
      <p className="text-sm mt-1">
        <strong>Vendor:</strong> {selectedLine.vendor_name}<br />
        <strong>Description:</strong> {selectedLine.description}<br />
        <strong>Tax Amount:</strong> ${selectedLine.tax_amount}
      </p>
    </div>

    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Question for Client:
      </label>
      <textarea
        name="question"
        required
        rows={5}
        className="w-full border-gray-300 rounded-md"
        placeholder="Example: This invoice shows a charge for 'system integration services.' Can you clarify whether this was custom software development work or configuration of prewritten software?"
      />
    </div>

    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Specific Information Needed:
      </label>
      <div className="space-y-2">
        <label className="flex items-center">
          <input type="checkbox" name="info_type[]" value="service_type" className="mr-2" />
          <span className="text-sm">Type of service provided</span>
        </label>
        <label className="flex items-center">
          <input type="checkbox" name="info_type[]" value="delivery_location" className="mr-2" />
          <span className="text-sm">Where service was delivered</span>
        </label>
        <label className="flex items-center">
          <input type="checkbox" name="info_type[]" value="tangible_goods" className="mr-2" />
          <span className="text-sm">Whether tangible goods were included</span>
        </label>
        <label className="flex items-center">
          <input type="checkbox" name="info_type[]" value="contract_terms" className="mr-2" />
          <span className="text-sm">Contract or statement of work</span>
        </label>
      </div>
    </div>

    <div className="flex justify-end space-x-2">
      <button type="button" onClick={() => setIsClientQuestionOpen(false)} className="btn-secondary">
        Cancel
      </button>
      <button type="submit" className="btn-primary">
        Send to Client
      </button>
    </div>
  </form>
</Modal>
```

**Backend Processing**:
```python
@app.post("/api/reviews/send-to-client")
async def send_to_client(request: ClientQuestionRequest):
    """
    Send question to client and pause review.
    """
    # Create client question record
    question_id = create_client_question({
        'analysis_id': request.analysis_id,
        'question_text': request.question,
        'info_needed': request.info_types,
        'asked_by': request.analyst,
        'status': 'pending_client_response'
    })

    # Update analysis status
    update_analysis(request.analysis_id, {
        'review_status': 'awaiting_client',
        'client_question_id': question_id
    })

    # Send email to client
    send_email({
        'to': request.client_email,
        'subject': f'Question about Invoice {request.invoice_number}',
        'template': 'client_question',
        'data': {
            'vendor': request.vendor_name,
            'description': request.description,
            'question': request.question,
            'response_link': f'{BASE_URL}/client/respond/{question_id}'
        }
    })

    return {
        'question_id': question_id,
        'status': 'sent_to_client'
    }
```

---

#### Option D: Flag for Senior Review
**When to Use**: Complex case beyond analyst's expertise

**Action**: Click "Escalate" button

**System Behavior**:
```python
def handle_escalation(analysis_id: str, analyst: str, reason: str):
    """
    Escalate transaction to senior analyst.
    """
    update_analysis(analysis_id, {
        'review_status': 'escalated',
        'escalated_by': analyst,
        'escalation_reason': reason,
        'queue': 'senior_review'
    })

    # Notify senior analyst
    notify_senior_analyst({
        'analysis_id': analysis_id,
        'escalated_by': analyst,
        'reason': reason
    })

    return {'status': 'escalated'}
```

---

#### Option E: Mark as Exception (No Refund)
**When to Use**: Tax was correctly charged, no refund due

**Action**: Click "Mark as Correctly Taxed" button

**System Shows Confirmation**:
```typescript
<Modal isOpen={isNoRefundModalOpen} title="Mark as Correctly Taxed">
  <div className="mb-4">
    <p className="text-sm text-gray-700">
      You are marking this transaction as correctly taxed with no refund due.
      This will remove it from the claim sheet.
    </p>
  </div>

  <div className="mb-4">
    <label className="block text-sm font-medium text-gray-700 mb-2">
      Reason (Optional):
    </label>
    <textarea
      name="no_refund_reason"
      rows={3}
      className="w-full border-gray-300 rounded-md"
      placeholder="Example: Vendor provided tangible goods with installation, tax correctly applied to goods portion."
    />
  </div>

  <div className="flex justify-end space-x-2">
    <button onClick={() => setIsNoRefundModalOpen(false)} className="btn-secondary">
      Cancel
    </button>
    <button onClick={handleNoRefund} className="btn-primary">
      Confirm No Refund
    </button>
  </div>
</Modal>
```

### Step 7: Review Confirmation

After any decision, system shows confirmation:

```typescript
// Success Toast
<Toast type="success" duration={3000}>
  ✅ Review submitted successfully
  {patternExtracted && (
    <p className="text-xs mt-1">
      🧠 New pattern learned: "{patternName}"
    </p>
  )}
  {appliedToSimilar > 0 && (
    <p className="text-xs mt-1">
      ⚡ Applied to {appliedToSimilar} similar transactions
    </p>
  )}
</Toast>
```

## Workflow Diagram

```
START
  ↓
[Select Transaction from Queue]
  ↓
[Review AI Analysis]
  ↓
[Optional: Request Rationale] ←─────┐
  ↓                                  │
[Review Supporting Docs]             │
  ↓                                  │
[Check Similar Past Cases]           │
  ↓                                  │
[Make Decision] ────────────────────┘
  ├─→ Accept ────────────→ [Update DB] ──→ [Next Transaction]
  ├─→ Override ──→ [Explain] ──→ [Extract Pattern] ──→ [Apply to Similar] ──→ [Next Transaction]
  ├─→ Send to Client ──→ [Email Client] ──→ [Pause] ──→ [Wait for Response]
  ├─→ Escalate ──→ [Notify Senior] ──→ [Next Transaction]
  └─→ No Refund ──→ [Update DB] ──→ [Next Transaction]
```

## Keyboard Shortcuts

To improve analyst efficiency:

| Key | Action |
|-----|--------|
| `A` | Accept AI determination |
| `O` | Override (opens form) |
| `R` | Request AI rationale |
| `C` | Send to client |
| `E` | Escalate to senior |
| `N` | Mark as no refund |
| `↑/↓` | Navigate between transactions |
| `Enter` | Confirm action |
| `Esc` | Close modal |

## Batch Review Operations

For experienced analysts reviewing many similar cases:

```typescript
// Batch Review Mode
const BatchReviewPanel = () => {
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);

  return (
    <div className="batch-review-panel">
      <h3>Batch Review Mode</h3>
      <p className="text-sm text-gray-600">
        Select multiple similar transactions to apply the same determination.
      </p>

      <div className="selected-count">
        {selectedTransactions.length} transactions selected
      </div>

      <button
        onClick={() => applyBatchDecision(selectedTransactions)}
        disabled={selectedTransactions.length === 0}
        className="btn-primary"
      >
        Apply Decision to Selected
      </button>
    </div>
  );
};
```

## Quality Assurance

### Random Spot Checks

10% of auto-approved transactions (≥90% confidence) randomly flagged for spot check:

```python
def flag_for_spot_check():
    """
    Randomly select 10% of auto-approved transactions for QA.
    """
    auto_approved = get_auto_approved_transactions()
    sample_size = len(auto_approved) * 0.1

    spot_check_sample = random.sample(auto_approved, int(sample_size))

    for transaction in spot_check_sample:
        update_analysis(transaction['id'], {
            'review_status': 'spot_check_required',
            'queue': 'qa_review'
        })
```

### Senior Analyst Review

Senior analysts review:
- All escalated cases
- Random sample of junior analyst decisions (5%)
- All transactions > $50,000 tax amount
- First 20 decisions by new analysts

```python
def flag_for_senior_review(analysis: Dict, analyst: Dict):
    """
    Determine if transaction needs senior review.
    """
    # High dollar amount
    if analysis['tax_amount'] > 50000:
        return True, 'high_dollar_amount'

    # New analyst (first 20 reviews)
    if analyst['total_reviews'] < 20:
        return True, 'new_analyst_training'

    # Random sample of experienced analysts (5%)
    if random.random() < 0.05:
        return True, 'random_qa'

    return False, None
```

## Performance Metrics

Track analyst performance to identify training needs:

```python
analyst_metrics = {
    'reviews_completed': 142,
    'avg_review_time_seconds': 245,  # ~4 minutes
    'override_rate': 0.23,  # 23% of AI determinations overridden
    'accept_rate': 0.77,
    'escalation_rate': 0.05,
    'client_question_rate': 0.08,
    'patterns_learned': 12,
    'accuracy_vs_senior': 0.91,  # 91% agreement with senior reviews
    'reviews_per_day': 28
}
```

**Ideal Targets**:
- Override rate: 15-25% (too low = not catching errors, too high = AI not learning)
- Avg review time: 3-5 minutes
- Escalation rate: < 10%
- Accuracy vs senior: > 90%
- Reviews per day: 20-40 (depending on complexity)

## Next Steps

1. Implement override form with explanation requirement
2. Create similar case detection algorithm
3. Build pattern extraction from explanations
4. Add keyboard shortcuts to ReviewPage
5. Create QA spot check system
6. Build senior review queue
7. Add analyst performance dashboard
8. Test workflow with sample reviews
