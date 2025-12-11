"""
Historical Tax Rates Module
===========================

Loads and indexes WA DOR quarterly tax rate files for historical lookups.

WA DOR provides quarterly Excel files at:
https://dor.wa.gov/taxes-rates/sales-use-tax-rates

File naming convention expected:
- Rates_2024Q1.xlsx, Rates_2024Q2.xlsx, etc.
- Or: 2024_Q1_Rates.xlsx, etc.

Usage:
    from core.historical_rates import HistoricalRateDB

    rates = HistoricalRateDB("data/wa_rates/")
    rate = rates.get_rate("Seattle", "King", "98101", date(2023, 6, 15))
    # Returns: 10.25 (percent)
"""

import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Quarter effective dates (first day of each quarter)
QUARTER_START = {
    1: (1, 1),   # Q1: Jan 1
    2: (4, 1),   # Q2: Apr 1
    3: (7, 1),   # Q3: Jul 1
    4: (10, 1),  # Q4: Oct 1
}


class HistoricalRateDB:
    """
    Historical tax rate database loaded from WA DOR quarterly files.

    Indexes rates by location and effective date for fast lookups.
    Falls back to WA DOR API for current rates if historical not available.
    """

    def __init__(self, rates_folder: str):
        """
        Load all quarterly rate files from a folder.

        Args:
            rates_folder: Path to folder containing WA DOR Excel files
        """
        self.folder = Path(rates_folder)
        if not self.folder.exists():
            raise FileNotFoundError(f"Rates folder not found: {rates_folder}")

        # Index structure: {(year, quarter): DataFrame}
        self._quarterly_data: Dict[Tuple[int, int], pd.DataFrame] = {}

        # Location index: {location_key: {(year, quarter): rate}}
        self._location_rates: Dict[str, Dict[Tuple[int, int], float]] = {}

        self._load_all_files()

    def _load_all_files(self):
        """Load all Excel/CSV files from the rates folder."""
        files = list(self.folder.glob("*.xlsx")) + list(self.folder.glob("*.csv"))

        if not files:
            print(f"  Warning: No rate files found in {self.folder}")
            return

        loaded = 0
        for file_path in files:
            year_quarter = self._parse_filename(file_path.name)
            if year_quarter:
                year, quarter = year_quarter
                try:
                    df = self._load_rate_file(file_path)
                    self._quarterly_data[(year, quarter)] = df
                    self._index_rates(df, year, quarter)
                    loaded += 1
                except Exception as e:
                    print(f"  Warning: Failed to load {file_path.name}: {e}")

        print(f"  Loaded {loaded} quarterly rate files from {self.folder.name}")

    def _parse_filename(self, filename: str) -> Optional[Tuple[int, int]]:
        """
        Extract year and quarter from filename.

        Supports patterns:
        - WA DOR format: Q126_Excel_LSU-rates.xlsx (Q1 2026)
        - WA DOR format: Q425_Excel_LSU.xlsx (Q4 2025)
        - WA DOR older: ExcelLocalSlsUserates_24_Q4.xlsx (Q4 2024)
        - Generic: Rates_2024Q1.xlsx, 2024_Q1_Rates.xlsx
        - Generic: Q1_2024.xlsx, rates-2024-q1.csv
        """
        filename_lower = filename.lower()

        # WA DOR format: Q126 = Q1 2026, Q425 = Q4 2025
        match = re.search(r'q(\d)(\d{2})[-_]', filename_lower)
        if match:
            quarter = int(match.group(1))
            year = 2000 + int(match.group(2))
            return year, quarter

        # WA DOR older format: ExcelLocalSlsUserates_24_Q4.xlsx
        match = re.search(r'_(\d{2})_q(\d)', filename_lower)
        if match:
            year = 2000 + int(match.group(1))
            quarter = int(match.group(2))
            return year, quarter

        # Pattern: 2024Q1 or 2024_Q1 or 2024-Q1
        match = re.search(r'(\d{4})[_\-]?q(\d)', filename_lower)
        if match:
            return int(match.group(1)), int(match.group(2))

        # Pattern: Q1_2024 or Q1-2024
        match = re.search(r'q(\d)[_\-]?(\d{4})', filename_lower)
        if match:
            return int(match.group(2)), int(match.group(1))

        return None

    def _load_rate_file(self, file_path: Path) -> pd.DataFrame:
        """Load a single rate file (Excel or CSV)."""
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        else:
            # Try to find header row (WA DOR files have blank rows at top)
            # Read first few rows to find the header
            df_peek = pd.read_excel(file_path, header=None, nrows=5)
            header_row = 0
            for i, row in df_peek.iterrows():
                if 'Location' in str(row.values) or 'location' in str(row.values).lower():
                    header_row = i
                    break

            df = pd.read_excel(file_path, header=header_row)

        # Normalize column names (remove newlines, lowercase, strip whitespace)
        df.columns = [str(c).lower().replace('\n', ' ').replace('  ', ' ').strip() for c in df.columns]

        # Drop rows where location is empty (header rows, blanks)
        # Handle both "location" and "location name" column names
        location_col = 'location' if 'location' in df.columns else 'location name' if 'location name' in df.columns else None
        if location_col:
            df = df.dropna(subset=[location_col])

        return df

    def _index_rates(self, df: pd.DataFrame, year: int, quarter: int):
        """Index rates from a quarterly file for fast lookup."""
        # WA DOR files have columns: Location, County, Location Code, Combined Sales Tax

        # Find location columns
        city_col = self._find_column(df, ["location", "city", "location name"])
        county_col = self._find_column(df, ["county", "county name"])
        code_col = self._find_column(df, ["location code", "locationcode", "code"])
        rate_col = self._find_column(df, ["combined sales tax", "combined rate", "rate", "tax rate", "total rate"])

        if not rate_col:
            print(f"    Warning: No rate column found for {year}Q{quarter}")
            return

        for _, row in df.iterrows():
            # Build location key
            city = str(row.get(city_col, "")).strip() if city_col else ""
            county = str(row.get(county_col, "")).strip() if county_col else ""
            code = str(row.get(code_col, "")).strip() if code_col else ""

            # Get rate (handle percentage format)
            rate_val = row.get(rate_col, 0)
            if pd.isna(rate_val):
                continue

            rate = float(rate_val)
            # If rate is < 1, it's a decimal (0.10 = 10%)
            if rate < 1:
                rate = rate * 100

            # Index by multiple keys for flexible lookup
            keys = []
            if city and county:
                keys.append(f"{city.lower()},{county.lower()}")
            if city:
                keys.append(city.lower())
            if code:
                keys.append(code)

            for key in keys:
                if key not in self._location_rates:
                    self._location_rates[key] = {}
                self._location_rates[key][(year, quarter)] = rate

    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Find a column by trying candidate names in priority order."""
        # Try candidates in order (first match wins)
        for candidate in candidates:
            for col in df.columns:
                col_lower = str(col).lower()
                if candidate in col_lower:
                    return col
        return None

    def get_rate(
        self,
        city: str = "",
        county: str = "",
        zip_code: str = "",
        invoice_date: date = None,
        location_code: str = "",
        address: str = "",
        use_api_fallback: bool = True
    ) -> Optional[float]:
        """
        Look up tax rate for a location and date.

        Args:
            city: City name
            county: County name
            zip_code: ZIP code (used for API fallback)
            invoice_date: Date to look up rate for (determines which quarter)
            location_code: WA DOR location code (if known)
            address: Street address (used for API fallback)
            use_api_fallback: If True, call WA DOR API to get location code when not found

        Returns:
            Tax rate as percentage (e.g., 10.25), or None if not found
        """
        if not invoice_date:
            invoice_date = date.today()

        # Determine which quarter
        year = invoice_date.year
        if invoice_date.month <= 3:
            quarter = 1
        elif invoice_date.month <= 6:
            quarter = 2
        elif invoice_date.month <= 9:
            quarter = 3
        else:
            quarter = 4

        # Try different lookup keys
        lookup_keys = []
        if location_code:
            lookup_keys.append(location_code)
        if city and county:
            lookup_keys.append(f"{city.lower()},{county.lower()}")
        if city:
            lookup_keys.append(city.lower())

        rate = self._lookup_rate_by_keys(lookup_keys, year, quarter)
        if rate:
            return rate

        # Fallback: Use API to get location code, then lookup by code
        if use_api_fallback and (city or zip_code):
            api_location_code = self._get_location_code_from_api(address, city, zip_code)
            if api_location_code and api_location_code not in lookup_keys:
                rate = self._lookup_rate_by_keys([api_location_code], year, quarter)
                if rate:
                    return rate

        return None

    def _lookup_rate_by_keys(
        self, lookup_keys: list, year: int, quarter: int
    ) -> Optional[float]:
        """Look up rate using list of keys, with adjacent quarter fallback."""
        for key in lookup_keys:
            if key in self._location_rates:
                rates = self._location_rates[key]
                if (year, quarter) in rates:
                    return rates[(year, quarter)]

                # Try adjacent quarters if exact not found
                for q_offset in [1, -1, 2, -2]:
                    adj_quarter = quarter + q_offset
                    adj_year = year
                    if adj_quarter < 1:
                        adj_quarter += 4
                        adj_year -= 1
                    elif adj_quarter > 4:
                        adj_quarter -= 4
                        adj_year += 1

                    if (adj_year, adj_quarter) in rates:
                        return rates[(adj_year, adj_quarter)]
        return None

    def _get_location_code_from_api(
        self, address: str, city: str, zip_code: str
    ) -> Optional[str]:
        """Call WA DOR API to get location code for an address."""
        try:
            from core.wa_tax_rate_lookup import lookup_tax_rate
            result = lookup_tax_rate(address=address, city=city, zip_code=zip_code)
            return result.get("location_code")
        except Exception:
            return None

    def get_effective_quarter(self, invoice_date: date) -> Tuple[int, int]:
        """Get the year and quarter for a given date."""
        year = invoice_date.year
        if invoice_date.month <= 3:
            quarter = 1
        elif invoice_date.month <= 6:
            quarter = 2
        elif invoice_date.month <= 9:
            quarter = 3
        else:
            quarter = 4
        return year, quarter

    def has_data_for_quarter(self, year: int, quarter: int) -> bool:
        """Check if we have rate data for a specific quarter."""
        return (year, quarter) in self._quarterly_data

    def get_available_quarters(self) -> List[Tuple[int, int]]:
        """Return list of available (year, quarter) tuples."""
        return sorted(self._quarterly_data.keys())

    def __len__(self) -> int:
        """Return number of quarters loaded."""
        return len(self._quarterly_data)


# Global instance for convenience
_global_rates: Optional[HistoricalRateDB] = None


def load_historical_rates(rates_folder: str) -> HistoricalRateDB:
    """
    Load historical rates database (cached globally).

    Args:
        rates_folder: Path to folder with quarterly rate files

    Returns:
        HistoricalRateDB instance
    """
    global _global_rates
    _global_rates = HistoricalRateDB(rates_folder)
    return _global_rates


def get_historical_rate(
    city: str = "",
    county: str = "",
    zip_code: str = "",
    invoice_date: date = None,
    location_code: str = "",
    address: str = "",
    use_api_fallback: bool = True
) -> Optional[float]:
    """
    Look up historical rate using globally loaded database.

    Args:
        city: City name
        county: County name
        zip_code: ZIP code
        invoice_date: Date for rate lookup
        location_code: WA DOR location code (if known)
        address: Street address (for API fallback)
        use_api_fallback: If True, use API to get location code when city not found

    Returns:
        Tax rate as percentage, or None
    """
    # Try historical first (includes API fallback for location code)
    if _global_rates:
        rate = _global_rates.get_rate(
            city, county, zip_code, invoice_date,
            location_code, address, use_api_fallback
        )
        if rate:
            return rate

    return None
