#!/usr/bin/env python3
"""
Test Excel versioning performance with large files (60K+ rows)
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.excel_versioning import ExcelVersionManager

def create_large_test_file(num_rows=60000):
    """Create a large Excel file for performance testing"""
    print(f"\n[1] Creating large test file with {num_rows:,} rows...")

    # Generate synthetic data
    data = {
        'Vendor_Number': [f'V-{i:05d}' for i in range(num_rows)],
        'Vendor_Name': [f'Vendor_{i}' for i in range(num_rows)],
        'Invoice_Number': [f'INV-2024-{i:06d}' for i in range(num_rows)],
        'Line_Item_Amount': np.random.randint(100, 100000, num_rows),
        'Tax_Remitted': np.random.randint(10, 10000, num_rows),
        'Total_Amount': np.random.randint(110, 110000, num_rows),
        'Product_Description': [f'Product description {i}' for i in range(num_rows)],
        'Expected_Refund_Basis': np.random.choice(['MPU', 'Non-Taxable', 'Out of State'], num_rows),
    }

    df = pd.DataFrame(data)
    return df

def test_large_file_performance():
    """Test performance with large files"""

    print("=" * 80)
    print("LARGE FILE PERFORMANCE TEST (60K rows)")
    print("=" * 80)

    manager = ExcelVersionManager()

    # File paths
    test_file_v1 = "/tmp/large_test_v1.xlsx"
    test_file_v2 = "/tmp/large_test_v2.xlsx"

    try:
        # Create and save v1
        start_time = time.time()
        df_v1 = create_large_test_file(60000)
        df_v1.to_excel(test_file_v1, index=False)
        create_time = time.time() - start_time
        print(f"✓ File created in {create_time:.2f}s")

        # Upload v1
        print(f"\n[2] Uploading version 1 ({len(df_v1):,} rows)...")
        start_time = time.time()
        file_id = manager.upload_file(
            file_path=test_file_v1,
            project_id=None,
            user_email="test@example.com"
        )
        upload_time = time.time() - start_time
        print(f"✓ Upload completed in {upload_time:.2f}s")
        print(f"  File ID: {file_id}")

        # Make changes to 100 rows (realistic scenario)
        print(f"\n[3] Making changes to 100 rows (0.17% of total)...")
        df_v2 = df_v1.copy()

        # Change 100 vendor names
        for i in range(0, 100):
            df_v2.loc[i, 'Vendor_Name'] = f'MODIFIED_Vendor_{i}'

        # Change 100 amounts
        for i in range(100, 200):
            df_v2.loc[i, 'Line_Item_Amount'] = 999999

        df_v2.to_excel(test_file_v2, index=False)
        print(f"✓ Modified 200 cells across 100 rows")

        # Upload v2 (this will trigger change detection)
        print(f"\n[4] Uploading version 2 and detecting changes...")
        print("    This is the performance-critical operation...")

        start_time = time.time()
        version_id = manager.create_version(
            file_id=file_id,
            file_path=test_file_v2,
            user_email="test@example.com",
            change_summary="Performance test with 100 row changes"
        )
        version_time = time.time() - start_time

        print(f"✓ Version created in {version_time:.2f}s")
        print(f"  Version ID: {version_id}")

        # Verify changes detected
        print(f"\n[5] Verifying change detection...")
        version_record = manager.supabase.table('excel_file_versions')\
            .select('*')\
            .eq('id', version_id)\
            .single()\
            .execute()

        cell_changes = manager.supabase.table('excel_cell_changes')\
            .select('*')\
            .eq('version_id', version_id)\
            .execute()

        print(f"✓ Rows Modified: {version_record.data['rows_modified']}")
        print(f"✓ Cell Changes Detected: {len(cell_changes.data)}")

        # Performance summary
        print(f"\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"File size: {len(df_v1):,} rows × {len(df_v1.columns)} columns")
        print(f"Initial upload: {upload_time:.2f}s")
        print(f"Change detection (100 rows): {version_time:.2f}s")
        print(f"Changes detected: {len(cell_changes.data)}")

        if version_time < 30:
            print(f"\n✅ EXCELLENT - System handles 60K rows efficiently!")
        elif version_time < 60:
            print(f"\n⚠️  ACCEPTABLE - Works but may need optimization for frequent uploads")
        else:
            print(f"\n❌ SLOW - Needs optimization for production use")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print(f"\n[Cleanup] Removing test files...")
        for f in [test_file_v1, test_file_v2]:
            if os.path.exists(f):
                os.remove(f)
        print("✓ Cleanup complete")

if __name__ == "__main__":
    success = test_large_file_performance()
    sys.exit(0 if success else 1)
