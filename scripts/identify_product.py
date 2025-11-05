#!/usr/bin/env python3
"""
Product Identification for Washington State Tax Refund Engine

AI-powered product classification for tax analysis.
Determines: product type, digital vs physical, service vs product, primarily human effort.

Usage:
    python scripts/identify_product.py --line_item_id 1
    python scripts/identify_product.py --invoice_id 1
"""

import argparse
import sys
import os
import sqlite3
import json
from pathlib import Path

# AI
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

def get_database_connection():
    """Get database connection."""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "refund_engine.db"
    return sqlite3.connect(str(db_path))

def identify_product(line_item_id, conn):
    """
    Identify product characteristics for a line item.

    Returns:
        dict with product info
    """
    cursor = conn.cursor()

    # Get line item and invoice details
    cursor.execute("""
        SELECT
            li.item_description,
            li.line_total,
            li.sales_tax_on_line,
            i.vendor_name,
            i.invoice_date,
            i.invoice_number
        FROM invoice_line_items li
        JOIN invoices i ON li.invoice_id = i.id
        WHERE li.id = ?
    """, (line_item_id,))

    row = cursor.fetchone()
    if not row:
        print(f"❌ Line item {line_item_id} not found")
        return None

    item_description, line_total, sales_tax, vendor_name, invoice_date, invoice_number = row

    print(f"\n🔍 Identifying product: {item_description[:80]}...")
    print(f"  Vendor: {vendor_name}")
    print(f"  Amount: ${line_total:.2f}")

    # Build AI prompt for product identification
    prompt = f"""You are a product classification expert specializing in Washington State sales tax analysis.

PRODUCT/SERVICE INFORMATION:
- Description: {item_description}
- Vendor: {vendor_name}
- Amount: ${line_total}
- Sales Tax Charged: ${sales_tax or 0}
- Invoice Date: {invoice_date}
- Invoice Number: {invoice_number}

TASK: Classify this product/service with precision for tax analysis.

CRITICAL CLASSIFICATIONS:

1. PRODUCT NAME: What is this product/service actually called?

2. CATEGORY: Primary category (choose one):
   - software (applications, platforms, SaaS)
   - hardware (physical equipment, computers, machinery)
   - service (consulting, professional services, labor)
   - equipment (tools, machinery, manufacturing equipment)
   - supplies (office supplies, consumables)
   - digital_content (ebooks, downloads, digital media)
   - subscription (recurring service or software access)
   - construction (building, installation services)
   - agriculture (farming equipment, agricultural products)
   - other

3. IS_DIGITAL: Is this delivered/accessed electronically? (true/false)
   - True: Software, SaaS, digital downloads, online services
   - False: Physical products, in-person services, tangible goods

4. IS_SERVICE: Is this a service rather than a product? (true/false)
   - True: Consulting, labor, professional services, custom work
   - False: Products, software licenses, tangible goods

5. PRIMARILY_HUMAN_EFFORT (CRITICAL FOR WA TAX LAW):
   This determines taxability under ESSB 5814 / RCW 82.04.050

   TRUE (not taxable) if service is:
   - Custom consulting requiring human expertise
   - Professional services (legal, accounting, engineering)
   - Manual labor or human-performed work
   - Creative services (design, writing, analysis)
   - Personalized training or education
   - Human-driven problem solving

   FALSE (potentially taxable) if:
   - Automated software platform or SaaS
   - Pre-built software with minimal customization
   - Automated services with no human customization
   - Software subscriptions
   - Platform access fees

   IMPORTANT: This field is ONLY relevant if is_service = true
   For non-services (products), set to null

6. AUTOMATION_LEVEL:
   - high: Fully automated, no human involvement
   - medium: Some automation but human oversight/customization
   - low: Primarily manual/human work
   - null: Not applicable (physical product)

7. CONFIDENCE: How confident are you? (0-100)
   - 90-100: Very clear from description
   - 70-89: Reasonably confident
   - 50-69: Some uncertainty
   - <50: Need more information

Return ONLY valid JSON (no markdown, no backticks):
{{
  "product_name": "specific product name",
  "product_category": "category from list above",
  "is_digital": true/false,
  "is_service": true/false,
  "primarily_human_effort": true/false/null,
  "automation_level": "high/medium/low/null",
  "confidence_score": 0-100,
  "reasoning": "detailed explanation of your classification",
  "evidence": ["key", "features", "that", "informed", "decision"]
}}"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        product_info = json.loads(result_text)

        confidence = product_info.get('confidence_score', 0)

        print(f"  ✅ Product: {product_info.get('product_name', 'Unknown')}")
        print(f"  📦 Category: {product_info.get('product_category', 'Unknown')}")
        print(f"  💻 Digital: {product_info.get('is_digital', False)}")
        print(f"  🔧 Service: {product_info.get('is_service', False)}")
        print(f"  👤 Primarily Human Effort: {product_info.get('primarily_human_effort', 'N/A')}")
        print(f"  🎯 Confidence: {confidence}%")

        # If confidence is low, could implement web search here
        # For now, we'll skip that and just flag low confidence

        if confidence < 70:
            print(f"  ⚠️  Low confidence - may need manual review")

        # Insert into product_identifications table
        cursor.execute("""
            INSERT INTO product_identifications (
                line_item_id, product_name, product_category, is_digital,
                is_service, primarily_human_effort, automation_level,
                confidence_score, web_search_used, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            line_item_id,
            product_info.get('product_name'),
            product_info.get('product_category'),
            product_info.get('is_digital'),
            product_info.get('is_service'),
            product_info.get('primarily_human_effort'),
            product_info.get('automation_level'),
            confidence,
            False,  # web_search_used
            json.dumps({
                'reasoning': product_info.get('reasoning', ''),
                'evidence': product_info.get('evidence', [])
            })
        ))

        # Update invoice_line_items with classification
        cursor.execute("""
            UPDATE invoice_line_items
            SET
                product_category = ?,
                is_digital = ?,
                is_service = ?,
                primarily_human_effort = ?
            WHERE id = ?
        """, (
            product_info.get('product_category'),
            product_info.get('is_digital'),
            product_info.get('is_service'),
            product_info.get('primarily_human_effort'),
            line_item_id
        ))

        conn.commit()

        return product_info

    except Exception as e:
        print(f"  ❌ Identification failed: {e}")
        conn.rollback()
        return None

def batch_identify_products(invoice_id, conn):
    """Identify all products on an invoice."""
    print(f"\n📊 Processing all line items for invoice ID {invoice_id}...")

    cursor = conn.cursor()

    # Get all line items
    cursor.execute("""
        SELECT id, item_description
        FROM invoice_line_items
        WHERE invoice_id = ?
    """, (invoice_id,))

    line_items = cursor.fetchall()

    print(f"  Found {len(line_items)} line items\n")

    results = []
    for line_item_id, description in line_items:
        print(f"\n--- Line Item {line_item_id} ---")
        result = identify_product(line_item_id, conn)
        if result:
            results.append(result)

    print("\n" + "="*70)
    print("BATCH IDENTIFICATION SUMMARY")
    print("="*70)
    print(f"\n✅ Identified: {len(results)} / {len(line_items)} line items")

    # Category breakdown
    categories = {}
    for r in results:
        cat = r.get('product_category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n📦 Category Breakdown:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}")

    # Service analysis
    services = [r for r in results if r.get('is_service')]
    if services:
        human_effort_services = [s for s in services if s.get('primarily_human_effort')]
        print(f"\n🔧 Service Analysis:")
        print(f"  Total services: {len(services)}")
        print(f"  Primarily human effort: {len(human_effort_services)}")
        print(f"  Automated services: {len(services) - len(human_effort_services)}")

    print("\n" + "="*70 + "\n")

    return results

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Identify product characteristics for tax analysis"
    )
    parser.add_argument('--line_item_id', type=int, help="Specific line item ID")
    parser.add_argument('--invoice_id', type=int, help="Process all items on invoice")

    args = parser.parse_args()

    if not args.line_item_id and not args.invoice_id:
        print("❌ Error: Must specify either --line_item_id or --invoice_id")
        return 1

    print("\n" + "="*70)
    print("PRODUCT IDENTIFICATION")
    print("="*70)

    conn = get_database_connection()

    if args.line_item_id:
        identify_product(args.line_item_id, conn)
    elif args.invoice_id:
        batch_identify_products(args.invoice_id, conn)

    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
