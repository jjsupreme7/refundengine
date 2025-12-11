#!/usr/bin/env python3
"""
Download WA DOR Historical Tax Rate Files
==========================================

Downloads quarterly Excel files from WA DOR for historical rate lookups.

Usage:
    python scripts/download_wa_rate_files.py --years 2022 2023 2024
    python scripts/download_wa_rate_files.py --all  # Downloads 2017-2025
"""

import argparse
import os
import requests
from pathlib import Path


# WA DOR file URL patterns (based on their naming convention)
# Format changed over time, so we need multiple patterns
URL_PATTERNS = {
    # 2024-2026: Q126_Excel_LSU-rates.xlsx format
    "new": "https://dor.wa.gov/sites/default/files/{upload_date}/Q{q}{yy}_Excel_LSU-rates.xlsx",
    # 2020-2023: Similar but sometimes without -rates
    "mid": "https://dor.wa.gov/sites/default/files/{upload_date}/Q{q}{yy}_Excel_LSU.xlsx",
    # 2017-2019: ExcelLocalSlsUserates_YY_Q#.xlsx format
    "old": "https://dor.wa.gov/sites/default/files/{upload_date}/ExcelLocalSlsUserates_{yy}_Q{q}.xlsx",
}

# Known working URLs (manually verified)
KNOWN_URLS = {
    (2025, 4): "https://dor.wa.gov/sites/default/files/2025-09/Q425_Excel_LSU.xlsx",
    (2025, 3): "https://dor.wa.gov/sites/default/files/2025-06/Q325_Excel_LSU.xlsx",
    (2025, 2): "https://dor.wa.gov/sites/default/files/2025-03/Q225_Excel_LSU.xlsx",
    (2025, 1): "https://dor.wa.gov/sites/default/files/2024-12/Q125_Excel_LSU.xlsx",
    (2024, 4): "https://dor.wa.gov/sites/default/files/2024-09/Q424_Excel_LSU-rates.xlsx",
    (2024, 3): "https://dor.wa.gov/sites/default/files/2024-06/Q324_Excel_LSU-rates.xlsx",
    (2024, 2): "https://dor.wa.gov/sites/default/files/2024-03/Q224_Excel_LSU-rates.xlsx",
    (2024, 1): "https://dor.wa.gov/sites/default/files/2023-12/Q124_Excel_LSU-rates.xlsx",
    (2023, 4): "https://dor.wa.gov/sites/default/files/2023-09/Q423_Excel_LSU-rates.xlsx",
    (2023, 3): "https://dor.wa.gov/sites/default/files/2023-06/Q323_Excel_LSU-rates.xlsx",
    (2023, 2): "https://dor.wa.gov/sites/default/files/2023-03/Q223_Excel_LSU-rates.xlsx",
    (2023, 1): "https://dor.wa.gov/sites/default/files/2022-12/Q123_Excel_LSU-rates.xlsx",
    (2022, 4): "https://dor.wa.gov/sites/default/files/2022-09/Q422_Excel_LSU-rates.xlsx",
    (2022, 3): "https://dor.wa.gov/sites/default/files/2022-06/Q322_Excel_LSU-rates.xlsx",
    (2022, 2): "https://dor.wa.gov/sites/default/files/2022-03/Q222_Excel_LSU-rates.xlsx",
    (2022, 1): "https://dor.wa.gov/sites/default/files/2021-12/Q122_Excel_LSU-rates.xlsx",
}


def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from URL to destination path."""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            dest_path.write_bytes(response.content)
            return True
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


def download_quarter(year: int, quarter: int, output_dir: Path) -> bool:
    """Download rate file for a specific quarter."""
    # Try known URL first
    if (year, quarter) in KNOWN_URLS:
        url = KNOWN_URLS[(year, quarter)]
        filename = url.split("/")[-1]
        dest = output_dir / filename

        if dest.exists():
            print(f"  Q{quarter} {year}: Already exists ({filename})")
            return True

        print(f"  Q{quarter} {year}: Downloading...", end=" ")
        if download_file(url, dest):
            print(f"OK ({filename})")
            return True
        print("FAILED")

    print(f"  Q{quarter} {year}: No known URL - download manually from WA DOR website")
    return False


def main():
    parser = argparse.ArgumentParser(description="Download WA DOR historical tax rate files")
    parser.add_argument("--years", nargs="+", type=int, help="Years to download (e.g., 2022 2023 2024)")
    parser.add_argument("--all", action="store_true", help="Download all available years (2022-2025)")
    parser.add_argument("--output", default="data/wa_rates", help="Output directory (default: data/wa_rates)")

    args = parser.parse_args()

    if args.all:
        years = [2022, 2023, 2024, 2025]
    elif args.years:
        years = args.years
    else:
        print("Please specify --years or --all")
        print("Example: python scripts/download_wa_rate_files.py --years 2022 2023 2024")
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading WA DOR tax rate files to: {output_dir}")
    print("=" * 50)

    downloaded = 0
    failed = 0

    for year in sorted(years):
        print(f"\n{year}:")
        for quarter in [1, 2, 3, 4]:
            if download_quarter(year, quarter, output_dir):
                downloaded += 1
            else:
                failed += 1

    print("\n" + "=" * 50)
    print(f"Downloaded: {downloaded} files")
    if failed:
        print(f"Failed/Missing: {failed} files")
        print("\nFor missing files, download manually from:")
        print("https://dor.wa.gov/forms-publications/publications-subject/local-sales-use-tax-rate-history-excel-file-format")

    print(f"\nTo use these rates, run the analyzer with:")
    print(f"  --rates-folder {output_dir}")


if __name__ == "__main__":
    main()
