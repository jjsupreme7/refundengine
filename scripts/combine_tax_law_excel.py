#!/usr/bin/env python3
"""
Combine all individual year Excel files into one master Excel file

Reads WA_Tax_Law_2010.xlsx through WA_Tax_Law_2025.xlsx and combines
them into a single WA_Tax_Decisions_Complete.xlsx file sorted by year.
"""

import pandas as pd
from pathlib import Path


def combine_excel_files():
    """Combine all year Excel files into one master file"""

    output_dir = Path("outputs")

    # Years to combine
    years = range(2010, 2026)  # 2010-2025

    all_data = []
    total_docs = 0

    print("=" * 70)
    print("Combining Tax Decision Excel Files")
    print("=" * 70)

    for year in years:
        excel_file = output_dir / f"WA_Tax_Law_{year}.xlsx"

        if not excel_file.exists():
            print(f"⚠️  Skipping {year}: File not found")
            continue

        try:
            df = pd.read_excel(excel_file, sheet_name="Metadata")
            count = len(df)
            total_docs += count
            all_data.append(df)
            print(f"✅ {year}: {count} documents")
        except Exception as e:
            print(f"❌ Error reading {year}: {e}")

    if not all_data:
        print("\n❌ No data found to combine!")
        return

    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)

    # Sort by File_Path (newest first - files are named with year in path)
    if 'File_Path' in combined_df.columns:
        combined_df = combined_df.sort_values('File_Path', ascending=False)
    elif 'effective_date' in combined_df.columns:
        combined_df = combined_df.sort_values('effective_date', ascending=False)

    # Save to master Excel file
    master_file = output_dir / "WA_Tax_Decisions_Complete.xlsx"

    with pd.ExcelWriter(master_file, engine='openpyxl') as writer:
        combined_df.to_excel(writer, sheet_name="Metadata", index=False)

    print("\n" + "=" * 70)
    print("✅ Master Excel File Created!")
    print("=" * 70)
    print(f"📁 File: {master_file}")
    print(f"📊 Total documents: {total_docs}")
    print(f"📅 Years: 2010-2025")
    print("\n📋 Next steps:")
    print("  1. Open outputs/WA_Tax_Decisions_Complete.xlsx")
    print("  2. Review AI suggestions in each row")
    print("  3. Edit any fields you want to change")
    print("  4. Update 'Status' column:")
    print("     - 'Approved' = Ready to ingest")
    print("     - 'Skip' = Don't ingest this document")
    print("  5. Save the Excel file")
    print("  6. Run: python core/ingest_documents.py --import-metadata outputs/WA_Tax_Decisions_Complete.xlsx")
    print("=" * 70)


if __name__ == "__main__":
    combine_excel_files()
