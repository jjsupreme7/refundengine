"""
Site ID Lookup Module
=====================

Maps Site IDs to address information using a master sheet.

Usage:
    from core.site_id_lookup import SiteIDLookup

    lookup = SiteIDLookup("path/to/site_master.xlsx")
    location = lookup.lookup("SITE-001")
    # Returns: {"address": "123 Main St", "city": "Seattle", "state": "WA", ...}
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional


class SiteIDLookup:
    """
    Loads a site ID master sheet and provides lookup by site ID.

    Expected columns (flexible naming):
    - site_id / Site_ID / SiteID
    - address / Address / Street
    - city / City
    - state / State
    - county / County
    - zip / ZIP / Zip_Code / Postal_Code
    """

    # Column name variations to look for
    COLUMN_MAPPINGS = {
        "site_id": ["site_id", "siteid", "site id", "site", "location_id", "locationid"],
        "address": ["address", "street", "street_address", "addr"],
        "city": ["city", "ship_city", "ship_to_city"],
        "state": ["state", "ship_state", "ship_to_state"],
        "county": ["county", "county_name"],
        "zip": ["zip", "zip_code", "zipcode", "postal_code", "postal"],
    }

    def __init__(self, master_sheet_path: str, sheet_name: str = None):
        """
        Load site ID master sheet into memory.

        Args:
            master_sheet_path: Path to Excel file with site ID mappings
            sheet_name: Optional sheet name (default: first sheet)
        """
        self.path = Path(master_sheet_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Site ID master sheet not found: {master_sheet_path}")

        # Load and normalize
        if sheet_name:
            self.df = pd.read_excel(master_sheet_path, sheet_name=sheet_name)
        else:
            self.df = pd.read_excel(master_sheet_path)
        self._normalize_columns()
        self._build_index()

        print(f"  Loaded {len(self.df)} site IDs from {self.path.name}")

    def _normalize_columns(self):
        """Map various column names to standard names."""
        # Lowercase all column names for matching
        col_map = {}
        for col in self.df.columns:
            col_lower = col.lower().strip()
            for standard, variations in self.COLUMN_MAPPINGS.items():
                if col_lower in variations:
                    col_map[col] = standard
                    break

        # Rename columns to standard names
        self.df = self.df.rename(columns=col_map)

        # Check required columns
        if "site_id" not in self.df.columns:
            raise ValueError(
                f"Site ID column not found. Expected one of: {self.COLUMN_MAPPINGS['site_id']}\n"
                f"Found columns: {list(self.df.columns)}"
            )

    def _build_index(self):
        """Build lookup index by site ID."""
        # Convert site_id to string and create index
        self.df["site_id"] = self.df["site_id"].astype(str).str.strip()
        # Drop duplicates (keep first occurrence)
        df_unique = self.df.drop_duplicates(subset=["site_id"], keep="first")
        self._index = df_unique.set_index("site_id").to_dict("index")

    def lookup(self, site_id: str) -> Optional[Dict]:
        """
        Look up address info for a site ID.

        Args:
            site_id: The site ID to look up

        Returns:
            Dict with address info, or None if not found:
            {
                "address": "123 Main St",
                "city": "Seattle",
                "state": "WA",
                "county": "King",
                "zip": "98101"
            }
        """
        if not site_id:
            return None

        site_id = str(site_id).strip()

        if site_id in self._index:
            record = self._index[site_id]
            return {
                "address": str(record.get("address", "")).strip(),
                "city": str(record.get("city", "")).strip(),
                "state": str(record.get("state", "")).strip(),
                "county": str(record.get("county", "")).strip(),
                "zip": str(record.get("zip", "")).strip(),
            }

        return None

    def get_location_key(self, site_id: str) -> Optional[str]:
        """
        Get location key for rate lookup (city, county format).

        Args:
            site_id: The site ID to look up

        Returns:
            Location key string like "Seattle, King" or None if not found
        """
        location = self.lookup(site_id)
        if location:
            city = location.get("city", "")
            county = location.get("county", "")
            if city and county:
                return f"{city}, {county}"
            elif city:
                return city
        return None

    def has_site_id(self, site_id: str) -> bool:
        """Check if a site ID exists in the master sheet."""
        if not site_id:
            return False
        return str(site_id).strip() in self._index

    def is_washington_site(self, site_id: str) -> bool:
        """
        Check if a site ID is in Washington state.

        Args:
            site_id: The site ID to check

        Returns:
            True if state == "WA", False otherwise
        """
        location = self.lookup(site_id)
        if location:
            state = location.get("state", "").upper().strip()
            return state == "WA" or state == "WASHINGTON"
        return False

    def is_out_of_state(self, site_id: str) -> bool:
        """
        Check if a site ID is for a non-Washington location.

        Args:
            site_id: The site ID to check

        Returns:
            True if state is known and != "WA", False if WA or unknown
        """
        location = self.lookup(site_id)
        if location:
            state = location.get("state", "").upper().strip()
            # Only return True if we have a state and it's not WA
            if state and state != "WA" and state != "WASHINGTON":
                return True
        return False

    def get_all_site_ids(self) -> list:
        """Return list of all site IDs in the master sheet."""
        return list(self._index.keys())

    def __len__(self) -> int:
        """Return number of site IDs in the master sheet."""
        return len(self._index)

    def __contains__(self, site_id: str) -> bool:
        """Allow 'if site_id in lookup:' syntax."""
        return self.has_site_id(site_id)


# Convenience function for one-off lookups
_global_lookup: Optional[SiteIDLookup] = None


def load_site_master(master_sheet_path: str, sheet_name: str = None) -> SiteIDLookup:
    """
    Load site ID master sheet (cached globally).

    Args:
        master_sheet_path: Path to Excel file
        sheet_name: Optional sheet name (default: first sheet)

    Returns:
        SiteIDLookup instance
    """
    global _global_lookup
    _global_lookup = SiteIDLookup(master_sheet_path, sheet_name=sheet_name)
    return _global_lookup


def lookup_site_id(site_id: str) -> Optional[Dict]:
    """
    Look up a site ID using the globally loaded master sheet.

    Args:
        site_id: The site ID to look up

    Returns:
        Dict with address info, or None

    Raises:
        RuntimeError if master sheet not loaded
    """
    if _global_lookup is None:
        raise RuntimeError("Site ID master sheet not loaded. Call load_site_master() first.")
    return _global_lookup.lookup(site_id)
