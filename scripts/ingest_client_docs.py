#!/usr/bin/env python3
"""
Client Documents Ingestion for Washington State Tax Refund Engine

Process client documents with auto-detection and organization.
AI automatically classifies invoices, POs, SOWs, and other documents.

Usage:
    python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1
"""

import argparse
import sys
import os
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Import our utilities
sys.path.insert(0, str(Path(__file__).parent))
from document_classifier import extract_text_preview, get_file_metadata, detect_document_type
from metadata_extractor import (
    extract_invoice_metadata,
    extract_purchase_order_metadata,
    extract_sow_metadata
)

from dotenv import load_dotenv
load_dotenv()

def get_database_connection():
    """Get database connection."""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "refund_engine.db"
    return sqlite3.connect(str(db_path))

def get_organized_folder(document_type, client_name):
    """Get organized folder path for document type."""
    project_root = Path(__file__).parent.parent
    base = project_root / "client_documents"

    folder_map = {
        'invoice': base / "invoices" / client_name,
        'purchase_order': base / "purchase_orders" / client_name,
        'statement_of_work': base / "statements_of_work" / client_name,
        'contract': base / "supporting_docs" / client_name / "contracts",
        'receipt': base / "supporting_docs" / client_name / "receipts",
        'other': base / "supporting_docs" / client_name / "other"
    }

    folder = folder_map.get(document_type, base / "supporting_docs" / client_name / "uncategorized")
    folder.mkdir(parents=True, exist_ok=True)

    return folder

def process_invoice(client_document_id, file_path, text, client_id, conn):
    """Process invoice and insert into database."""
    try:
        # Extract invoice metadata
        metadata = extract_invoice_metadata(file_path, text)

        if metadata.get('confidence_score', 0) < 30:
            return {
                'success': False,
                'reason': f"Low extraction confidence ({metadata.get('confidence_score', 0)}%)"
            }

        # Insert into invoices table
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (
                client_id, client_document_id, filename, file_path,
                vendor_name, vendor_address, vendor_city, vendor_state, vendor_zip,
                invoice_date, invoice_number, purchase_order_number,
                total_amount, sales_tax_charged, use_tax_charged,
                customer_name, ship_to_address, ship_to_city, ship_to_state,
                bill_to_address, payment_terms, raw_extracted_text, extraction_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            client_document_id,
            Path(file_path).name,
            str(file_path),
            metadata.get('vendor_name'),
            metadata.get('vendor_address'),
            metadata.get('vendor_city'),
            metadata.get('vendor_state'),
            metadata.get('vendor_zip'),
            metadata.get('invoice_date'),
            metadata.get('invoice_number'),
            metadata.get('purchase_order_number'),
            metadata.get('total_amount'),
            metadata.get('sales_tax'),
            metadata.get('use_tax', 0),
            metadata.get('customer_name'),
            metadata.get('ship_to_address'),
            metadata.get('ship_to_city'),
            metadata.get('ship_to_state'),
            metadata.get('bill_to_address'),
            metadata.get('payment_terms'),
            text[:10000],
            metadata.get('confidence_score')
        ))

        invoice_id = cursor.lastrowid

        # Insert line items
        line_items = metadata.get('line_items', [])
        for item in line_items:
            cursor.execute("""
                INSERT INTO invoice_line_items (
                    invoice_id, line_number, item_description, quantity,
                    unit_price, line_total, sales_tax_on_line, product_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                item.get('line_number'),
                item.get('item_description'),
                item.get('quantity'),
                item.get('unit_price'),
                item.get('line_total'),
                item.get('sales_tax_on_line'),
                item.get('product_code')
            ))

        conn.commit()

        return {
            'success': True,
            'invoice_id': invoice_id,
            'line_items': len(line_items),
            'total': metadata.get('total_amount', 0)
        }

    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'reason': str(e)
        }

def process_purchase_order(client_document_id, file_path, text, client_id, conn):
    """Process purchase order and insert into database."""
    try:
        metadata = extract_purchase_order_metadata(file_path, text)

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO purchase_orders (
                client_id, client_document_id, po_number, po_date,
                vendor_name, total_amount, items_ordered
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            client_document_id,
            metadata.get('po_number'),
            metadata.get('po_date'),
            metadata.get('vendor_name'),
            metadata.get('total_amount'),
            metadata.get('items_ordered')
        ))

        po_id = cursor.lastrowid
        conn.commit()

        return {
            'success': True,
            'po_id': po_id
        }

    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'reason': str(e)
        }

def process_sow(client_document_id, file_path, text, client_id, conn):
    """Process statement of work and insert into database."""
    try:
        metadata = extract_sow_metadata(file_path, text)

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO statements_of_work (
                client_id, client_document_id, sow_title, sow_date,
                vendor_name, service_description, is_primarily_human_effort,
                total_contract_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            client_document_id,
            metadata.get('sow_title'),
            metadata.get('sow_date'),
            metadata.get('vendor_name'),
            metadata.get('service_description'),
            metadata.get('is_primarily_human_effort'),
            metadata.get('total_contract_value')
        ))

        sow_id = cursor.lastrowid
        conn.commit()

        return {
            'success': True,
            'sow_id': sow_id,
            'primarily_human_effort': metadata.get('is_primarily_human_effort')
        }

    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'reason': str(e)
        }

def process_client_document(file_path, client_id, conn):
    """Process a single client document through the full pipeline."""
    try:
        filename = Path(file_path).name

        # Get file metadata
        file_meta = get_file_metadata(file_path)

        # Check for duplicates
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, document_type FROM client_documents WHERE content_hash = ? AND client_id = ?",
            (file_meta['content_hash'], client_id)
        )
        existing = cursor.fetchone()
        if existing:
            return {
                'success': False,
                'filename': filename,
                'reason': f"Duplicate (already processed)"
            }

        # Extract text
        text = extract_text_preview(file_path)

        if not text or len(text) < 20:
            return {
                'success': False,
                'filename': filename,
                'reason': "Insufficient text extracted"
            }

        # Classify document (no folder hint - pure AI classification)
        classification = detect_document_type(file_path, folder_hint=None)

        if classification['confidence'] < 40:
            # Still process but mark as uncertain
            doc_type = 'other'
            confidence = classification['confidence']
        else:
            doc_type = classification['document_type']
            confidence = classification['confidence']

        # Get client name for organized folder
        cursor.execute("SELECT client_name FROM clients WHERE id = ?", (client_id,))
        client_result = cursor.fetchone()
        client_name = client_result[0] if client_result else f"client_{client_id}"

        # Insert into client_documents table
        cursor.execute("""
            INSERT INTO client_documents (
                client_id, document_type, filename, file_path, file_format,
                file_size_bytes, processed, processing_status, classification_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            doc_type,
            filename,
            str(file_path),
            file_meta['file_format'],
            file_meta['file_size_bytes'],
            0,  # Not yet fully processed
            'classified',
            confidence
        ))

        client_document_id = cursor.lastrowid
        conn.commit()

        # Route to appropriate handler
        handler_result = {'success': True}

        if doc_type == 'invoice':
            handler_result = process_invoice(client_document_id, file_path, text, client_id, conn)
        elif doc_type == 'purchase_order':
            handler_result = process_purchase_order(client_document_id, file_path, text, client_id, conn)
        elif doc_type == 'statement_of_work':
            handler_result = process_sow(client_document_id, file_path, text, client_id, conn)
        # contract, receipt, other - just keep in client_documents

        if handler_result['success']:
            # Update processing status
            cursor.execute("""
                UPDATE client_documents
                SET processed = 1, processing_status = 'completed'
                WHERE id = ?
            """, (client_document_id,))
            conn.commit()

            # Move file to organized folder
            organized_folder = get_organized_folder(doc_type, client_name)
            new_path = organized_folder / filename

            # Handle filename conflicts
            counter = 1
            while new_path.exists():
                stem = Path(filename).stem
                ext = Path(filename).suffix
                new_path = organized_folder / f"{stem}_{counter}{ext}"
                counter += 1

            shutil.copy2(file_path, new_path)

            # Update file path in database
            cursor.execute("""
                UPDATE client_documents SET file_path = ? WHERE id = ?
            """, (str(new_path), client_document_id))

            cursor.execute("""
                UPDATE invoices SET file_path = ? WHERE client_document_id = ?
            """, (str(new_path), client_document_id))

            conn.commit()

        else:
            # Update with error
            cursor.execute("""
                UPDATE client_documents
                SET processing_status = 'error', error_message = ?
                WHERE id = ?
            """, (handler_result.get('reason', 'Unknown error'), client_document_id))
            conn.commit()

        return {
            'success': handler_result['success'],
            'filename': filename,
            'document_type': doc_type,
            'confidence': confidence,
            'details': handler_result
        }

    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'filename': Path(file_path).name,
            'reason': str(e)
        }

def batch_process_uploads(folder_path, client_id):
    """Batch process all documents in uploads folder."""
    print("\n" + "="*70)
    print("CLIENT DOCUMENTS INGESTION")
    print("="*70)
    print(f"\n📁 Scanning folder: {folder_path}")
    print(f"👤 Client ID: {client_id}\n")

    # Find all supported files
    supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.tiff']
    files = []

    for ext in supported_extensions:
        files.extend(Path(folder_path).glob(f'*{ext}'))

    print(f"📄 Found {len(files)} documents to process\n")

    if len(files) == 0:
        print("⚠️  No documents found. Exiting.")
        return

    # Connect to database
    conn = get_database_connection()

    # Verify client exists
    cursor = conn.cursor()
    cursor.execute("SELECT client_name FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()

    if not client:
        print(f"❌ Error: Client ID {client_id} not found in database")
        conn.close()
        return

    print(f"✅ Processing for client: {client[0]}\n")

    # Process each file
    results = {
        'invoices': [],
        'purchase_orders': [],
        'statements_of_work': [],
        'other': [],
        'failed': []
    }

    print("🔄 Processing documents...\n")

    for file_path in tqdm(files, desc="Processing", unit="doc"):
        result = process_client_document(str(file_path), client_id, conn)

        if result['success']:
            doc_type = result['document_type']
            if doc_type == 'invoice':
                results['invoices'].append(result)
            elif doc_type == 'purchase_order':
                results['purchase_orders'].append(result)
            elif doc_type == 'statement_of_work':
                results['statements_of_work'].append(result)
            else:
                results['other'].append(result)
        else:
            results['failed'].append(result)

    conn.close()

    # Print summary
    print("\n" + "="*70)
    print("INGESTION SUMMARY")
    print("="*70)

    print(f"\n📊 Document Type Counts:")
    print(f"  📄 Invoices: {len(results['invoices'])}")
    print(f"  📋 Purchase Orders: {len(results['purchase_orders'])}")
    print(f"  📝 Statements of Work: {len(results['statements_of_work'])}")
    print(f"  📁 Other Documents: {len(results['other'])}")
    print(f"  ❌ Failed: {len(results['failed'])}")

    if results['invoices']:
        total_invoice_value = sum(r['details'].get('total', 0) for r in results['invoices'])
        total_line_items = sum(r['details'].get('line_items', 0) for r in results['invoices'])
        print(f"\n💰 Invoice Statistics:")
        print(f"  Total invoice value: ${total_invoice_value:,.2f}")
        print(f"  Total line items: {total_line_items}")

    if results['failed']:
        print(f"\n❌ Failed Documents:")
        for r in results['failed'][:5]:
            print(f"  - {r['filename']}: {r['reason']}")

    # Save detailed log
    project_root = Path(__file__).parent.parent
    log_path = project_root / "logs" / f"client_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    with open(log_path, 'w') as f:
        f.write(f"CLIENT DOCUMENTS INGESTION LOG\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Client: {client[0]} (ID: {client_id})\n\n")

        for category, items in results.items():
            f.write(f"\n{category.upper()}:\n")
            for item in items:
                f.write(f"  {item['filename']}\n")

    print(f"\n📝 Detailed log saved to: {log_path}")
    print("\n" + "="*70)
    print("✨ Client document ingestion complete!")
    print("="*70 + "\n")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Ingest client documents with auto-classification"
    )
    parser.add_argument('--folder', required=True, help="Folder containing client documents")
    parser.add_argument('--client_id', required=True, type=int, help="Client ID")

    args = parser.parse_args()

    # Validate folder exists
    if not os.path.exists(args.folder):
        print(f"❌ Error: Folder not found: {args.folder}")
        return 1

    # Process documents
    batch_process_uploads(args.folder, args.client_id)

    return 0

if __name__ == "__main__":
    sys.exit(main())
