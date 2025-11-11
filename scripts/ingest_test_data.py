#!/usr/bin/env python3
"""
Test Data Ingestion Script
Process all documents and Excel files from the Test Data folder

Handles:
- Invoices folder (PDF, TIF, XLS files)
- Purchase Orders folder (PDF, MSG, Excel attachments)
- Denodo Sales Tax Excel files
- Use Tax Phase 3 Excel files

Usage:
    # Process all Test Data
    python scripts/ingest_test_data.py

    # Process specific folder
    python scripts/ingest_test_data.py --folder "Test Data/Invoices"

    # Dry run (no database writes)
    python scripts/ingest_test_data.py --dry-run

    # Process only Excel tax data
    python scripts/ingest_test_data.py --excel-only
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
from datetime import datetime

# Optional progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # Fallback: simple pass-through iterator
    def tqdm(iterable, desc="Processing"):
        print(f"{desc}...")
        return iterable

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our custom modules
from core.document_extractors import extract_text_from_file, check_dependencies
from analysis.excel_processors import (
    DenodoSalesTaxProcessor,
    UseTaxProcessor,
    auto_detect_file_type
)

# Supabase for database storage
try:
    from supabase import create_client, Client
    from dotenv import load_dotenv

    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_AVAILABLE = True
    else:
        print("[WARN]  Supabase credentials not found. Running in analysis-only mode.")
        SUPABASE_AVAILABLE = False
except ImportError:
    print("[WARN]  Supabase not installed. Running in analysis-only mode.")
    SUPABASE_AVAILABLE = False


class TestDataIngester:
    """Main class for ingesting Test Data folder"""

    def __init__(self, test_data_root: str = "Test Data", dry_run: bool = False):
        """
        Initialize ingester

        Args:
            test_data_root: Path to Test Data folder
            dry_run: If True, don't write to database
        """
        self.test_data_root = Path(test_data_root)
        self.dry_run = dry_run
        self.stats = {
            'invoices_processed': 0,
            'purchase_orders_processed': 0,
            'excel_files_processed': 0,
            'errors': 0,
            'total_files': 0
        }

        if not self.test_data_root.exists():
            raise FileNotFoundError(f"Test Data folder not found: {test_data_root}")

        print(f"Test Data root: {self.test_data_root.absolute()}")
        if dry_run:
            print("[DRY RUN] DRY RUN MODE - No database writes")

    def process_invoices_folder(self):
        """Process all files in Invoices folder"""
        invoices_folder = self.test_data_root / "Invoices"

        if not invoices_folder.exists():
            print("[WARN]  Invoices folder not found")
            return

        print("\n" + "=" * 70)
        print(" PROCESSING INVOICES FOLDER")
        print("=" * 70)

        # Find all files
        files = list(invoices_folder.glob("*"))
        supported_files = [
            f for f in files
            if f.suffix.lower() in ['.pdf', '.tif', '.tiff', '.xls', '.xlsx']
        ]

        print(f"Found {len(supported_files)} files to process")

        for file in tqdm(supported_files, desc="Processing invoices"):
            try:
                self._process_invoice_file(file)
                self.stats['invoices_processed'] += 1
            except Exception as e:
                print(f"\n[ERROR] Error processing {file.name}: {e}")
                self.stats['errors'] += 1

        print(f"\n[OK] Processed {self.stats['invoices_processed']} invoices")

    def _process_invoice_file(self, file_path: Path):
        """Process a single invoice file"""
        # Extract text
        text, pages = extract_text_from_file(str(file_path))

        if not text or not text.strip():
            print(f"\n[WARN]  No text extracted from {file_path.name}")
            return

        # Parse invoice number from filename (e.g., 000005000021-1.PDF)
        invoice_number = file_path.stem

        # Prepare document metadata
        doc_metadata = {
            'document_type': 'invoice',
            'title': f"Invoice {invoice_number}",
            'source_file': str(file_path),
            'file_type': file_path.suffix,
            'total_pages': pages,
            'extracted_text': text[:1000],  # First 1000 chars for preview
            'processing_status': 'extracted'
        }

        # Store in database if not dry run
        if not self.dry_run and SUPABASE_AVAILABLE:
            self._store_document(doc_metadata, text)

        self.stats['total_files'] += 1

    def process_purchase_orders_folder(self):
        """Process all files in Purchase Orders folder"""
        po_folder = self.test_data_root / "Purchase Orders"

        if not po_folder.exists():
            print("[WARN]  Purchase Orders folder not found")
            return

        print("\n" + "=" * 70)
        print(" PROCESSING PURCHASE ORDERS FOLDER")
        print("=" * 70)

        # Find all files
        files = list(po_folder.glob("*"))
        supported_files = [
            f for f in files
            if f.suffix.lower() in ['.pdf', '.msg', '.xls', '.xlsx', '.doc', '.docx']
        ]

        print(f"Found {len(supported_files)} files to process")

        for file in tqdm(supported_files, desc="Processing POs"):
            try:
                self._process_po_file(file)
                self.stats['purchase_orders_processed'] += 1
            except Exception as e:
                print(f"\n[ERROR] Error processing {file.name}: {e}")
                self.stats['errors'] += 1

        print(f"\n[OK] Processed {self.stats['purchase_orders_processed']} purchase orders")

    def _process_po_file(self, file_path: Path):
        """Process a single purchase order file"""
        # Extract text
        text, pages = extract_text_from_file(str(file_path))

        if not text or not text.strip():
            print(f"\n[WARN]  No text extracted from {file_path.name}")
            return

        # Parse PO number from filename (e.g., PO_4900668309_ERICSSON_...)
        po_number = "Unknown"
        if file_path.name.startswith("PO_"):
            parts = file_path.name.split("_")
            if len(parts) >= 2:
                po_number = parts[1]

        # Prepare document metadata
        doc_metadata = {
            'document_type': 'purchase_order',
            'title': f"PO {po_number}",
            'source_file': str(file_path),
            'file_type': file_path.suffix,
            'total_pages': pages,
            'extracted_text': text[:1000],
            'processing_status': 'extracted',
            'po_number': po_number
        }

        # Store in database if not dry run
        if not self.dry_run and SUPABASE_AVAILABLE:
            self._store_document(doc_metadata, text)

        self.stats['total_files'] += 1

    def process_excel_tax_files(self):
        """Process all Denodo and Use Tax Excel files"""
        print("\n" + "=" * 70)
        print(" PROCESSING EXCEL TAX DATA FILES")
        print("=" * 70)

        # Find all Excel files in Test Data root
        excel_files = list(self.test_data_root.glob("*.xlsx"))
        excel_files.extend(list(self.test_data_root.glob("*.xls")))

        print(f"Found {len(excel_files)} Excel files")

        for file in excel_files:
            try:
                file_type = auto_detect_file_type(str(file))

                if file_type == 'denodo_sales_tax':
                    self._process_denodo_file(file)
                elif file_type == 'use_tax':
                    self._process_use_tax_file(file)
                else:
                    print(f"\n[WARN]  Unknown Excel file type: {file.name}")
                    continue

                self.stats['excel_files_processed'] += 1

            except Exception as e:
                print(f"\n[ERROR] Error processing {file.name}: {e}")
                self.stats['errors'] += 1

    def _process_denodo_file(self, file_path: Path):
        """Process a Denodo Sales Tax file"""
        print(f"\n Processing Denodo Sales Tax: {file_path.name}")

        processor = DenodoSalesTaxProcessor()
        df = processor.load_file(str(file_path))

        # Get statistics
        stats = processor.get_summary_stats(df)
        print(f"   Total rows: {stats['total_rows']:,}")
        print(f"   Total tax amount: ${stats['total_tax_amount']:,.2f}")
        print(f"   Unique vendors: {stats['unique_vendors']:,}")
        print(f"   Unique invoices: {stats['unique_invoices']:,}")

        # Extract key fields
        key_df = processor.extract_key_fields(df)

        # Filter for refund opportunities
        refund_df = processor.filter_for_refund_opportunities(df)

        print(f"   Potential refund opportunities: {len(refund_df):,}")

        # Store summary in database if not dry run
        if not self.dry_run and SUPABASE_AVAILABLE:
            summary = {
                'file_name': file_path.name,
                'file_type': 'denodo_sales_tax',
                'total_rows': stats['total_rows'],
                'total_tax_amount': float(stats['total_tax_amount']),
                'unique_vendors': stats['unique_vendors'],
                'refund_opportunities': len(refund_df),
                'processed_at': datetime.now().isoformat()
            }
            # Store summary (you may want to create a tax_data_summary table)
            print(f"   [OK] Would store summary in database")

        self.stats['total_files'] += 1

    def _process_use_tax_file(self, file_path: Path):
        """Process a Use Tax Phase 3 file"""
        print(f"\n Processing Use Tax: {file_path.name}")

        processor = UseTaxProcessor()
        df = processor.load_file(str(file_path))

        # Get statistics
        stats = processor.get_summary_stats(df)
        print(f"   Total rows: {stats['total_rows']:,}")
        print(f"   Total tax amount: ${stats['total_tax_amount']:,.2f}")
        print(f"   Unique vendors: {stats['unique_vendors']:,}")
        print(f"   Unique invoices: {stats['unique_invoices']:,}")

        # Filter for items needing research
        research_df = processor.filter_for_research(df)

        print(f"   Items needing research: {len(research_df):,}")

        # Store summary in database if not dry run
        if not self.dry_run and SUPABASE_AVAILABLE:
            summary = {
                'file_name': file_path.name,
                'file_type': 'use_tax',
                'total_rows': stats['total_rows'],
                'total_tax_amount': float(stats['total_tax_amount']),
                'unique_vendors': stats['unique_vendors'],
                'items_needing_research': len(research_df),
                'processed_at': datetime.now().isoformat()
            }
            print(f"   [OK] Would store summary in database")

        self.stats['total_files'] += 1

    def _store_document(self, metadata: Dict, full_text: str):
        """Store document in Supabase database"""
        # This is a placeholder - implement based on your database schema
        # You may want to store in knowledge_documents table or create a new table
        try:
            # Insert document metadata
            result = supabase.table("client_documents").insert(metadata).execute()
            print(f"   [OK] Stored in database: {metadata['title']}")
        except Exception as e:
            print(f"   [WARN]  Database error: {e}")

    def print_summary(self):
        """Print final statistics"""
        print("\n" + "=" * 70)
        print(" INGESTION SUMMARY")
        print("=" * 70)
        print(f"Invoices processed:        {self.stats['invoices_processed']:,}")
        print(f"Purchase orders processed: {self.stats['purchase_orders_processed']:,}")
        print(f"Excel files processed:     {self.stats['excel_files_processed']:,}")
        print(f"Total files:               {self.stats['total_files']:,}")
        print(f"Errors:                    {self.stats['errors']:,}")
        print("=" * 70)

    def run_full_ingestion(self, excel_only: bool = False):
        """Run full ingestion of all Test Data"""
        print("\n" + "=" * 70)
        print(" TEST DATA INGESTION")
        print("=" * 70)

        # Check dependencies
        deps = check_dependencies()
        print("\nDependency check:")
        for lib, available in deps.items():
            status = "[OK]" if available else "[X]"
            print(f"  {status} {lib}")

        if not excel_only:
            # Process documents
            self.process_invoices_folder()
            self.process_purchase_orders_folder()

        # Process Excel files
        self.process_excel_tax_files()

        # Print summary
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Test Data folder (invoices, POs, Excel tax files)"
    )
    parser.add_argument(
        "--folder",
        default="Test Data",
        help="Path to Test Data folder (default: 'Test Data')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database, just analyze"
    )
    parser.add_argument(
        "--excel-only",
        action="store_true",
        help="Process only Excel tax files, skip documents"
    )

    args = parser.parse_args()

    try:
        ingester = TestDataIngester(
            test_data_root=args.folder,
            dry_run=args.dry_run
        )
        ingester.run_full_ingestion(excel_only=args.excel_only)

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
