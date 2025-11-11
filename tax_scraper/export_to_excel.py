"""
Export scraped RCW sections from SQLite to WA_Tax_Law.xlsx format for manual review/approval
Matches the existing outputs/WA_Tax_Law.xlsx structure
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DB_PATH = Path(__file__).parent / "tax_laws.db"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "WA_Tax_Law.xlsx"


def export_rcw_to_wa_tax_law():
    """Export all RCW sections to WA_Tax_Law.xlsx with Metadata sheet"""

    logger.info(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        # Read all RCW sections
        query = """
            SELECT
                citation,
                title,
                chapter,
                section,
                full_text,
                effective_date,
                url,
                pdf_path,
                scraped_at
            FROM rcw_sections
            ORDER BY chapter, section
        """

        df = pd.read_sql_query(query, conn)
        logger.info(f"Loaded {len(df)} RCW sections from database")

        # Transform to WA_Tax_Law.xlsx format matching existing structure
        metadata_df = pd.DataFrame({
            'File_Name': df['citation'].str.replace(' ', '_') + '.pdf',  # e.g., RCW_82.08.010.pdf
            'Status': '',  # Empty - you'll fill with 'Approved' or leave blank
            'Document_Type': 'tax_law',  # All are tax laws
            'document_title': df['title'],
            'citation': df['citation'],
            'law_category': '',  # Empty - optionally categorize (e.g., 'definition', 'exemption')
            'effective_date': df['effective_date'],
            'topic_tags': '',  # Empty - optionally add tags
            'tax_types': '',  # Empty - optionally specify (e.g., 'sales tax', 'use tax')
            'industries': '',  # Empty - optionally specify affected industries
            'keywords': '',  # Empty - optionally add keywords
            'referenced_statutes': '',  # Empty - optionally extract references
            'document_summary': df['full_text'].str[:500] + '...',  # First 500 chars as preview
            'AI_Confidence': '',  # Empty - not AI-generated
            'Total_Pages': 1,  # Default to 1 for now
            'File_Path': df['pdf_path']
        })

        # Check if WA_Tax_Law.xlsx exists
        if OUTPUT_FILE.exists():
            logger.info(f"File exists: {OUTPUT_FILE}")
            logger.info("Reading existing data...")

            # Read existing data
            existing_df = pd.read_excel(OUTPUT_FILE, sheet_name='Metadata')
            logger.info(f"Found {len(existing_df)} existing records")

            # Get existing citations to avoid duplicates
            existing_citations = set(existing_df['citation'].dropna())

            # Filter out RCW sections that already exist
            new_records = metadata_df[~metadata_df['citation'].isin(existing_citations)]
            logger.info(f"New RCW sections to add: {len(new_records)}")

            if len(new_records) > 0:
                # Append new records to existing data
                combined_df = pd.concat([existing_df, new_records], ignore_index=True)
                logger.info(f"Total records after merge: {len(combined_df)}")
            else:
                logger.info("No new records to add. All RCW sections already exist.")
                combined_df = existing_df
        else:
            logger.info(f"Creating new file: {OUTPUT_FILE}")
            combined_df = metadata_df

        # Write to Excel with Metadata sheet
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            combined_df.to_excel(writer, sheet_name='Metadata', index=False)

            # Get the worksheet to apply formatting
            worksheet = writer.sheets['Metadata']

            # Set column widths for readability
            worksheet.column_dimensions['A'].width = 25  # File_Name
            worksheet.column_dimensions['B'].width = 12  # Status
            worksheet.column_dimensions['C'].width = 15  # Document_Type
            worksheet.column_dimensions['D'].width = 50  # document_title
            worksheet.column_dimensions['E'].width = 20  # citation
            worksheet.column_dimensions['F'].width = 15  # law_category
            worksheet.column_dimensions['G'].width = 15  # effective_date
            worksheet.column_dimensions['H'].width = 30  # topic_tags
            worksheet.column_dimensions['I'].width = 20  # tax_types
            worksheet.column_dimensions['J'].width = 20  # industries
            worksheet.column_dimensions['K'].width = 30  # keywords
            worksheet.column_dimensions['L'].width = 20  # referenced_statutes
            worksheet.column_dimensions['M'].width = 60  # document_summary
            worksheet.column_dimensions['N'].width = 15  # AI_Confidence
            worksheet.column_dimensions['O'].width = 12  # Total_Pages
            worksheet.column_dimensions['P'].width = 50  # File_Path

            # Freeze first row (headers)
            worksheet.freeze_panes = 'A2'

        logger.info(f"✓ Exported to: {OUTPUT_FILE}")
        logger.info(f"\nNext steps:")
        logger.info(f"1. Open {OUTPUT_FILE.name}")
        logger.info(f"2. Review the Metadata sheet")
        logger.info(f"3. Mark 'Status' column with 'Approved' for sections you want to import")
        logger.info(f"4. Optionally fill in: law_category, topic_tags, tax_types, industries, keywords")
        logger.info(f"5. Save the file")
        logger.info(f"6. Run: python core/ingest_documents.py --import-metadata outputs/WA_Tax_Law.xlsx")

        return OUTPUT_FILE

    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}", exc_info=True)
        return None

    finally:
        conn.close()


def get_export_stats():
    """Print statistics about scraped data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total sections
    cursor.execute("SELECT COUNT(*) FROM rcw_sections")
    total = cursor.fetchone()[0]

    # Sections by chapter
    cursor.execute("""
        SELECT chapter, COUNT(*) as count
        FROM rcw_sections
        GROUP BY chapter
        ORDER BY chapter
    """)
    chapters = cursor.fetchall()

    logger.info(f"\n=== Export Statistics ===")
    logger.info(f"Total RCW sections: {total}")
    logger.info(f"Chapters covered: {len(chapters)}")
    logger.info(f"\nSections per chapter:")
    for chapter, count in chapters:
        logger.info(f"  82.{chapter}: {count} sections")

    conn.close()


if __name__ == "__main__":
    logger.info("=== RCW Export to WA_Tax_Law.xlsx ===")

    # Show stats
    get_export_stats()

    # Export to Excel
    excel_path = export_rcw_to_wa_tax_law()

    if excel_path:
        logger.info(f"\n✓ Export complete!")
        logger.info(f"Review file: {excel_path}")
