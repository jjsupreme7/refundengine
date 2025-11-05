#!/usr/bin/env python3
"""
Document Linking for Washington State Tax Refund Engine

Intelligently links related documents in 4-level hierarchy:
- Invoices → Purchase Orders (by PO number)
- Invoices → Statements of Work (by vendor, dates, descriptions)
- SOWs → Master Agreements (by agreement references and vendor matching)

Hierarchy: Master Agreement → (SOW, PO) → Invoice

Usage:
    python scripts/link_documents.py --client_id 1
    python scripts/link_documents.py --client_id 1 --relink
    python scripts/link_documents.py --client_id 1 --view
"""

import argparse
import sys
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

# AI
from anthropic import Anthropic
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

def get_database_connection():
    """Get database connection."""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "refund_engine.db"
    return sqlite3.connect(str(db_path))

def link_invoice_to_po(invoice_id, conn):
    """
    Link invoice to purchase order by PO number.

    Returns:
        dict with linking result
    """
    cursor = conn.cursor()

    # Get invoice PO number
    cursor.execute("""
        SELECT purchase_order_number, vendor_name, invoice_number
        FROM invoices
        WHERE id = ?
    """, (invoice_id,))

    result = cursor.fetchone()
    if not result or not result[0]:
        return {'success': False, 'reason': 'No PO number on invoice'}

    po_number, vendor, invoice_num = result

    print(f"\n🔗 Linking Invoice {invoice_num} (PO: {po_number})")

    # Find matching PO
    cursor.execute("""
        SELECT cd.id, po.id, po.vendor_name
        FROM purchase_orders po
        JOIN client_documents cd ON po.client_document_id = cd.id
        WHERE po.po_number = ? OR po.po_number LIKE ?
    """, (po_number, f"%{po_number}%"))

    matches = cursor.fetchall()

    if not matches:
        print(f"  ⚠️  No matching PO found for: {po_number}")
        return {'success': False, 'reason': f'PO {po_number} not found'}

    # Get invoice's client_document_id
    cursor.execute("""
        SELECT client_document_id FROM invoices WHERE id = ?
    """, (invoice_id,))
    invoice_doc_id = cursor.fetchone()[0]

    # Link to first match (or all if multiple)
    for po_doc_id, po_id, po_vendor in matches:
        # Check if relationship already exists
        cursor.execute("""
            SELECT id FROM document_relationships
            WHERE source_document_id = ? AND target_document_id = ?
        """, (invoice_doc_id, po_doc_id))

        if cursor.fetchone():
            print(f"  ✓ Already linked to PO (vendor: {po_vendor})")
            continue

        # Create relationship
        cursor.execute("""
            INSERT INTO document_relationships (
                source_document_id, source_document_type,
                target_document_id, target_document_type,
                relationship_type, confidence_score, matched_reference, matching_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_doc_id, 'invoice',
            po_doc_id, 'purchase_order',
            'invoice_references_po',
            100,  # Exact PO number match
            po_number,
            'po_number_match'
        ))

        print(f"  ✅ Linked to PO (vendor: {po_vendor})")

    conn.commit()
    return {'success': True, 'po_number': po_number}

def link_invoice_to_sow(invoice_id, conn):
    """
    Link invoice to statement of work using AI analysis.

    Matches by: vendor, date range, service descriptions
    """
    cursor = conn.cursor()

    # Get invoice details
    cursor.execute("""
        SELECT
            i.invoice_number, i.vendor_name, i.invoice_date,
            GROUP_CONCAT(li.item_description, ' | ') as descriptions
        FROM invoices i
        LEFT JOIN invoice_line_items li ON i.id = li.invoice_id
        WHERE i.id = ?
        GROUP BY i.id
    """, (invoice_id,))

    invoice_data = cursor.fetchone()
    if not invoice_data:
        return {'success': False, 'reason': 'Invoice not found'}

    invoice_num, vendor, invoice_date, descriptions = invoice_data

    print(f"\n🔗 Finding SOW for Invoice {invoice_num}")
    print(f"  Vendor: {vendor}")
    print(f"  Date: {invoice_date}")

    # Get all SOWs for same vendor (or similar)
    cursor.execute("""
        SELECT
            cd.id, sow.id, sow.sow_title, sow.sow_date,
            sow.vendor_name, sow.service_description
        FROM statements_of_work sow
        JOIN client_documents cd ON sow.client_document_id = cd.id
        WHERE sow.vendor_name LIKE ?
    """, (f"%{vendor}%",))

    sows = cursor.fetchall()

    if not sows:
        print(f"  ⚠️  No SOWs found for vendor: {vendor}")
        return {'success': False, 'reason': 'No matching SOWs'}

    print(f"  📋 Found {len(sows)} potential SOW(s)")

    # Use AI to match invoice to best SOW
    prompt = f"""You are an expert at matching invoices to statements of work.

INVOICE INFORMATION:
- Invoice Number: {invoice_num}
- Vendor: {vendor}
- Date: {invoice_date}
- Line Items: {descriptions[:500]}

AVAILABLE STATEMENTS OF WORK:
"""

    for i, (doc_id, sow_id, title, date, sow_vendor, desc) in enumerate(sows, 1):
        prompt += f"""
SOW {i}:
- Title: {title}
- Vendor: {sow_vendor}
- Date: {date}
- Description: {desc[:300]}
---
"""

    prompt += """
TASK: Determine which SOW (if any) this invoice is billing work for.

Consider:
- Vendor match (exact or similar company name)
- Date proximity (invoice after SOW)
- Service descriptions (does invoice work match SOW scope?)
- Project/engagement names

Return ONLY valid JSON (no markdown):
{
  "matches": [
    {
      "sow_index": 1,
      "confidence": 85,
      "reasoning": "explanation"
    }
  ]
}

If no good match, return {"matches": []}
"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        analysis = json.loads(result_text)

        # Get invoice's client_document_id
        cursor.execute("""
            SELECT client_document_id FROM invoices WHERE id = ?
        """, (invoice_id,))
        invoice_doc_id = cursor.fetchone()[0]

        linked_count = 0
        for match in analysis.get('matches', []):
            sow_index = match['sow_index'] - 1  # Convert to 0-based
            confidence = match['confidence']
            reasoning = match['reasoning']

            if confidence < 60:
                print(f"  ⚠️  Low confidence match to SOW {match['sow_index']}: {confidence}%")
                continue

            # Get SOW document ID
            sow_doc_id = sows[sow_index][0]
            sow_title = sows[sow_index][2]

            # Check if relationship already exists
            cursor.execute("""
                SELECT id FROM document_relationships
                WHERE source_document_id = ? AND target_document_id = ?
            """, (invoice_doc_id, sow_doc_id))

            if cursor.fetchone():
                print(f"  ✓ Already linked to SOW: {sow_title}")
                continue

            # Create relationship
            cursor.execute("""
                INSERT INTO document_relationships (
                    source_document_id, source_document_type,
                    target_document_id, target_document_type,
                    relationship_type, confidence_score, matched_reference, matching_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_doc_id, 'invoice',
                sow_doc_id, 'statement_of_work',
                'invoice_bills_sow',
                confidence,
                reasoning[:200],
                'ai_semantic_match'
            ))

            print(f"  ✅ Linked to SOW: {sow_title} (confidence: {confidence}%)")
            linked_count += 1

        conn.commit()

        if linked_count == 0:
            print(f"  ℹ️  No high-confidence SOW matches found")
            return {'success': False, 'reason': 'No confident matches'}

        return {'success': True, 'linked_count': linked_count}

    except Exception as e:
        print(f"  ❌ AI matching failed: {e}")
        return {'success': False, 'reason': str(e)}

def link_sow_to_master_agreement(sow_id, conn):
    """
    Link statement of work to master agreement.

    Matches by: master_agreement_reference field and vendor matching
    """
    cursor = conn.cursor()

    # Get SOW details
    cursor.execute("""
        SELECT
            sow.id, cd.id, sow.sow_title, sow.vendor_name,
            sow.sow_date, sow.master_agreement_reference
        FROM statements_of_work sow
        JOIN client_documents cd ON sow.client_document_id = cd.id
        WHERE sow.id = ?
    """, (sow_id,))

    sow_data = cursor.fetchone()
    if not sow_data:
        return {'success': False, 'reason': 'SOW not found'}

    sow_id, sow_doc_id, sow_title, vendor, sow_date, ma_ref = sow_data

    print(f"\n🔗 Finding Master Agreement for SOW: {sow_title}")
    print(f"  Vendor: {vendor}")
    print(f"  MA Reference: {ma_ref or 'None'}")

    # Get all master agreements for same vendor
    cursor.execute("""
        SELECT
            cd.id, ma.id, ma.agreement_number, ma.agreement_title,
            ma.vendor_name, ma.agreement_date
        FROM master_agreements ma
        JOIN client_documents cd ON ma.client_document_id = cd.id
        WHERE ma.vendor_name LIKE ?
    """, (f"%{vendor}%",))

    mas = cursor.fetchall()

    if not mas:
        print(f"  ⚠️  No Master Agreements found for vendor: {vendor}")
        return {'success': False, 'reason': 'No matching MAs'}

    print(f"  📜 Found {len(mas)} potential Master Agreement(s)")

    # Try exact reference match first
    if ma_ref:
        for ma_doc_id, ma_id, ma_num, ma_title, ma_vendor, ma_date in mas:
            # Check if SOW's reference matches MA number or title
            if ma_ref in str(ma_num) or (ma_title and ma_ref in ma_title):
                # Check if relationship already exists
                cursor.execute("""
                    SELECT id FROM document_relationships
                    WHERE source_document_id = ? AND target_document_id = ?
                """, (sow_doc_id, ma_doc_id))

                if cursor.fetchone():
                    print(f"  ✓ Already linked to MA: {ma_title}")
                    return {'success': True, 'already_linked': True}

                # Create relationship with 100% confidence (exact reference match)
                cursor.execute("""
                    INSERT INTO document_relationships (
                        source_document_id, source_document_type,
                        target_document_id, target_document_type,
                        relationship_type, confidence_score, matched_reference, matching_method
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sow_doc_id, 'statement_of_work',
                    ma_doc_id, 'master_agreement',
                    'sow_under_master_agreement',
                    100,  # Exact reference match
                    f"Reference: {ma_ref}",
                    'agreement_reference_match'
                ))

                conn.commit()
                print(f"  ✅ Linked to MA: {ma_title} (exact reference match)")
                return {'success': True, 'ma_title': ma_title}

    # If no exact match, use AI for semantic matching
    prompt = f"""You are an expert at matching statements of work to master agreements.

SOW INFORMATION:
- Title: {sow_title}
- Vendor: {vendor}
- Date: {sow_date}
- MA Reference in SOW: {ma_ref or 'None'}

AVAILABLE MASTER AGREEMENTS:
"""

    for i, (doc_id, ma_id, ma_num, ma_title, ma_vendor, ma_date) in enumerate(mas, 1):
        prompt += f"""
MA {i}:
- Agreement Number: {ma_num}
- Title: {ma_title}
- Vendor: {ma_vendor}
- Date: {ma_date}
---
"""

    prompt += """
TASK: Determine which Master Agreement (if any) this SOW operates under.

Consider:
- Vendor match (exact or similar company name)
- Date (SOW should be after MA date)
- Agreement references
- Project scope alignment

Return ONLY valid JSON (no markdown):
{
  "matches": [
    {
      "ma_index": 1,
      "confidence": 85,
      "reasoning": "explanation"
    }
  ]
}

If no good match, return {"matches": []}
"""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        analysis = json.loads(result_text)

        for match in analysis.get('matches', []):
            ma_index = match['ma_index'] - 1  # Convert to 0-based
            confidence = match['confidence']
            reasoning = match['reasoning']

            if confidence < 70:  # Higher threshold for MA linking
                print(f"  ⚠️  Low confidence match to MA {match['ma_index']}: {confidence}%")
                continue

            # Get MA document ID
            ma_doc_id = mas[ma_index][0]
            ma_title = mas[ma_index][3]

            # Check if relationship already exists
            cursor.execute("""
                SELECT id FROM document_relationships
                WHERE source_document_id = ? AND target_document_id = ?
            """, (sow_doc_id, ma_doc_id))

            if cursor.fetchone():
                print(f"  ✓ Already linked to MA: {ma_title}")
                continue

            # Create relationship
            cursor.execute("""
                INSERT INTO document_relationships (
                    source_document_id, source_document_type,
                    target_document_id, target_document_type,
                    relationship_type, confidence_score, matched_reference, matching_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sow_doc_id, 'statement_of_work',
                ma_doc_id, 'master_agreement',
                'sow_under_master_agreement',
                confidence,
                reasoning[:200],
                'ai_semantic_match'
            ))

            conn.commit()
            print(f"  ✅ Linked to MA: {ma_title} (confidence: {confidence}%)")
            return {'success': True, 'ma_title': ma_title}

        print(f"  ℹ️  No high-confidence MA matches found")
        return {'success': False, 'reason': 'No confident matches'}

    except Exception as e:
        print(f"  ❌ AI matching failed: {e}")
        return {'success': False, 'reason': str(e)}

def link_all_documents_for_client(client_id, conn, relink=False):
    """
    Link all documents for a client.

    Args:
        client_id: Client ID
        relink: If True, clear existing links and re-link
    """
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"DOCUMENT LINKING - Client ID {client_id}")
    print(f"{'='*70}\n")

    # Clear existing links if relinking
    if relink:
        print("🔄 Clearing existing links...")
        cursor.execute("""
            DELETE FROM document_relationships
            WHERE source_document_id IN (
                SELECT id FROM client_documents WHERE client_id = ?
            )
        """, (client_id,))
        conn.commit()
        print("  ✅ Existing links cleared\n")

    # Get all invoices for client
    cursor.execute("""
        SELECT id, invoice_number FROM invoices WHERE client_id = ?
    """, (client_id,))

    invoices = cursor.fetchall()

    if not invoices:
        print("⚠️  No invoices found for this client")
        return

    print(f"📄 Processing {len(invoices)} invoices...\n")

    stats = {
        'po_links': 0,
        'sow_links': 0,
        'ma_links': 0,
        'failed': 0
    }

    for invoice_id, invoice_num in invoices:
        print(f"{'─'*70}")
        print(f"Invoice: {invoice_num}")

        # Link to PO
        po_result = link_invoice_to_po(invoice_id, conn)
        if po_result['success']:
            stats['po_links'] += 1

        # Link to SOW
        sow_result = link_invoice_to_sow(invoice_id, conn)
        if sow_result['success']:
            stats['sow_links'] += sow_result.get('linked_count', 1)

    # Link SOWs to Master Agreements
    print(f"\n{'─'*70}")
    print(f"{'─'*70}")
    print(f"\n📝 Processing SOWs for Master Agreement linking...\n")

    cursor.execute("""
        SELECT id, sow_title FROM statements_of_work
        WHERE client_id = ?
    """, (client_id,))

    sows = cursor.fetchall()

    if sows:
        print(f"📝 Found {len(sows)} SOW(s) to link\n")
        for sow_id, sow_title in sows:
            print(f"{'─'*70}")
            print(f"SOW: {sow_title}")

            ma_result = link_sow_to_master_agreement(sow_id, conn)
            if ma_result['success'] and not ma_result.get('already_linked'):
                stats['ma_links'] += 1
    else:
        print("  ℹ️  No SOWs found to link to Master Agreements\n")

    # Print summary
    print(f"\n{'='*70}")
    print("LINKING SUMMARY")
    print(f"{'='*70}\n")
    print(f"📊 Statistics:")
    print(f"  Invoice → PO Links: {stats['po_links']}")
    print(f"  Invoice → SOW Links: {stats['sow_links']}")
    print(f"  SOW → Master Agreement Links: {stats['ma_links']}")
    print(f"  Total Relationships Created: {stats['po_links'] + stats['sow_links'] + stats['ma_links']}")
    print(f"\n{'='*70}\n")

def view_relationships(client_id, conn):
    """View all document relationships for a client."""
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"DOCUMENT RELATIONSHIPS - Client ID {client_id}")
    print(f"{'='*70}\n")

    cursor.execute("""
        SELECT
            dr.relationship_type,
            dr.confidence_score,
            dr.matched_reference,
            src_doc.filename as source_file,
            src_doc.document_type as source_type,
            tgt_doc.filename as target_file,
            tgt_doc.document_type as target_type
        FROM document_relationships dr
        JOIN client_documents src_doc ON dr.source_document_id = src_doc.id
        JOIN client_documents tgt_doc ON dr.target_document_id = tgt_doc.id
        WHERE src_doc.client_id = ?
        ORDER BY dr.relationship_type, dr.created_date
    """, (client_id,))

    relationships = cursor.fetchall()

    if not relationships:
        print("ℹ️  No document relationships found")
        print("   Run: python scripts/link_documents.py --client_id 1")
        return

    # Group by relationship type
    by_type = {}
    for rel in relationships:
        rel_type = rel[0]
        if rel_type not in by_type:
            by_type[rel_type] = []
        by_type[rel_type].append(rel)

    # Display grouped
    for rel_type, rels in by_type.items():
        print(f"📋 {rel_type.upper().replace('_', ' ')}")
        print(f"   ({len(rels)} relationships)\n")

        for rel in rels:
            _, confidence, reference, src_file, src_type, tgt_file, tgt_type = rel
            print(f"  {src_file}")
            print(f"    └─→ {tgt_file}")
            print(f"        Confidence: {confidence}%")
            if reference:
                print(f"        Reference: {reference[:60]}...")
            print()

    print(f"{'='*70}\n")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Link related documents (invoices ↔ POs, invoices ↔ SOWs)"
    )
    parser.add_argument('--client_id', required=True, type=int, help="Client ID")
    parser.add_argument('--relink', action='store_true', help="Clear and re-link all documents")
    parser.add_argument('--view', action='store_true', help="View existing relationships")

    args = parser.parse_args()

    conn = get_database_connection()

    if args.view:
        view_relationships(args.client_id, conn)
    else:
        link_all_documents_for_client(args.client_id, conn, args.relink)

    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
