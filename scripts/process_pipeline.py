#!/usr/bin/env python3
"""
Full Processing Pipeline for Washington State Tax Refund Engine

Orchestrates end-to-end processing: ingest → identify → analyze → report

Usage:
    python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Import all pipeline components
from ingest_client_docs import batch_process_uploads
from identify_product import batch_identify_products, get_database_connection
from analyze_refund import batch_analyze_invoice
from generate_client_report import generate_client_refund_report
from generate_dor_filing import generate_dor_filing_worksheet
from generate_internal_workbook import generate_internal_analysis_workbook

def print_banner():
    """Print pipeline banner."""
    print("\n" + "="*70)
    print("  WASHINGTON STATE TAX REFUND ENGINE")
    print("  Full Processing Pipeline")
    print("="*70 + "\n")

def run_full_pipeline(client_id, invoice_folder_path=None):
    """
    Run the full end-to-end processing pipeline.

    Args:
        client_id: Client ID
        invoice_folder_path: Optional path to invoice folder (if new documents to ingest)
    """
    print_banner()

    start_time = datetime.now()

    # STEP 1: Ingest documents (if folder provided)
    if invoice_folder_path and os.path.exists(invoice_folder_path):
        print("\n" + "🔹"*35)
        print("STEP 1: INGESTING CLIENT DOCUMENTS")
        print("🔹"*35 + "\n")

        batch_process_uploads(invoice_folder_path, client_id)
    else:
        print("\n⏭️  Skipping document ingestion (no folder provided or already ingested)")

    # Get all invoices for this client
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM invoices WHERE client_id = ? ORDER BY id", (client_id,))
    invoice_ids = [row[0] for row in cursor.fetchall()]

    if not invoice_ids:
        print(f"\n❌ No invoices found for client {client_id}")
        print("   Please run document ingestion first.")
        conn.close()
        return

    print(f"\n✅ Found {len(invoice_ids)} invoices to process")

    # STEP 2: Identify products
    print("\n" + "🔹"*35)
    print("STEP 2: IDENTIFYING PRODUCTS")
    print("🔹"*35 + "\n")

    for invoice_id in invoice_ids:
        print(f"\n📦 Processing Invoice ID {invoice_id}...")
        batch_identify_products(invoice_id, conn)

    # STEP 3: Analyze refunds
    print("\n" + "🔹"*35)
    print("STEP 3: ANALYZING REFUND ELIGIBILITY")
    print("🔹"*35 + "\n")

    for invoice_id in invoice_ids:
        print(f"\n⚖️  Analyzing Invoice ID {invoice_id}...")
        batch_analyze_invoice(invoice_id, conn)

    conn.close()

    # STEP 4: Generate reports
    print("\n" + "🔹"*35)
    print("STEP 4: GENERATING REPORTS")
    print("🔹"*35 + "\n")

    print("\n1️⃣  Generating Client Report...")
    client_report = generate_client_refund_report(client_id)

    print("\n2️⃣  Generating DOR Filing Worksheet...")
    dor_filing = generate_dor_filing_worksheet(client_id)

    print("\n3️⃣  Generating Internal Analysis Workbook...")
    internal_workbook = generate_internal_analysis_workbook(client_id)

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Get final stats
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(CASE WHEN ra.potentially_eligible = 1 THEN 1 END) as eligible_count,
            SUM(CASE WHEN ra.potentially_eligible = 1 THEN ra.estimated_refund_amount ELSE 0 END) as total_refund
        FROM refund_analysis ra
        JOIN invoices i ON ra.invoice_id = i.id
        WHERE i.client_id = ?
    """, (client_id,))

    eligible_count, total_refund = cursor.fetchone()
    conn.close()

    print("\n" + "="*70)
    print("  🎉 PIPELINE COMPLETE")
    print("="*70)

    print(f"\n📊 SUMMARY:")
    print(f"  ⏱️  Processing Time: {duration:.1f} seconds")
    print(f"  📄 Invoices Processed: {len(invoice_ids)}")
    print(f"  ✅ Eligible Line Items: {eligible_count or 0}")
    print(f"  💰 Total Potential Refund: ${total_refund or 0:,.2f}")

    print(f"\n📁 GENERATED REPORTS:")
    if client_report:
        print(f"  📊 Client Report: {client_report}")
    if dor_filing:
        print(f"  📋 DOR Filing: {dor_filing}")
    if internal_workbook:
        print(f"  📈 Internal Analysis: {internal_workbook}")

    print("\n" + "="*70)
    print("✨ All done! Review the reports in the outputs/ directory.")
    print("="*70 + "\n")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Run full refund analysis pipeline"
    )
    parser.add_argument(
        '--client_id',
        required=True,
        type=int,
        help="Client ID"
    )
    parser.add_argument(
        '--invoices',
        required=False,
        help="Optional path to invoices folder (if ingesting new documents)"
    )

    args = parser.parse_args()

    # Validate invoice folder if provided
    if args.invoices and not os.path.exists(args.invoices):
        print(f"❌ Error: Invoice folder not found: {args.invoices}")
        return 1

    # Run pipeline
    run_full_pipeline(args.client_id, args.invoices)

    return 0

if __name__ == "__main__":
    sys.exit(main())
