"""
PII Detection Module

Detects personally identifiable information (PII) and sensitive financial data
in invoice and purchase order documents.

Uses Microsoft Presidio for ML-based detection + custom regex patterns.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer


@dataclass
class PIIFinding:
    """Represents a detected PII instance"""

    type: str  # PII type (e.g., "BANK_ACCOUNT", "EMAIL", "SSN")
    value: str  # The detected value
    start: int  # Start position in text
    end: int  # End position in text
    confidence: float  # Detection confidence (0.0-1.0)


class PIIDetector:
    """
    Detects PII and sensitive financial information in text.

    Detected types:
    - BANK_ACCOUNT: Bank account numbers
    - ROUTING_NUMBER: ABA routing numbers
    - CREDIT_CARD: Credit card numbers
    - SSN: Social Security Numbers
    - TAX_ID: Tax ID/EIN numbers
    - EMAIL: Email addresses (personal only)
    - PHONE: Phone numbers (personal only)
    - PERSON_NAME: Individual names (in sensitive contexts)
    """

    def __init__(self):
        """Initialize the PII detector with custom patterns"""
        self.analyzer = AnalyzerEngine()
        self._add_custom_recognizers()

    def _add_custom_recognizers(self):
        """Add custom pattern recognizers for financial data"""

        # Bank account number patterns (8-17 digits, various formats)
        bank_account_pattern = Pattern(
            name="bank_account_pattern",
            regex=r"\b(?:Account|Acct|A/C)[:\s#]*([0-9]{8,17})\b",
            score=0.85,
        )
        bank_account_recognizer = PatternRecognizer(
            supported_entity="BANK_ACCOUNT", patterns=[bank_account_pattern]
        )

        # ABA routing number (9 digits)
        routing_pattern = Pattern(
            name="routing_number_pattern",
            regex=r"\b(?:ABA|Routing|RTN)[:\s#]*([0-9]{9})\b",
            score=0.9,
        )
        routing_recognizer = PatternRecognizer(
            supported_entity="ROUTING_NUMBER", patterns=[routing_pattern]
        )

        # Tax ID/EIN (XX-XXXXXXX format)
        tax_id_pattern = Pattern(
            name="tax_id_pattern",
            regex=r"\b(?:EIN|Tax\s*ID|TIN)[:\s#]*([0-9]{2}-[0-9]{7})\b",
            score=0.9,
        )
        tax_id_recognizer = PatternRecognizer(
            supported_entity="TAX_ID", patterns=[tax_id_pattern]
        )

        # Add all custom recognizers
        self.analyzer.registry.add_recognizer(bank_account_recognizer)
        self.analyzer.registry.add_recognizer(routing_recognizer)
        self.analyzer.registry.add_recognizer(tax_id_recognizer)

    def detect(self, text: str, language: str = "en") -> List[PIIFinding]:
        """
        Detect PII in text.

        Args:
            text: Text to analyze
            language: Language code (default: "en")

        Returns:
            List of PIIFinding objects with detected PII
        """
        if not text or not text.strip():
            return []

        # Run Presidio analysis
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                "BANK_ACCOUNT",
                "ROUTING_NUMBER",
                "CREDIT_CARD",
                "US_SSN",
                "TAX_ID",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "PERSON",
            ],
        )

        # Convert to PIIFinding objects
        findings = []
        for result in results:
            # Extract the actual text value
            value = text[result.start : result.end]

            # Filter out false positives
            if self._is_valid_finding(result.entity_type, value):
                findings.append(
                    PIIFinding(
                        type=result.entity_type,
                        value=value,
                        start=result.start,
                        end=result.end,
                        confidence=result.score,
                    )
                )

        return findings

    def _is_valid_finding(self, entity_type: str, value: str) -> bool:
        """
        Filter out false positives.

        For example:
        - Emails: Keep personal emails, filter generic (e.g., info@, sales@)
        - Names: Only in sensitive contexts (near "SSN", "Account")
        """
        if entity_type == "EMAIL_ADDRESS":
            # Filter out generic department emails
            generic_prefixes = [
                "info",
                "sales",
                "support",
                "contact",
                "admin",
                "accounts",
                "billing",
                "invoice",
                "orders",
            ]
            email_prefix = value.split("@")[0].lower()
            if any(prefix in email_prefix for prefix in generic_prefixes):
                return False

        if entity_type == "PHONE_NUMBER":
            # Filter out toll-free numbers (1-800, 1-888, etc.)
            if re.search(r"1-8[0-9]{2}-", value):
                return False

        return True

    def detect_in_invoice(self, invoice_text: str) -> Dict[str, List[PIIFinding]]:
        """
        Detect PII in invoice text, grouped by type.

        Args:
            invoice_text: Raw invoice text

        Returns:
            Dictionary mapping PII type to list of findings
        """
        all_findings = self.detect(invoice_text)

        # Group by type
        grouped = {}
        for finding in all_findings:
            if finding.type not in grouped:
                grouped[finding.type] = []
            grouped[finding.type].append(finding)

        return grouped

    def has_pii(self, text: str) -> bool:
        """
        Check if text contains any PII (quick check).

        Args:
            text: Text to check

        Returns:
            True if PII detected, False otherwise
        """
        findings = self.detect(text)
        return len(findings) > 0

    def get_pii_summary(self, text: str) -> Dict[str, int]:
        """
        Get summary count of PII types found.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping PII type to count
        """
        grouped = self.detect_in_invoice(text)
        return {pii_type: len(findings) for pii_type, findings in grouped.items()}
