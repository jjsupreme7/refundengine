#!/usr/bin/env python3
"""
Quick script to check if projects table exists in Supabase
and verify the excel_file_tracking structure
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import get_supabase_client


def main():
    print("=" * 70)
    print("CHECKING SUPABASE DATABASE FOR PROJECTS TABLE")
    print("=" * 70)

    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✓ Connected to Supabase")

        # Check 1: Try to query projects table
        print("\n[Check 1] Looking for 'projects' table...")
        try:
            result = supabase.table('projects').select('*', count='exact').limit(0).execute()
            print(f"✅ 'projects' table EXISTS!")
            print(f"   Total rows: {result.count if hasattr(result, 'count') else 'unknown'}")

            # Get sample data if any exists
            sample = supabase.table('projects').select('*').limit(5).execute()
            if sample.data:
                print(f"\n   Sample projects:")
                for proj in sample.data:
                    print(f"   - {proj.get('id')}: {proj.get('name', 'N/A')}")
            else:
                print("   (Table exists but is empty)")

        except Exception as e:
            print(f"❌ 'projects' table DOES NOT EXIST")
            print(f"   Error: {str(e)}")

        # Check 2: Verify excel_file_tracking has project_id column
        print("\n[Check 2] Checking 'excel_file_tracking' structure...")
        try:
            result = supabase.table('excel_file_tracking').select('*').limit(1).execute()
            if result.data and len(result.data) > 0:
                first_row = result.data[0]
                columns = list(first_row.keys())

                print(f"✓ 'excel_file_tracking' table has {len(columns)} columns:")
                for col in sorted(columns):
                    print(f"   - {col}")

                # Check specifically for project_id
                if 'project_id' in columns:
                    print(f"\n✅ 'project_id' column EXISTS in excel_file_tracking")
                else:
                    print(f"\n❌ 'project_id' column MISSING from excel_file_tracking")
            else:
                print("   Table exists but is empty - can't verify column structure")

        except Exception as e:
            print(f"❌ Error checking excel_file_tracking: {str(e)}")

        # Check 3: List all tables (if possible)
        print("\n[Check 3] Attempting to list all tables...")
        try:
            # Use RPC if you have a custom function, or we can try a different approach
            # For now, let's try querying common tables we know should exist
            common_tables = [
                'projects',
                'excel_file_tracking',
                'excel_file_versions',
                'excel_cell_changes',
                'knowledge_documents',
                'vendor_background',
                'analysis_results',
                'analysis_reviews',
                'learned_patterns'
            ]

            print("\nChecking for common tables:")
            for table_name in common_tables:
                try:
                    supabase.table(table_name).select('id', count='exact').limit(0).execute()
                    print(f"   ✅ {table_name}")
                except:
                    print(f"   ❌ {table_name}")

        except Exception as e:
            print(f"   Could not list tables: {str(e)}")

        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        print("\nMake sure:")
        print("  1. SUPABASE_URL is set in .env")
        print("  2. SUPABASE_SERVICE_ROLE_KEY is set in .env")
        print("  3. Database is accessible")
        sys.exit(1)


if __name__ == '__main__':
    main()
