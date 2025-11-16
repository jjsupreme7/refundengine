#!/usr/bin/env python3
"""
Test Excel Versioning System

This script tests the complete versioning workflow:
1. Upload an Excel file
2. Create a new version
3. Generate diff between versions
4. Test file locking

Usage:
    python scripts/test_excel_versioning.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.excel_versioning import ExcelVersionManager

load_dotenv()


def create_test_excel_file(filename: str, num_rows: int = 10) -> str:
    """Create a test Excel file

    Args:
        filename: Output filename
        num_rows: Number of rows to create

    Returns:
        Path to created file
    """
    test_data = {
        'Vendor': [f'Vendor {i}' for i in range(num_rows)],
        'Invoice_Number': [f'INV-{1000+i}' for i in range(num_rows)],
        'Amount': [1000 + (i * 100) for i in range(num_rows)],
        'Tax': [100 + (i * 10) for i in range(num_rows)],
        'Estimated_Refund': [0 for i in range(num_rows)],
        'Review_Status': ['Pending' for i in range(num_rows)]
    }

    df = pd.DataFrame(test_data)
    output_path = f"/tmp/{filename}"
    df.to_excel(output_path, index=False)

    print(f"✅ Created test file: {output_path}")
    print(f"   - Rows: {len(df)}")
    print(f"   - Columns: {', '.join(df.columns)}")

    return output_path


def modify_test_excel_file(input_path: str, output_path: str) -> str:
    """Modify test Excel file to create a new version

    Args:
        input_path: Path to original file
        output_path: Path for modified file

    Returns:
        Path to modified file
    """
    df = pd.read_excel(input_path)

    # Modify some values
    df.loc[0, 'Estimated_Refund'] = 250  # Update first row
    df.loc[1, 'Estimated_Refund'] = 320  # Update second row
    df.loc[2, 'Review_Status'] = 'Approved'  # Update status

    # Add a new row
    new_row = {
        'Vendor': 'New Vendor',
        'Invoice_Number': 'INV-9999',
        'Amount': 5000,
        'Tax': 500,
        'Estimated_Refund': 425,
        'Review_Status': 'Pending'
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_excel(output_path, index=False)

    print(f"✅ Created modified file: {output_path}")
    print(f"   - Modified 3 cells")
    print(f"   - Added 1 row")

    return output_path


def main():
    """Run comprehensive test of versioning system"""

    print("=" * 70)
    print("🧪 Testing Excel Versioning System")
    print("=" * 70)
    print()

    # Initialize manager
    try:
        manager = ExcelVersionManager()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

    print()

    # Test 1: Upload initial file
    print("📤 Test 1: Upload Initial File")
    print("-" * 70)

    try:
        test_file_v1 = create_test_excel_file("test_refunds_v1.xlsx", num_rows=10)

        # Create a dummy project_id (in real use, this would come from database)
        test_project_id = "test-project-123"
        test_user_email = "test@example.com"

        file_id = manager.upload_file(
            file_path=test_file_v1,
            project_id=test_project_id,
            user_email=test_user_email
        )

        print(f"✅ Test 1 PASSED - File uploaded with ID: {file_id}")
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return

    print()

    # Test 2: Acquire lock
    print("🔒 Test 2: File Locking")
    print("-" * 70)

    try:
        # Acquire lock
        lock_acquired = manager.acquire_lock(file_id, test_user_email)

        if lock_acquired:
            print(f"✅ Lock acquired by {test_user_email}")
        else:
            print(f"❌ Failed to acquire lock")
            return

        # Try to acquire lock with different user (should fail)
        lock_acquired_2 = manager.acquire_lock(file_id, "other@example.com")

        if not lock_acquired_2:
            print(f"✅ Correctly prevented lock by other user")
        else:
            print(f"❌ Lock should have been denied")
            return

        # Release lock
        lock_released = manager.release_lock(file_id, test_user_email)

        if lock_released:
            print(f"✅ Lock released successfully")
        else:
            print(f"❌ Failed to release lock")
            return

        print(f"✅ Test 2 PASSED - File locking works correctly")
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        return

    print()

    # Test 3: Create new version
    print("📝 Test 3: Create New Version")
    print("-" * 70)

    try:
        # Create modified version
        test_file_v2 = modify_test_excel_file(
            test_file_v1,
            "/tmp/test_refunds_v2.xlsx"
        )

        version_id = manager.create_version(
            file_id=file_id,
            file_path=test_file_v2,
            user_email=test_user_email,
            change_summary="Updated 3 refund amounts, added 1 new invoice"
        )

        print(f"✅ Test 3 PASSED - Version created with ID: {version_id}")
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        return

    print()

    # Test 4: Get version history
    print("📚 Test 4: Version History")
    print("-" * 70)

    try:
        versions = manager.get_version_history(file_id)

        print(f"✅ Found {len(versions)} versions:")
        for v in versions:
            print(f"   - Version {v['version_number']}: {v['change_summary']}")
            print(f"     Created by: {v['created_by']} at {v['created_at']}")

        print(f"✅ Test 4 PASSED - Version history retrieved")
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return

    print()

    # Test 5: Generate diff
    print("🔍 Test 5: Generate Version Diff")
    print("-" * 70)

    try:
        critical_columns = ['Estimated_Refund', 'Review_Status']

        diff = manager.get_version_diff(
            file_id=file_id,
            version_1=1,
            version_2=2,
            critical_columns=critical_columns
        )

        print(f"✅ Diff generated successfully:")
        print(f"   - Rows added: {diff['rows_added']}")
        print(f"   - Rows deleted: {diff['rows_deleted']}")
        print(f"   - Rows modified: {diff['rows_modified']}")
        print(f"   - Total cells changed: {len(diff['cells_changed'])}")
        print(f"   - Critical changes: {len(diff['critical_changes'])}")

        if diff['critical_changes']:
            print(f"\n   Critical changes:")
            for change in diff['critical_changes'][:5]:  # Show first 5
                print(f"     - Row {change['row_index']}, {change['column']}: "
                      f"{change['old_value']} → {change['new_value']}")

        print(f"✅ Test 5 PASSED - Diff generation works")
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    print()

    # Test 6: Download version
    print("💾 Test 6: Download Specific Version")
    print("-" * 70)

    try:
        download_path = "/tmp/downloaded_v1.xlsx"

        manager.download_version(
            file_id=file_id,
            version_number=1,
            output_path=download_path
        )

        # Verify file exists and is valid Excel
        df = pd.read_excel(download_path)
        print(f"   - Downloaded file has {len(df)} rows")

        print(f"✅ Test 6 PASSED - Version download works")
    except Exception as e:
        print(f"❌ Test 6 FAILED: {e}")
        return

    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("🎉 Excel Versioning System is working correctly!")
    print()
    print("📋 Test Summary:")
    print("  ✓ File upload and initial version creation")
    print("  ✓ File locking (acquire/release)")
    print("  ✓ Creating new versions")
    print("  ✓ Version history retrieval")
    print("  ✓ Diff generation with critical field tracking")
    print("  ✓ Version download")
    print()
    print("🚀 Ready to integrate with dashboard!")
    print()


if __name__ == "__main__":
    main()
