-- ============================================================================
-- User Feedback & Continuous Learning Schema
-- ============================================================================
-- Purpose: Track user feedback on RAG responses to continuously improve
-- the system through learning loops
-- ============================================================================

-- 1. Core feedback table: captures all user feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Session info
    session_id TEXT,  -- Track feedback across a conversation session
    user_id TEXT,     -- Optional: if you have user authentication

    -- Query & Response
    query TEXT NOT NULL,
    response_text TEXT NOT NULL,

    -- RAG metadata (what was used to generate the response)
    decision_action TEXT,  -- USE_CACHED, USE_RULES, RETRIEVE_SIMPLE, RETRIEVE_ENHANCED
    retrieved_chunks JSONB, -- The chunks that were used
    confidence_score FLOAT,

    -- User feedback
    feedback_type TEXT CHECK (feedback_type IN (
        'thumbs_up',
        'thumbs_down',
        'better_answer',
        'better_structure',
        'better_citations',
        'missing_info',
        'incorrect_info'
    )),

    rating INTEGER CHECK (rating BETWEEN 1 AND 5), -- 1-5 star rating

    -- Detailed feedback
    suggested_answer TEXT,           -- What user thinks answer should be
    suggested_structure TEXT,        -- How user wants answer formatted
    suggested_citations TEXT[],      -- Which citations user would prefer
    suggested_chunks JSONB,          -- Alternative chunks user suggests
    feedback_comment TEXT,           -- Free-form feedback

    -- Feedback metadata
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,

    -- Indexes
    CONSTRAINT feedback_type_check CHECK (
        feedback_type IS NOT NULL OR rating IS NOT NULL
    )
);

-- 2. Learned improvements: actionable insights from feedback
CREATE TABLE IF NOT EXISTS learned_improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- What was learned
    improvement_type TEXT CHECK (improvement_type IN (
        'query_rewrite_rule',      -- Learned better way to rewrite queries
        'citation_preference',     -- User prefers certain citation types
        'answer_template',         -- User prefers specific answer structure
        'chunk_relevance_boost',   -- Boost/demote specific chunks
        'entity_mapping',          -- Map business terms to legal terms
        'retrieval_strategy'       -- Prefer certain retrieval strategies
    )),

    -- The pattern/rule
    pattern_match JSONB,  -- Conditions when this applies (e.g., {"query_contains": ["SaaS", "taxable"]})
    action JSONB,         -- What to do (e.g., {"boost_citations": ["WAC 458-20-15502"]})

    -- Metadata
    confidence FLOAT DEFAULT 0.5,     -- How confident we are in this improvement
    times_applied INTEGER DEFAULT 0,   -- How many times we've used it
    times_validated INTEGER DEFAULT 0, -- How many times users liked it
    validation_rate FLOAT,             -- times_validated / times_applied

    -- Source
    source_feedback_ids UUID[],  -- Which feedback entries led to this learning

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    deactivated_at TIMESTAMPTZ,
    deactivation_reason TEXT
);

-- 3. Query-Answer pairs that work well (golden dataset)
CREATE TABLE IF NOT EXISTS golden_qa_pairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- The golden Q&A
    question TEXT NOT NULL,
    golden_answer TEXT NOT NULL,
    golden_citations TEXT[],
    golden_structure TEXT, -- Template/format

    -- Source
    created_from_feedback_id UUID REFERENCES user_feedback(id),
    curator_notes TEXT,

    -- Usage
    times_referenced INTEGER DEFAULT 0,  -- Used as example for few-shot learning
    last_referenced_at TIMESTAMPTZ,

    -- Categorization
    query_category TEXT,  -- e.g., "software_taxation", "use_tax_rules"
    difficulty TEXT CHECK (difficulty IN ('simple', 'medium', 'complex')),

    -- Quality control
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by TEXT,
    verified_at TIMESTAMPTZ
);

-- 4. Citation preference tracking
CREATE TABLE IF NOT EXISTS citation_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Citation info
    citation TEXT NOT NULL UNIQUE,  -- e.g., "WAC 458-20-15503"
    document_id UUID,               -- Link to knowledge_documents

    -- Preference metrics
    times_suggested_by_user INTEGER DEFAULT 0,   -- User explicitly suggested it
    times_chosen_in_feedback INTEGER DEFAULT 0,   -- User selected it as better
    times_retrieved_and_liked INTEGER DEFAULT 0,  -- Retrieved and got thumbs up
    times_retrieved_and_disliked INTEGER DEFAULT 0, -- Retrieved and got thumbs down

    -- Computed preference score
    preference_score FLOAT,  -- Weighted score based on above metrics

    -- Context
    preferred_for_topics TEXT[],  -- e.g., ["software", "saas", "digital_goods"]

    CONSTRAINT valid_preference_score CHECK (preference_score IS NULL OR preference_score BETWEEN -1 AND 1)
);

-- 5. Answer structure templates (learned from feedback)
CREATE TABLE IF NOT EXISTS answer_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Template info
    template_name TEXT NOT NULL,
    template_structure TEXT NOT NULL,  -- Markdown template with placeholders

    -- When to use this template
    applies_to_query_types TEXT[],  -- e.g., ["Is X taxable?", "How is X classified?"]
    applies_to_categories TEXT[],   -- e.g., ["software_taxation"]

    -- Template content
    template_text TEXT,  -- Example: "According to {citation}, {product} is {classification}..."

    -- Metadata
    source_feedback_ids UUID[],
    times_used INTEGER DEFAULT 0,
    avg_rating FLOAT,

    is_active BOOLEAN DEFAULT TRUE
);

-- 6. Feedback analytics view
CREATE OR REPLACE VIEW feedback_analytics AS
SELECT
    DATE_TRUNC('day', created_at) as feedback_date,
    feedback_type,
    COUNT(*) as count,
    AVG(rating) as avg_rating,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN is_resolved THEN 1 END) as resolved_count
FROM user_feedback
GROUP BY DATE_TRUNC('day', created_at), feedback_type
ORDER BY feedback_date DESC;

-- ============================================================================
-- Indexes for performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON user_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON user_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON user_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON user_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_query ON user_feedback USING gin(to_tsvector('english', query));

CREATE INDEX IF NOT EXISTS idx_improvements_type ON learned_improvements(improvement_type);
CREATE INDEX IF NOT EXISTS idx_improvements_active ON learned_improvements(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_improvements_pattern ON learned_improvements USING gin(pattern_match);

CREATE INDEX IF NOT EXISTS idx_golden_category ON golden_qa_pairs(query_category);
CREATE INDEX IF NOT EXISTS idx_golden_verified ON golden_qa_pairs(is_verified) WHERE is_verified = TRUE;

CREATE INDEX IF NOT EXISTS idx_citation_pref_score ON citation_preferences(preference_score DESC);
CREATE INDEX IF NOT EXISTS idx_citation_pref_topics ON citation_preferences USING gin(preferred_for_topics);

-- ============================================================================
-- Helper functions
-- ============================================================================

-- Function: Update preference score for citations
CREATE OR REPLACE FUNCTION update_citation_preference_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.preference_score := (
        (NEW.times_suggested_by_user * 1.0) +
        (NEW.times_chosen_in_feedback * 0.8) +
        (NEW.times_retrieved_and_liked * 0.5) -
        (NEW.times_retrieved_and_disliked * 0.7)
    ) / NULLIF(
        (NEW.times_suggested_by_user + NEW.times_chosen_in_feedback +
         NEW.times_retrieved_and_liked + NEW.times_retrieved_and_disliked),
        0
    );

    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate preference score
DROP TRIGGER IF EXISTS trg_update_citation_score ON citation_preferences;
CREATE TRIGGER trg_update_citation_score
    BEFORE INSERT OR UPDATE ON citation_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_citation_preference_score();

-- Function: Update validation rate for improvements
CREATE OR REPLACE FUNCTION update_improvement_validation_rate()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.times_applied > 0 THEN
        NEW.validation_rate := NEW.times_validated::FLOAT / NEW.times_applied;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate validation rate
DROP TRIGGER IF EXISTS trg_update_validation_rate ON learned_improvements;
CREATE TRIGGER trg_update_validation_rate
    BEFORE INSERT OR UPDATE ON learned_improvements
    FOR EACH ROW
    EXECUTE FUNCTION update_improvement_validation_rate();

-- ============================================================================
-- Sample queries for analysis
-- ============================================================================

-- Find most common feedback issues
-- SELECT feedback_type, COUNT(*), AVG(rating)
-- FROM user_feedback
-- WHERE created_at > NOW() - INTERVAL '7 days'
-- GROUP BY feedback_type
-- ORDER BY COUNT(*) DESC;

-- Find highest performing improvements
-- SELECT improvement_type, validation_rate, times_applied, confidence
-- FROM learned_improvements
-- WHERE is_active = TRUE AND times_applied > 5
-- ORDER BY validation_rate DESC;

-- Find most preferred citations
-- SELECT citation, preference_score, preferred_for_topics
-- FROM citation_preferences
-- WHERE preference_score > 0.5
-- ORDER BY preference_score DESC;
