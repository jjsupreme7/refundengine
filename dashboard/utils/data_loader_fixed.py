"""
Fixed version of get_documents_from_db function
"""

import pandas as pd
from typing import List, Dict


def get_documents_from_db(df: pd.DataFrame) -> List[Dict]:
    """
    Get documents from analyzed transactions data.
    Aggregates multiple line items per document to show totals.

    Returns:
        List of document dictionaries with aggregated amounts
    """
    if df.empty:
        return []

    documents = []
    seen_files = set()

    # Process Invoice_File_Name_1
    if 'Invoice_File_Name_1' in df.columns:
        file1_groups = df[df['Invoice_File_Name_1'].notna()].groupby('Invoice_File_Name_1')

        for file_name, group in file1_groups:
            if file_name in seen_files:
                continue
            seen_files.add(file_name)

            # Aggregate amounts across all line items for this document
            total_amount = group['Total_Amount'].sum()
            total_tax = group['Tax_Amount'].sum()
            line_items_count = len(group)

            # Get first row for metadata
            first_row = group.iloc[0]

            # Determine status
            if group['Final_Decision'].notna().any():
                status = 'Analyzed'
            elif group['Tax_Category'].notna().any():
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

            # Combine all line item descriptions
            descriptions = group['Line_Item_Description'].dropna().unique().tolist()
            combined_description = f"{line_items_count} line items: " + "; ".join(descriptions[:3])
            if len(descriptions) > 3:
                combined_description += f" ... and {len(descriptions) - 3} more"

            documents.append({
                'id': file_name,
                'vendor': first_row['Vendor_Name'],
                'date': 'N/A',
                'project_id': 'WA-UT-2022_2024',
                'status': status,
                'type': doc_type,
                'file_extension': file_ext,
                'invoice_number': first_row['Invoice_Number'],
                'purchase_order': first_row.get('Purchase_Order_Number', 'N/A'),
                'amount': total_amount,
                'tax_amount': total_tax,
                'line_items_count': line_items_count,
                'description': combined_description,
            })

    # Process Invoice_File_Name_2
    if 'Invoice_File_Name_2' in df.columns:
        file2_groups = df[df['Invoice_File_Name_2'].notna()].groupby('Invoice_File_Name_2')

        for file_name, group in file2_groups:
            if file_name in seen_files:
                continue
            seen_files.add(file_name)

            total_amount = group['Total_Amount'].sum()
            total_tax = group['Tax_Amount'].sum()
            line_items_count = len(group)
            first_row = group.iloc[0]

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

            descriptions = group['Line_Item_Description'].dropna().unique().tolist()
            combined_description = f"{line_items_count} line items: " + "; ".join(descriptions[:3])
            if len(descriptions) > 3:
                combined_description += f" ... and {len(descriptions) - 3} more"

            documents.append({
                'id': file_name,
                'vendor': first_row['Vendor_Name'],
                'date': 'N/A',
                'project_id': 'WA-UT-2022_2024',
                'status': 'Analyzed',
                'type': doc_type,
                'file_extension': file_ext,
                'invoice_number': first_row['Invoice_Number'],
                'purchase_order': first_row.get('Purchase_Order_Number', 'N/A'),
                'amount': total_amount,
                'tax_amount': total_tax,
                'line_items_count': line_items_count,
                'description': combined_description,
            })

    return documents
