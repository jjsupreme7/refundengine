"""
Document URL Generation Utilities

This module provides functions to generate URLs for tax law documents,
including WAC (Washington Administrative Code) citations, RCW (Revised Code of Washington)
citations, and local PDF files.
"""

import re
from typing import Optional
from urllib.parse import quote


def generate_wac_url(citation: str) -> Optional[str]:
    """
    Generate the official Washington State Legislature URL for a WAC citation.

    Args:
        citation: WAC citation string (e.g., "WAC 458-20-100", "458-20-100")

    Returns:
        Full URL to the WAC section, or None if citation format is invalid

    Examples:
        >>> generate_wac_url("WAC 458-20-100")
        'https://apps.leg.wa.gov/wac/default.aspx?cite=458-20-100'
        >>> generate_wac_url("458-20-100")
        'https://apps.leg.wa.gov/wac/default.aspx?cite=458-20-100'
    """
    if not citation:
        return None

    # Remove "WAC" prefix if present and clean whitespace
    cleaned = citation.strip().upper().replace("WAC", "").strip()

    # Match WAC pattern: XXX-XX-XXX or XXX-XX-XXXXX (e.g., 458-20-100)
    wac_pattern = r'^(\d{3}-\d{2,3}-\d{3,5}[A-Z]?)$'
    match = re.match(wac_pattern, cleaned)

    if match:
        wac_number = match.group(1)
        return f"https://apps.leg.wa.gov/wac/default.aspx?cite={wac_number}"

    return None


def generate_rcw_url(citation: str) -> Optional[str]:
    """
    Generate the official Washington State Legislature URL for an RCW citation.

    Args:
        citation: RCW citation string (e.g., "RCW 82.04.050", "82.04.050")

    Returns:
        Full URL to the RCW section, or None if citation format is invalid

    Examples:
        >>> generate_rcw_url("RCW 82.04.050")
        'https://apps.leg.wa.gov/rcw/default.aspx?cite=82.04.050'
        >>> generate_rcw_url("82.04")
        'https://apps.leg.wa.gov/rcw/default.aspx?cite=82.04'
    """
    if not citation:
        return None

    # Remove "RCW" prefix if present and clean whitespace
    cleaned = citation.strip().upper().replace("RCW", "").strip()

    # Match RCW pattern: XX.XX or XX.XX.XXX (e.g., 82.04 or 82.04.050)
    rcw_pattern = r'^(\d{1,3}\.\d{2,3}(?:\.\d{3,4})?[A-Z]?)$'
    match = re.match(rcw_pattern, cleaned)

    if match:
        rcw_number = match.group(1)
        return f"https://apps.leg.wa.gov/rcw/default.aspx?cite={rcw_number}"

    return None


def generate_document_url(citation: Optional[str], source_file: Optional[str],
                         document_type: str = 'tax_law') -> Optional[str]:
    """
    Generate the appropriate URL for a document based on its citation and source file.

    This is the main function to use for generating document URLs. It automatically
    detects the type of document and generates the appropriate URL.

    Args:
        citation: Document citation (e.g., "WAC 458-20-100", "RCW 82.04")
        source_file: Local file path (e.g., "knowledge_base/wa_tax_law/some_doc.pdf")
        document_type: Type of document ('tax_law' or 'vendor_background')

    Returns:
        URL string (either official legislature URL or local serving endpoint)

    Priority:
        1. If citation contains "WAC", generate WAC URL
        2. If citation contains "RCW", generate RCW URL
        3. If source_file is HTML from wa_tax_law, try to extract citation
        4. If source_file is PDF, generate local serving URL
        5. Otherwise, return None
    """
    # Try to generate URL from citation first
    if citation:
        citation_upper = citation.upper()

        if "WAC" in citation_upper:
            url = generate_wac_url(citation)
            if url:
                return url

        if "RCW" in citation_upper:
            url = generate_rcw_url(citation)
            if url:
                return url

    # If no citation URL, check source file
    if source_file:
        source_file_lower = source_file.lower()

        # For HTML files from wa_tax_law, try to extract citation from filename
        if source_file_lower.endswith('.html') and 'wa_tax_law' in source_file_lower:
            # Try to extract WAC or RCW from filename
            # Example: "458_20_100_HTML.html" -> "458-20-100"

            # WAC pattern in filename
            wac_file_pattern = r'(\d{3})_(\d{2,3})_(\d{3,5}[A-Za-z]?)(?:_HTML)?\.html'
            wac_match = re.search(wac_file_pattern, source_file)
            if wac_match:
                wac_citation = f"{wac_match.group(1)}-{wac_match.group(2)}-{wac_match.group(3)}"
                return generate_wac_url(wac_citation)

            # RCW pattern in filename
            rcw_file_pattern = r'(\d{1,3})\.(\d{2,3})(?:\.(\d{3,4}))?(?:_HTML)?\.html'
            rcw_match = re.search(rcw_file_pattern, source_file)
            if rcw_match:
                if rcw_match.group(3):
                    rcw_citation = f"{rcw_match.group(1)}.{rcw_match.group(2)}.{rcw_match.group(3)}"
                else:
                    rcw_citation = f"{rcw_match.group(1)}.{rcw_match.group(2)}"
                return generate_rcw_url(rcw_citation)

        # For PDF files, generate local serving URL
        if source_file_lower.endswith('.pdf'):
            # Extract just the filename from the path
            filename = source_file.split('/')[-1]
            return f"http://localhost:5001/documents/{quote(filename)}"

    return None


def extract_citation_from_text(text: str) -> Optional[str]:
    """
    Extract WAC or RCW citation from a text string.

    Args:
        text: Text that may contain a citation reference

    Returns:
        First citation found, or None

    Examples:
        >>> extract_citation_from_text("See WAC 458-20-100 for details")
        'WAC 458-20-100'
        >>> extract_citation_from_text("According to RCW 82.04.050")
        'RCW 82.04.050'
    """
    # Try WAC pattern first
    wac_pattern = r'WAC\s+(\d{3}-\d{2,3}-\d{3,5}[A-Z]?)'
    wac_match = re.search(wac_pattern, text, re.IGNORECASE)
    if wac_match:
        return f"WAC {wac_match.group(1)}"

    # Try RCW pattern
    rcw_pattern = r'RCW\s+(\d{1,3}\.\d{2,3}(?:\.\d{3,4})?[A-Z]?)'
    rcw_match = re.search(rcw_pattern, text, re.IGNORECASE)
    if rcw_match:
        return f"RCW {rcw_match.group(1)}"

    return None


if __name__ == "__main__":
    # Test the functions
    print("Testing URL generation functions...\n")

    # Test WAC URLs
    print("WAC URL Tests:")
    print(f"  WAC 458-20-100: {generate_wac_url('WAC 458-20-100')}")
    print(f"  458-20-100: {generate_wac_url('458-20-100')}")
    print(f"  WAC 458-20-15502: {generate_wac_url('WAC 458-20-15502')}")

    print("\nRCW URL Tests:")
    print(f"  RCW 82.04: {generate_rcw_url('RCW 82.04')}")
    print(f"  82.04.050: {generate_rcw_url('82.04.050')}")
    print(f"  RCW 82.32.010: {generate_rcw_url('RCW 82.32.010')}")

    print("\nDocument URL Tests:")
    print(f"  WAC citation: {generate_document_url('WAC 458-20-100', None)}")
    print(f"  RCW citation: {generate_document_url('RCW 82.04', None)}")
    print(f"  HTML file: {generate_document_url(None, 'knowledge_base/wa_tax_law/wac/458_20_100_HTML.html')}")
    print(f"  PDF file: {generate_document_url(None, 'knowledge_base/wa_tax_law/some_document.pdf')}")

    print("\nCitation Extraction Tests:")
    print(f"  'See WAC 458-20-100': {extract_citation_from_text('See WAC 458-20-100 for details')}")
    print(f"  'According to RCW 82.04.050': {extract_citation_from_text('According to RCW 82.04.050')}")
