#!/usr/bin/env python3
"""
Run Use Tax Analysis on Phase 3 Use Tax files.

This script:
1. Loads the Phase 3 Use Tax Excel file
2. Applies filters (INDICATOR=Remit, blank KOM Analysis & Notes)
3. Runs analysis using fast_batch_analyzer

Usage:
    # Analyze 2024 Use Tax
    python scripts/run_use_tax_phase3.py --year 2024

    # Analyze 2023 Use Tax
    python scripts/run_use_tax_phase3.py --year 2023

    # Test with first 50 rows
    python scripts/run_use_tax_phase3.py --year 2024 --limit 50
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

# Paths
DATA_FOLDER = Path.home() / "Desktop" / "Files-Refund-Engine"
USE_TAX_FILES = {
    2021: DATA_FOLDER / "Phase_3_2021_Use Tax_10-17-25.xlsx",
    2022: DATA_FOLDER / "Phase_3_2022_UseTax_10-17-25.xlsx",
    2023: DATA_FOLDER / "Phase_3_2023_Use Tax_10-17-25.xlsx",
    2024: DATA_FOLDER / "Phase_3_2024_Use Tax_10-17-25.xlsx",
}


# Column mappings for Phase 3 Use Tax format
class UseTaxPhase3Columns:
    """Column names for Phase 3 Use Tax files."""
    # Filter columns
    INDICATOR = "INDICATOR"           # Column AD - "Remit" vs "Do Not Remit"
    KOM_ANALYSIS = "KOM Analysis & Notes"  # Column W - filter on blank

    # Key data columns
    VENDOR_NAME = "Vendor Name"       # Column B
    TAX_REMIT = "Tax Remit"           # Column K - Tax amount
    TAX_RATE = "Tax Rate Charged"     # Column L
    TOTAL_TAX = "Total Tax"           # Column G - Backup tax amount
    STATE = "STATE"                   # Column H
    INV_1 = "Inv-1PDF"                # Column N - Invoice filename 1
    INV_2 = "Inv-2 PDF"               # Column O - Invoice filename 2
    INV_FILE_PATH = "Inv File Path"   # Column S - Path to invoices


def filter_use_tax_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter Use Tax rows based on criteria.

    Filters:
    - INDICATOR = "Remit" (exact match, not "Do Not Remit")
    - KOM Analysis & Notes = empty (not yet analyzed)
    """
    cols = UseTaxPhase3Columns

    # Check if required columns exist
    if cols.INDICATOR not in df.columns:
        print(f"Warning: Column '{cols.INDICATOR}' not found")
        return df

    # Filter: INDICATOR = "Remit" (exact match)
    indicator_mask = df[cols.INDICATOR].astype(str).str.strip() == "Remit"

    # Filter: KOM Analysis is empty
    if cols.KOM_ANALYSIS in df.columns:
        empty_mask = df[cols.KOM_ANALYSIS].isna() | (
            df[cols.KOM_ANALYSIS].astype(str).str.strip() == ""
        )
    else:
        print(f"Warning: Column '{cols.KOM_ANALYSIS}' not found, skipping filter")
        empty_mask = pd.Series([True] * len(df), index=df.index)

    # Combine filters
    combined_mask = indicator_mask & empty_mask

    filtered = df[combined_mask].copy()
    print(f"  Filtered to {len(filtered):,} rows (from {len(df):,})")
    print(f"    INDICATOR=Remit: {indicator_mask.sum():,}")
    print(f"    Blank KOM Analysis: {empty_mask.sum():,}")

    return filtered


def prepare_for_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare Use Tax data for fast_batch_analyzer.

    Maps column names to the standard names expected by the analyzer.
    """
    cols = UseTaxPhase3Columns
    result = pd.DataFrame()

    # Map to standard column names
    result["Vendor"] = df.get(cols.VENDOR_NAME, "")
    result["name1_po_vendor_name"] = df.get(cols.VENDOR_NAME, "")
    result["Inv 1 File Name"] = df.get(cols.INV_1, "")
    result["Inv 2 File Name"] = df.get(cols.INV_2, "")
    result["Invoice Folder Path"] = df.get(cols.INV_FILE_PATH, "")

    # Use Tax Remit as primary tax amount, fall back to Total Tax
    tax_remit = df.get(cols.TAX_REMIT, pd.Series([0] * len(df)))
    total_tax = df.get(cols.TOTAL_TAX, pd.Series([0] * len(df)))
    # Use Tax Remit if available, otherwise Total Tax
    result["Tax Remitted"] = tax_remit.where(tax_remit > 0, total_tax)
    result["hwste_tax_amount_lc"] = result["Tax Remitted"]

    result["tax_jurisdiction_state"] = df.get(cols.STATE, "WA")

    # Keep original index
    result.index = df.index

    return result


def run_analysis(year: int, limit: int = None):
    """Run the use tax analysis for a specific year."""
    print(f"\n{'='*70}")
    print(f"USE TAX ANALYSIS - PHASE 3 {year}")
    print(f"{'='*70}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get file path
    if year not in USE_TAX_FILES:
        print(f"ERROR: Invalid year: {year}. Available: {list(USE_TAX_FILES.keys())}")
        sys.exit(1)

    file_path = USE_TAX_FILES[year]

    # Load the Excel file
    print(f"\nLoading {file_path.name}...")

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    df = pd.read_excel(file_path)
    print(f"   Loaded {len(df):,} total rows")

    # Apply filters
    print(f"\nApplying filters...")
    filtered_df = filter_use_tax_rows(df)

    # Apply limit if specified
    if limit and limit < len(filtered_df):
        filtered_df = filtered_df.head(limit)
        print(f"   Limited to first {limit} rows")

    if len(filtered_df) == 0:
        print("ERROR: No rows match the filter criteria")
        sys.exit(0)

    # Prepare data for analyzer
    print(f"\nPreparing data for analysis...")
    analysis_df = prepare_for_analysis(filtered_df)
    print(f"   {len(analysis_df):,} rows ready for analysis")

    # Save to temporary XLSX for fast_batch_analyzer
    temp_file = DATA_FOLDER / f"_temp_use_tax_{year}_analysis.xlsx"
    analysis_df.to_excel(temp_file, index=False)
    print(f"   Saved to: {temp_file.name}")

    # Determine output file name
    output_file = DATA_FOLDER / f"Phase_3_{year}_Use Tax - Analyzed.xlsx"

    # Run fast_batch_analyzer
    print(f"\nRunning fast_batch_analyzer...")
    print(f"   Output: {output_file.name}")

    import subprocess
    cmd = [
        sys.executable,
        str(Path(__file__).parent.parent / "analysis" / "fast_batch_analyzer.py"),
        "--excel", str(temp_file),
        "--state", "washington",
        "--tax-type", "use_tax",
        "--output", str(output_file),
    ]

    if limit:
        cmd.extend(["--limit", str(limit)])

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))

    # Clean up temp file
    if temp_file.exists():
        temp_file.unlink()
        print(f"\nCleaned up temp file")

    print(f"\n{'='*70}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if output_file.exists():
        print(f"Results saved to: {output_file}")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run Use Tax Analysis on Phase 3 files"
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        choices=[2021, 2022, 2023, 2024],
        help="Year to analyze (2021, 2022, 2023, or 2024)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit to first N rows (for testing)",
    )

    args = parser.parse_args()

    return run_analysis(year=args.year, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
