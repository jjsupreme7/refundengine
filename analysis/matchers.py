"""
Pattern Matching Module

Combines vendor and keyword matching for historical pattern discovery.

Contains:
- VendorMatcher: Fuzzy matching for vendor names
- KeywordMatcher: Pattern matching for product descriptions

Usage:
    from analysis.matchers import VendorMatcher, KeywordMatcher

    vendor_matcher = VendorMatcher()
    keyword_matcher = KeywordMatcher()

    # Match vendors
    vendor_match = vendor_matcher.get_best_match("American Tower Company")

    # Match product descriptions
    pattern = keyword_matcher.match_description("Tower construction services")
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

            # Manual filtering and scoring (Supabase client may not support array
            # overlap directly)
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


class KeywordMatcher:
    """
    Matches product descriptions to historical patterns using keyword overlap.

    Matching Strategy:
    1. Extract keywords from description
    2. Find historical patterns with keyword overlap
    3. Return pattern with highest overlap score
    """

    def __init__(self):
        """Initialize the keyword matcher."""
        self.supabase = get_supabase_client()

    def _extract_keywords(self, description: str) -> List[str]:
        """
        Extract meaningful keywords from product description.

        Args:
            description: Product description text

        Returns:
            List of keywords (lowercase, no stopwords)

        Example:
            "Tower construction services for cell site" →
            ["tower", "construction", "services", "cell", "site"]
        """
        if not description or description.strip() == "":
            return []

        # Remove common stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "for",
            "of",
            "to",
            "in",
            "on",
            "at",
            "by",
            "from",
            "with",
            "is",
            "was",
            "are",
            "were",
        }

        # Clean and split
        text = str(description).lower()
        # Remove special characters but keep spaces
        text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
        words = text.split()

        # Filter out stopwords and short words
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords

    def match_description(
        self, description: str, min_overlap: int = 2
    ) -> Optional[Dict]:
        """
        Find best matching keyword pattern for a description.

        Args:
            description: Product description to match
            min_overlap: Minimum number of keyword overlaps required (default: 2)

        Returns:
            Best matching pattern with metadata, or None if no match

        Example:
            pattern = matcher.match_description("Tower construction services")

            # Returns:
            {
                'keywords': ['tower', 'construction', 'services'],
                'success_rate': 0.92,
                'typical_basis': 'Out-of-State Services',
                'sample_count': 15234,
                'overlap_keywords': ['tower', 'construction'],
                'overlap_count': 2
            }
        """
        if not description or description.strip() == "":
            return None

        # Extract keywords from description
        input_keywords = self._extract_keywords(description)

        if len(input_keywords) < min_overlap:
            logger.debug(f"Description has too few keywords: {input_keywords}")
            return None

        try:
            # Query keyword patterns
            result = (
                self.supabase.table("keyword_patterns")
                .select("*")
                .not_.is_("keywords", "null")
                .execute()
            )

            # Find best match by keyword overlap
            best_match = None
            best_overlap_count = 0

            for pattern in result.data:
                if not pattern.get("keywords"):
                    continue

                pattern_keywords = pattern["keywords"]

                # Calculate overlap
                overlap = set(input_keywords) & set(pattern_keywords)
                overlap_count = len(overlap)

                if overlap_count >= min_overlap and overlap_count > best_overlap_count:
                    best_match = pattern.copy()
                    best_match["overlap_keywords"] = list(overlap)
                    best_match["overlap_count"] = overlap_count
                    best_overlap_count = overlap_count

            return best_match

        except Exception as e:
            logger.error(f"Error matching description keywords: {e}")
            return None

    def match_vendor_description_keywords(
        self, vendor_name: str, min_overlap: int = 2
    ) -> Optional[Dict]:
        """
        Find vendor's typical description keywords and match to patterns.

        Args:
            vendor_name: Vendor name to lookup
            min_overlap: Minimum keyword overlap required

        Returns:
            Best matching pattern based on vendor's typical product keywords

        Example:
            # Vendor "ATC TOWER SERVICES" has description_keywords: ["tower", "construction", "wireless"]
            pattern = matcher.match_vendor_description_keywords("ATC TOWER SERVICES")

            # Returns pattern that matches vendor's typical products
        """
        try:
            # Get vendor's typical description keywords
            vendor = (
                self.supabase.table("vendor_products")
                .select("description_keywords")
                .eq("vendor_name", vendor_name.upper().strip())
                .execute()
            )

            if not vendor.data or not vendor.data[0].get("description_keywords"):
                return None

            vendor_keywords = vendor.data[0]["description_keywords"]

            # Query keyword patterns
            patterns = (
                self.supabase.table("keyword_patterns")
                .select("*")
                .not_.is_("keywords", "null")
                .execute()
            )

            # Find best match
            best_match = None
            best_overlap_count = 0

            for pattern in patterns.data:
                if not pattern.get("keywords"):
                    continue

                pattern_keywords = pattern["keywords"]

                # Calculate overlap
                overlap = set(vendor_keywords) & set(pattern_keywords)
                overlap_count = len(overlap)

                if overlap_count >= min_overlap and overlap_count > best_overlap_count:
                    best_match = pattern.copy()
                    best_match["overlap_keywords"] = list(overlap)
                    best_match["overlap_count"] = overlap_count
                    best_overlap_count = overlap_count

            return best_match

        except Exception as e:
            logger.error(f"Error matching vendor description keywords: {e}")
            return None

    def get_pattern_context(self, description: str) -> Optional[str]:
        """
        Get human-readable historical context for a description.

        Args:
            description: Product description

        Returns:
            Human-readable string with pattern context, or None if no match

        Example:
            context = matcher.get_pattern_context("Tower construction services")
            # Returns: "Matched historical pattern: 15,234 cases with 92% success rate. Typical basis: Out-of-State Services"
        """
        pattern = self.match_description(description)

        if not pattern:
            return None

        sample_count = pattern.get("sample_count", 0)
        success_rate = pattern.get("success_rate", 0)
        typical_basis = pattern.get("typical_basis", "Unknown")
        overlap_keywords = pattern.get("overlap_keywords", [])

        context = f"Matched historical pattern: {sample_count:,} cases "
        context += f"with {success_rate:.0%} success rate. "

        if typical_basis and typical_basis != "Unknown":
            context += f"Typical basis: {typical_basis}. "

        if overlap_keywords:
            context += f"(Matched on: {', '.join(overlap_keywords)})"

        return context

    def get_all_high_confidence_patterns(
        self, min_success_rate: float = 0.80, min_samples: int = 10
    ) -> List[Dict]:
        """
        Get all high-confidence keyword patterns.

        Args:
            min_success_rate: Minimum success rate (default: 0.80 = 80%)
            min_samples: Minimum sample count (default: 10)

        Returns:
            List of high-confidence patterns sorted by success rate

        Example:
            patterns = matcher.get_all_high_confidence_patterns()

            for pattern in patterns:
                print(f"{pattern['keywords']}: {pattern['success_rate']:.0%} ({pattern['sample_count']} cases)")
        """
        try:
            result = (
                self.supabase.table("keyword_patterns")
                .select("*")
                .gte("success_rate", min_success_rate)
                .gte("sample_count", min_samples)
                .order("success_rate", desc=True)
                .execute()
            )

            return result.data

        except Exception as e:
            logger.error(f"Error fetching high-confidence patterns: {e}")
            return []

    def suggest_refund_basis(self, description: str) -> Optional[str]:
        """
        Suggest refund basis based on description keywords.

        Args:
            description: Product description

        Returns:
            Suggested refund basis, or None if no match

        Example:
            basis = matcher.suggest_refund_basis("Software maintenance renewal")
            # Returns: "Software Maintenance"
        """
        pattern = self.match_description(description)

        if not pattern:
            return None

        return pattern.get("typical_basis")
