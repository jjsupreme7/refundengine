#!/usr/bin/env python3
"""
Copy ALL invoices from source Excel files to a local folder.

This script reads the original Excel files and copies all referenced invoices
from the network share to a local destination folder.

Run overnight - this will take several hours for ~71,000 files.

Usage:
    python scripts/copy_all_invoices.py
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Source and destination paths
SOURCE_BASE = Path(r"\\KOMAZSRV02\KOM-Public\T-Mobile\T-Mobile - Tax incentive refunds\Phase 2\Review Invoices")
DEST_BASE = Path.home() / "Desktop" / "Analyzed_Invoices"
DATA_FOLDER = Path.home() / "Desktop" / "Files-Refund-Engine"


def log(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def get_sales_tax_invoices() -> set:
    """Get invoice filenames from Sales Tax 2024 (XLSB file)."""
    f = DATA_FOLDER / "Copy of Final 2024 Denodo Review_MWR VENDOR REVIEW FOR KEY OPPS.xlsb"
    log(f"  Reading {f.name}...")

    df = pd.read_excel(f, sheet_name="Real Run", engine="pyxlsb")
    log(f"  Loaded {len(df):,} rows")

    # Columns J and K (0-indexed: 9 and 10)
    inv1 = df.iloc[:, 9].dropna().astype(str)
    inv2 = df.iloc[:, 10].dropna().astype(str)

    filenames = set()
    for val in inv1:
        val = val.strip()
        if val and val.lower() not in ("nan", "none", ""):
            filenames.add(val)
    for val in inv2:
        val = val.strip()
        if val and val.lower() not in ("nan", "none", ""):
            filenames.add(val)

    log(f"  Found {len(filenames):,} unique invoices")
    return filenames


def get_use_tax_invoices(year: int) -> set:
    """Get invoice filenames from Use Tax files."""
    if year == 2023:
        f = DATA_FOLDER / "Phase_3_2023_Use Tax_10-17-25.xlsx"
    else:
        f = DATA_FOLDER / "Phase_3_2024_Use Tax_10-17-25.xlsx"

    log(f"  Reading {f.name}...")

    df = pd.read_excel(f, sheet_name=0)  # First sheet explicitly
    log(f"  Loaded {len(df):,} rows")

    filenames = set()
    inv_cols = ["Inv-1PDF", "Inv-2 PDF"]

    for col in inv_cols:
        if col in df.columns:
            for val in df[col].dropna().astype(str):
                val = val.strip()
                if val and val.lower() not in ("nan", "none", ""):
                    filenames.add(val)

    log(f"  Found {len(filenames):,} unique invoices")
    return filenames


def find_invoice_file(filename: str, search_paths: list, subdir_cache: dict) -> Path | None:
    """Find an invoice file in the search paths."""
    for base_path in search_paths:
        # Try direct path first
        direct = base_path / filename
        if direct.exists():
            return direct

        # Try cached subdirectories
        if base_path not in subdir_cache:
            try:
                subdir_cache[base_path] = [d for d in base_path.iterdir() if d.is_dir()]
            except Exception:
                subdir_cache[base_path] = []

        for subdir in subdir_cache[base_path]:
            candidate = subdir / filename
            if candidate.exists():
                return candidate

    return None


def copy_files(filenames: set, dest_folder: Path, subdir_cache: dict) -> tuple:
    """Copy invoice files to destination."""
    dest_folder.mkdir(parents=True, exist_ok=True)

    search_paths = [SOURCE_BASE]

    copied = 0
    skipped = 0
    not_found = 0
    errors = 0

    total = len(filenames)

    for i, filename in enumerate(sorted(filenames)):
        # Progress every 1000 files
        if (i + 1) % 1000 == 0:
            log(f"  Progress: {i+1:,}/{total:,} ({(i+1)/total*100:.1f}%) - Copied: {copied:,}, Skipped: {skipped:,}, Not found: {not_found:,}")

        dest_file = dest_folder / filename

        # Skip if already exists
        if dest_file.exists():
            skipped += 1
            continue

        # Find source file
        source_file = find_invoice_file(filename, search_paths, subdir_cache)

        if source_file:
            try:
                shutil.copy2(source_file, dest_file)
                copied += 1
            except Exception as e:
                errors += 1
                if errors <= 10:
                    log(f"    Error copying {filename}: {e}")
        else:
            not_found += 1

    return copied, skipped, not_found, errors


def main():
    log("=" * 60)
    log("INVOICE COPY SCRIPT - ALL FILES")
    log("=" * 60)
    log(f"Source: {SOURCE_BASE}")
    log(f"Destination: {DEST_BASE}")

    # Check source accessibility
    if not SOURCE_BASE.exists():
        log(f"\nERROR: Cannot access source folder:")
        log(f"  {SOURCE_BASE}")
        log("  Make sure you're connected to the network.")
        return 1

    DEST_BASE.mkdir(parents=True, exist_ok=True)
    subdir_cache = {}

    start_time = datetime.now()

    total_copied = 0
    total_skipped = 0
    total_not_found = 0
    total_errors = 0

    # Sales Tax 2024
    log("\n" + "=" * 60)
    log("Processing: Sales_Tax_2024")
    log("=" * 60)
    filenames = get_sales_tax_invoices()
    if filenames:
        copied, skipped, not_found, errors = copy_files(filenames, DEST_BASE / "Sales_Tax_2024", subdir_cache)
        log(f"  DONE: Copied {copied:,}, Skipped {skipped:,}, Not found {not_found:,}, Errors {errors}")
        total_copied += copied
        total_skipped += skipped
        total_not_found += not_found
        total_errors += errors

    # Use Tax 2023
    log("\n" + "=" * 60)
    log("Processing: Use_Tax_2023")
    log("=" * 60)
    filenames = get_use_tax_invoices(2023)
    if filenames:
        copied, skipped, not_found, errors = copy_files(filenames, DEST_BASE / "Use_Tax_2023", subdir_cache)
        log(f"  DONE: Copied {copied:,}, Skipped {skipped:,}, Not found {not_found:,}, Errors {errors}")
        total_copied += copied
        total_skipped += skipped
        total_not_found += not_found
        total_errors += errors

    # Use Tax 2024
    log("\n" + "=" * 60)
    log("Processing: Use_Tax_2024")
    log("=" * 60)
    filenames = get_use_tax_invoices(2024)
    if filenames:
        copied, skipped, not_found, errors = copy_files(filenames, DEST_BASE / "Use_Tax_2024", subdir_cache)
        log(f"  DONE: Copied {copied:,}, Skipped {skipped:,}, Not found {not_found:,}, Errors {errors}")
        total_copied += copied
        total_skipped += skipped
        total_not_found += not_found
        total_errors += errors

    elapsed = datetime.now() - start_time

    log("\n" + "=" * 60)
    log("FINAL SUMMARY")
    log("=" * 60)
    log(f"Total copied: {total_copied:,}")
    log(f"Total skipped (already exist): {total_skipped:,}")
    log(f"Total not found: {total_not_found:,}")
    log(f"Total errors: {total_errors}")
    log(f"Elapsed time: {elapsed}")
    log(f"Destination: {DEST_BASE}")

    return 0


if __name__ == "__main__":
    exit(main())
