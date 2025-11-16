#!/bin/bash

# Deploy Excel File Tracking Schema to Supabase
# Applies migration_excel_file_tracking.sql

# Supabase connection details
DB_HOST="aws-0-us-west-1.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.aomkrzblkbhbikqanfat"
DB_NAME="postgres"
DB_PASSWORD="jSnuCinRda65zCuA"

SCHEMA_FILE="database/schema/migration_excel_file_tracking.sql"

echo "========================================================================"
echo "DEPLOYING EXCEL FILE TRACKING SCHEMA"
echo "========================================================================"
echo "Schema file: $SCHEMA_FILE"
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Check if schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ Schema file not found: $SCHEMA_FILE"
    exit 1
fi

# Deploy using psql
echo "🔄 Deploying schema..."
echo ""

export PGPASSWORD="$DB_PASSWORD"

psql -h "$DB_HOST" \
     -p "$DB_PORT" \
     -U "$DB_USER" \
     -d "$DB_NAME" \
     -f "$SCHEMA_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL"
    echo "========================================================================"
    echo ""
    echo "Tables created:"
    echo "  • excel_file_tracking"
    echo "  • excel_row_tracking"
    echo ""
    echo "Functions created:"
    echo "  • get_unprocessed_rows()"
    echo "  • mark_file_processed()"
    echo "  • mark_row_processed()"
    echo ""
    echo "View created:"
    echo "  • v_excel_file_status"
    echo ""
    echo "Next steps:"
    echo "  1. Test with: python core/excel_file_watcher.py --file test_data/Refund_Claim_Sheet_Test.xlsx"
    echo "  2. Integrate with refund analysis engine"
    echo ""
else
    echo ""
    echo "❌ Deployment failed"
    exit 1
fi
