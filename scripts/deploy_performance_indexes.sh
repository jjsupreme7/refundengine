#!/bin/bash
# ============================================================================
# Deploy Migration 004: Performance Optimization Indexes
# ============================================================================

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Migration 004: Performance Indexes${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Load environment variables
source .env

# Verify required variables
if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo -e "${RED}Error: SUPABASE_DB_PASSWORD not set in .env${NC}"
    exit 1
fi

# Database connection details
DB_HOST="${SUPABASE_DB_HOST:-aws-0-us-west-1.pooler.supabase.com}"
DB_PORT="${SUPABASE_DB_PORT:-6543}"
DB_NAME="${SUPABASE_DB_NAME:-postgres}"
DB_USER="${SUPABASE_DB_USER:-postgres.ngcqkbgnjvccqfbuflkz}"

echo -e "${BLUE}Connecting to database...${NC}"
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "Database: $DB_NAME"
echo ""

# Run the migration
echo -e "${BLUE}Running migration...${NC}"
PGPASSWORD=$SUPABASE_DB_PASSWORD psql \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    -f database/migrations/migration_004_performance_indexes.sql

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Migration 004 completed successfully!${NC}"
    echo ""
    echo -e "${GREEN}Performance indexes are now active.${NC}"
    echo -e "${GREEN}Your queries should be significantly faster!${NC}"
else
    echo ""
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi
