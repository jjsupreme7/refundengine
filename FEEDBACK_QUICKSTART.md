# User Feedback System - Quick Start Guide

## What This Does

Your RAG system can now **continuously learn and improve** from user feedback! Users can:
- Give thumbs up/down on answers
- Rate answers 1-5 stars
- Suggest better answers
- Indicate preferred answer structure
- Select which citations they prefer

The system automatically learns from this feedback and improves future responses.

## Quick Setup (5 Minutes)

### Step 1: Deploy Database Schema

```bash
export SUPABASE_DB_PASSWORD='jSnuCinRda65zCuA'
./scripts/deploy_feedback_schema.sh
```

This creates 5 new tables:
- `user_feedback` - Stores all feedback
- `learned_improvements` - Auto-generated improvement rules
- `golden_qa_pairs` - High-quality Q&A examples
- `citation_preferences` - Which citations users prefer
- `answer_templates` - Learned answer formats

### Step 2: Run the New UI

```bash
streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503
```

Open http://localhost:8503

### Step 3: Try It Out!

1. Ask a question (e.g., "Is SaaS taxable in Washington?")
2. Get an answer
3. Click 👍 or 👎
4. Click "💡 Suggest Improvement" for detailed feedback
5. Watch the "🧠 System Learning Insights" panel to see what's been learned

### Step 4: View Analytics (Optional)

```bash
streamlit run chatbot/feedback_analytics.py --server.port 8504
```

Open http://localhost:8504 to see:
- Feedback trends over time
- Learning progress
- Citation preferences
- Golden Q&A dataset growth

## How It Works

### The Learning Loop

```
User asks question → AI generates answer → User provides feedback
                                              ↓
                        Better future answers ← System learns patterns
```

### Types of Learning

1. **Answer Quality Learning**
   - User suggests better answer
   - AI analyzes what makes it better
   - Creates rule for similar queries

2. **Citation Preference Learning**
   - Tracks which citations get positive feedback
   - Boosts preferred citations in future searches
   - Deprioritizes disliked citations

3. **Answer Structure Learning**
   - User indicates preferred format
   - Creates template for similar query types
   - Applies template to future answers

4. **Pattern Recognition**
   - Groups similar feedback (3+ instances)
   - Auto-creates improvement rules
   - Applies rules when patterns match

5. **Golden Dataset Building**
   - High-rated answers (4-5 stars) saved as examples
   - Used for few-shot learning
   - Improves answer quality over time

## Feedback Types

### Quick Feedback
- **👍 Thumbs Up**: Answer was helpful
- **👎 Thumbs Down**: Answer wasn't helpful
- **⭐ Rating**: 1-5 star rating

### Detailed Feedback
- **Better Answer**: Suggest what the answer should have been
- **Better Structure**: Describe preferred format
- **Better Citations**: Select which sources to use
- **Missing Info**: Indicate what was left out
- **Incorrect Info**: Report errors

## Example Usage Flow

### Scenario: User Gets Unhelpful Answer

1. **User asks**: "How is Azure taxed?"
2. **AI responds**: Generic answer about cloud services
3. **User clicks**: 👎 and "💡 Suggest Improvement"
4. **User selects**: "Better answer content"
5. **User writes**: "Azure should be classified as IaaS/PaaS, which is taxable as a digital automated service under RCW 82.04.192..."
6. **User submits** feedback

### What Happens Next

1. **Immediate**: Feedback saved to database
2. **Within seconds**: AI analyzes the suggestion
3. **Learning extracted**: System learns "For Azure queries, emphasize IaaS/PaaS classification and cite RCW 82.04.192"
4. **Improvement created**: New rule added to `learned_improvements` table
5. **Future queries**: Similar questions get better answers automatically

## Monitoring Progress

### Check Learning Insights (in UI)

The sidebar shows:
- Number of active improvement rules
- Validation rates (how often rules help)
- Golden dataset size

### Check Analytics Dashboard

View detailed metrics:
- Feedback volume over time
- Rating distribution
- Top performing improvements
- Most preferred citations
- Recent detailed feedback

### Check Database Directly

```sql
-- See what the system has learned
SELECT improvement_type, confidence, validation_rate, times_applied
FROM learned_improvements
WHERE is_active = true
ORDER BY validation_rate DESC;

-- See preferred citations
SELECT citation, preference_score, preferred_for_topics
FROM citation_preferences
WHERE preference_score > 0
ORDER BY preference_score DESC;

-- See golden Q&A pairs
SELECT question, query_category, difficulty, is_verified
FROM golden_qa_pairs
ORDER BY created_at DESC;
```

## Key Features

### Automatic Learning
- No manual configuration needed
- Learns from patterns automatically
- Creates rules when 3+ similar feedback instances

### Real-Time Application
- Learned improvements applied immediately
- Citation preferences update in real-time
- Answer templates used for matching queries

### Quality Control
- Validation tracking (success rate of each rule)
- Manual verification option for golden pairs
- Ability to deactivate low-performing rules

### Comprehensive Feedback
- Multiple feedback types
- Both quick and detailed options
- Session tracking across conversations

## File Structure

```
refund-engine/
├── database/
│   └── feedback_schema.sql          # Database schema
├── core/
│   └── feedback_system.py           # Learning engine
├── chatbot/
│   ├── rag_ui_with_feedback.py     # Main UI with feedback
│   └── feedback_analytics.py        # Analytics dashboard
├── scripts/
│   └── deploy_feedback_schema.sh    # Deployment script
└── docs/
    └── FEEDBACK_SYSTEM_GUIDE.md     # Detailed documentation
```

## Common Questions

### How much feedback is needed before the system learns?

- **Quick learning**: Thumbs up/down and ratings are used immediately
- **Pattern learning**: Requires 3+ similar instances to create rules
- **Golden dataset**: High-rated answers (4-5 stars) added immediately

### Can I manually add improvement rules?

Yes! Insert directly into `learned_improvements` table:

```sql
INSERT INTO learned_improvements (improvement_type, pattern_match, action, confidence)
VALUES (
    'citation_preference',
    '{"query_contains": ["software"]}',
    '{"prefer_citations": ["WAC 458-20-15502", "WAC 458-20-15503"]}',
    0.9
);
```

### How do I deactivate a bad rule?

```sql
UPDATE learned_improvements
SET is_active = false, deactivation_reason = 'Not helpful'
WHERE id = '<rule_id>';
```

### Can I export learnings?

Yes, see the "Export Learnings" section in the full guide (docs/FEEDBACK_SYSTEM_GUIDE.md).

## Next Steps

1. ✅ Deploy schema
2. ✅ Run UI with feedback
3. ✅ Collect feedback from users
4. ✅ Monitor analytics
5. Review and verify golden pairs
6. Fine-tune improvement rules as needed
7. Export learnings for backup

## Support

For detailed documentation, see: `docs/FEEDBACK_SYSTEM_GUIDE.md`

For issues or questions:
- Check database logs
- Review analytics dashboard
- Verify OpenAI API key is set

## Example Results After 1 Week

With ~50 feedback instances:
- 10-15 learned improvement rules
- 5-8 golden Q&A pairs
- 20+ citation preferences
- 3-5 answer templates
- Noticeable improvement in answer quality
- Higher user satisfaction (increased ratings)

## Success Metrics

Track these over time:
- **Average rating**: Should trend upward (target: 4+)
- **Validation rate**: Percentage of improvements that help (target: 60%+)
- **Golden dataset size**: High-quality examples (target: 50+)
- **Thumbs up ratio**: Up votes vs down votes (target: 3:1)

Happy learning! 🧠
