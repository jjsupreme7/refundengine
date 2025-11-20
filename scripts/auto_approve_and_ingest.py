#!/usr/bin/env python3
"""
Auto-approve all documents in Excel metadata files and ingest to Supabase
"""
import subprocess
import time
from pathlib import Path

import pandas as pd


def auto_approve_excel(excel_path: str):
    """Change all Status values to 'Approved'"""
    print(f"\n📝 Auto-approving all documents in {excel_path}...")

    df = pd.read_excel(excel_path, sheet_name="Metadata")

    # Change all Status to 'Approved'
    df["Status"] = "Approved"

    # Save back to Excel
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Metadata", index=False)

        # Get workbook and worksheet for formatting
        workbook = writer.book
        worksheet = writer.sheets["Metadata"]

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except BaseException:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap at 50
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"✅ Approved {len(df)} documents")
    return len(df)


def wait_for_file(file_path: str, timeout: int = 3600):
    """Wait for a file to exist"""
    print(f"\n⏳ Waiting for {file_path} to be created...")
    start_time = time.time()

    while not Path(file_path).exists():
        if time.time() - start_time > timeout:
            print(f"❌ Timeout waiting for {file_path}")
            return False
        time.sleep(5)

    print(f"✅ Found {file_path}")
    return True


def ingest_excel(excel_path: str):
    """Run the import command"""
    print(f"\n🚀 Ingesting {excel_path} to Supabase...")
    print("=" * 70)

    cmd = [
        "python",
        "core/ingest_documents.py",
        "--import-metadata",
        excel_path,
        "--yes",  # Auto-confirm
        "--force",  # Force all documents regardless of Status
    ]

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        print(f"✅ Successfully ingested {excel_path}")
        return True
    else:
        print(f"❌ Failed to ingest {excel_path}")
        return False


def main():
    excel_files = [
        "outputs/WA_ETAs_Metadata.xlsx",
        "outputs/WA_ESSB_5814_Metadata.xlsx",
        "outputs/WA_Other_Guidance_Metadata.xlsx",
    ]

    print("=" * 70)
    print("AUTO-APPROVE AND INGEST DOCUMENTS TO SUPABASE")
    print("=" * 70)

    # Wait for all files to be created
    for excel_file in excel_files:
        if not wait_for_file(excel_file):
            print(f"❌ Failed to find {excel_file}")
            return

    print("\n✅ All Excel files found!")

    # Auto-approve all documents
    total_docs = 0
    for excel_file in excel_files:
        count = auto_approve_excel(excel_file)
        total_docs += count

    print(f"\n✅ Total documents approved: {total_docs}")
    print("\n" + "=" * 70)
    print("STARTING INGESTION PROCESS")
    print("=" * 70)

    # Ingest each file sequentially
    successful = 0
    failed = 0

    for excel_file in excel_files:
        if ingest_excel(excel_file):
            successful += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully ingested: {successful}/{len(excel_files)} files")
    print(f"❌ Failed: {failed}/{len(excel_files)} files")
    print(f"📊 Total documents processed: {total_docs}")
    print("=" * 70)


if __name__ == "__main__":
    main()
