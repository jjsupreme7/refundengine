#!/usr/bin/env python3
"""
Create Master Excel Sheet - EXACT Structure

Columns as specified:
INPUT COLUMNS (User provides):
- Vendor_ID
- Vendor_Name
- Invoice_Number
- Purchase_Order_Number
- Total_Amount
- Tax_Amount
- Tax_Remitted
- Tax_Rate_Charged (as percentage)
- Invoice_File_Name_1 (vendor invoice)
- Invoice_File_Name_2 (internal invoice)

OUTPUT COLUMNS (AI populates):
- Analysis_Notes
- Final_Decision
- Tax_Category
- Additional_Info
- Refund_Basis
- Estimated_Refund
- Legal_Citation
- AI_Confidence
"""

from datetime import datetime
from pathlib import Path

import pandas as pd


def create_master_excel_sheet():
    """
    Create master Excel sheet with exact structure
    """

    # Test transactions matching your structure
    transactions = [
        # REFUND OPPORTUNITY 1 - DAS with MPU
        {
            "Vendor_ID": "V-10001",
            "Vendor_Name": "Microsoft Corporation",
            "Invoice_Number": "INV-2024-0001",
            "Purchase_Order_Number": "PO-5001",
            "Total_Amount": 11155.00,
            "Tax_Amount": 1155.00,
            "Tax_Remitted": 1155.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0001.pd",  # Vendor invoice
            "Invoice_File_Name_2": "0001_internal.pd",  # Internal version
            # OUTPUT COLUMNS (blank for now - AI will fill)
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # REFUND OPPORTUNITY 2 - DAS with MPU
        {
            "Vendor_ID": "V-10002",
            "Vendor_Name": "Salesforce Inc",
            "Invoice_Number": "INV-2024-0002",
            "Purchase_Order_Number": "PO-5002",
            "Total_Amount": 19890.00,
            "Tax_Amount": 1890.00,
            "Tax_Remitted": 1890.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0002.pd",
            "Invoice_File_Name_2": "",  # No internal version
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # REFUND OPPORTUNITY 3 - Out of State Shipment (Large $)
        {
            "Vendor_ID": "V-10003",
            "Vendor_Name": "Dell Technologies",
            "Invoice_Number": "INV-2024-0003",
            "Purchase_Order_Number": "PO-5003",
            "Total_Amount": 112710.00,
            "Tax_Amount": 10710.00,
            "Tax_Remitted": 10710.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0003.pd",
            "Invoice_File_Name_2": "0003_internal.pd",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # REFUND OPPORTUNITY 4 - Professional Services
        {
            "Vendor_ID": "V-10004",
            "Vendor_Name": "Deloitte Consulting LLP",
            "Invoice_Number": "INV-2024-0004",
            "Purchase_Order_Number": "PO-5004",
            "Total_Amount": 77350.00,
            "Tax_Amount": 7350.00,
            "Tax_Remitted": 7350.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0004.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # REFUND OPPORTUNITY 5 - Custom Software (OLD LAW - not taxable)
        {
            "Vendor_ID": "V-10005",
            "Vendor_Name": "Accenture",
            "Invoice_Number": "INV-2024-0005",
            "Purchase_Order_Number": "PO-5005",
            "Total_Amount": 93925.00,
            "Tax_Amount": 8925.00,
            "Tax_Remitted": 8925.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0005.pd",
            "Invoice_File_Name_2": "0005_internal.pd",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # SMALL DOLLAR - AWS (< $20K)
        {
            "Vendor_ID": "V-10006",
            "Vendor_Name": "Amazon Web Services",
            "Invoice_Number": "INV-2024-0006",
            "Purchase_Order_Number": "",  # No PO
            "Total_Amount": 13812.50,
            "Tax_Amount": 1312.50,
            "Tax_Remitted": 1312.50,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0006.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # SMALL DOLLAR - Zoom (< $20K)
        {
            "Vendor_ID": "V-10007",
            "Vendor_Name": "Zoom Video Communications",
            "Invoice_Number": "INV-2024-0007",
            "Purchase_Order_Number": "PO-5007",
            "Total_Amount": 19890.00,
            "Tax_Amount": 1890.00,
            "Tax_Remitted": 1890.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0007.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # SMALL DOLLAR - Slack (< $20K)
        {
            "Vendor_ID": "V-10008",
            "Vendor_Name": "Slack Technologies",
            "Invoice_Number": "INV-2024-0008",
            "Purchase_Order_Number": "",
            "Total_Amount": 6630.00,
            "Tax_Amount": 630.00,
            "Tax_Remitted": 630.00,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0008.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # LICENSE vs SAAS - Needs review (ambiguous)
        {
            "Vendor_ID": "V-10009",
            "Vendor_Name": "Oracle America Inc",
            "Invoice_Number": "INV-2024-0009",
            "Purchase_Order_Number": "PO-5009",
            "Total_Amount": 52237.50,
            "Tax_Amount": 4987.50,
            "Tax_Remitted": 4987.50,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0009.pd",
            "Invoice_File_Name_2": "0009_internal.pd",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # NO REFUND - Telecom (properly taxed)
        {
            "Vendor_ID": "V-10010",
            "Vendor_Name": "Verizon Wireless",
            "Invoice_Number": "INV-2024-0010",
            "Purchase_Order_Number": "",
            "Total_Amount": 4696.25,
            "Tax_Amount": 446.25,
            "Tax_Remitted": 446.25,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0010.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # NO REFUND - Office Supplies (properly taxed)
        {
            "Vendor_ID": "V-10011",
            "Vendor_Name": "Office Depot",
            "Invoice_Number": "INV-2024-0011",
            "Purchase_Order_Number": "",
            "Total_Amount": 933.73,
            "Tax_Amount": 88.73,
            "Tax_Remitted": 88.73,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0011.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
        # NO REFUND - Internet Service (properly taxed)
        {
            "Vendor_ID": "V-10012",
            "Vendor_Name": "Comcast Business",
            "Invoice_Number": "INV-2024-0012",
            "Purchase_Order_Number": "",
            "Total_Amount": 938.73,
            "Tax_Amount": 89.37,
            "Tax_Remitted": 89.37,
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": "0012.pd",
            "Invoice_File_Name_2": "",
            "Analysis_Notes": "",
            "Final_Decision": "",
            "Tax_Category": "",
            "Additional_Info": "",
            "Refund_Basis": "",
            "Estimated_Refund": "",
            "Legal_Citation": "",
            "AI_Confidence": "",
        },
    ]

    # Create DataFrame
    df = pd.DataFrame(transactions)

    # Define column order exactly as specified
    column_order = [
        # INPUT COLUMNS
        "Vendor_ID",
        "Vendor_Name",
        "Invoice_Number",
        "Purchase_Order_Number",
        "Total_Amount",
        "Tax_Amount",
        "Tax_Remitted",
        "Tax_Rate_Charged",
        "Invoice_File_Name_1",
        "Invoice_File_Name_2",
        # OUTPUT COLUMNS (AI will populate)
        "Analysis_Notes",
        "Final_Decision",
        "Tax_Category",
        "Additional_Info",
        "Refund_Basis",
        "Estimated_Refund",
        "Legal_Citation",
        "AI_Confidence",
    ]

    df = df[column_order]

    # Save to Excel
    output_path = Path("test_data/Master_Claim_Sheet.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Claim Sheet", index=False)

        # Auto-adjust column widths
        worksheet = writer.sheets["Claim Sheet"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except BaseException:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print("=" * 80)
    print("MASTER CLAIM SHEET CREATED")
    print("=" * 80)
    print()
    print(f"📄 File: {output_path}")
    print(f"📊 Rows: {len(df)}")
    print()

    # Calculate summary
    total_tax = df["Tax_Amount"].sum()
    refund_opps = 9  # Based on expected refunds
    properly_taxed = 3

    print("Summary:")
    print(f"  Total Tax Charged: ${total_tax:,.2f}")
    print(f"  Expected Refund Opportunities: {refund_opps}")
    print(f"  Properly Taxed Items: {properly_taxed}")
    print()

    print("Column Structure:")
    print("  INPUT COLUMNS (User provides):")
    print("    - Vendor_ID")
    print("    - Vendor_Name")
    print("    - Invoice_Number")
    print("    - Purchase_Order_Number")
    print("    - Total_Amount")
    print("    - Tax_Amount")
    print("    - Tax_Remitted")
    print("    - Tax_Rate_Charged")
    print("    - Invoice_File_Name_1 (vendor invoice)")
    print("    - Invoice_File_Name_2 (internal invoice)")
    print()
    print("  OUTPUT COLUMNS (AI populates):")
    print("    - Analysis_Notes")
    print("    - Final_Decision")
    print("    - Tax_Category")
    print("    - Additional_Info")
    print("    - Refund_Basis")
    print("    - Estimated_Refund")
    print("    - Legal_Citation")
    print("    - AI_Confidence")
    print()

    print("Expected AI Output Values:")
    print()
    print("  Final_Decision:")
    print("    - 'Add to Claim - Refund Sample' (if < $20,000)")
    print("    - Tax Category name (if >= $20,000)")
    print()
    print("  Tax_Category:")
    print("    - Custom Software, DAS, DAS/License, Digital Goods")
    print("    - Hardware Support, License, Services, Services/Tangible Goods")
    print("    - Software Maintenance, Software Support, Tangible Goods")
    print()
    print("  Additional_Info:")
    print("    - Advertising, Data Processing, Hosting, Internet Access")
    print("    - Professional, Software Development/Configuration, Testing")
    print("    - Website Development, Website Hosting, etc.")
    print()
    print("  Refund_Basis:")
    print("    - MPU (Multiple Points of Use)")
    print("    - Non-Taxable")
    print("    - Out of State - Services")
    print("    - Out of State - Shipment")
    print("    - Partial Out-of-State Services")
    print("    - Resale")
    print("    - Wrong Rate")
    print()
    print("=" * 80)

    return output_path


if __name__ == "__main__":
    create_master_excel_sheet()
