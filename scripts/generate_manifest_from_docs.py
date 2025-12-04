#!/usr/bin/env python3
"""
Generate Claims Manifest from Document Folder

Scans a folder of invoices and POs, extracts basic data from each,
and generates a claims manifest Excel file ready for analysis.

Usage:
    python scripts/generate_manifest_from_docs.py \
        --source "/Users/jacoballen/Desktop/Synthetic_Documents/Sales Tax" \
        --output "SalesTax_Claims.xlsx"

    python scripts/generate_manifest_from_docs.py \
        --source "/Users/jacoballen/Desktop/Synthetic_Documents/Use Tax" \
        --output "UseTax_Claims.xlsx"
"""

import argparse
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Load environment
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supported file extensions
INVOICE_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".png", ".jpg", ".jpeg"}
PO_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".eml"}


def find_files(folder: Path, subfolder_name: str) -> List[Path]:
    """Find all files in a specific subfolder (Invoices or Purchase Orders)."""
    target_folder = folder / subfolder_name
    if not target_folder.exists():
        print(f"  Warning: {subfolder_name} folder not found at {target_folder}")
        return []

    files = []
    for f in target_folder.iterdir():
        if f.is_file() and f.suffix.lower() in INVOICE_EXTENSIONS:
            files.append(f)
    return sorted(files)


def extract_pdf_text(file_path: Path) -> str:
    """Extract text from all pages of a PDF."""
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            all_text = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    all_text.append(text)
            return "\n\n".join(all_text)
    except Exception as e:
        print(f"  Error extracting PDF {file_path.name}: {e}")
        return ""


def extract_excel_text(file_path: Path) -> str:
    """Extract text from Excel file."""
    try:
        df = pd.read_excel(str(file_path))
        return df.to_string()
    except Exception as e:
        print(f"  Error extracting Excel {file_path.name}: {e}")
        return ""


def extract_word_text(file_path: Path) -> str:
    """Extract text from Word document."""
    try:
        from docx import Document
        doc = Document(str(file_path))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"  Error extracting Word {file_path.name}: {e}")
        return ""


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from any supported file type."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return extract_pdf_text(file_path)
    elif suffix in {".xlsx", ".xls"}:
        return extract_excel_text(file_path)
    elif suffix in {".docx", ".doc"}:
        return extract_word_text(file_path)
    elif suffix in {".png", ".jpg", ".jpeg"}:
        # For images, we'd need vision API - skip for now
        return f"[Image file: {file_path.name}]"
    elif suffix == ".eml":
        # Email files - basic text extraction
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except:
            return ""
    else:
        return ""


def parse_invoice_with_ai(text: str, filename: str) -> Dict[str, Any]:
    """Use AI to extract structured data from invoice text."""
    if not text or len(text) < 50:
        return {"error": "Insufficient text"}

    prompt = f"""Extract the following fields from this invoice document. Return ONLY valid JSON with these exact keys:

{{
    "vendor_name": "string - the company that issued the invoice",
    "invoice_number": "string - the invoice number/ID",
    "po_number": "string or null - purchase order number if mentioned",
    "invoice_date": "string - date in format YYYY-MM-DD if possible",
    "subtotal": "number or null - subtotal before tax",
    "tax_amount": "number or null - tax amount charged",
    "tax_rate": "number or null - tax rate as percentage (e.g., 6.5 for 6.5%)",
    "total_amount": "number - total amount due",
    "line_items": "string - brief category (e.g., 'IT Equipment', 'Software License')",
    "line_items_detail": "string - detailed line items with qty and price (e.g., '2x Server ($15,000 ea), 5x Switch ($2,000 ea)')",
    "document_preview": "string - first 150 chars of key invoice content/description",
    "key_terms": "string - comma-separated product names, SKUs, service types (e.g., 'PowerEdge R750, VMware vSphere, 3-year support')"
}}

Document text:
{text[:6000]}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        result["source_file"] = filename
        return result
    except Exception as e:
        print(f"  AI extraction error for {filename}: {e}")
        return {"error": str(e), "source_file": filename}


def parse_po_with_ai(text: str, filename: str) -> Dict[str, Any]:
    """Use AI to extract PO number from purchase order text."""
    if not text or len(text) < 50:
        return {"error": "Insufficient text"}

    prompt = f"""Extract the purchase order number from this document. Return ONLY valid JSON:

{{
    "po_number": "string - the PO number",
    "vendor_name": "string or null - vendor if mentioned"
}}

Document text:
{text[:4000]}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        result["source_file"] = filename
        return result
    except Exception as e:
        return {"error": str(e), "source_file": filename}


def process_invoice(file_path: Path) -> Dict[str, Any]:
    """Process a single invoice file."""
    text = extract_text_from_file(file_path)
    data = parse_invoice_with_ai(text, file_path.name)
    data["file_path"] = str(file_path)
    return data


def process_po(file_path: Path) -> Dict[str, Any]:
    """Process a single PO file."""
    text = extract_text_from_file(file_path)
    data = parse_po_with_ai(text, file_path.name)
    data["file_path"] = str(file_path)
    return data


def generate_manifest(
    invoice_data: List[Dict],
    po_data: List[Dict],
    output_path: str,
    source_folder: Path
):
    """Generate the claims manifest Excel file."""

    # Build PO lookup by PO number
    po_lookup = {}
    for po in po_data:
        po_num = po.get("po_number")
        if po_num:
            # Normalize PO number for matching
            po_num_normalized = str(po_num).strip().upper()
            po_lookup[po_num_normalized] = po

    # Get list of PDF PO files for sequential fallback
    po_pdf_files = [po for po in po_data if po.get("source_file", "").endswith(".pdf")]

    rows = []
    po_index = 0  # For sequential assignment fallback
    for i, inv in enumerate(invoice_data):
        if "error" in inv and not inv.get("vendor_name"):
            continue  # Skip failed extractions

        # Try to match PO by PO number first
        po_num = inv.get("po_number")
        matched_po = None
        if po_num:
            po_num_normalized = str(po_num).strip().upper()
            matched_po = po_lookup.get(po_num_normalized)

        # Fallback: assign PO files sequentially if no match found
        if not matched_po and po_index < len(po_pdf_files):
            matched_po = po_pdf_files[po_index]
            po_index += 1

        row = {
            "Vendor ID": f"V{i+1:04d}",
            "Vendor": inv.get("vendor_name", "Unknown"),
            "Inv-1 FileName": inv.get("source_file", ""),
            "Inv-2 FileName": "",
            "PO_FileName": matched_po.get("source_file", "") if matched_po else "",
            "Inv No": inv.get("invoice_number", ""),
            "PO No": inv.get("po_number", ""),
            "Date": inv.get("invoice_date", ""),
            "Initial Amount": inv.get("subtotal"),
            "Tax Paid": inv.get("tax_amount"),
            "Total Amount": inv.get("total_amount"),
            "Tax Rate": inv.get("tax_rate"),
            "Description": inv.get("line_items", ""),
            "Line Items Detail": inv.get("line_items_detail", ""),
            "Document Preview": inv.get("document_preview", ""),
            "Key Terms": inv.get("key_terms", ""),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(str(output_path), index=False)
    print(f"\nGenerated manifest: {output_path}")
    print(f"  Total rows: {len(df)}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Generate claims manifest from document folder")
    parser.add_argument("--source", required=True, help="Source folder containing Invoices and Purchase Orders subfolders")
    parser.add_argument("--output", required=True, help="Output Excel file path")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    args = parser.parse_args()

    source_folder = Path(args.source)
    if not source_folder.exists():
        print(f"Error: Source folder not found: {source_folder}")
        sys.exit(1)

    print("=" * 70)
    print("GENERATE CLAIMS MANIFEST FROM DOCUMENTS")
    print("=" * 70)
    print(f"\nSource: {source_folder}")
    print(f"Output: {args.output}")

    # Find all invoice files
    print("\n1. Scanning for files...")
    invoice_files = find_files(source_folder, "Invoices")
    po_files = find_files(source_folder, "Purchase Orders")

    print(f"   Found {len(invoice_files)} invoice files")
    print(f"   Found {len(po_files)} PO files")

    if not invoice_files:
        print("\nError: No invoice files found!")
        sys.exit(1)

    # Process invoices in parallel
    print("\n2. Extracting invoice data...")
    invoice_data = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(tqdm(
            executor.map(process_invoice, invoice_files),
            total=len(invoice_files),
            desc="   Processing invoices"
        ))
        invoice_data = results

    # Process POs in parallel
    print("\n3. Extracting PO data...")
    po_data = []
    if po_files:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            results = list(tqdm(
                executor.map(process_po, po_files),
                total=len(po_files),
                desc="   Processing POs"
            ))
            po_data = results

    # Generate manifest
    print("\n4. Generating manifest...")
    df = generate_manifest(invoice_data, po_data, args.output, source_folder)

    # Summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"\nManifest generated: {args.output}")
    print(f"Total claims: {len(df)}")

    # Show sample
    print("\nSample rows:")
    print(df[["Vendor", "Inv No", "Total Amount", "Tax Paid"]].head(5).to_string())

    print(f"\nNext step: Run the analyzer:")
    print(f"  python analysis/fast_batch_analyzer.py --excel \"{args.output}\" --state washington --tax-type sales_tax")


if __name__ == "__main__":
    main()
