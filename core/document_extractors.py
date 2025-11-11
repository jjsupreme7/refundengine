#!/usr/bin/env python3
"""
Document Extractors Module
Handles extraction from various file formats: PDF, TIF, MSG, Excel, etc.

Supports:
- PDF files (via pdfplumber and PyPDF2)
- TIF/TIFF images (via OCR with pytesseract)
- MSG files (Outlook emails via extract-msg)
- Excel files (via openpyxl/pandas)

Usage:
    from core.document_extractors import extract_text_from_file

    text, pages = extract_text_from_file("invoice.pdf")
    text, pages = extract_text_from_file("scan.tif")
    text, pages = extract_text_from_file("email.msg")
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Optional
import warnings

# PDF extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# Image/OCR extraction
try:
    from PIL import Image
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    warnings.warn("pytesseract or Pillow not available. TIF extraction will fail.")

# MSG extraction
try:
    import extract_msg
    EXTRACTMSG_AVAILABLE = True
except ImportError:
    EXTRACTMSG_AVAILABLE = False
    warnings.warn("extract-msg not available. MSG file extraction will fail.")

# Excel extraction
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> Tuple[str, int]:
    """
    Extract text from PDF using pdfplumber (preferred) or PyPDF2 (fallback)

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract (None = all pages)

    Returns:
        Tuple of (extracted_text, total_pages)
    """
    if PDFPLUMBER_AVAILABLE:
        return _extract_with_pdfplumber(pdf_path, max_pages)
    elif PYPDF2_AVAILABLE:
        return _extract_with_pypdf2(pdf_path, max_pages)
    else:
        raise ImportError("No PDF library available. Install: pip install pdfplumber")


def _extract_with_pdfplumber(pdf_path: str, max_pages: int = None) -> Tuple[str, int]:
    """Extract text using pdfplumber (better quality)"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages) if max_pages else total_pages

            text = ""
            for page in pdf.pages[:pages_to_extract]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            return text, total_pages
    except Exception as e:
        print(f"Error extracting PDF with pdfplumber: {e}")
        return "", 0


def _extract_with_pypdf2(pdf_path: str, max_pages: int = None) -> Tuple[str, int]:
    """Extract text using PyPDF2 (fallback)"""
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            pages_to_extract = min(total_pages, max_pages) if max_pages else total_pages

            text = ""
            for page in pdf_reader.pages[:pages_to_extract]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            return text, total_pages
    except Exception as e:
        print(f"Error extracting PDF with PyPDF2: {e}")
        return "", 0


def extract_text_from_tif(tif_path: str) -> Tuple[str, int]:
    """
    Extract text from TIF/TIFF image using OCR (Tesseract)

    Args:
        tif_path: Path to TIF/TIFF file

    Returns:
        Tuple of (extracted_text, page_count)

    Note:
        Requires Tesseract OCR to be installed on the system.
        Install: https://github.com/tesseract-ocr/tesseract
    """
    if not TESSERACT_AVAILABLE:
        raise ImportError("pytesseract not available. Install: pip install pytesseract Pillow")

    try:
        # Check if Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            error_msg = (
                "Tesseract OCR not found on system. Please install:\n"
                "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  Mac: brew install tesseract\n"
                "  Linux: sudo apt-get install tesseract-ocr"
            )
            raise RuntimeError(error_msg)

        # Open and process image
        image = Image.open(tif_path)

        # Handle multi-page TIFFs
        text = ""
        page_count = 0

        try:
            # Try to iterate through pages
            while True:
                # Extract text from current page
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n\n"
                page_count += 1

                # Try to move to next page
                image.seek(image.tell() + 1)
        except EOFError:
            # No more pages
            pass

        return text.strip(), page_count

    except Exception as e:
        print(f"Error extracting TIF with OCR: {e}")
        return "", 0


def extract_text_from_msg(msg_path: str) -> Tuple[str, Dict]:
    """
    Extract text and metadata from Outlook MSG file

    Args:
        msg_path: Path to MSG file

    Returns:
        Tuple of (email_body_text, metadata_dict)
        where metadata_dict contains:
        - subject: Email subject
        - sender: Sender email/name
        - recipients: List of recipients
        - date: Email date
        - attachments: List of attachment filenames
    """
    if not EXTRACTMSG_AVAILABLE:
        raise ImportError("extract-msg not available. Install: pip install extract-msg")

    try:
        msg = extract_msg.Message(msg_path)

        # Extract email body
        body = msg.body or ""

        # Extract metadata
        metadata = {
            "subject": msg.subject or "No Subject",
            "sender": msg.sender or "Unknown",
            "recipients": [str(r) for r in (msg.recipients or [])],
            "date": str(msg.date) if msg.date else None,
            "attachments": [att.longFilename or att.shortFilename for att in (msg.attachments or [])],
        }

        # Combine body and metadata into readable text
        text = f"""
EMAIL MESSAGE
=============
Subject: {metadata['subject']}
From: {metadata['sender']}
Date: {metadata['date']}
Attachments: {', '.join(metadata['attachments']) if metadata['attachments'] else 'None'}

MESSAGE BODY:
{body}
"""

        return text.strip(), metadata

    except Exception as e:
        print(f"Error extracting MSG file: {e}")
        return "", {}


def extract_text_from_excel(excel_path: str, sheet_name: Optional[str] = None) -> Tuple[str, int]:
    """
    Extract text from Excel file (XLS/XLSX)

    Args:
        excel_path: Path to Excel file
        sheet_name: Specific sheet to extract (None = first sheet)

    Returns:
        Tuple of (text_representation, number_of_sheets)
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas not available. Install: pip install pandas openpyxl")

    try:
        # Read Excel file
        if sheet_name:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            sheets_processed = 1
        else:
            # Read all sheets
            excel_file = pd.ExcelFile(excel_path)
            dfs = []
            for sheet in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet)
                dfs.append(f"--- Sheet: {sheet} ---\n{df.to_string()}")
            text = "\n\n".join(dfs)
            sheets_processed = len(excel_file.sheet_names)
            return text, sheets_processed

        # Convert DataFrame to string
        text = df.to_string()
        return text, sheets_processed

    except Exception as e:
        print(f"Error extracting Excel file: {e}")
        return "", 0


def extract_text_from_file(file_path: str, max_pages: int = None) -> Tuple[str, int]:
    """
    Universal file extractor - automatically detects file type and extracts text

    Supported formats:
    - PDF (.pdf)
    - TIF/TIFF (.tif, .tiff) - requires Tesseract OCR
    - MSG (.msg) - Outlook emails
    - Excel (.xls, .xlsx)

    Args:
        file_path: Path to file
        max_pages: Maximum pages to extract for PDF files (None = all)

    Returns:
        Tuple of (extracted_text, page_or_item_count)

    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist

    Example:
        >>> text, pages = extract_text_from_file("invoice.pdf")
        >>> text, pages = extract_text_from_file("scan.tif")
        >>> text, metadata = extract_text_from_file("email.msg")
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == '.pdf':
        return extract_text_from_pdf(file_path, max_pages)

    elif suffix in ['.tif', '.tiff']:
        return extract_text_from_tif(file_path)

    elif suffix == '.msg':
        text, metadata = extract_text_from_msg(file_path)
        return text, 1  # Return 1 as "page count" for consistency

    elif suffix in ['.xls', '.xlsx']:
        return extract_text_from_excel(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {suffix}\n"
            f"Supported formats: .pdf, .tif, .tiff, .msg, .xls, .xlsx"
        )


def check_dependencies() -> Dict[str, bool]:
    """
    Check which document extraction dependencies are available

    Returns:
        Dictionary mapping library names to availability status
    """
    status = {
        "pdfplumber": PDFPLUMBER_AVAILABLE,
        "PyPDF2": PYPDF2_AVAILABLE,
        "pytesseract": TESSERACT_AVAILABLE,
        "extract-msg": EXTRACTMSG_AVAILABLE,
        "pandas": PANDAS_AVAILABLE,
    }

    # Check if Tesseract binary is installed
    if TESSERACT_AVAILABLE:
        try:
            pytesseract.get_tesseract_version()
            status["tesseract_binary"] = True
        except:
            status["tesseract_binary"] = False
    else:
        status["tesseract_binary"] = False

    return status


if __name__ == "__main__":
    # Self-test and dependency check
    print("Document Extractors Module - Dependency Check")
    print("=" * 70)

    deps = check_dependencies()
    for lib, available in deps.items():
        status = "[OK] Available" if available else "[X] Missing"
        print(f"{lib:20s}: {status}")

    print("\n" + "=" * 70)
    print("Supported file types:")
    print("  - PDF (.pdf) - Available" if deps["pdfplumber"] or deps["PyPDF2"] else "  - PDF (.pdf) - NOT AVAILABLE")
    print("  - TIF (.tif, .tiff) - Available" if deps["tesseract_binary"] else "  - TIF (.tif, .tiff) - NOT AVAILABLE (need Tesseract)")
    print("  - MSG (.msg) - Available" if deps["extract-msg"] else "  - MSG (.msg) - NOT AVAILABLE")
    print("  - Excel (.xls, .xlsx) - Available" if deps["pandas"] else "  - Excel (.xls, .xlsx) - NOT AVAILABLE")
    print("=" * 70)
