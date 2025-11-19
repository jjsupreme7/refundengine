"""
Fuzzy Vendor Name Matching

Handles cases where vendor names don't exactly match historical records.

Example:
    Upload file has: "American Tower Company"
    Historical data has: "ATC TOWER SERVICES LLC"

    Match: Both contain "TOWER" keyword → Fuzzy match found

Usage:
    from analysis.vendor_matcher import VendorMatcher

    matcher = VendorMatcher()

    # Find exact match first
    match = matcher.match_vendor("ATC TOWER SERVICES")

    # If no exact match, find fuzzy matches
    fuzzy_matches = matcher.fuzzy_match_vendor("American Tower Company")
"""

import logging
from typing import Dict, List, Optional, Tuple

from core.database import get_supabase_client

logger = logging.getLogger(__name__)


class VendorMatcher:
    """
    Matches vendor names using exact and fuzzy matching strategies.

    Matching Priority:
    1. Exact match (vendor_name = input)
    2. Fuzzy match (keyword overlap >= 50%)
    3. No match (novel vendor)
    """

    def __init__(self):
        """Initialize the vendor matcher."""
        self.supabase = get_supabase_client()

    def _extract_vendor_keywords(self, vendor_name: str) -> List[str]:
        """
        Extract keywords from vendor name for fuzzy matching.

        Args:
            vendor_name: Vendor name string

        Returns:
            List of keywords (uppercase, no stopwords)

        Example:
            "ATC TOWER SERVICES LLC" → ["ATC", "TOWER", "SERVICES"]
        """
        if not vendor_name or vendor_name.strip() == "":
            return []

        # Remove common suffixes
        stopwords = {
            "LLC",
            "INC",
            "CORP",
            "CO",
            "LTD",
            "LP",
            "CORPORATION",
            "COMPANY",
            "INCORPORATED",
            "LIMITED",
            "THE",
            "AND",
            "&",
        }

        # Split on spaces and filter
        words = str(vendor_name).upper().replace(",", " ").replace(".", " ").split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords

    def match_vendor(self, vendor_name: str) -> Optional[Dict]:
        """
        Find exact vendor match in historical data.

        Args:
            vendor_name: Vendor name to match

        Returns:
            Vendor record with historical data, or None if not found
        """
        if not vendor_name or vendor_name.strip() == "":
            return None

        vendor_upper = vendor_name.strip().upper()

        try:
            result = (
                self.supabase.table("vendor_products")
                .select("*")
                .eq("vendor_name", vendor_upper)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            logger.error(f"Error matching vendor {vendor_name}: {e}")
            return None

    def fuzzy_match_vendor(
        self, vendor_name: str, min_overlap: int = 1
    ) -> List[Tuple[Dict, int]]:
        """
        Find fuzzy vendor matches using keyword overlap.

        Args:
            vendor_name: Vendor name to match
            min_overlap: Minimum number of keyword overlaps required (default: 1)

        Returns:
            List of (vendor_record, overlap_count) tuples, sorted by overlap count descending

        Example:
            Input: "American Tower Company"
            Keywords: ["AMERICAN", "TOWER", "COMPANY"]

            Historical vendor "ATC TOWER SERVICES":
            Keywords: ["ATC", "TOWER", "SERVICES"]
            Overlap: ["TOWER"] → overlap_count = 1
        """
        if not vendor_name or vendor_name.strip() == "":
            return []

        # Extract keywords from input vendor name
        input_keywords = self._extract_vendor_keywords(vendor_name)

        if not input_keywords:
            return []

        try:
            # Query vendors with keyword overlap using PostgreSQL array overlap operator
            # The && operator returns true if arrays have any elements in common
            result = (
                self.supabase.table("vendor_products")
                .select("*")
                .not_.is_("vendor_keywords", "null")
                .execute()
            )

            # Manual filtering and scoring (Supabase client may not support array overlap directly)
            matches = []
            for vendor in result.data:
                if not vendor.get("vendor_keywords"):
                    continue

                vendor_keywords = vendor["vendor_keywords"]

                # Calculate overlap count
                overlap = set(input_keywords) & set(vendor_keywords)
                overlap_count = len(overlap)

                if overlap_count >= min_overlap:
                    matches.append((vendor, overlap_count))

            # Sort by overlap count descending
            matches.sort(key=lambda x: x[1], reverse=True)

            return matches

        except Exception as e:
            logger.error(f"Error fuzzy matching vendor {vendor_name}: {e}")
            return []

    def get_best_match(self, vendor_name: str) -> Optional[Dict]:
        """
        Get the best vendor match (exact or fuzzy).

        Args:
            vendor_name: Vendor name to match

        Returns:
            Best matching vendor record with additional metadata:
            - match_type: 'exact' or 'fuzzy'
            - match_score: overlap count for fuzzy matches

        Example:
            result = matcher.get_best_match("American Tower Company")

            if result:
                print(f"Match type: {result['match_type']}")
                print(f"Matched vendor: {result['vendor_name']}")
                print(f"Historical success rate: {result['historical_success_rate']}")
        """
        # Try exact match first
        exact_match = self.match_vendor(vendor_name)
        if exact_match:
            exact_match["match_type"] = "exact"
            exact_match["match_score"] = len(self._extract_vendor_keywords(vendor_name))
            return exact_match

        # Try fuzzy match
        fuzzy_matches = self.fuzzy_match_vendor(vendor_name, min_overlap=1)
        if fuzzy_matches:
            best_match, overlap_count = fuzzy_matches[0]
            best_match["match_type"] = "fuzzy"
            best_match["match_score"] = overlap_count
            best_match["fuzzy_match_keywords"] = list(
                set(self._extract_vendor_keywords(vendor_name))
                & set(best_match.get("vendor_keywords", []))
            )
            return best_match

        # No match found
        return None

    def get_vendor_historical_context(self, vendor_name: str) -> Optional[str]:
        """
        Get human-readable historical context for a vendor.

        Args:
            vendor_name: Vendor name to lookup

        Returns:
            Human-readable string with historical context, or None if no match

        Example:
            context = matcher.get_vendor_historical_context("ATC TOWER SERVICES")
            # Returns: "This vendor has 2,799 historical cases with 100% refund success rate. Typical basis: Out-of-State Services"
        """
        match = self.get_best_match(vendor_name)

        if not match:
            return None

        match_type = match.get("match_type", "unknown")
        vendor = match.get("vendor_name", "Unknown")
        sample_count = match.get("historical_sample_count", 0)
        success_rate = match.get("historical_success_rate", 0)
        typical_basis = match.get("typical_refund_basis", "Unknown")

        context = f"Historical precedent ({match_type} match): "
        context += f"Vendor '{vendor}' has {sample_count:,} historical cases "
        context += f"with {success_rate:.0%} refund success rate. "

        if typical_basis and typical_basis != "Unknown":
            context += f"Typical basis: {typical_basis}"

        if match_type == "fuzzy":
            keywords = match.get("fuzzy_match_keywords", [])
            if keywords:
                context += f" (Matched on keywords: {', '.join(keywords)})"

        return context
