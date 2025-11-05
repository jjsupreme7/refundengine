#!/usr/bin/env python3
"""
Metadata Extractor for Washington State Tax Refund Engine

Extract structured metadata from documents using AI.

Usage:
    python scripts/metadata_extractor.py --file path/to/doc.pdf --type legal
    python scripts/metadata_extractor.py --file path/to/invoice.pdf --type invoice
    python scripts/metadata_extractor.py --file path/to/sow.pdf --type sow
"""

import argparse
import sys
import os
import json
from pathlib import Path

# AI
from anthropic import Anthropic
from dotenv import load_dotenv

# Import document classifier functions
sys.path.insert(0, str(Path(__file__).parent))
from document_classifier import extract_text_preview

# Load environment
load_dotenv()

def extract_legal_document_metadata(file_path, document_text, document_type):
    """
    Extract metadata from legal documents (RCW, WAC, WTD, ETA).

    Returns:
        dict with citation, title, dates, tags, concepts, etc.
    """
    print(f"\n📚 Extracting legal document metadata...")

    prompt = f"""You are a legal document metadata extraction expert specializing in Washington State tax law.

DOCUMENT TYPE: {document_type}

DOCUMENT TEXT:
{document_text[:6000]}

TASK: Extract structured metadata from this legal document.

For RCW/WAC documents:
- Citation: The RCW or WAC number (e.g., "RCW 82.08.02565" or "WAC 458-20-13601")
- Title: The official title or subject matter
- Document date: When it was enacted/published
- Effective date: When it takes effect
- Expiration date: If applicable

For WTD/ETA documents:
- Citation: The WTD/ETA number
- Title: The subject matter
- Document date: Issue date

Extract these metadata fields:
- citation: Official citation/number
- title: Document title or subject
- document_date: YYYY-MM-DD format (null if not found)
- effective_date: YYYY-MM-DD format (null if not found)
- expiration_date: YYYY-MM-DD format (null if not found)
- topic_tags: Array of topic keywords (e.g., ["manufacturing", "exemption", "equipment"])
- industries: Array of applicable industries (e.g., ["manufacturing", "aerospace", "food_processing"])
- key_concepts: Array of key legal concepts (e.g., ["sales tax exemption", "direct use in manufacturing"])
- tax_types: Array of tax types mentioned (e.g., ["sales_tax", "use_tax", "B&O_tax"])
- exemption_categories: Array of exemption types (e.g., ["manufacturing", "resale", "interstate_commerce"])
- referenced_statutes: Array of other RCW/WAC cited (e.g., ["RCW 82.04.050", "WAC 458-20-102"])

Return ONLY valid JSON (no markdown, no backticks):
{{
  "citation": "string or null",
  "title": "string or null",
  "document_date": "YYYY-MM-DD or null",
  "effective_date": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "topic_tags": ["array", "of", "tags"],
  "industries": ["array", "of", "industries"],
  "key_concepts": ["array", "of", "concepts"],
  "tax_types": ["array", "of", "tax", "types"],
  "exemption_categories": ["array", "of", "exemption", "types"],
  "referenced_statutes": ["array", "of", "citations"],
  "confidence_score": 0-100
}}"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        metadata = json.loads(result_text)

        print(f"  ✅ Citation: {metadata.get('citation', 'Not found')}")
        print(f"  ✅ Title: {metadata.get('title', 'Not found')[:80]}...")
        print(f"  ✅ Confidence: {metadata.get('confidence_score', 0)}%")

        return metadata

    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return {
            'citation': None,
            'title': None,
            'confidence_score': 0,
            'error': str(e)
        }

def extract_invoice_metadata(file_path, document_text):
    """
    Extract metadata from invoices.

    Returns:
        dict with vendor info, invoice details, line items, etc.
    """
    print(f"\n🧾 Extracting invoice metadata...")

    prompt = f"""You are an invoice data extraction expert.

INVOICE TEXT:
{document_text[:8000]}

TASK: Extract ALL structured data from this invoice with high precision.

Extract these fields:

VENDOR INFORMATION:
- vendor_name: Company name
- vendor_address: Street address
- vendor_city: City
- vendor_state: State (2-letter code)
- vendor_zip: ZIP code

INVOICE DETAILS:
- invoice_number: Invoice/bill number
- invoice_date: YYYY-MM-DD format
- purchase_order_number: PO number (null if not present)
- payment_terms: Payment terms (e.g., "Net 30")

CUSTOMER INFORMATION:
- customer_name: Billing customer name
- bill_to_address: Billing address
- ship_to_address: Shipping address (null if same as billing)
- ship_to_city: Shipping city
- ship_to_state: Shipping state

FINANCIAL TOTALS:
- subtotal: Subtotal before tax
- sales_tax: Sales tax amount charged
- use_tax: Use tax amount (usually 0)
- total_amount: Grand total

LINE ITEMS (array of objects):
For each line item on the invoice, extract:
- line_number: Sequential number (1, 2, 3...)
- item_description: Full description of item/service
- quantity: Quantity (null if not specified)
- unit_price: Price per unit
- line_total: Total for this line
- sales_tax_on_line: Tax for this line (null if not itemized)
- product_code: SKU or product code (null if not present)

Return ONLY valid JSON (no markdown, no backticks):
{{
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "vendor_city": "string or null",
  "vendor_state": "string or null",
  "vendor_zip": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "purchase_order_number": "string or null",
  "payment_terms": "string or null",
  "customer_name": "string or null",
  "bill_to_address": "string or null",
  "ship_to_address": "string or null",
  "ship_to_city": "string or null",
  "ship_to_state": "string or null",
  "subtotal": number or null,
  "sales_tax": number or null,
  "use_tax": number or null,
  "total_amount": number or null,
  "line_items": [
    {{
      "line_number": 1,
      "item_description": "string",
      "quantity": number or null,
      "unit_price": number or null,
      "line_total": number,
      "sales_tax_on_line": number or null,
      "product_code": "string or null"
    }}
  ],
  "confidence_score": 0-100
}}"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        metadata = json.loads(result_text)

        print(f"  ✅ Vendor: {metadata.get('vendor_name', 'Not found')}")
        print(f"  ✅ Invoice #: {metadata.get('invoice_number', 'Not found')}")
        print(f"  ✅ Date: {metadata.get('invoice_date', 'Not found')}")
        print(f"  ✅ Total: ${metadata.get('total_amount', 0):.2f}")
        print(f"  ✅ Sales Tax: ${metadata.get('sales_tax', 0):.2f}")
        print(f"  ✅ Line Items: {len(metadata.get('line_items', []))}")
        print(f"  ✅ Confidence: {metadata.get('confidence_score', 0)}%")

        return metadata

    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return {
            'vendor_name': None,
            'total_amount': None,
            'confidence_score': 0,
            'line_items': [],
            'error': str(e)
        }

def extract_purchase_order_metadata(file_path, document_text):
    """Extract metadata from purchase orders."""
    print(f"\n📋 Extracting purchase order metadata...")

    prompt = f"""You are a purchase order data extraction expert.

PURCHASE ORDER TEXT:
{document_text[:6000]}

TASK: Extract structured data from this purchase order.

Extract these fields:
- po_number: PO number
- po_date: YYYY-MM-DD format
- vendor_name: Vendor/supplier name
- total_amount: Total PO amount (may be estimated)
- items_ordered: Brief summary of items (string, not array)

Return ONLY valid JSON (no markdown, no backticks):
{{
  "po_number": "string or null",
  "po_date": "YYYY-MM-DD or null",
  "vendor_name": "string or null",
  "total_amount": number or null,
  "items_ordered": "string summary",
  "confidence_score": 0-100
}}"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        metadata = json.loads(result_text)

        print(f"  ✅ PO #: {metadata.get('po_number', 'Not found')}")
        print(f"  ✅ Vendor: {metadata.get('vendor_name', 'Not found')}")
        print(f"  ✅ Confidence: {metadata.get('confidence_score', 0)}%")

        return metadata

    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return {'po_number': None, 'confidence_score': 0, 'error': str(e)}

def extract_sow_metadata(file_path, document_text):
    """
    Extract metadata from statements of work.

    CRITICAL: Determines is_primarily_human_effort flag.
    """
    print(f"\n📝 Extracting statement of work metadata...")

    prompt = f"""You are an expert in analyzing service agreements and Washington State tax law.

STATEMENT OF WORK TEXT:
{document_text[:6000]}

TASK: Extract structured data from this statement of work.

CRITICAL ANALYSIS - Primarily Human Effort Test:
Under Washington State law (ESSB 5814 / RCW 82.04.050), services that are "primarily human effort" are NOT subject to sales tax, even if delivered digitally.

Primarily Human Effort = TRUE if:
- Custom services requiring human expertise, judgment, or creativity
- Consulting, professional services, manual labor
- Human-driven analysis, design, or problem-solving
- Services that cannot be automated or standardized

Primarily Human Effort = FALSE if:
- Automated software platforms or SaaS subscriptions
- Pre-built digital products or tools
- Standardized automated services
- Technology platforms with minimal human customization

Extract these fields:
- sow_title: Title or subject of SOW
- sow_date: YYYY-MM-DD format
- vendor_name: Service provider name
- service_description: Detailed description of services
- is_primarily_human_effort: TRUE/FALSE based on analysis above
- human_effort_analysis: Explanation of your determination
- total_contract_value: Total contract amount
- deliverables: Array of key deliverables
- master_agreement_reference: Any reference to master agreement (number, title, etc.)

Return ONLY valid JSON (no markdown, no backticks):
{{
  "sow_title": "string or null",
  "sow_date": "YYYY-MM-DD or null",
  "vendor_name": "string or null",
  "service_description": "detailed string",
  "is_primarily_human_effort": true/false,
  "human_effort_analysis": "explanation of determination",
  "total_contract_value": number or null,
  "deliverables": ["array", "of", "deliverables"],
  "master_agreement_reference": "string or null",
  "confidence_score": 0-100
}}"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        metadata = json.loads(result_text)

        print(f"  ✅ Title: {metadata.get('sow_title', 'Not found')}")
        print(f"  ✅ Vendor: {metadata.get('vendor_name', 'Not found')}")
        print(f"  ⚖️  Primarily Human Effort: {metadata.get('is_primarily_human_effort', 'Unknown')}")
        print(f"  💭 Analysis: {metadata.get('human_effort_analysis', '')[:100]}...")
        print(f"  ✅ Confidence: {metadata.get('confidence_score', 0)}%")

        return metadata

    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return {'sow_title': None, 'confidence_score': 0, 'error': str(e)}

def extract_master_agreement_metadata(file_path, document_text):
    """
    Extract metadata from master agreements.
    """
    print(f"\n📄 Extracting master agreement metadata...")

    prompt = f"""You are an expert in analyzing master service agreements and framework agreements.

MASTER AGREEMENT TEXT:
{document_text[:6000]}

TASK: Extract structured data from this master agreement.

Extract these fields:
- agreement_number: Agreement number or ID
- agreement_title: Title or name of agreement
- agreement_date: YYYY-MM-DD format (signing date)
- effective_date: YYYY-MM-DD format (when it takes effect)
- expiration_date: YYYY-MM-DD format (when it expires)
- vendor_name: Service provider/vendor name
- total_contract_value: Total contract value (if stated)
- agreement_type: Type (e.g., "Master Service Agreement", "Framework Agreement")
- scope_description: High-level scope of what's covered

Return ONLY valid JSON (no markdown, no backticks):
{{
  "agreement_number": "string or null",
  "agreement_title": "string or null",
  "agreement_date": "YYYY-MM-DD or null",
  "effective_date": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "vendor_name": "string or null",
  "total_contract_value": number or null,
  "agreement_type": "string or null",
  "scope_description": "brief description",
  "confidence_score": 0-100
}}"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        metadata = json.loads(result_text)

        print(f"  ✅ Agreement: {metadata.get('agreement_title', 'Not found')}")
        print(f"  ✅ Vendor: {metadata.get('vendor_name', 'Not found')}")
        print(f"  ✅ Confidence: {metadata.get('confidence_score', 0)}%")

        return metadata

    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return {'agreement_number': None, 'confidence_score': 0, 'error': str(e)}

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Extract structured metadata from documents using AI"
    )
    parser.add_argument('--file', required=True, help="Path to document file")
    parser.add_argument(
        '--type',
        required=True,
        choices=['legal', 'invoice', 'purchase_order', 'sow', 'master_agreement'],
        help="Document type"
    )
    parser.add_argument(
        '--document_type',
        required=False,
        help="Specific legal document type (rcw, wac, wtd, eta)"
    )

    args = parser.parse_args()

    # Validate file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        return 1

    print("\n" + "="*70)
    print("METADATA EXTRACTOR")
    print("="*70)
    print(f"\n📄 File: {Path(args.file).name}")
    print(f"📋 Type: {args.type}")

    # Extract text
    try:
        document_text = extract_text_preview(args.file)
        print(f"✅ Extracted {len(document_text)} characters")
    except Exception as e:
        print(f"❌ Failed to extract text: {e}")
        return 1

    # Extract metadata based on type
    if args.type == 'legal':
        doc_type = args.document_type or 'legal'
        metadata = extract_legal_document_metadata(args.file, document_text, doc_type)
    elif args.type == 'invoice':
        metadata = extract_invoice_metadata(args.file, document_text)
    elif args.type == 'purchase_order':
        metadata = extract_purchase_order_metadata(args.file, document_text)
    elif args.type == 'sow':
        metadata = extract_sow_metadata(args.file, document_text)
    elif args.type == 'master_agreement':
        metadata = extract_master_agreement_metadata(args.file, document_text)
    else:
        print(f"❌ Unknown type: {args.type}")
        return 1

    # Print results
    print("\n" + "="*70)
    print("EXTRACTED METADATA")
    print("="*70)
    print(json.dumps(metadata, indent=2))
    print("="*70 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
