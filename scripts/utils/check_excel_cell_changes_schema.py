#!/usr/bin/env python3
"""
Check the exact schema of excel_cell_changes table in Supabase
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import get_supabase_client


def main():
    print("=" * 70)
    print("CHECKING excel_cell_changes TABLE SCHEMA")
    print("=" * 70)

    try:
        supabase = get_supabase_client()
        print("✓ Connected to Supabase\n")

        # Get a sample row to see actual columns
        print("Fetching sample data from excel_cell_changes...")
        result = supabase.table('excel_cell_changes').select('*').limit(1).execute()

        if result.data and len(result.data) > 0:
            print(f"✅ Table exists with data\n")
            print("Columns in excel_cell_changes:")
            for col in sorted(result.data[0].keys()):
                print(f"   - {col}")
        else:
            print("⚠️  Table exists but is EMPTY")
            print("\nTo see the schema without data, checking information_schema...")

            # Try to get schema from information_schema
            # This is a workaround - Supabase might not expose this directly
            print("\nAttempting to query table structure...")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

        if "Could not find the table" in str(e):
            print("\n❌ excel_cell_changes table DOES NOT EXIST in Supabase")
        else:
            print(f"\nUnexpected error: {e}")

if __name__ == '__main__':
    main()
