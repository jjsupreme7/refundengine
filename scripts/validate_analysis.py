"""
Analysis Validator - Enforces CLAUDE.md requirements programmatically.

Validates invoice analysis output before writing to Excel.
Rejects non-compliant rows with clear error messages.
"""

import re
from pathlib import Path

# Load valid RCWs once at module import
_VALID_RCWS = set()
_KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "target_rcws.txt"

def _load_valid_rcws():
    """Load valid RCW citations from knowledge base."""
    global _VALID_RCWS
    if _VALID_RCWS:
        return _VALID_RCWS

    if _KB_PATH.exists():
        with open(_KB_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    _VALID_RCWS.add(line)
    return _VALID_RCWS


def is_valid_citation(citation: str) -> bool:
    """
    Check if a citation is valid against target_rcws.txt.
    Handles formats like "RCW 82.12.0208(7)" or just "82.12.0208(7)".
    Also accepts WAC citations (WAC 458-20-XXX format).
    """
    if not citation:
        return True  # Empty citation is OK for NO REFUND cases

    valid_rcws = _load_valid_rcws()

    wac_pattern = re.compile(
        r"^WAC\s+458-20-\d+[A-Z]?(?:\([^)]+\))*$",
        re.IGNORECASE,
    )

    # Handle multiple citations separated by / or ,
    for part in re.split(r'[/,]', citation):
        part = part.strip()
        if not part:
            continue

        # Validate WAC citations by format (WAC 458-20-XXX...)
        if part.upper().startswith('WAC'):
            if not wac_pattern.match(part):
                return False
            continue

        # Extract RCW number (remove "RCW " prefix if present)
        rcw_num = re.sub(r'^RCW\s*', '', part, flags=re.IGNORECASE).strip()

        # Check exact match first
        if rcw_num in valid_rcws:
            continue

        # Check if base RCW matches (e.g., 82.12.0208 matches 82.12.0208(7))
        base_rcw = re.sub(r'\([^)]+\)$', '', rcw_num)
        if base_rcw in valid_rcws:
            continue

        # No match found for this citation part
        return False

    return True


def validate_row(row: dict) -> tuple[bool, list[str]]:
    """
    Validate a single row's analysis against CLAUDE.md requirements.

    Returns:
        (is_valid, list_of_errors) - True if valid, errors list if not
    """
    errors = []
    reasoning = row.get('AI_Reasoning', '') or ''

    # Skip validation for rows without analysis
    if not reasoning.strip():
        return True, []

    # 1. Check mandatory headers (CLAUDE.md lines 320-322)
    if 'INVOICE VERIFIED:' not in reasoning:
        errors.append("Missing 'INVOICE VERIFIED:' header - must include invoice # and date from PDF")

    if 'SHIP-TO:' not in reasoning:
        errors.append("Missing 'SHIP-TO:' header - must include full address from invoice")

    if 'MATCHED LINE ITEM:' not in reasoning:
        errors.append("Missing 'MATCHED LINE ITEM:' header - must match Excel row to invoice line")

    decision = (row.get('Final_Decision', '') or '').upper()

    # 2. Check citation validity (CLAUDE.md lines 179-188)
    citation = row.get('Citation', '') or ''
    if decision == 'REFUND' and not str(citation).strip():
        errors.append("Missing citation for REFUND decision")
    if citation and not is_valid_citation(citation):
        errors.append(f"Invalid citation: '{citation}' - must be from target_rcws.txt or WAC 458-20-XXX")

    # 3. Check for lazy REVIEW (CLAUDE.md lines 168-175)
    if decision == 'REVIEW':
        research_indicators = ['web search', 'searched', 'research', 'looked up', 'found that']
        has_research = any(ind in reasoning.lower() for ind in research_indicators)
        if not has_research:
            errors.append("REVIEW decision without research evidence - must do web search before marking REVIEW")

    # 4. Check confidence score (valid range)
    confidence = row.get('Confidence')
    if confidence is not None:
        try:
            conf_val = float(confidence)
            if not (0.0 <= conf_val <= 1.0):
                errors.append(f"Confidence {conf_val} out of range - must be 0.0 to 1.0")
        except (ValueError, TypeError):
            errors.append(f"Invalid confidence value: {confidence}")

    # 5. Check Final_Decision is valid
    valid_decisions = {'REFUND', 'NO REFUND', 'REVIEW', 'PASS', ''}
    if decision and decision not in valid_decisions:
        errors.append(f"Invalid Final_Decision: '{decision}' - must be REFUND, NO REFUND, REVIEW, or PASS")

    return len(errors) == 0, errors


def validate_dataframe(df, raise_on_error: bool = False) -> tuple[bool, dict]:
    """
    Validate all rows in a DataFrame.

    Args:
        df: pandas DataFrame with analysis columns
        raise_on_error: If True, raise ValueError on first invalid row

    Returns:
        (all_valid, {row_index: [errors]}) - True if all valid, dict of errors by row
    """
    all_errors = {}

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        is_valid, errors = validate_row(row_dict)

        if not is_valid:
            all_errors[idx] = errors
            if raise_on_error:
                raise ValueError(f"Row {idx} validation failed: {'; '.join(errors)}")

    return len(all_errors) == 0, all_errors


def format_validation_report(errors: dict) -> str:
    """Format validation errors as a readable report."""
    if not errors:
        return "All rows passed validation."

    lines = [f"Validation failed for {len(errors)} row(s):", ""]
    for idx, row_errors in errors.items():
        lines.append(f"Row {idx}:")
        for err in row_errors:
            lines.append(f"  - {err}")
        lines.append("")

    return "\n".join(lines)


# Quick test if run directly
if __name__ == "__main__":
    # Test citation validation
    test_citations = [
        "RCW 82.12.0208(7)",  # Valid
        "82.08.0264",         # Valid
        "WAC 458-20-170",     # Valid (WAC)
        "82.99.9999",         # Invalid
        "82.12.0208(7) / 82.08.0264",  # Valid (multiple)
    ]

    print("Citation validation tests:")
    for cit in test_citations:
        result = is_valid_citation(cit)
        print(f"  {cit}: {'VALID' if result else 'INVALID'}")

    # Test row validation
    print("\nRow validation tests:")

    good_row = {
        'AI_Reasoning': '''INVOICE VERIFIED: Invoice #12345 dated 2024-01-15
SHIP-TO: 123 Main St, Seattle WA 98101
MATCHED LINE ITEM: Cloud Services @ $1,000 (Line 1 on invoice)
---
Based on web search, this is SaaS used by employees nationwide.''',
        'Citation': 'RCW 82.12.0208(7)',
        'Final_Decision': 'REFUND',
        'Confidence': 0.85
    }

    bad_row = {
        'AI_Reasoning': 'This looks like software.',
        'Citation': '82.99.FAKE',
        'Final_Decision': 'REVIEW',
        'Confidence': 2.5
    }

    valid, errors = validate_row(good_row)
    print(f"  Good row: {'PASS' if valid else 'FAIL'} - {errors}")

    valid, errors = validate_row(bad_row)
    print(f"  Bad row: {'PASS' if valid else 'FAIL'} - {errors}")
