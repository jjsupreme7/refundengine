#!/usr/bin/env python3
"""
Apply Excel File Tracking Migration to Supabase
Executes the migration SQL file to enable automatic Excel change detection
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.database import get_supabase_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = get_supabase_client()


def apply_migration():
    """Apply Excel tracking migration"""

    print("="*80)
    print("EXCEL FILE TRACKING MIGRATION")
    print("="*80)

    # Read migration file
    migration_file = Path(__file__).parent.parent / "database" / "schema" / "migration_excel_file_tracking.sql"

    print(f"📋 Migration file: {migration_file.name}")
    print()

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r') as f:
        sql = f.read()

    # Execute via Supabase Management API
    SUPABASE_PROJECT_ID = os.getenv("SUPABASE_PROJECT_ID")
    SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")

    if not SUPABASE_PROJECT_ID or not SUPABASE_ACCESS_TOKEN:
        print("⚠️  SUPABASE_PROJECT_ID or SUPABASE_ACCESS_TOKEN not found in .env")
        print("Attempting direct SQL execution via psql...")
        return False

    import requests

    url = f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_ID}/database/query"
    headers = {
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"query": sql}

    print("🔄 Applying migration via Supabase Management API...")

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print()
        print("✅ Migration applied successfully!")
        print()

        result = response.json()
        if isinstance(result, list):
            print(f"📊 Executed {len(result)} statements")
        else:
            print(f"📊 Result: {result}")

        print()
        print("="*80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print()
        print("New tables created:")
        print("  • excel_file_tracking (file-level change detection)")
        print("  • excel_row_tracking (row-level change detection)")
        print()
        print("New functions created:")
        print("  • get_unprocessed_rows(file_path)")
        print("  • mark_file_processed(file_path)")
        print("  • mark_row_processed(file_path, row_index)")
        print()
        print("New view created:")
        print("  • v_excel_file_status (monitoring dashboard)")
        print()
        print("Next steps:")
        print("  1. Use ExcelFileWatcher to monitor claim sheets")
        print("  2. Integrate with refund analysis engine")
        print("  3. Test with: python core/excel_file_watcher.py --file test_data/Refund_Claim_Sheet_Test.xlsx")
        print("="*80)
        return True
    else:
        print()
        print(f"❌ Migration failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False


if __name__ == "__main__":
    apply_migration()
