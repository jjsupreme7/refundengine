#!/bin/bash

# Deploy Vendor Products Enrichment Schema
# Adds industry, business model, products metadata to vendor_products table

set -e  # Exit on error

echo "Deploying Vendor Products Enrichment Schema..."

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Check required environment variables
if [ -z "$SUPABASE_DB_HOST" ] || [ -z "$SUPABASE_DB_USER" ] || [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo "Error: Missing required environment variables"
    echo "Required: SUPABASE_DB_HOST, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD"
    exit 1
fi

# Execute migration
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
    -h $SUPABASE_DB_HOST \
    -U $SUPABASE_DB_USER \
    -d ${SUPABASE_DB_NAME:-postgres} \
    -p ${SUPABASE_DB_PORT:-6543} \
    -f database/schema/migration_vendor_products_enrichment.sql

echo ""
echo "Vendor products enrichment schema deployment complete!"
echo ""
echo "New fields available:"
echo "  - industry, business_model, primary_products"
echo "  - typical_delivery, wa_tax_classification"
echo "  - research_notes, web_research_date, data_quality_score"
echo ""
echo "Next: Run vendor research automation"
