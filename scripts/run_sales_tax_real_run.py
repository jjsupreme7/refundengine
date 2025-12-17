#!/usr/bin/env python3
"""
Run Sales Tax Analysis on "Real Run" sheet from Final 2024 workbook.

This script:
1. Loads the XLSB file with "Real Run" sheet
2. Applies filters (Paid=PAID, blank Recon Analysis, has invoice)
3. Optionally splits by quadrant
4. Runs analysis using fast_batch_analyzer

Usage:
    # Analyze all filtered rows
    python scripts/run_sales_tax_real_run.py

    # Analyze only "In WA" rows
    python scripts/run_sales_tax_real_run.py --quadrant "In WA"

    # Analyze only "NOT in WA" rows
    python scripts/run_sales_tax_real_run.py --quadrant "NOT in WA"

    # Test with first 50 rows
    python scripts/run_sales_tax_real_run.py --limit 50
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from analysis.xlsb_processor import (
    load_xlsb,
    filter_real_run_rows,
    extract_real_run_data,
    RealRunColumns,
)

# Paths
DATA_FOLDER = Path.home() / "Desktop" / "Files-Refund-Engine"
SALES_TAX_FILE = DATA_FOLDER / "Copy of Final 2024 Denodo Review_MWR VENDOR REVIEW FOR KEY OPPS.xlsb"
SHEET_NAME = "Real Run"


def prepare_for_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare Real Run data for fast_batch_analyzer.

    Maps column names to the standard names expected by the analyzer.
    """
    # Extract the key columns into a standardized format
    extracted = extract_real_run_data(df)

    # Create output DataFrame with column names the analyzer expects
    result = pd.DataFrame()

    # Map to standard column names
    result["Vendor"] = extracted["vendor_name"]
    result["name1_po_vendor_name"] = extracted["vendor_name"]
    result["Inv 1 File Name"] = extracted["invoice_1"]
    result["Inv 2 File Name"] = extracted["invoice_2"]
    result["Invoice Folder Path"] = extracted["inv_file_path"]
    result["hwste_tax_amount_lc"] = extracted["tax_amount"]
    result["hwbas_tax_base_lc"] = extracted["tax_base"]
    result["rate"] = extracted["rate"]
    result["txz01_po_description"] = extracted["description"]
    result["tax_jurisdiction_state"] = extracted["jurisdiction_state"]
    result["quadrant"] = extracted["quadrant"]

    # Keep original index
    result.index = df.index

    return result


def run_analysis(
    quadrant_filter: str = None,
    limit: int = None,
    output_suffix: str = "",
):
    """Run the sales tax analysis."""
    print(f"\n{'='*70}")
    print("SALES TAX ANALYSIS - REAL RUN SHEET")
    print(f"{'='*70}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load the XLSB file
    print(f"\nLoading {SALES_TAX_FILE.name}...")
    print(f"   Sheet: {SHEET_NAME}")

    if not SALES_TAX_FILE.exists():
        print(f"ERROR: File not found: {SALES_TAX_FILE}")
        sys.exit(1)

    df = load_xlsb(str(SALES_TAX_FILE), sheet_name=SHEET_NAME)
    print(f"   Loaded {len(df):,} total rows")

    # Apply filters
    print(f"\nApplying filters...")
    filtered_df = filter_real_run_rows(df, quadrant_value=quadrant_filter)

    if quadrant_filter:
        print(f"   Quadrant filter: '{quadrant_filter}'")

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

    # Save to temporary XLSX for fast_batch_analyzer (include quadrant in name to avoid race conditions)
    quadrant_slug = quadrant_filter.replace(" ", "_").replace(",", "") if quadrant_filter else "all"
    temp_file = DATA_FOLDER / f"_temp_real_run_analysis_{quadrant_slug}.xlsx"
    analysis_df.to_excel(temp_file, index=False)
    print(f"   Saved to: {temp_file.name}")

    # Determine output file name
    if quadrant_filter:
        quadrant_slug = quadrant_filter.replace(" ", "_").replace(",", "")
        output_file = DATA_FOLDER / f"SalesTax_RealRun_{quadrant_slug} - Analyzed.xlsx"
    else:
        output_file = DATA_FOLDER / "SalesTax_RealRun_All - Analyzed.xlsx"

    # Run fast_batch_analyzer
    print(f"\nRunning fast_batch_analyzer...")
    print(f"   Output: {output_file.name}")

    import subprocess
    cmd = [
        sys.executable,
        str(Path(__file__).parent.parent / "analysis" / "fast_batch_analyzer.py"),
        "--excel", str(temp_file),
        "--state", "washington",
        "--tax-type", "sales_tax",
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
        description="Run Sales Tax Analysis on Real Run sheet"
    )
    parser.add_argument(
        "--quadrant",
        choices=["In WA", "NOT in WA"],
        help="Filter by quadrant value (default: analyze all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit to first N rows (for testing)",
    )

    args = parser.parse_args()

    return run_analysis(
        quadrant_filter=args.quadrant,
        limit=args.limit,
    )


if __name__ == "__main__":
    sys.exit(main())
