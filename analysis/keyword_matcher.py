"""
Keyword-Based Pattern Matching

Matches invoice descriptions to historical patterns using keywords,
without relying on Vertex Category codes (CON-R-NENG).

Example:
    Upload file has: "Tower construction services for cell site"
    Keywords extracted: ["tower", "construction", "services", "cell", "site"]

    Historical pattern: ["tower", "construction"] → 92% success rate

Usage:
    from analysis.keyword_matcher import KeywordMatcher

    matcher = KeywordMatcher()

    # Match description to historical patterns
    pattern = matcher.match_description("Tower construction services")

    # Returns: {
    #   'keywords': ['tower', 'construction', 'services'],
    #   'success_rate': 0.92,
    #   'typical_basis': 'Out-of-State Services',
    #   'sample_count': 15234
    # }
"""

from typing import List, Dict, Optional, Tuple
from core.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)


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
        if not description or description.strip() == '':
            return []

        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'of', 'to', 'in', 'on',
                    'at', 'by', 'from', 'with', 'is', 'was', 'are', 'were'}

        # Clean and split
        text = str(description).lower()
        # Remove special characters but keep spaces
        text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
        words = text.split()

        # Filter out stopwords and short words
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords

    def match_description(self, description: str, min_overlap: int = 2) -> Optional[Dict]:
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
        if not description or description.strip() == '':
            return None

        # Extract keywords from description
        input_keywords = self._extract_keywords(description)

        if len(input_keywords) < min_overlap:
            logger.debug(f"Description has too few keywords: {input_keywords}")
            return None

        try:
            # Query keyword patterns
            result = self.supabase.table('keyword_patterns')\
                .select('*')\
                .not_.is_('keywords', 'null')\
                .execute()

            # Find best match by keyword overlap
            best_match = None
            best_overlap_count = 0

            for pattern in result.data:
                if not pattern.get('keywords'):
                    continue

                pattern_keywords = pattern['keywords']

                # Calculate overlap
                overlap = set(input_keywords) & set(pattern_keywords)
                overlap_count = len(overlap)

                if overlap_count >= min_overlap and overlap_count > best_overlap_count:
                    best_match = pattern.copy()
                    best_match['overlap_keywords'] = list(overlap)
                    best_match['overlap_count'] = overlap_count
                    best_overlap_count = overlap_count

            return best_match

        except Exception as e:
            logger.error(f"Error matching description keywords: {e}")
            return None

    def match_vendor_description_keywords(self, vendor_name: str, min_overlap: int = 2) -> Optional[Dict]:
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
            vendor = self.supabase.table('vendor_products')\
                .select('description_keywords')\
                .eq('vendor_name', vendor_name.upper().strip())\
                .execute()

            if not vendor.data or not vendor.data[0].get('description_keywords'):
                return None

            vendor_keywords = vendor.data[0]['description_keywords']

            # Query keyword patterns
            patterns = self.supabase.table('keyword_patterns')\
                .select('*')\
                .not_.is_('keywords', 'null')\
                .execute()

            # Find best match
            best_match = None
            best_overlap_count = 0

            for pattern in patterns.data:
                if not pattern.get('keywords'):
                    continue

                pattern_keywords = pattern['keywords']

                # Calculate overlap
                overlap = set(vendor_keywords) & set(pattern_keywords)
                overlap_count = len(overlap)

                if overlap_count >= min_overlap and overlap_count > best_overlap_count:
                    best_match = pattern.copy()
                    best_match['overlap_keywords'] = list(overlap)
                    best_match['overlap_count'] = overlap_count
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

        sample_count = pattern.get('sample_count', 0)
        success_rate = pattern.get('success_rate', 0)
        typical_basis = pattern.get('typical_basis', 'Unknown')
        overlap_keywords = pattern.get('overlap_keywords', [])

        context = f"Matched historical pattern: {sample_count:,} cases "
        context += f"with {success_rate:.0%} success rate. "

        if typical_basis and typical_basis != 'Unknown':
            context += f"Typical basis: {typical_basis}. "

        if overlap_keywords:
            context += f"(Matched on: {', '.join(overlap_keywords)})"

        return context

    def get_all_high_confidence_patterns(self, min_success_rate: float = 0.80, min_samples: int = 10) -> List[Dict]:
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
            result = self.supabase.table('keyword_patterns')\
                .select('*')\
                .gte('success_rate', min_success_rate)\
                .gte('sample_count', min_samples)\
                .order('success_rate', desc=True)\
                .execute()

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

        return pattern.get('typical_basis')
