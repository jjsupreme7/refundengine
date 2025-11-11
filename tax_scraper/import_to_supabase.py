"""
Import approved RCW sections from Excel into Supabase knowledge_base
Only imports rows where 'approved' column = 'YES'
"""

import pandas as pd
import os
from pathlib import Path
import logging
from datetime import datetime
from supabase import create_client, Client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
EXPORTS_DIR = Path(__file__).parent / "exports"

# Supabase credentials (from environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for admin operations


def get_latest_review_file() -> Path:
    """Find the most recent review Excel file"""
    excel_files = list(EXPORTS_DIR.glob("rcw_sections_review_*.xlsx"))

    if not excel_files:
        raise FileNotFoundError(f"No review files found in {EXPORTS_DIR}")

    # Sort by modification time, most recent first
    latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Using review file: {latest_file.name}")

    return latest_file


def import_approved_sections(excel_path: Path = None):
    """Import only approved sections from Excel into Supabase"""

    # Validate credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
        )

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Connected to Supabase")

    # Get Excel file
    if excel_path is None:
        excel_path = get_latest_review_file()

    # Read Excel file
    logger.info(f"Reading review file: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='RCW Sections')

    # Filter for approved sections only
    # Accept variations: 'YES', 'yes', 'Yes', 'Y', 'y', 'APPROVED', 'approved'
    approved_values = ['YES', 'yes', 'Yes', 'Y', 'y', 'APPROVED', 'approved', 'Approved']
    df_approved = df[df['approved'].isin(approved_values)]

    logger.info(f"Total sections in Excel: {len(df)}")
    logger.info(f"Approved sections: {len(df_approved)}")

    if len(df_approved) == 0:
        logger.warning("No approved sections found. Did you mark the 'approved' column with 'YES'?")
        return

    # Prepare records for Supabase
    records_inserted = 0
    records_updated = 0
    records_failed = 0

    for idx, row in df_approved.iterrows():
        try:
            # Prepare document data
            document = {
                'source_type': 'rcw',
                'citation': row['citation'],
                'title': row['title'] if pd.notna(row['title']) else None,
                'content': row['full_text'],
                'metadata': {
                    'chapter': row['chapter'] if pd.notna(row['chapter']) else None,
                    'section': row['section'] if pd.notna(row['section']) else None,
                    'effective_date': row['effective_date'] if pd.notna(row['effective_date']) else None,
                    'source_url': row['url'] if pd.notna(row['url']) else None,
                    'pdf_path': row['pdf_path'] if pd.notna(row['pdf_path']) else None,
                    'reviewed_by': row['reviewed_by'] if pd.notna(row['reviewed_by']) else None,
                    'review_date': row['review_date'] if pd.notna(row['review_date']) else None,
                    'review_notes': row['notes'] if pd.notna(row['notes']) else None,
                    'scraped_at': row['scraped_at'] if pd.notna(row['scraped_at']) else None
                },
                'uploaded_at': datetime.now().isoformat()
            }

            # Upsert into knowledge_base table
            # Check if document already exists by citation
            existing = supabase.table('knowledge_base') \
                .select('id') \
                .eq('citation', row['citation']) \
                .execute()

            if existing.data:
                # Update existing record
                result = supabase.table('knowledge_base') \
                    .update(document) \
                    .eq('citation', row['citation']) \
                    .execute()
                records_updated += 1
                logger.info(f"Updated: {row['citation']}")
            else:
                # Insert new record
                result = supabase.table('knowledge_base') \
                    .insert(document) \
                    .execute()
                records_inserted += 1
                logger.info(f"Inserted: {row['citation']}")

        except Exception as e:
            records_failed += 1
            logger.error(f"Failed to import {row['citation']}: {e}")

    # Summary
    logger.info(f"\n=== Import Summary ===")
    logger.info(f"Total approved: {len(df_approved)}")
    logger.info(f"Inserted: {records_inserted}")
    logger.info(f"Updated: {records_updated}")
    logger.info(f"Failed: {records_failed}")
    logger.info(f"Success rate: {((records_inserted + records_updated) / len(df_approved) * 100):.1f}%")


def verify_import():
    """Verify imported data in Supabase"""

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing Supabase credentials")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Count RCW documents
    result = supabase.table('knowledge_base') \
        .select('id', count='exact') \
        .eq('source_type', 'rcw') \
        .execute()

    count = result.count if hasattr(result, 'count') else len(result.data)
    logger.info(f"\n=== Verification ===")
    logger.info(f"Total RCW documents in Supabase: {count}")

    # Show sample
    sample = supabase.table('knowledge_base') \
        .select('citation, title') \
        .eq('source_type', 'rcw') \
        .limit(5) \
        .execute()

    logger.info(f"\nSample documents:")
    for doc in sample.data:
        logger.info(f"  - {doc['citation']}: {doc.get('title', 'No title')[:50]}")


if __name__ == "__main__":
    logger.info("=== Import Approved RCW Sections to Supabase ===")

    try:
        # Import approved sections
        import_approved_sections()

        # Verify import
        verify_import()

        logger.info(f"\n✓ Import complete!")

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
