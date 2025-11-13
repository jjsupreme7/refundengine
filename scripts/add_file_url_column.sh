#!/bin/bash
# Add file_url column to knowledge_documents table

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🔄 Adding file_url column to knowledge_documents table..."

# Run migration using curl to Supabase REST API
SQL="ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS file_url text;"

curl -X POST \
    "https://aebqzqepntwxdgqggteu.supabase.co/rest/v1/rpc/query" \
    -H "apikey: $SUPABASE_SERVICE_KEY" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$SQL\"}"

echo ""
echo "✅ Migration complete!"
