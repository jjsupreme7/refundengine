#!/bin/bash
#
# Deploy file_url update to search_tax_law RPC function
#

set -e

echo "🚀 Deploying file_url update to Supabase..."

# Load environment variables
export $(cat .env | xargs)

# Deploy the SQL migration
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
    -h $SUPABASE_HOST \
    -p $SUPABASE_PORT \
    -U $SUPABASE_USER \
    -d $SUPABASE_DB \
    -f database/migrations/add_file_url_to_search_tax_law.sql

echo "✅ Successfully deployed file_url update!"
echo ""
echo "The search_tax_law function now includes file_url field with clickable links to source documents."
