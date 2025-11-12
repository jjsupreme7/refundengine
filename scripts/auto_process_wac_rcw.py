#!/usr/bin/env python3
"""
Auto-process WAC and RCW documents after downloads complete

Monitors download completion, then automatically runs AI analysis
and generates Excel files for user review.
"""

import os
import subprocess
import time
from pathlib import Path


def check_downloads_complete():
    """Check if WAC and RCW downloads are complete"""
    wac_dir = Path("knowledge_base/wa_tax_law/wac/title_458/chapter_458_20")
    rcw_82_04_dir = Path("knowledge_base/wa_tax_law/rcw/title_82/chapter_82_04")
    rcw_82_08_dir = Path("knowledge_base/wa_tax_law/rcw/title_82/chapter_82_08")
    rcw_82_12_dir = Path("knowledge_base/wa_tax_law/rcw/title_82/chapter_82_12")
    rcw_82_14_dir = Path("knowledge_base/wa_tax_law/rcw/title_82/chapter_82_14")
    rcw_82_32_dir = Path("knowledge_base/wa_tax_law/rcw/title_82/chapter_82_32")

    # Check if directories exist and have files
    # Updated to actual download counts (not estimates)
    wac_complete = wac_dir.exists() and len(list(wac_dir.glob("*.html"))) >= 191
    rcw_04_complete = rcw_82_04_dir.exists() and len(list(rcw_82_04_dir.glob("*.html"))) >= 687
    rcw_08_complete = rcw_82_08_dir.exists() and len(list(rcw_82_08_dir.glob("*.html"))) >= 177
    rcw_12_complete = rcw_82_12_dir.exists() and len(list(rcw_82_12_dir.glob("*.html"))) >= 147
    rcw_14_complete = rcw_82_14_dir.exists() and len(list(rcw_82_14_dir.glob("*.html"))) >= 184
    rcw_32_complete = rcw_82_32_dir.exists() and len(list(rcw_82_32_dir.glob("*.html"))) >= 357

    return {
        'wac': wac_complete,
        'rcw_82_04': rcw_04_complete,
        'rcw_82_08': rcw_08_complete,
        'rcw_82_12': rcw_12_complete,
        'rcw_82_14': rcw_14_complete,
        'rcw_82_32': rcw_32_complete,
        'all_complete': all([wac_complete, rcw_04_complete, rcw_08_complete, rcw_12_complete, rcw_14_complete, rcw_32_complete])
    }


def run_ai_analysis(folder, output_file):
    """Run AI analysis on a folder and export to Excel"""
    print(f"\n{'='*70}")
    print(f"Running AI analysis: {folder}")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")

    cmd = [
        "python", "core/ingest_documents.py",
        "--type", "tax_law",
        "--folder", folder,
        "--export-metadata", output_file
    ]

    subprocess.run(cmd)


def combine_all_excel_files():
    """Combine all tax law Excel files into master files"""
    print(f"\n{'='*70}")
    print("Combining all Excel files into master files")
    print(f"{'='*70}\n")

    # Combine tax decisions (already done, but regenerate to be safe)
    subprocess.run(["python", "scripts/combine_tax_law_excel.py"])

    # Create WAC master file
    subprocess.run([
        "python", "-c",
        """
import pandas as pd
from pathlib import Path

output_dir = Path("outputs")
wac_file = output_dir / "WA_Tax_Law_WAC_458-20.xlsx"

if wac_file.exists():
    df = pd.read_excel(wac_file, sheet_name="Metadata")
    print(f"WAC 458-20: {len(df)} sections")
"""
    ])

    # Create RCW master file
    subprocess.run([
        "python", "-c",
        """
import pandas as pd
from pathlib import Path

output_dir = Path("outputs")
files = [
    "WA_Tax_Law_RCW_82-04.xlsx",
    "WA_Tax_Law_RCW_82-08.xlsx",
    "WA_Tax_Law_RCW_82-12.xlsx",
    "WA_Tax_Law_RCW_82-14.xlsx",
    "WA_Tax_Law_RCW_82-32.xlsx"
]

all_data = []
for f in files:
    file_path = output_dir / f
    if file_path.exists():
        df = pd.read_excel(file_path, sheet_name="Metadata")
        all_data.append(df)
        print(f"{f}: {len(df)} sections")

if all_data:
    combined = pd.concat(all_data, ignore_index=True)
    output_file = output_dir / "WA_Tax_Law_RCW_Complete.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        combined.to_excel(writer, sheet_name="Metadata", index=False)
    print(f"\\nCombined RCW file: {output_file}")
    print(f"Total RCW sections: {len(combined)}")
"""
    ])


def main():
    """Main monitoring and processing loop"""
    print("="*70)
    print("WAC/RCW Download Monitor & Auto-Processor")
    print("="*70)
    print("\nMonitoring downloads...")
    print("- WAC Chapter 458-20: 191 sections")
    print("- RCW Chapter 82.04: 687 sections (B&O tax)")
    print("- RCW Chapter 82.08: 177 sections (Retail sales tax)")
    print("- RCW Chapter 82.12: 147 sections (Use tax)")
    print("- RCW Chapter 82.14: 184 sections (Local taxes)")
    print("- RCW Chapter 82.32: 357 sections (Administrative provisions)")
    print("\nAI analysis will start automatically when downloads complete.")
    print("Estimated cost: ~$1.50 (GPT-4o-mini)")
    print("="*70)

    processed = {
        'wac': False,
        'rcw_82_04': False,
        'rcw_82_08': False,
        'rcw_82_12': False,
        'rcw_82_14': False,
        'rcw_82_32': False
    }

    check_interval = 300  # Check every 5 minutes

    while True:
        status = check_downloads_complete()

        # Process WAC if complete and not yet processed
        if status['wac'] and not processed['wac']:
            print("\n✅ WAC Chapter 458-20 download complete!")
            run_ai_analysis(
                "knowledge_base/wa_tax_law/wac/title_458/chapter_458_20",
                "outputs/WA_Tax_Law_WAC_458-20.xlsx"
            )
            processed['wac'] = True

        # Process RCW 82.08 if complete and not yet processed
        if status['rcw_82_08'] and not processed['rcw_82_08']:
            print("\n✅ RCW Chapter 82.08 download complete!")
            run_ai_analysis(
                "knowledge_base/wa_tax_law/rcw/title_82/chapter_82_08",
                "outputs/WA_Tax_Law_RCW_82-08.xlsx"
            )
            processed['rcw_82_08'] = True

        # Process RCW 82.12 if complete and not yet processed
        if status['rcw_82_12'] and not processed['rcw_82_12']:
            print("\n✅ RCW Chapter 82.12 download complete!")
            run_ai_analysis(
                "knowledge_base/wa_tax_law/rcw/title_82/chapter_82_12",
                "outputs/WA_Tax_Law_RCW_82-12.xlsx"
            )
            processed['rcw_82_12'] = True

        # Process RCW 82.04 if complete and not yet processed
        if status['rcw_82_04'] and not processed['rcw_82_04']:
            print("\n✅ RCW Chapter 82.04 download complete!")
            run_ai_analysis(
                "knowledge_base/wa_tax_law/rcw/title_82/chapter_82_04",
                "outputs/WA_Tax_Law_RCW_82-04.xlsx"
            )
            processed['rcw_82_04'] = True

        # Process RCW 82.14 if complete and not yet processed
        if status['rcw_82_14'] and not processed['rcw_82_14']:
            print("\n✅ RCW Chapter 82.14 download complete!")
            run_ai_analysis(
                "knowledge_base/wa_tax_law/rcw/title_82/chapter_82_14",
                "outputs/WA_Tax_Law_RCW_82-14.xlsx"
            )
            processed['rcw_82_14'] = True

        # Process RCW 82.32 if complete and not yet processed
        if status['rcw_82_32'] and not processed['rcw_82_32']:
            print("\n✅ RCW Chapter 82.32 download complete!")
            run_ai_analysis(
                "knowledge_base/wa_tax_law/rcw/title_82/chapter_82_32",
                "outputs/WA_Tax_Law_RCW_82-32.xlsx"
            )
            processed['rcw_82_32'] = True

        # If everything is complete, combine and exit
        if all(processed.values()):
            print("\n✅ All downloads and AI analysis complete!")
            combine_all_excel_files()

            print("\n" + "="*70)
            print("🎉 COMPLETE! All documents processed.")
            print("="*70)
            print("\n📋 Review these Excel files:")
            print("  1. outputs/WA_Tax_Decisions_Complete.xlsx (755 tax decisions)")
            print("  2. outputs/WA_Tax_Law_WAC_458-20.xlsx (191 WAC sections)")
            print("  3. outputs/WA_Tax_Law_RCW_Complete.xlsx (1,552 RCW sections)")
            print("     - RCW 82.04: 687 sections (B&O tax)")
            print("     - RCW 82.08: 177 sections (Retail sales tax)")
            print("     - RCW 82.12: 147 sections (Use tax)")
            print("     - RCW 82.14: 184 sections (Local taxes)")
            print("     - RCW 82.32: 357 sections (Administrative provisions)")
            print("\n📊 Total: 2,498 legal documents ready for review!")
            print("="*70)
            break

        # Sleep and check again
        incomplete = [k for k, v in status.items() if k != 'all_complete' and not v]
        if incomplete:
            print(f"\n⏳ Still downloading: {', '.join(incomplete)}")
            print(f"   Checking again in {check_interval//60} minutes...")
            time.sleep(check_interval)


if __name__ == "__main__":
    main()
