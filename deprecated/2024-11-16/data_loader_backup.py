"""
Data loading utilities for the TaxDesk dashboard.

Provides functions to load data from various sources:
- Excel files (analyzed transactions)
- Supabase database (projects, documents, knowledge base)
- Test data generation
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.database import get_supabase_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def load_analyzed_transactions(excel_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load analyzed transactions from Excel file.

    Args:
        excel_path: Path to Excel file. If None, uses default test data path.

    Returns:
        DataFrame with analyzed transactions
    """
    if excel_path is None:
        excel_path = Path(__file__).parent.parent.parent / "test_data" / "Master_Claim_Sheet_ANALYZED.xlsx"

    try:
        df = pd.read_excel(excel_path)
        return df
    except FileNotFoundError:
        # Return empty DataFrame with expected columns if file doesn't exist
        return pd.DataFrame(columns=[
            'Vendor_Name', 'Invoice_Number', 'Line_Item_Description',
            'Total_Amount', 'Tax_Amount', 'Final_Decision', 'AI_Confidence',
            'Tax_Category', 'Estimated_Refund', 'AI_Reasoning'
        ])


def get_dashboard_stats(df: pd.DataFrame) -> Dict:
    """
    Calculate dashboard statistics from analyzed transactions.

    Args:
        df: DataFrame with analyzed transactions

    Returns:
        Dictionary with statistics
    """
    if df.empty:
        return {
            'total_transactions': 0,
            'unique_invoices': 0,
            'total_refund': 0.0,
            'avg_confidence': 0.0,
            'flagged_count': 0,
            'flagged_pct': 0.0,
            'refund_rows': 0,
            'unique_vendors': 0,
        }

    total_transactions = len(df)
    unique_invoices = df['Invoice_Number'].nunique()
    total_refund = df['Estimated_Refund'].sum()
    avg_confidence = df['AI_Confidence'].mean()
    flagged = df[df['AI_Confidence'] < 90]
    flagged_count = len(flagged)
    flagged_pct = (flagged_count / total_transactions * 100) if total_transactions > 0 else 0
    refund_rows = len(df[df['Estimated_Refund'] > 0])
    unique_vendors = df['Vendor_Name'].nunique()

    return {
        'total_transactions': total_transactions,
        'unique_invoices': unique_invoices,
        'total_refund': total_refund,
        'avg_confidence': avg_confidence,
        'flagged_count': flagged_count,
        'flagged_pct': flagged_pct,
        'refund_rows': refund_rows,
        'unique_vendors': unique_vendors,
    }


def get_review_queue(df: pd.DataFrame, confidence_threshold: float = 90.0) -> pd.DataFrame:
    """
    Get transactions that need review (below confidence threshold).

    Args:
        df: DataFrame with analyzed transactions
        confidence_threshold: Minimum confidence for auto-approval

    Returns:
        DataFrame with flagged transactions
    """
    if df.empty:
        return df

    return df[df['AI_Confidence'] < confidence_threshold].copy()


def get_vendor_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get breakdown by vendor with summary statistics.

    Args:
        df: DataFrame with analyzed transactions

    Returns:
        DataFrame with vendor statistics
    """
    if df.empty:
        return pd.DataFrame(columns=['Vendor', 'Transactions', 'Total_Refund', 'Avg_Confidence'])

    vendor_stats = df.groupby('Vendor_Name').agg({
        'Invoice_Number': 'count',
        'Estimated_Refund': 'sum',
        'AI_Confidence': 'mean'
    }).reset_index()

    vendor_stats.columns = ['Vendor', 'Transactions', 'Total_Refund', 'Avg_Confidence']
    vendor_stats = vendor_stats.sort_values('Total_Refund', ascending=False)

    return vendor_stats


def get_projects_from_db() -> List[Dict]:
    """
    Get projects from database (or return mock data if DB unavailable).

    Returns:
        List of project dictionaries
    """
    # For now, return mock data matching the React mockup
    return [
        {
            'id': 'WA-UT-2022_2024',
            'name': 'Washington Use Tax Review',
            'period': '2022–2024',
            'est_refund': 184230,
            'status': 'Analyzing',
            'description': 'Comprehensive review of use tax liabilities for Washington State',
        },
        {
            'id': 'OR-UT-2023',
            'name': 'Oregon Use Tax (Audit Support)',
            'period': '2023',
            'est_refund': 0,
            'status': 'On Hold',
            'description': 'Supporting documentation for Oregon use tax audit',
        },
    ]


def get_documents_from_db() -> List[Dict]:
    """
    Get documents from analyzed transactions data.
    Aggregates multiple line items per document.

    Returns:
        List of document dictionaries
    """
    # Load from Excel file
    df = load_analyzed_transactions()

    if df.empty:
        return []

    # Group by invoice file to aggregate line items
    documents = []

    # Process Invoice_File_Name_1
    if 'Invoice_File_Name_1' in df.columns:
        file1_groups = df[df['Invoice_File_Name_1'].notna()].groupby('Invoice_File_Name_1')

        for file_name, group in file1_groups:
        # Check Invoice_File_Name_1
        if pd.notna(row.get('Invoice_File_Name_1')) and row['Invoice_File_Name_1'] not in seen_files:
            file_name = row['Invoice_File_Name_1']
            seen_files.add(file_name)

            # Determine status based on whether it's been analyzed
            if pd.notna(row.get('Final_Decision')):
                status = 'Analyzed'
            elif pd.notna(row.get('Tax_Category')):
                status = 'Parsed'
            else:
                status = 'Uploaded'

            # Determine file type from extension
            file_ext = file_name.split('.')[-1].upper() if '.' in file_name else 'Unknown'
            file_type_map = {
                'PDF': 'PDF Invoice',
                'XLSX': 'Excel Invoice',
                'XLS': 'Excel Invoice',
                'JPG': 'Scanned Invoice (JPG)',
                'JPEG': 'Scanned Invoice (JPEG)',
                'PNG': 'Scanned Invoice (PNG)',
            }
            doc_type = file_type_map.get(file_ext, f'Invoice ({file_ext})')

            documents.append({
                'id': file_name,
                'vendor': row['Vendor_Name'],
                'date': 'N/A',  # Not in current data
                'project_id': 'WA-UT-2022_2024',
                'status': status,
                'type': doc_type,
                'file_extension': file_ext,
                'invoice_number': row['Invoice_Number'],
                'purchase_order': row.get('Purchase_Order_Number', 'N/A'),
                'amount': row.get('Total_Amount', 0),
                'tax_amount': row.get('Tax_Amount', 0),
                'description': row.get('Line_Item_Description', 'N/A'),
            })

        # Check Invoice_File_Name_2 if it exists
        if pd.notna(row.get('Invoice_File_Name_2')) and row['Invoice_File_Name_2'] not in seen_files:
            file_name = row['Invoice_File_Name_2']
            seen_files.add(file_name)

            file_ext = file_name.split('.')[-1].upper() if '.' in file_name else 'Unknown'
            file_type_map = {
                'PDF': 'PDF Invoice',
                'XLSX': 'Excel Invoice',
                'XLS': 'Excel Invoice',
                'JPG': 'Scanned Invoice (JPG)',
                'JPEG': 'Scanned Invoice (JPEG)',
                'PNG': 'Scanned Invoice (PNG)',
            }
            doc_type = file_type_map.get(file_ext, f'Invoice ({file_ext})')

            documents.append({
                'id': file_name,
                'vendor': row['Vendor_Name'],
                'date': 'N/A',
                'project_id': 'WA-UT-2022_2024',
                'status': 'Analyzed',
                'type': doc_type,
                'file_extension': file_ext,
                'invoice_number': row['Invoice_Number'],
                'purchase_order': row.get('Purchase_Order_Number', 'N/A'),
                'amount': row.get('Total_Amount', 0),
                'tax_amount': row.get('Tax_Amount', 0),
                'description': row.get('Line_Item_Description', 'N/A'),
            })

    return documents


def get_tax_rules() -> List[Dict]:
    """
    Get tax rules and guidance.

    Returns:
        List of rule dictionaries
    """
    return [
        {
            'id': 'RCW 82.08.*',
            'title': 'RCW 82.08.* - Retail Sales Tax',
            'category': 'Statute',
            'summary': 'Sale of tangible personal property (TPP) generally taxable.',
        },
        {
            'id': 'WAC 458-20-15503',
            'title': 'WAC 458-20-15503 - Digital Automated Services',
            'category': 'Regulation',
            'summary': 'Digital automated services (DAS) rules; SaaS presumptively taxable unless exclusion applies.',
        },
        {
            'id': 'ESSB 5814',
            'title': 'ESSB 5814 - Service Taxation Changes',
            'category': 'Legislation',
            'summary': 'Effective Oct 1, 2025. Expands B&O and retail sales tax to certain services.',
        },
    ]
