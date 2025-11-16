# User Feedback & Continuous Learning System

## Overview

This system enables your RAG chatbot to continuously learn and improve from user feedback. Users can provide feedback in various forms, and the system automatically learns patterns and updates itself to provide better responses over time.

## Architecture

### Components

1. **Database Schema** (`database/feedback_schema.sql`)
   - `user_feedback`: Stores all user feedback
   - `learned_improvements`: Actionable improvement rules extracted from feedback
   - `golden_qa_pairs`: High-quality Q&A examples for few-shot learning
   - `citation_preferences`: Tracks which citations users prefer
   - `answer_templates`: Learned answer structure templates

2. **Feedback System** (`core/feedback_system.py`)
   - Collects and stores feedback
   - Analyzes feedback patterns
   - Extracts learnings automatically
   - Applies learnings to improve future responses

3. **Enhanced UI** (`chatbot/rag_ui_with_feedback.py`)
   - Chat interface with integrated feedback widgets
   - Multiple feedback types (thumbs up/down, ratings, detailed suggestions)
   - Real-time learning insights
   - Session tracking

4. **Analytics Dashboard** (`chatbot/feedback_analytics.py`)
   - Visualize feedback trends
   - Track learning progress
   - Monitor system improvements
   - Citation preference analysis

## How It Works

### Feedback Collection

Users can provide feedback in multiple ways:

1. **Quick Feedback**
   - 👍 Thumbs up
   - 👎 Thumbs down
   - ⭐ 1-5 star rating

2. **Detailed Feedback**
   - Suggest better answer
   - Suggest better structure/format
   - Select preferred citations
   - Indicate missing information
   - Report incorrect information

### Learning Process

The system learns from feedback through several mechanisms:

#### 1. Answer Quality Learning
When users suggest better answers:
- AI analyzes the difference between the original and suggested answer
- Extracts what makes the suggested answer better
- Creates improvement rules (e.g., "For software taxation queries, emphasize classification first")

#### 2. Citation Preference Learning
When users indicate preferred citations:
- Tracks which citations users suggest
- Monitors which citations get positive/negative feedback
- Calculates preference scores
- Boosts preferred citations in future retrievals

#### 3. Answer Structure Learning
When users suggest better formatting:
- Extracts the preferred structure pattern
- Creates answer templates for similar query types
- Applies templates to future similar queries

#### 4. Pattern Recognition
System automatically identifies patterns:
- Groups similar feedback instances
- Creates improvement rules when patterns emerge (3+ similar instances)
- Applies rules to matching future queries

#### 5. Golden Dataset Building
High-quality responses (4-5 star ratings):
- Automatically added to golden Q&A dataset
- Used for few-shot learning in future queries
- Helps AI learn from best examples

### Learning Application

When processing new queries, the system:

1. **Retrieves Learned Improvements**
   ```python
   improvements = feedback_system.get_active_improvements(query)
   ```

2. **Gets Preferred Citations**
   ```python
   preferred_citations = feedback_system.get_preferred_citations(query)
   ```

3. **Applies Answer Templates**
   ```python
   template = feedback_system.get_answer_template(query)
   ```

4. **Uses Golden Examples**
   ```python
   examples = feedback_system.get_golden_examples(query, limit=2)
   ```

## Setup Instructions

### 1. Deploy Database Schema

```bash
# Set your database password
export SUPABASE_DB_PASSWORD='your-password'

# Run deployment script
chmod +x scripts/deploy_feedback_schema.sh
./scripts/deploy_feedback_schema.sh
```

This creates all necessary tables, indexes, triggers, and functions.

### 2. Install Dependencies

All required dependencies should already be installed, but ensure you have:
- `streamlit`
- `openai`
- `supabase`
- `pandas`
- `plotly`

### 3. Run the Enhanced UI

```bash
streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503
```

### 4. Run the Analytics Dashboard (Optional)

```bash
streamlit run chatbot/feedback_analytics.py --server.port 8504
```

## Usage Guide

### For End Users

1. **Ask Your Question**
   - Type your question in the chat interface
   - Get an AI-generated answer with sources

2. **Provide Quick Feedback**
   - Click 👍 if the answer was helpful
   - Click 👎 if it wasn't helpful
   - Rate 1-5 stars

3. **Provide Detailed Feedback** (Optional)
   - Click "💡 Suggest Improvement"
   - Choose what to improve:
     - Better answer content
     - Better structure/format
     - Better citations
     - Missing information
     - Incorrect information
   - Provide suggestions in the form
   - Submit feedback

4. **Watch System Improve**
   - The "🧠 System Learning Insights" panel shows what the system has learned
   - You'll see better responses as the system learns

### For Administrators

1. **Monitor Analytics**
   - Open the analytics dashboard (port 8504)
   - View feedback trends
   - Track learning progress
   - Identify areas needing improvement

2. **Verify Golden Q&A Pairs**
   - Review unverified golden pairs in the database
   - Manually verify high-quality examples:
     ```sql
     UPDATE golden_qa_pairs
     SET is_verified = true, verified_by = 'admin_name'
     WHERE id = '<pair_id>';
     ```

3. **Manage Improvement Rules**
   - Review learned improvements
   - Deactivate low-performing rules:
     ```sql
     UPDATE learned_improvements
     SET is_active = false, deactivation_reason = 'Low validation rate'
     WHERE validation_rate < 0.3 AND times_applied > 10;
     ```

## Database Schema Details

### user_feedback Table
```sql
- id: UUID (primary key)
- created_at: Timestamp
- session_id: Session identifier
- query: User's question
- response_text: AI's answer
- feedback_type: Type of feedback
- rating: 1-5 star rating
- suggested_answer: User's suggested better answer
- suggested_structure: Preferred format
- suggested_citations: Preferred sources
- feedback_comment: Additional notes
- decision_action: RAG decision used
- retrieved_chunks: Sources used
- confidence_score: RAG confidence
```

### learned_improvements Table
```sql
- id: UUID (primary key)
- improvement_type: Type of improvement
- pattern_match: When to apply (JSON)
- action: What to do (JSON)
- confidence: Confidence in this rule
- times_applied: Usage count
- times_validated: Success count
- validation_rate: Success percentage (auto-calculated)
- is_active: Whether rule is active
```

### golden_qa_pairs Table
```sql
- id: UUID (primary key)
- question: The question
- golden_answer: High-quality answer
- golden_citations: Sources used
- query_category: Topic category
- difficulty: simple/medium/complex
- is_verified: Manual verification status
- times_referenced: Usage in few-shot learning
```

### citation_preferences Table
```sql
- id: UUID (primary key)
- citation: Citation string (e.g., "WAC 458-20-15503")
- times_suggested_by_user: User suggestions
- times_chosen_in_feedback: Selected in feedback
- times_retrieved_and_liked: Retrieved + thumbs up
- times_retrieved_and_disliked: Retrieved + thumbs down
- preference_score: Calculated score (auto-updated via trigger)
- preferred_for_topics: Relevant topics
```

### answer_templates Table
```sql
- id: UUID (primary key)
- template_name: Template identifier
- template_structure: Format/structure
- applies_to_query_types: When to use
- times_used: Usage count
- avg_rating: Average user rating
- is_active: Whether template is active
```

## Advanced Features

### Custom Learning Rules

You can manually add learning rules:

```sql
INSERT INTO learned_improvements (
    improvement_type,
    pattern_match,
    action,
    confidence,
    is_active
) VALUES (
    'query_rewrite_rule',
    '{"query_contains": ["SaaS", "taxable"]}',
    '{"expand_query_to": "software as a service digital automated services taxation"}',
    0.8,
    true
);
```

### Batch Analysis

Run batch analysis on feedback:

```python
from core.feedback_system import FeedbackSystem

fs = FeedbackSystem()

# Get all unresolved feedback
feedback = fs.supabase.table("user_feedback")\
    .select("*")\
    .eq("is_resolved", False)\
    .execute()

# Process each
for fb in feedback.data:
    fs._trigger_learning_from_feedback(fb['id'], fb)
```

### Export Learnings

Export learnings for review or backup:

```python
import json

# Get all active improvements
improvements = fs.supabase.table("learned_improvements")\
    .select("*")\
    .eq("is_active", True)\
    .execute()

with open("learned_improvements_backup.json", "w") as f:
    json.dump(improvements.data, f, indent=2, default=str)
```

## Performance Optimization

### Automatic Cleanup

Consider implementing automatic cleanup of:
- Low-performing improvements (validation_rate < 0.3)
- Unused improvements (times_applied = 0 after 30 days)
- Old unresolved feedback (> 90 days)

### Caching

The system uses caching for:
- Embeddings (in-memory cache in EnhancedRAG)
- Learned improvements (fetched per query)

### Monitoring

Monitor these metrics:
- Average rating trend (should improve over time)
- Validation rate of improvements (target: >60%)
- Golden dataset growth
- Feedback volume

## Troubleshooting

### No Learnings Being Created

**Problem:** Feedback is being collected but no improvements are learned.

**Solutions:**
1. Check if you have at least 3 similar feedback instances (required for pattern detection)
2. Verify OpenAI API key is set and working
3. Check database logs for errors

### Low Validation Rates

**Problem:** Improvements have low validation rates.

**Solutions:**
1. Review improvement rules manually
2. Deactivate rules with validation_rate < 0.3
3. Collect more feedback to refine patterns

### Database Connection Issues

**Problem:** Cannot connect to Supabase.

**Solutions:**
1. Verify `SUPABASE_DB_PASSWORD` is set
2. Check network connectivity
3. Verify database credentials

## Future Enhancements

Potential additions to the system:

1. **A/B Testing**
   - Test different answer formats
   - Compare with/without learned improvements

2. **User Profiles**
   - Track individual user preferences
   - Personalize responses

3. **Advanced NLP**
   - Better query similarity detection
   - Semantic clustering of feedback

4. **Active Learning**
   - Identify uncertain responses
   - Proactively request feedback

5. **Multi-modal Feedback**
   - Voice feedback
   - Screenshot annotations

## API Reference

### FeedbackSystem Class

```python
from core.feedback_system import FeedbackSystem

fs = FeedbackSystem()

# Save feedback
feedback_id = fs.save_feedback(
    query="Is SaaS taxable?",
    response_text="Yes, SaaS is taxable...",
    feedback_data={
        "feedback_type": "thumbs_up",
        "rating": 5
    },
    session_id="session-123",
    rag_metadata=search_result
)

# Get active improvements
improvements = fs.get_active_improvements(
    query="Is SaaS taxable?",
    context={}
)

# Get preferred citations
citations = fs.get_preferred_citations(
    query="Is SaaS taxable?",
    top_k=5
)

# Get answer template
template = fs.get_answer_template(query="Is SaaS taxable?")

# Get golden examples
examples = fs.get_golden_examples(
    query="Is SaaS taxable?",
    limit=3
)
```

## Best Practices

1. **Encourage Feedback**
   - Make feedback widgets prominent
   - Keep feedback forms simple
   - Show users how their feedback helps

2. **Review Regularly**
   - Check analytics dashboard weekly
   - Verify golden Q&A pairs
   - Deactivate underperforming rules

3. **Iterate**
   - Start with simple feedback (thumbs up/down)
   - Add detailed feedback options later
   - Continuously refine learning algorithms

4. **Quality Control**
   - Manually verify critical improvements
   - Monitor for incorrect learnings
   - Test system regularly

## Conclusion

This feedback system creates a virtuous cycle:
- Users provide feedback
- System learns patterns
- Responses improve
- User satisfaction increases
- More users provide positive feedback

Over time, your RAG system becomes increasingly accurate and aligned with user preferences, creating a truly intelligent and adaptive assistant.
