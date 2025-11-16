#!/usr/bin/env python3
"""
Test script for Excel versioning and change tracking
"""
import os
import sys
import pandas as pd
from pathlib import Path
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.excel_versioning import ExcelVersionManager

def test_excel_versioning():
    """Test the complete Excel versioning workflow"""

    print("=" * 80)
    print("EXCEL VERSIONING TEST")
    print("=" * 80)

    # Initialize manager
    manager = ExcelVersionManager()

    # Test file paths - use timestamp to ensure uniqueness
    import time
    timestamp = int(time.time())
    original_file = "test_data/Refund_Claim_Sheet_Test.xlsx"
    test_file_v1 = f"/tmp/test_excel_v1_{timestamp}.xlsx"
    test_file_v2 = f"/tmp/test_excel_v2_{timestamp}.xlsx"

    # Step 1: Create initial test file
    print("\n[1] Creating initial test file...")
    shutil.copy(original_file, test_file_v1)
    df = pd.read_excel(test_file_v1)
    print(f"✓ Initial file created with {len(df)} rows")

    # Step 2: Upload initial version
    print("\n[2] Uploading initial version...")
    try:
        file_id = manager.upload_file(
            file_path=test_file_v1,
            project_id=None,  # Use None for testing
            user_email="test@example.com"
        )
        print(f"✓ Initial upload successful - File ID: {file_id}")
    except Exception as e:
        print(f"✗ Initial upload failed: {e}")
        return False

    # Step 3: Make changes to the file
    print("\n[3] Making changes to Excel file...")
    df = pd.read_excel(test_file_v1)

    # Make specific changes
    changes_made = []

    # Change 1: Modify a vendor name
    if len(df) > 0:
        old_vendor = df.loc[0, 'Vendor_Name']
        df.loc[0, 'Vendor_Name'] = "MODIFIED_VENDOR_NAME"
        changes_made.append(f"Row 0, Vendor_Name: '{old_vendor}' → 'MODIFIED_VENDOR_NAME'")

    # Change 2: Modify an amount
    if len(df) > 1:
        old_amount = df.loc[1, 'Line_Item_Amount']
        df.loc[1, 'Line_Item_Amount'] = 99999
        changes_made.append(f"Row 1, Line_Item_Amount: {old_amount} → 99999")

    # Change 3: Add a new row
    new_row = df.iloc[-1].copy()
    new_row['Vendor_Name'] = "NEW_TEST_VENDOR"
    new_row['Invoice_Number'] = "TEST-999"
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    changes_made.append(f"Added new row with Vendor_Name='NEW_TEST_VENDOR'")

    # Save modified file
    df.to_excel(test_file_v2, index=False)
    print(f"✓ Made {len(changes_made)} changes:")
    for change in changes_made:
        print(f"  - {change}")

    # Step 4: Upload modified version
    print("\n[4] Uploading modified version...")
    try:
        version_id = manager.create_version(
            file_id=file_id,
            file_path=test_file_v2,
            user_email="test@example.com",
            change_summary="Test changes for verification"
        )
        print(f"✓ Version upload successful - Version ID: {version_id}")
    except Exception as e:
        print(f"✗ Version upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Verify changes were detected
    print("\n[5] Verifying change detection...")
    try:
        # Get version record
        version_record = manager.supabase.table('excel_file_versions')\
            .select('*')\
            .eq('id', version_id)\
            .single()\
            .execute()

        version_data = version_record.data
        print(f"✓ Version record found:")
        print(f"  - Rows Modified: {version_data.get('rows_modified', 0)}")
        print(f"  - Rows Added: {version_data.get('rows_added', 0)}")
        print(f"  - Rows Deleted: {version_data.get('rows_deleted', 0)}")

        # Get cell changes
        cell_changes = manager.supabase.table('excel_cell_changes')\
            .select('*')\
            .eq('version_id', version_id)\
            .execute()

        changes = cell_changes.data
        print(f"\n✓ Found {len(changes)} cell-level changes:")

        if len(changes) == 0:
            print("✗ ERROR: No cell changes detected! This is the problem.")
            return False

        for i, change in enumerate(changes[:10], 1):  # Show first 10
            print(f"  {i}. Row {change['row_index']}, {change['column_name']}: "
                  f"'{change['old_value']}' → '{change['new_value']}'")

        if len(changes) > 10:
            print(f"  ... and {len(changes) - 10} more changes")

        # Verify expected changes are present
        vendor_change_found = any(
            c['column_name'] == 'Vendor_Name' and
            c['new_value'] == 'MODIFIED_VENDOR_NAME'
            for c in changes
        )

        amount_change_found = any(
            c['column_name'] == 'Line_Item_Amount' and
            c['new_value'] == '99999'
            for c in changes
        )

        print(f"\n[6] Verification Results:")
        print(f"  ✓ Vendor name change detected: {vendor_change_found}")
        print(f"  ✓ Amount change detected: {amount_change_found}")
        print(f"  ✓ Total cell changes: {len(changes)}")
        print(f"  ✓ Rows modified: {version_data.get('rows_modified', 0)}")

        if vendor_change_found and amount_change_found and len(changes) > 0:
            print("\n" + "=" * 80)
            print("✓ ALL TESTS PASSED - Change tracking is working correctly!")
            print("=" * 80)
            return True
        else:
            print("\n" + "=" * 80)
            print("✗ TEST FAILED - Some changes were not detected")
            print("=" * 80)
            return False

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n[Cleanup] Removing test files...")
        for f in [test_file_v1, test_file_v2]:
            if os.path.exists(f):
                os.remove(f)
        print("✓ Cleanup complete")

if __name__ == "__main__":
    success = test_excel_versioning()
    sys.exit(0 if success else 1)
