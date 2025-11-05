#!/usr/bin/env python3
"""
Document Classifier for Washington State Tax Refund Engine

AI-powered document type detection using content analysis combined with folder hints.

Usage:
    python scripts/document_classifier.py --file path/to/document.pdf
    python scripts/document_classifier.py --file path/to/document.pdf --folder_hint rcw
"""

import argparse
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# PDF and document processing
import pdfplumber
from docx import Document as DocxDocument
import pandas as pd
from PIL import Image
import pytesseract

# AI
from anthropic import Anthropic
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

def extract_text_from_pdf(file_path, max_pages=2):
    """Extract text from first N pages of PDF."""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                page_text = page.extract_text() or ""
                text += f"\n--- Page {i+1} ---\n{page_text}"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract PDF text: {e}")

def extract_text_from_docx(file_path):
    """Extract text from Word document."""
    try:
        doc = DocxDocument(file_path)
        text = "\n".join([para.text for para in doc.paragraphs[:50]])  # First 50 paragraphs
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract DOCX text: {e}")

def extract_text_from_excel(file_path):
    """Extract text from Excel file."""
    try:
        df = pd.read_excel(file_path, nrows=50)  # First 50 rows
        text = df.to_string()
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract Excel text: {e}")

def extract_text_from_image(file_path):
    """Extract text from image using OCR."""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract image text (OCR): {e}")

def extract_text_preview(file_path):
    """Extract text preview based on file format."""
    file_ext = Path(file_path).suffix.lower()

    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        return extract_text_from_excel(file_path)
    elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif']:
        return extract_text_from_image(file_path)
    elif file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(5000)  # First 5000 characters
    else:
        raise Exception(f"Unsupported file format: {file_ext}")

def get_file_metadata(file_path):
    """Get file metadata."""
    path = Path(file_path)

    # Calculate content hash
    with open(file_path, 'rb') as f:
        content_hash = hashlib.md5(f.read()).hexdigest()

    metadata = {
        'filename': path.name,
        'file_format': path.suffix.lower().replace('.', ''),
        'file_size_bytes': path.stat().st_size,
        'creation_date': datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
        'modification_date': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        'content_hash': content_hash
    }

    return metadata

def detect_document_type(file_path, folder_hint=None):
    """
    Detect document type using AI content analysis with optional folder hint.

    Args:
        file_path: Path to document
        folder_hint: Optional hint from folder name (e.g., 'rcw', 'wac', 'wtd', 'eta', 'invoices')

    Returns:
        dict with document_type, confidence, reasoning, key_identifiers
    """
    print(f"\n🔍 Analyzing document: {Path(file_path).name}")

    if folder_hint:
        print(f"  📁 Folder hint: {folder_hint}")

    # Extract text preview
    try:
        text_preview = extract_text_preview(file_path)
        print(f"  ✅ Extracted {len(text_preview)} characters")
    except Exception as e:
        print(f"  ❌ Text extraction failed: {e}")
        return {
            'document_type': 'unknown',
            'confidence': 0,
            'reasoning': f"Failed to extract text: {e}",
            'key_identifiers': []
        }

    # Build AI prompt
    prompt = f"""You are a document classification expert specializing in Washington State tax law documents and business documents.

DOCUMENT TEXT (first 2 pages):
{text_preview[:4000]}

FOLDER HINT: {folder_hint if folder_hint else "None - classify purely from content"}

TASK: Classify this document into ONE of these categories:

LEGAL DOCUMENTS:
- rcw: Revised Code of Washington (state statutes)
  * Typically has RCW citations like "RCW 82.08.02565"
  * Legislative language with section numbers
  * Official state law format

- wac: Washington Administrative Code (regulations)
  * Typically has WAC citations like "WAC 458-20-13601"
  * Administrative rules and regulations
  * More detailed implementation guidance than RCW

- wtd: Written Tax Determination
  * DOR rulings on specific tax questions
  * Has WTD number or reference
  * Case-specific guidance from Department of Revenue

- eta: Excise Tax Advisory
  * General tax guidance from DOR
  * Has ETA number or reference
  * Broader guidance than WTD

- case_law: Court decisions
  * Has case name (e.g., "Smith v. Washington")
  * Court opinions and decisions
  * Legal precedent

CLIENT DOCUMENTS:
- invoice: Vendor invoice/bill
  * Has "Invoice", "Bill", line items, amounts
  * Vendor name and customer name
  * Itemized charges with tax

- purchase_order: Purchase order
  * Has "Purchase Order" or "PO#"
  * List of items to be ordered
  * May not have final amounts

- statement_of_work: Statement of work/service agreement
  * Describes services to be performed
  * Scope of work, deliverables
  * Service contracts

- contract: General contract/agreement
  * Legal agreement language
  * Terms and conditions
  * Not specifically an SOW or invoice

- receipt: Payment receipt
  * Proof of payment
  * Usually simpler than invoice
  * May be credit card receipt

- other: Doesn't fit above categories

IMPORTANT:
- The folder hint is a SUGGESTION, not definitive
- Base your decision primarily on CONTENT
- If content contradicts folder hint, trust the content
- If unclear, indicate lower confidence

Return ONLY valid JSON (no markdown, no backticks):
{{
  "document_type": "one of the types above",
  "confidence": 0-100,
  "reasoning": "explain what features led to this classification",
  "key_identifiers": ["list", "of", "identifying", "features", "found"],
  "folder_hint_correct": true/false/null
}}"""

    # Call Claude API
    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        result_text = response.content[0].text.strip()

        # Parse JSON response
        result = json.loads(result_text)

        print(f"  ✅ Classification: {result['document_type']} (confidence: {result['confidence']}%)")
        print(f"  📝 Reasoning: {result['reasoning'][:100]}...")

        return result

    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse AI response as JSON: {e}")
        return {
            'document_type': 'unknown',
            'confidence': 0,
            'reasoning': f"AI response parsing failed: {e}",
            'key_identifiers': []
        }
    except Exception as e:
        print(f"  ❌ Classification failed: {e}")
        return {
            'document_type': 'unknown',
            'confidence': 0,
            'reasoning': f"Error: {e}",
            'key_identifiers': []
        }

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Classify document type using AI content analysis"
    )
    parser.add_argument(
        '--file',
        required=True,
        help="Path to document file"
    )
    parser.add_argument(
        '--folder_hint',
        required=False,
        help="Optional folder hint (rcw, wac, wtd, eta, invoices, etc.)"
    )

    args = parser.parse_args()

    # Validate file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        return 1

    # Get file metadata
    metadata = get_file_metadata(args.file)

    print("\n" + "="*70)
    print("DOCUMENT CLASSIFIER")
    print("="*70)
    print(f"\n📄 File: {metadata['filename']}")
    print(f"📊 Size: {metadata['file_size_bytes']:,} bytes")
    print(f"📁 Format: {metadata['file_format']}")

    # Classify document
    classification = detect_document_type(args.file, args.folder_hint)

    # Print results
    print("\n" + "="*70)
    print("CLASSIFICATION RESULTS")
    print("="*70)
    print(f"\n📋 Document Type: {classification['document_type']}")
    print(f"🎯 Confidence: {classification['confidence']}%")
    print(f"\n💭 Reasoning:\n{classification['reasoning']}")
    print(f"\n🔑 Key Identifiers:")
    for identifier in classification['key_identifiers']:
        print(f"  - {identifier}")

    if 'folder_hint_correct' in classification and classification['folder_hint_correct'] is not None:
        if classification['folder_hint_correct']:
            print(f"\n✅ Folder hint was correct")
        else:
            print(f"\n⚠️  Folder hint was incorrect - content analysis overrode it")

    print("\n" + "="*70 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
