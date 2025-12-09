#!/usr/bin/env python3
"""
Excel File Watcher and Update Detector

Monitors Excel claim sheet files for changes and triggers incremental processing:
- Tracks file modification timestamps
- Computes row-level hashes to detect changes
- Processes only new or modified rows
- Stores processing state in database

Database Schema Required:
- excel_file_tracking table (file-level metadata)
- excel_row_tracking table (row-level hashes)
"""

from core.database import get_supabase_client
from dotenv import load_dotenv
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Load environment
load_dotenv()

# Initialize Supabase client
supabase = get_supabase_client()


class ExcelFileWatcher:
    """
    Monitors Excel claim sheets for changes and triggers incremental processing
    """

    def __init__(self):
        self.supabase = supabase

    def get_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of entire file for quick change detection
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    # Output columns added by analysis - exclude from hash
    OUTPUT_COLUMNS = {
        'Product_Desc', 'Product_Type', 'Refund_Basis', 'Citation',
        'Confidence', 'Estimated_Refund', 'Explanation',
        # Standard names from excel_column_definitions
        'Analysis_Notes', 'Final_Decision', 'Tax_Category', 'Additional_Info',
        'Legal_Citation', 'AI_Confidence', 'AI_Reasoning',
        'Anomalies_Detected', 'Patterns_Applied',
        # Human review flags
        'Needs_Review', 'Follow_Up_Questions'
    }

    def get_row_hash(self, row: pd.Series) -> str:
        """
        Compute hash of a single row to detect row-level changes.
        Only hashes INPUT columns - excludes OUTPUT columns so that
        analysis results don't trigger re-analysis.
        """
        # Filter to only input columns (exclude output columns)
        input_values = [
            str(v) for k, v in row.items()
            if k not in self.OUTPUT_COLUMNS
        ]
        row_str = "|".join(input_values)
        return hashlib.md5(row_str.encode()).hexdigest()

    def is_file_modified(self, file_path: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if file has been modified since last processing

        Returns:
            (is_modified, previous_record)
        """
        # Get file modification time
        file_stat = os.stat(file_path)
        current_mtime = datetime.fromtimestamp(file_stat.st_mtime)
        current_hash = self.get_file_hash(file_path)

        # Query database for previous tracking record
        result = (
            self.supabase.table("excel_file_tracking")
            .select("*")
            .eq("file_path", file_path)
            .limit(1)
            .execute()
        )

        if not result.data or len(result.data) == 0:
            # File not yet tracked
            return True, None

        previous = result.data[0]

        # Compare hashes
        if previous.get("file_hash") != current_hash:
            return True, previous

        return False, previous

    def get_changed_rows(
        self, file_path: str, df: pd.DataFrame
    ) -> List[Tuple[int, str, bool]]:
        """
        Identify which rows have been added or modified

        Returns:
            List of (row_index, row_hash, is_new)
        """
        changed_rows = []

        # Get previous row hashes from database
        result = (
            self.supabase.table("excel_row_tracking")
            .select("row_index, row_hash")
            .eq("file_path", file_path)
            .execute()
        )

        # Build lookup dict of previous hashes
        previous_hashes = {}
        if result.data:
            for row in result.data:
                previous_hashes[row["row_index"]] = row["row_hash"]

        # Check each current row
        for idx, row in df.iterrows():
            current_hash = self.get_row_hash(row)
            previous_hash = previous_hashes.get(idx)

            if previous_hash is None:
                # New row
                changed_rows.append((idx, current_hash, True))
            elif previous_hash != current_hash:
                # Modified row
                changed_rows.append((idx, current_hash, False))

        return changed_rows

    def update_file_tracking(self, file_path: str, row_count: int):
        """
        Update file-level tracking record in database
        """
        file_stat = os.stat(file_path)
        file_hash = self.get_file_hash(file_path)

        data = {
            "file_path": file_path,
            "file_hash": file_hash,
            "last_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "last_processed": datetime.now().isoformat(),
            "row_count": row_count,
            "processing_status": "completed",
        }

        # Upsert (insert or update)
        result = (
            self.supabase.table("excel_file_tracking")
            .upsert(data, on_conflict="file_path")
            .execute()
        )

        return result

    def update_row_tracking(self, file_path: str, row_index: int, row_hash: str):
        """
        Update row-level tracking record in database
        """
        data = {
            "file_path": file_path,
            "row_index": row_index,
            "row_hash": row_hash,
            "last_processed": datetime.now().isoformat(),
            "processing_status": "completed",
        }

        # Upsert
        result = (
            self.supabase.table("excel_row_tracking")
            .upsert(data, on_conflict="file_path,row_index")
            .execute()
        )

        return result

    def process_excel_file(self, file_path: str, processor_callback=None) -> Dict:
        """
        Main workflow: Check for changes and process incrementally

        Args:
            file_path: Path to Excel claim sheet
            processor_callback: Function to call for each changed row
                               Signature: processor_callback(row_index, row_data) -> bool

        Returns:
            Dictionary with processing summary
        """
        print(f"\n{'=' * 70}")
        print("EXCEL FILE CHANGE DETECTION")
        print(f"{'=' * 70}")
        print(f"File: {file_path}")
        print()

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return {"status": "error", "message": "File not found"}

        # Check if file has been modified
        is_modified, previous = self.is_file_modified(file_path)

        if not is_modified and previous:
            print("✅ No changes detected since last processing")
            print(f"   Last processed: {previous.get('last_processed')}")
            return {
                "status": "no_changes",
                "last_processed": previous.get("last_processed"),
            }

        print("🔄 Changes detected, analyzing rows...")

        # Load Excel file
        try:
            df = pd.read_excel(file_path, sheet_name=0)  # First sheet
        except Exception as e:
            print(f"❌ Error loading Excel file: {e}")
            return {"status": "error", "message": str(e)}

        print(f"   Total rows in file: {len(df)}")

        # Get changed rows
        changed_rows = self.get_changed_rows(file_path, df)

        if len(changed_rows) == 0:
            print("✅ No row-level changes detected")
            self.update_file_tracking(file_path, len(df))
            return {
                "status": "no_row_changes",
                "total_rows": len(df),
            }

        print(f"   Changed rows: {len(changed_rows)}")
        print()

        # Process each changed row
        processed_count = 0
        error_count = 0

        for row_idx, row_hash, is_new in changed_rows:
            row_data = df.iloc[row_idx]

            status = "new" if is_new else "modified"
            print(
                f"   [{processed_count +
                       1}/{len(changed_rows)}] Row {row_idx} ({status})"
            )

            # Call processor callback if provided
            if processor_callback:
                try:
                    success = processor_callback(row_idx, row_data)
                    if success:
                        # Update row tracking on success
                        self.update_row_tracking(file_path, row_idx, row_hash)
                        processed_count += 1
                        print("      ✅ Processed successfully")
                    else:
                        error_count += 1
                        print("      ❌ Processing failed")
                except Exception as e:
                    error_count += 1
                    print(f"      ❌ Error: {e}")
            else:
                # No callback, just track the row
                self.update_row_tracking(file_path, row_idx, row_hash)
                processed_count += 1

        # Update file tracking
        self.update_file_tracking(file_path, len(df))

        print()
        print(f"{'=' * 70}")
        print("✅ PROCESSING COMPLETE")
        print(f"{'=' * 70}")
        print(f"Total rows in file: {len(df)}")
        print(f"Changed rows: {len(changed_rows)}")
        print(f"Successfully processed: {processed_count}")
        print(f"Errors: {error_count}")
        print()

        return {
            "status": "completed",
            "total_rows": len(df),
            "changed_rows": len(changed_rows),
            "processed": processed_count,
            "errors": error_count,
        }

    def watch_directory(
        self, directory: str, pattern: str = "*.xlsx", processor_callback=None
    ):
        """
        Watch a directory for Excel files matching pattern

        Args:
            directory: Directory to watch
            pattern: File pattern (e.g., "*.xlsx", "Refund_Claim_*.xlsx")
            processor_callback: Function to call for each changed row
        """
        print(f"\n{'=' * 70}")
        print("WATCHING DIRECTORY FOR EXCEL FILES")
        print(f"{'=' * 70}")
        print(f"Directory: {directory}")
        print(f"Pattern: {pattern}")
        print()

        import glob  # noqa: E402
        from pathlib import Path  # noqa: E402

        # Find matching files
        search_path = Path(directory) / pattern
        files = glob.glob(str(search_path))

        if not files:
            print(f"⚠️  No files found matching pattern: {pattern}")
            return

        print(f"Found {len(files)} file(s):")
        for f in files:
            print(f"  • {Path(f).name}")
        print()

        # Process each file
        results = []
        for file_path in files:
            result = self.process_excel_file(file_path, processor_callback)
            results.append(
                {
                    "file": Path(file_path).name,
                    "result": result,
                }
            )

        return results


# Example processor callback
def example_processor(row_index: int, row_data: pd.Series) -> bool:
    """
    Example processor function - replace with actual refund analysis logic

    Args:
        row_index: Index of the row in the DataFrame
        row_data: pandas Series containing row data

    Returns:
        True if processing succeeded, False otherwise
    """
    # Extract key fields
    vendor_name = row_data.get("Vendor_Name")
    invoice_number = row_data.get("Invoice_Number")
    amount = row_data.get("Line_Item_Amount")

    print(f"      Processing: {vendor_name} | {invoice_number} | ${amount:,.2f}")

    # TODO: Call refund analysis engine here
    # - Extract invoice text
    # - Query tax law knowledge base
    # - Determine refund eligibility
    # - Update Excel with results

    # For now, just return True
    return True


def main():
    """
    Main entry point for testing
    """
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(
        description="Excel file change detection and processing"
    )
    parser.add_argument("--file", help="Single Excel file to process")
    parser.add_argument("--watch", help="Directory to watch for Excel files")
    parser.add_argument(
        "--pattern", default="*.xlsx", help="File pattern to match (default: *.xlsx)"
    )

    args = parser.parse_args()

    watcher = ExcelFileWatcher()

    if args.file:
        # Process single file
        result = watcher.process_excel_file(
            args.file, processor_callback=example_processor
        )
    elif args.watch:
        # Watch directory
        results = watcher.watch_directory(
            args.watch, args.pattern, processor_callback=example_processor
        )
    else:
        # Show usage
        parser.print_help()


if __name__ == "__main__":
    main()
