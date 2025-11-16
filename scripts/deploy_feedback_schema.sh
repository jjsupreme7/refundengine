#!/bin/bash
# Deploy Feedback & Learning Schema to Supabase

set -e

echo "=========================================="
echo "Deploying Feedback & Learning Schema"
echo "=========================================="
echo ""

# Database connection details
DB_HOST="aws-0-us-west-1.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.mkozinzidywrlurzlqtq"
DB_NAME="postgres"

# Check if password is set
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "Error: SUPABASE_DB_PASSWORD environment variable is not set"
    echo "Please set it using: export SUPABASE_DB_PASSWORD='your-password'"
    exit 1
fi

echo "Step 1: Testing database connection..."
PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

echo ""
echo "Step 2: Deploying feedback schema..."
PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/feedback_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Feedback schema deployed successfully"
else
    echo "❌ Schema deployment failed"
    exit 1
fi

echo ""
echo "Step 3: Verifying tables..."
echo ""

PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN (
    'user_feedback',
    'learned_improvements',
    'golden_qa_pairs',
    'citation_preferences',
    'answer_templates'
)
ORDER BY table_name;
"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Tables created:"
echo "  - user_feedback: Stores all user feedback"
echo "  - learned_improvements: Actionable improvement rules"
echo "  - golden_qa_pairs: High-quality Q&A examples"
echo "  - citation_preferences: Preferred citations based on feedback"
echo "  - answer_templates: Learned answer structures"
echo ""
echo "Next steps:"
echo "  1. Run the new UI: streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503"
echo "  2. Ask questions and provide feedback"
echo "  3. Watch the system learn and improve!"
echo ""
