"""
Text Redaction Module

Redacts PII from text before sending to external APIs (OpenAI, etc.).
Preserves business data needed for tax analysis while removing sensitive information.
"""

from typing import Dict, List, Tuple

from .pii_detector import PIIDetector, PIIFinding


class Redactor:
    """
    Redacts PII from text while preserving business context.

    Redaction tokens:
    - [REDACTED_ACCOUNT] - Bank account numbers
    - [REDACTED_ROUTING] - Routing numbers
    - [REDACTED_CARD] - Credit card numbers
    - [REDACTED_SSN] - Social Security Numbers
    - [REDACTED_TAX_ID] - Tax ID/EIN
    - [REDACTED_EMAIL] - Email addresses
    - [REDACTED_PHONE] - Phone numbers
    - [REDACTED_NAME] - Person names
    """

    # Redaction token mapping
    REDACTION_TOKENS = {
        "BANK_ACCOUNT": "[REDACTED_ACCOUNT]",
        "ROUTING_NUMBER": "[REDACTED_ROUTING]",
        "CREDIT_CARD": "[REDACTED_CARD]",
        "US_SSN": "[REDACTED_SSN]",
        "TAX_ID": "[REDACTED_TAX_ID]",
        "EMAIL_ADDRESS": "[REDACTED_EMAIL]",
        "PHONE_NUMBER": "[REDACTED_PHONE]",
        "PERSON": "[REDACTED_NAME]",
    }

    def __init__(self):
        """Initialize redactor with PII detector"""
        self.detector = PIIDetector()

    def redact(
        self, text: str, preserve_context: bool = True
    ) -> Tuple[str, Dict[str, List[str]]]:
        """
        Redact PII from text.

        Args:
            text: Text to redact
            preserve_context: If True, add context labels (e.g., "Email: [REDACTED_EMAIL]")

        Returns:
            Tuple of (redacted_text, redaction_map)
            - redacted_text: Text with PII replaced by tokens
            - redaction_map: Dictionary mapping token type to list of redacted values
        """
        if not text or not text.strip():
            return text, {}

        # Detect all PII
        findings = self.detector.detect(text)

        if not findings:
            return text, {}

        # Sort findings by position (reverse order to maintain positions during replacement)
        findings.sort(key=lambda f: f.start, reverse=True)

        # Build redaction map
        redaction_map = {}
        redacted_text = text

        for finding in findings:
            # Get redaction token
            token = self.REDACTION_TOKENS.get(
                finding.type, f"[REDACTED_{finding.type}]"
            )

            # Track redacted value
            if finding.type not in redaction_map:
                redaction_map[finding.type] = []
            redaction_map[finding.type].append(finding.value)

            # Replace in text (from end to start to maintain positions)
            redacted_text = (
                redacted_text[: finding.start] + token + redacted_text[finding.end :]
            )

        return redacted_text, redaction_map

    def redact_invoice(self, invoice_text: str) -> Tuple[str, Dict]:
        """
        Redact PII from invoice text for safe API processing.

        Args:
            invoice_text: Raw invoice text

        Returns:
            Tuple of (safe_text, redaction_report)
            - safe_text: Invoice text with all PII redacted
            - redaction_report: Report of what was redacted
        """
        redacted_text, redaction_map = self.redact(invoice_text)

        # Build redaction report
        report = {
            "redacted": bool(redaction_map),
            "pii_types_found": list(redaction_map.keys()),
            "total_redactions": sum(len(values) for values in redaction_map.values()),
            "details": {
                pii_type: len(values) for pii_type, values in redaction_map.items()
            },
        }

        return redacted_text, report

    def is_safe_for_api(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text is safe to send to external API.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_safe, issues_found)
            - is_safe: True if no PII detected
            - issues_found: List of PII types found (if any)
        """
        findings = self.detector.detect(text)

        if not findings:
            return True, []

        # Get unique PII types
        pii_types = list(set(f.type for f in findings))

        return False, pii_types

    def redact_structured_data(self, data: Dict) -> Tuple[Dict, Dict]:
        """
        Redact PII from structured data (e.g., extracted invoice JSON).

        Args:
            data: Dictionary with invoice/PO data

        Returns:
            Tuple of (safe_data, redaction_report)
        """
        safe_data = {}
        total_redactions = {}

        for key, value in data.items():
            if isinstance(value, str):
                redacted, redaction_map = self.redact(value)
                safe_data[key] = redacted

                # Track redactions
                if redaction_map:
                    total_redactions[key] = redaction_map

            elif isinstance(value, list):
                safe_list = []
                for item in value:
                    if isinstance(item, str):
                        redacted, redaction_map = self.redact(item)
                        safe_list.append(redacted)
                        if redaction_map:
                            if key not in total_redactions:
                                total_redactions[key] = {}
                            for pii_type, values in redaction_map.items():
                                if pii_type not in total_redactions[key]:
                                    total_redactions[key][pii_type] = []
                                total_redactions[key][pii_type].extend(values)
                    elif isinstance(item, dict):
                        redacted_item, item_redactions = self.redact_structured_data(
                            item
                        )
                        safe_list.append(redacted_item)
                        if item_redactions:
                            if key not in total_redactions:
                                total_redactions[key] = {}
                            total_redactions[key].update(item_redactions)
                    else:
                        safe_list.append(item)
                safe_data[key] = safe_list

            elif isinstance(value, dict):
                redacted_dict, dict_redactions = self.redact_structured_data(value)
                safe_data[key] = redacted_dict
                if dict_redactions:
                    total_redactions[key] = dict_redactions

            else:
                # Numbers, booleans, etc. are safe
                safe_data[key] = value

        report = {
            "redacted": bool(total_redactions),
            "fields_redacted": list(total_redactions.keys()),
            "details": total_redactions,
        }

        return safe_data, report
