# Feedback System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│  (chatbot/rag_ui_with_feedback.py)                                  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Ask        │  │   View       │  │   Provide    │              │
│  │   Question   │  │   Answer     │  │   Feedback   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ENHANCED RAG SYSTEM                             │
│  (core/enhanced_rag.py)                                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  Agentic RAG Decision Layer                            │         │
│  │  • Check cached knowledge                              │         │
│  │  • Check structured rules                              │         │
│  │  • Decide retrieval strategy                           │         │
│  │  • Apply learned improvements ◄────────────────────┐   │         │
│  └────────────────────────────────────────────────────┘   │         │
│                              │                             │         │
│                              ▼                             │         │
│  ┌────────────────────────────────────────────────────┐   │         │
│  │  Retrieval & Generation                            │   │         │
│  │  • Query expansion with learned terms              │───┘         │
│  │  • Boost preferred citations                       │             │
│  │  • Apply answer templates                          │             │
│  │  • Use golden examples for few-shot                │             │
│  └────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FEEDBACK SYSTEM                                 │
│  (core/feedback_system.py)                                          │
│                                                                      │
│  ┌──────────────────────┐                                           │
│  │  Collect Feedback    │                                           │
│  │  • Thumbs up/down    │                                           │
│  │  • Star ratings      │                                           │
│  │  • Detailed feedback │                                           │
│  └──────────────────────┘                                           │
│            │                                                         │
│            ▼                                                         │
│  ┌──────────────────────┐                                           │
│  │  Analyze & Learn     │                                           │
│  │  • Extract patterns  │                                           │
│  │  • Generate rules    │                                           │
│  │  • Update prefs      │                                           │
│  └──────────────────────┘                                           │
│            │                                                         │
│            ▼                                                         │
│  ┌──────────────────────┐                                           │
│  │  Store Learnings     │                                           │
│  │  • Improvements      │                                           │
│  │  • Preferences       │                                           │
│  │  • Templates         │                                           │
│  │  • Golden pairs      │                                           │
│  └──────────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DATABASE                                    │
│  (Supabase PostgreSQL)                                              │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ user_feedback   │  │ learned_         │  │ golden_qa_      │   │
│  │                 │  │ improvements     │  │ pairs           │   │
│  │ • query         │  │                  │  │                 │   │
│  │ • response      │  │ • type           │  │ • question      │   │
│  │ • rating        │  │ • pattern_match  │  │ • answer        │   │
│  │ • suggestions   │  │ • action         │  │ • citations     │   │
│  └─────────────────┘  │ • confidence     │  │ • category      │   │
│                       │ • validation_rate│  └─────────────────┘   │
│  ┌─────────────────┐  └──────────────────┘                         │
│  │ citation_       │  ┌──────────────────┐                         │
│  │ preferences     │  │ answer_          │                         │
│  │                 │  │ templates        │                         │
│  │ • citation      │  │                  │                         │
│  │ • score         │  │ • name           │                         │
│  │ • topics        │  │ • structure      │                         │
│  │ • metrics       │  │ • query_types    │                         │
│  └─────────────────┘  └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS DASHBOARD                               │
│  (chatbot/feedback_analytics.py)                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Feedback    │  │  Learning    │  │  Citation    │              │
│  │  Trends      │  │  Progress    │  │  Preferences │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Learning Flow Diagram

```
┌─────────────┐
│ User Feedback│
│   Received   │
└──────┬──────┘
       │
       ▼
┌────────────────────────────────────────┐
│  What Type of Feedback?                │
└────────────────────────────────────────┘
       │
       ├──► Thumbs Up/High Rating
       │    └──► Add to Golden Dataset
       │         └──► Use for Few-Shot Learning
       │
       ├──► Better Answer Suggestion
       │    └──► AI Analysis: What's Better?
       │         └──► Extract Improvement Pattern
       │              └──► Create Answer Rule
       │
       ├──► Better Citations
       │    └──► Update Citation Preferences
       │         └──► Boost in Future Searches
       │
       ├──► Better Structure
       │    └──► Extract Format Pattern
       │         └──► Create Answer Template
       │              └──► Apply to Similar Queries
       │
       └──► Pattern Detection (3+ similar)
            └──► AI Synthesis of Pattern
                 └──► Create Improvement Rule
                      └──► Apply When Pattern Matches
```

## Data Flow for Query Processing

```
User Query: "Is SaaS taxable?"
       │
       ▼
┌─────────────────────────────────────────┐
│  1. Load Learned Improvements           │
│     • Get active rules for this query   │
│     • Get preferred citations           │
│     • Get answer template               │
│     • Get golden examples               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  2. Apply Query Improvements            │
│     • Expand query with learned terms   │
│     • Include preferred citation boost  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  3. Retrieval with Preferences          │
│     • Vector search                     │
│     • Boost preferred citations         │
│     • Filter by learned criteria        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  4. Answer Generation with Template     │
│     • Use answer template if available  │
│     • Include golden examples           │
│     • Apply structure preferences       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  5. Present to User                     │
│     • Show answer                       │
│     • Show sources                      │
│     • Request feedback                  │
└────────────┬────────────────────────────┘
             │
             ▼
         Feedback Loop
         (Continuous Improvement)
```

## Database Relationships

```
user_feedback
    │
    ├──► learned_improvements
    │    (via source_feedback_ids)
    │
    ├──► golden_qa_pairs
    │    (via created_from_feedback_id)
    │
    └──► citation_preferences
         (indirect: citations extracted from feedback)

learned_improvements
    │
    └──► Applied during query processing
         (pattern matching)

golden_qa_pairs
    │
    └──► Used in few-shot prompts
         (similar query matching)

citation_preferences
    │
    └──► Boost scores during retrieval
         (topic matching)

answer_templates
    │
    └──► Applied during answer generation
         (query type matching)
```

## Feedback Processing Pipeline

```
Feedback Submitted
       │
       ▼
┌──────────────────────┐
│ Save to Database     │
│ (user_feedback table)│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Immediate Processing                 │
│ • Update citation preferences        │
│ • Check for high-quality answer      │
│ • Trigger pattern detection          │
└──────┬───────────────────────────────┘
       │
       ├──► If high rating (4-5 stars)
       │    └──► Add to golden_qa_pairs
       │
       ├──► If suggested answer
       │    └──► AI analyzes difference
       │         └──► Create improvement rule
       │
       ├──► If suggested citations
       │    └──► Update citation_preferences
       │
       └──► If suggested structure
            └──► Create/update answer_template
```

## Learning Rule Application

```
New Query Arrives
       │
       ▼
┌────────────────────────────────────────┐
│ Fetch Active Improvements              │
│ WHERE is_active = true                 │
│ ORDER BY confidence DESC               │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Filter by Pattern Match                │
│ • Check query_contains                 │
│ • Check context requirements           │
│ • Check category match                 │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Apply Matched Rules                    │
│ • Query expansion                      │
│ • Citation boosting                    │
│ • Template selection                   │
│ • Few-shot examples                    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Track Application                      │
│ • Increment times_applied              │
│ • Await user feedback                  │
│ • Update validation_rate               │
└────────────────────────────────────────┘
```

## Validation Rate Calculation

```
Improvement Rule Created
    │
    ▼
Applied to Query (times_applied++)
    │
    ▼
User Provides Feedback
    │
    ├──► Positive (thumbs up, 4-5 stars)
    │    └──► times_validated++
    │
    └──► Negative (thumbs down, 1-2 stars)
         └──► times_validated (no change)

validation_rate = times_validated / times_applied

If validation_rate > 0.6 → Keep active
If validation_rate < 0.3 AND times_applied > 10 → Consider deactivating
```

## Citation Preference Scoring

```
Citation Appears in Feedback
    │
    ├──► User explicitly suggests it
    │    └──► times_suggested_by_user++ (weight: 1.0)
    │
    ├──► User selects in feedback form
    │    └──► times_chosen_in_feedback++ (weight: 0.8)
    │
    ├──► Retrieved + User thumbs up
    │    └──► times_retrieved_and_liked++ (weight: 0.5)
    │
    └──► Retrieved + User thumbs down
         └──► times_retrieved_and_disliked++ (weight: -0.7)

preference_score =
    (times_suggested_by_user * 1.0) +
    (times_chosen_in_feedback * 0.8) +
    (times_retrieved_and_liked * 0.5) -
    (times_retrieved_and_disliked * 0.7)
    ─────────────────────────────────────
    total_instances

Higher score = More preferred citation
```

## System States Over Time

```
Week 0: Fresh System
├─ 0 feedback
├─ 0 improvements
├─ 0 golden pairs
└─ Baseline performance

Week 1: Initial Learning
├─ 20-50 feedback instances
├─ 5-10 improvements created
├─ 3-5 golden pairs
├─ 10-15 citation preferences
└─ Starting to see patterns

Week 2: Pattern Recognition
├─ 50-100 feedback instances
├─ 15-20 improvements
├─ 8-12 golden pairs
├─ 25-30 citation preferences
└─ Clear improvement in answers

Week 4: Mature System
├─ 150+ feedback instances
├─ 30-40 active improvements
├─ 20+ golden pairs
├─ 50+ citation preferences
└─ Significant quality improvement

Week 12: Optimized System
├─ 500+ feedback instances
├─ 50+ active improvements (low performers deactivated)
├─ 50+ verified golden pairs
├─ 100+ citation preferences
└─ Highly accurate, user-aligned responses
```

## Component Integration Points

```
┌─────────────────────────────────────────────────────────┐
│  enhanced_rag.py                                        │
│  ├─ search_with_decision()                              │
│  │  └─ Calls feedback_system.get_active_improvements()  │
│  │                                                       │
│  ├─ generate_answer()                                   │
│  │  ├─ Calls feedback_system.get_answer_template()      │
│  │  └─ Calls feedback_system.get_golden_examples()      │
│  │                                                       │
│  └─ basic_search()                                      │
│     └─ Can boost preferred citations                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  feedback_system.py                                     │
│  ├─ save_feedback()                                     │
│  │  └─ Triggers learning pipeline                       │
│  │                                                       │
│  ├─ get_active_improvements()                           │
│  │  └─ Returns matching rules for query                 │
│  │                                                       │
│  ├─ get_preferred_citations()                           │
│  │  └─ Returns high-scoring citations                   │
│  │                                                       │
│  ├─ get_answer_template()                               │
│  │  └─ Returns matching template                        │
│  │                                                       │
│  └─ get_golden_examples()                               │
│     └─ Returns similar Q&A pairs                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Database Tables (Supabase)                             │
│  ├─ user_feedback (all feedback)                        │
│  ├─ learned_improvements (rules)                        │
│  ├─ golden_qa_pairs (examples)                          │
│  ├─ citation_preferences (scores)                       │
│  └─ answer_templates (formats)                          │
└─────────────────────────────────────────────────────────┘
```

## Performance Optimization Points

1. **Caching**
   - Embedding cache (in-memory)
   - Active improvements cache (per session)
   - Golden examples cache (by category)

2. **Indexing**
   - GIN index on pattern_match (JSONB)
   - B-tree index on preference_score
   - Partial index on is_active = true

3. **Query Optimization**
   - Fetch only active improvements
   - Limit golden examples to top 3
   - Use materialized views for analytics

4. **Background Processing**
   - Pattern detection (async)
   - Rule validation updates (scheduled)
   - Preference score recalculation (triggered)

## Security Considerations

1. **Input Validation**
   - Sanitize user feedback text
   - Validate rating ranges (1-5)
   - Limit feedback text length

2. **Rate Limiting**
   - Limit feedback submissions per session
   - Prevent spam/abuse

3. **Data Privacy**
   - Optional user_id field
   - Can anonymize feedback
   - GDPR-compliant deletion

4. **Rule Safety**
   - Validation rate monitoring
   - Manual review for critical rules
   - Automatic deactivation of harmful rules
