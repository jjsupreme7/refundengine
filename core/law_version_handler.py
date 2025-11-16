#!/usr/bin/env python3
"""
Law Version Handler - Old Law vs New Law (ESSB 5814)

Handles filtering and comparison between:
- Old Law (before October 1, 2025)
- New Law (ESSB 5814, effective October 1, 2025)
"""

from datetime import datetime
from typing import Dict, List, Optional
from supabase import Client


class LawVersionHandler:
    """Manages old law vs new law filtering and comparison"""

    # Critical date: ESSB 5814 effective date
    ESSB_5814_EFFECTIVE_DATE = datetime(2025, 10, 1)

    # Services that changed under ESSB 5814
    ESSB_5814_AFFECTED_SERVICES = [
        "information technology services",
        "advertising services",
        "custom website development",
        "custom software",
        "temporary staffing",
        "investigation services",
        "security services",
        "live presentations"
    ]

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def filter_by_law_version(
        self,
        chunks: List[Dict],
        law_version: str = "new_law"
    ) -> List[Dict]:
        """
        Filter chunks by law version

        Args:
            chunks: List of retrieved chunks
            law_version: "old_law", "new_law", or "both"

        Returns:
            Filtered chunks
        """
        if law_version == "both":
            return chunks

        filtered = []

        for chunk in chunks:
            # Get document info
            doc_id = chunk.get('document_id')
            effective_date_str = chunk.get('effective_date')
            citation = chunk.get('citation', '')

            # Determine if this is old or new law
            is_new_law = self._is_new_law_document(
                effective_date_str,
                citation,
                chunk.get('chunk_text', '')
            )

            # Filter based on version requested
            if law_version == "new_law" and is_new_law:
                chunk['law_version'] = 'new_law'
                chunk['law_version_label'] = '📘 New Law (ESSB 5814, Oct 2025+)'
                filtered.append(chunk)
            elif law_version == "old_law" and not is_new_law:
                chunk['law_version'] = 'old_law'
                chunk['law_version_label'] = '📕 Old Law (Pre-Oct 2025)'
                filtered.append(chunk)

        return filtered

    def _is_new_law_document(
        self,
        effective_date_str: Optional[str],
        citation: str,
        text: str
    ) -> bool:
        """
        Determine if document represents new law

        Logic:
        1. If citation contains "ESSB 5814" → New law
        2. If effective_date >= Oct 1, 2025 → New law
        3. If text mentions ESSB 5814 → New law
        4. Otherwise → Old law (or pre-ESSB 5814)
        """
        # Check citation
        if "ESSB 5814" in citation or "essb 5814" in citation.lower():
            return True

        # Check text content
        text_lower = text.lower()
        if "essb 5814" in text_lower or "essb5814" in text_lower:
            return True

        if "october 1, 2025" in text_lower or "oct 1, 2025" in text_lower:
            # Likely discussing the new law
            return True

        # Check effective date
        if effective_date_str:
            try:
                effective_date = datetime.fromisoformat(effective_date_str.replace('Z', '+00:00'))
                if effective_date >= self.ESSB_5814_EFFECTIVE_DATE:
                    return True
            except:
                pass

        # Default to old law if not clearly new law
        return False

    def compare_old_vs_new(
        self,
        query: str,
        old_law_chunks: List[Dict],
        new_law_chunks: List[Dict]
    ) -> Dict:
        """
        Generate a comparison between old and new law

        Args:
            query: Original query
            old_law_chunks: Chunks from old law
            new_law_chunks: Chunks from new law (ESSB 5814)

        Returns:
            Dictionary with comparison analysis
        """
        comparison = {
            "query": query,
            "old_law": {
                "chunks": old_law_chunks,
                "summary": self._summarize_position(old_law_chunks, "old")
            },
            "new_law": {
                "chunks": new_law_chunks,
                "summary": self._summarize_position(new_law_chunks, "new")
            },
            "key_changes": self._identify_key_changes(old_law_chunks, new_law_chunks),
            "refund_implications": self._assess_refund_implications(query, old_law_chunks, new_law_chunks)
        }

        return comparison

    def _summarize_position(self, chunks: List[Dict], version: str) -> str:
        """Summarize the law's position from chunks"""
        if not chunks:
            return f"No {version} law information found."

        # Extract key text
        texts = [c.get('chunk_text', '')[:300] for c in chunks[:3]]
        citations = [c.get('citation', 'N/A') for c in chunks[:3]]

        summary = f"Based on {len(chunks)} source(s): {', '.join(citations)}"
        return summary

    def _identify_key_changes(
        self,
        old_law_chunks: List[Dict],
        new_law_chunks: List[Dict]
    ) -> List[str]:
        """Identify key changes between old and new law"""
        changes = []

        # Check if query is about a service affected by ESSB 5814
        for service in self.ESSB_5814_AFFECTED_SERVICES:
            # Check if mentioned in new law chunks
            if any(service in c.get('chunk_text', '').lower() for c in new_law_chunks):
                changes.append(f"🔄 {service.title()} is now subject to retail sales tax (effective Oct 1, 2025)")

        if not changes:
            changes.append("Analysis in progress - compare the sources below to identify changes")

        return changes

    def _assess_refund_implications(
        self,
        query: str,
        old_law_chunks: List[Dict],
        new_law_chunks: List[Dict]
    ) -> Optional[str]:
        """Assess if there are refund implications"""
        query_lower = query.lower()

        # Keywords suggesting this might involve refunds
        refund_keywords = ["refund", "sales tax", "charged", "paid", "before october"]

        if not any(kw in query_lower for kw in refund_keywords):
            return None

        # Check if this involves a service that changed
        for service in self.ESSB_5814_AFFECTED_SERVICES:
            if service in query_lower:
                return (
                    f"⚠️ REFUND POTENTIAL: {service.title()} was NOT subject to sales tax before October 1, 2025. "
                    f"If sales tax was charged before this date, a refund may be due."
                )

        return "Check if sales tax was charged before October 1, 2025 for services that became taxable under ESSB 5814."

    def get_essb_5814_context(self) -> str:
        """Get context about ESSB 5814 for AI prompts"""
        return """
CRITICAL CONTEXT - ESSB 5814 (Effective October 1, 2025):

ESSB 5814 made these services subject to retail sales tax for the FIRST TIME:
1. Information Technology Services
2. Advertising Services
3. Custom Website Development
4. Custom Software Development
5. Temporary Staffing Services
6. Investigation/Security Services
7. Live Presentations

BEFORE October 1, 2025: These services were subject to Service B&O tax ONLY (no sales tax)
AFTER October 1, 2025: These services are subject to Retailing B&O tax AND sales tax

REFUND RULE: If sales tax was charged BEFORE October 1, 2025 for any of these services,
it was charged in ERROR and a REFUND is due.

TRANSITION PERIOD: Contracts signed before Oct 1, 2025 have special rules through March 31, 2026.
"""

    def should_include_essb_context(self, query: str) -> bool:
        """Determine if ESSB 5814 context should be included in prompt"""
        query_lower = query.lower()

        # Include if asking about affected services
        if any(service in query_lower for service in self.ESSB_5814_AFFECTED_SERVICES):
            return True

        # Include if asking about recent changes
        if any(kw in query_lower for kw in ["new law", "essb", "5814", "october", "2025", "recent", "changed"]):
            return True

        # Include if asking about refunds for services
        if "refund" in query_lower and any(kw in query_lower for kw in ["service", "software", "advertising", "it", "tech"]):
            return True

        return False
