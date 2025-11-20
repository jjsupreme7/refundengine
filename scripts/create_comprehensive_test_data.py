#!/usr/bin/env python3
"""
Create comprehensive test data for the Tax Refund Engine.

This generates:
- 5 Purchase Orders (various formats: PDF, Excel, Email)
- 15 Invoices (various formats: PDF, Excel, Images)
- ~50 Excel rows showing hierarchical structure (1 PO → multiple invoices → multiple line items)

Scenarios covered:
1. Microsoft PO - Software/Services with itemized invoices
2. Construction PO - Progress payments with retainage issue
3. Out-of-State PO - Use tax scenario
4. Professional Services PO - Hidden tax on exempt services
5. Mixed Vendor PO - Bundled services (7+ line items)
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Controlled vocabularies (updated from user)
TAX_CATEGORIES = [
    "Custom Software",
    "DAS",
    "DAS/License",
    "Digital Goods",
    "Hardware Support",
    "License",
    "Services",
    "Services/Tangible Goods",
    "Software Maintenance",
    "Software Support",
    "Tangible Goods",
]

ADDITIONAL_INFO = [
    "Advertising",
    "Building Permits",
    "City Permit",
    "Cleaning",
    "Construction",
    "Credit Card Processing Fee",
    "Data Processing",
    "Decommissioning",
    "Dining",
    "Discount Codes",
    "Disposal",
    "Food",
    "Freight",
    "Gift Certificates",
    "Help Desk",
    "Hosting",
    "Inspection",
    "Installation",
    "Internet Access",
    "Janitorial",
    "Landscape",
    "Membership Dues",
    "Moving Permit",
    "Postage",
    "Professional",
    "Public Relations",
    "Recycling",
    "Repaired",
    "Repair",
    "Sign Installation",
    "Software Development/Configuration",
    "Storage",
    "Telecommunications",
    "Testing",
    "IT Reimbursement",
    "Warehousing",
    "Website Development",
    "Website Hosting",
]

REFUND_BASIS = [
    "MPU",
    "Non-Taxable",
    "Special Category Non-Taxable (Services in Respect to Construction)",
    "Out-of-State/Partial Out-of-State",
    "Out-of-State Services",
    "Out-of-State Shipment",
    "Wrong Rate",
    "Partial Out-of-State Shipments",
    "Resale",
]

WA_TAX_RATE = 0.105  # 10.5%


def create_test_transactions():
    """
    Create comprehensive test transactions with hierarchical structure.

    Returns:
        List[Dict]: Transaction rows for Excel
    """
    transactions = []

    # ========================================================================
    # SCENARIO 1: Microsoft PO - Multiple invoices with itemized line items
    # ========================================================================
    po_num = "PO-2024-001"
    po_files = "PO_2024_001_Microsoft.pd"
    vendor_id = "V-10001"
    vendor_name = "Microsoft Corporation"

    # Invoice 1: 3 line items (mixed taxable/exempt)
    inv_num = "MS-INV-2024-0451"
    inv_file = "MS_INV_2024_0451.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 25000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file,
            "Invoice_File_Name_2": f"{inv_num}_internal.pd",
            "Line_Item_Description": "Custom API Integration Development - 200 hours @ $125/hr",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 15000.00,
            "Tax_Amount": 1575.00,
            "Tax_Remitted": 1575.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file,
            "Invoice_File_Name_2": f"{inv_num}_internal.pd",
            "Line_Item_Description": "Microsoft 365 Enterprise Licenses (50 users)",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 8000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file,
            "Invoice_File_Name_2": f"{inv_num}_internal.pd",
            "Line_Item_Description": "Premier Support Services - Annual Contract",
        }
    )

    # Invoice 2: 5 line items (complex mixed scenario)
    inv_num2 = "MS-INV-2024-0628"
    inv_file2 = "MS_INV_2024_0628.xlsx"  # Excel invoice

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num2,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 12000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file2,
            "Invoice_File_Name_2": f"{inv_num2}_internal.pd",
            "Line_Item_Description": "Azure Cloud Hosting Services - Q1 2024",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num2,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 5525.00,  # ODD DOLLAR AMOUNT - hidden tax indicator!
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file2,
            "Invoice_File_Name_2": f"{inv_num2}_internal.pd",
            "Line_Item_Description": "Professional Consulting Services - System Architecture",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num2,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 3000.00,
            "Tax_Amount": 315.00,
            "Tax_Remitted": 315.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file2,
            "Invoice_File_Name_2": f"{inv_num2}_internal.pd",
            "Line_Item_Description": "Surface Pro Tablets (3 units)",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num2,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 6000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file2,
            "Invoice_File_Name_2": f"{inv_num2}_internal.pd",
            "Line_Item_Description": "Custom Software Configuration for ERP Integration",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num2,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 2500.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file2,
            "Invoice_File_Name_2": f"{inv_num2}_internal.pd",
            "Line_Item_Description": "Software Maintenance Agreement - Renewal",
        }
    )

    # Invoice 3: 2 line items
    inv_num3 = "MS-INV-2024-0892"
    inv_file3 = "MS_INV_2024_0892.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num3,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 18000.00,
            "Tax_Amount": 1890.00,
            "Tax_Remitted": 1890.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file3,
            "Invoice_File_Name_2": f"{inv_num3}_internal.pd",
            "Line_Item_Description": "Server Hardware - Dell PowerEdge R750",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id,
            "Vendor_Name": vendor_name,
            "Invoice_Number": inv_num3,
            "Purchase_Order_Number": po_num,
            "Purchase_Order_File_Name": po_files,
            "Total_Amount": 4000.00,
            "Tax_Amount": 420.00,
            "Tax_Remitted": 420.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file3,
            "Invoice_File_Name_2": f"{inv_num3}_internal.pd",
            "Line_Item_Description": "Installation and Setup Services",
        }
    )

    # ========================================================================
    # SCENARIO 2: Construction PO - Retainage Issue
    # ========================================================================
    po_num2 = "PO-2024-002"
    po_files2 = "PO_2024_002_BuildRight_Construction.pd"
    vendor_id2 = "V-20045"
    vendor_name2 = "BuildRight Construction LLC"

    # Invoice 1: First progress payment - TAX CHARGED ON FULL PO AMOUNT (WRONG!)
    inv_num4 = "BRC-2024-1501"
    inv_file4 = "BRC_2024_1501.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id2,
            "Vendor_Name": vendor_name2,
            "Invoice_Number": inv_num4,
            "Purchase_Order_Number": po_num2,
            "Purchase_Order_File_Name": po_files2,
            "Total_Amount": 80000.00,  # 80% of $100K PO
            "Tax_Amount": 10500.00,  # BUT taxed on full $100K! (WRONG)
            "Tax_Remitted": 10500.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file4,
            "Invoice_File_Name_2": f"{inv_num4}_internal.pd",
            "Line_Item_Description": "Progress Payment #1 - Foundation and Framing (80% complete, 20% retainage)",
        }
    )

    # Invoice 2: Second progress payment - No additional tax
    inv_num5 = "BRC-2024-1623"
    inv_file5 = "BRC_2024_1623.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id2,
            "Vendor_Name": vendor_name2,
            "Invoice_Number": inv_num5,
            "Purchase_Order_Number": po_num2,
            "Purchase_Order_File_Name": po_files2,
            "Total_Amount": 15000.00,  # Additional work
            "Tax_Amount": 0.00,  # No tax on this one
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file5,
            "Invoice_File_Name_2": f"{inv_num5}_internal.pd",
            "Line_Item_Description": "Progress Payment #2 - Electrical and Plumbing",
        }
    )

    # Invoice 3: Retainage release - Should get tax refund on original $20K retainage
    inv_num6 = "BRC-2024-1844"
    inv_file6 = "BRC_2024_1844.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id2,
            "Vendor_Name": vendor_name2,
            "Invoice_Number": inv_num6,
            "Purchase_Order_Number": po_num2,
            "Purchase_Order_File_Name": po_files2,
            "Total_Amount": 20000.00,  # Retainage release
            "Tax_Amount": 0.00,  # Tax already paid on invoice #1
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file6,
            "Invoice_File_Name_2": f"{inv_num6}_internal.pd",
            "Line_Item_Description": "Final Payment - Retainage Release (20% held back)",
        }
    )

    # ========================================================================
    # SCENARIO 3: Out-of-State Vendor - Use Tax
    # ========================================================================
    po_num3 = "PO-2024-003"
    po_files3 = "PO_2024_003_Salesforce_Email.pd"  # Email format
    vendor_id3 = "V-30012"
    vendor_name3 = "Salesforce Inc"

    # Invoice 1: Services only - Use tax self-assessed
    inv_num7 = "SF-2024-88451"
    inv_file7 = "SF_2024_88451.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id3,
            "Vendor_Name": vendor_name3,
            "Invoice_Number": inv_num7,
            "Purchase_Order_Number": po_num3,
            "Purchase_Order_File_Name": po_files3,
            "Total_Amount": 45000.00,
            "Tax_Amount": 4725.00,  # Self-assessed use tax
            "Tax_Remitted": 0.00,  # Vendor didn't collect it
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Use Tax",  # USE TAX!
            "Invoice_File_Name_1": inv_file7,
            "Invoice_File_Name_2": f"{inv_num7}_internal.pd",
            "Line_Item_Description": "Salesforce CRM Implementation Services - Remote",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id3,
            "Vendor_Name": vendor_name3,
            "Invoice_Number": inv_num7,
            "Purchase_Order_Number": po_num3,
            "Purchase_Order_File_Name": po_files3,
            "Total_Amount": 12000.00,
            "Tax_Amount": 1260.00,  # Self-assessed use tax
            "Tax_Remitted": 0.00,
            "Tax_Type": "Use Tax",
            "Tax_Rate_Charged": "10.5%",
            "Invoice_File_Name_1": inv_file7,
            "Invoice_File_Name_2": f"{inv_num7}_internal.pd",
            "Line_Item_Description": "Custom Workflow Automation Development",
        }
    )

    # Invoice 2: Mixed services + shipped goods
    inv_num8 = "SF-2024-90123"
    inv_file8 = "SF_2024_90123.jpg"  # Image format

    transactions.append(
        {
            "Vendor_ID": vendor_id3,
            "Vendor_Name": vendor_name3,
            "Invoice_Number": inv_num8,
            "Purchase_Order_Number": po_num3,
            "Purchase_Order_File_Name": po_files3,
            "Total_Amount": 8000.00,
            "Tax_Amount": 0.00,  # Services - exempt
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Use Tax",
            "Invoice_File_Name_1": inv_file8,
            "Invoice_File_Name_2": f"{inv_num8}_internal.pd",
            "Line_Item_Description": "Training Services - Delivered remotely from CA",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id3,
            "Vendor_Name": vendor_name3,
            "Invoice_Number": inv_num8,
            "Purchase_Order_Number": po_num3,
            "Purchase_Order_File_Name": po_files3,
            "Total_Amount": 2500.00,
            "Tax_Amount": 262.50,  # Self-assessed use tax on shipped goods
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Use Tax",
            "Invoice_File_Name_1": inv_file8,
            "Invoice_File_Name_2": f"{inv_num8}_internal.pd",
            "Line_Item_Description": "Hardware shipped from CA to WA",
        }
    )

    # ========================================================================
    # SCENARIO 4: Professional Services - Hidden Tax (Odd Dollar Amount)
    # ========================================================================
    po_num4 = "PO-2024-004"
    po_files4 = "PO_2024_004_Deloitte.pd"
    vendor_id4 = "V-40089"
    vendor_name4 = "Deloitte Consulting LLP"

    # Invoice 1: Consulting - Odd dollar amount indicates hidden tax
    inv_num9 = "DLT-2024-CC-9821"
    inv_file9 = "DLT_2024_CC_9821.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id4,
            "Vendor_Name": vendor_name4,
            "Invoice_Number": inv_num9,
            "Purchase_Order_Number": po_num4,
            "Purchase_Order_File_Name": po_files4,
            "Total_Amount": 55250.00,  # ODD! = $50,000 + 10.5% tax
            "Tax_Amount": 0.00,  # But shown as "no tax"
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file9,
            "Invoice_File_Name_2": f"{inv_num9}_internal.pd",
            "Line_Item_Description": "Management Consulting Services - Strategic Planning",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id4,
            "Vendor_Name": vendor_name4,
            "Invoice_Number": inv_num9,
            "Purchase_Order_Number": po_num4,
            "Purchase_Order_File_Name": po_files4,
            "Total_Amount": 22100.00,  # ODD! = $20,000 + 10.5% tax
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file9,
            "Invoice_File_Name_2": f"{inv_num9}_internal.pd",
            "Line_Item_Description": "Tax Advisory Services",
        }
    )

    # Invoice 2: Training services - correctly no tax
    inv_num10 = "DLT-2024-CC-9955"
    inv_file10 = "DLT_2024_CC_9955.xlsx"  # Excel invoice

    transactions.append(
        {
            "Vendor_ID": vendor_id4,
            "Vendor_Name": vendor_name4,
            "Invoice_Number": inv_num10,
            "Purchase_Order_Number": po_num4,
            "Purchase_Order_File_Name": po_files4,
            "Total_Amount": 15000.00,  # Clean amount - no hidden tax
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file10,
            "Invoice_File_Name_2": f"{inv_num10}_internal.pd",
            "Line_Item_Description": "Leadership Training - Executive Team Workshop",
        }
    )

    # ========================================================================
    # SCENARIO 5: Mixed Vendor - Bundled Services (7+ line items)
    # ========================================================================
    po_num5 = "PO-2024-005"
    po_files5 = "PO_2024_005_Oracle_Master.pdf, PO_2024_005_Oracle_Amendment_1.pd"  # Multiple POs!
    vendor_id5 = "V-50023"
    vendor_name5 = "Oracle Corporation"

    # Invoice 1: 7 line items - complex bundled deal
    inv_num11 = "ORA-2024-INV-44521"
    inv_file11 = "ORA_2024_INV_44521.pdf"

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,  # MULTIPLE POs comma-separated
            "Total_Amount": 30000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Oracle Database Custom Development and Integration",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 25000.00,
            "Tax_Amount": 2625.00,
            "Tax_Remitted": 2625.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Oracle Database Enterprise Edition Licenses (10 cores)",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 12000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Cloud Hosting and Infrastructure Services",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 8000.00,
            "Tax_Amount": 840.00,
            "Tax_Remitted": 840.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Server Hardware - Oracle Exadata Storage",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 5000.00,
            "Tax_Amount": 525.00,
            "Tax_Remitted": 525.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Installation Services - Hardware Setup",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 15000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Professional Services - Database Migration and Optimization",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num11,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 10000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file11,
            "Invoice_File_Name_2": f"{inv_num11}_internal.pd",
            "Line_Item_Description": "Annual Maintenance and Support Agreement",
        }
    )

    # Additional invoice with 4 items
    inv_num12 = "ORA-2024-INV-45789"
    inv_file12 = "ORA_2024_INV_45789.png"  # Image invoice

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num12,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 6000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file12,
            "Invoice_File_Name_2": f"{inv_num12}_internal.pd",
            "Line_Item_Description": "Software Development - Custom Reporting Module",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num12,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 4000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file12,
            "Invoice_File_Name_2": f"{inv_num12}_internal.pd",
            "Line_Item_Description": "Testing and Quality Assurance Services",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num12,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 3000.00,
            "Tax_Amount": 0.00,
            "Tax_Remitted": 0.00,
            "Tax_Rate_Charged": "0%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file12,
            "Invoice_File_Name_2": f"{inv_num12}_internal.pd",
            "Line_Item_Description": "Training Services - Administrator Training (8 hours)",
        }
    )

    transactions.append(
        {
            "Vendor_ID": vendor_id5,
            "Vendor_Name": vendor_name5,
            "Invoice_Number": inv_num12,
            "Purchase_Order_Number": po_num5,
            "Purchase_Order_File_Name": po_files5,
            "Total_Amount": 2000.00,
            "Tax_Amount": 210.00,
            "Tax_Remitted": 210.00,
            "Tax_Rate_Charged": "10.5%",
            "Tax_Type": "Sales Tax",
            "Invoice_File_Name_1": inv_file12,
            "Invoice_File_Name_2": f"{inv_num12}_internal.pd",
            "Line_Item_Description": "Documentation and User Manuals (printed materials)",
        }
    )

    return transactions


def create_master_excel():
    """Create master Excel file with all test transactions."""

    transactions = create_test_transactions()

    # Create DataFrame with proper column order
    df = pd.DataFrame(transactions)

    # Add empty OUTPUT columns
    output_columns = [
        "Analysis_Notes",
        "Final_Decision",
        "Tax_Category",
        "Additional_Info",
        "Refund_Basis",
        "Estimated_Refund",
        "Legal_Citation",
        "AI_Confidence",
    ]

    for col in output_columns:
        df[col] = ""

    # Reorder columns: INPUT first, then OUTPUT
    input_columns = [
        "Vendor_ID",
        "Vendor_Name",
        "Invoice_Number",
        "Purchase_Order_Number",
        "Purchase_Order_File_Name",
        "Total_Amount",
        "Tax_Amount",
        "Tax_Remitted",
        "Tax_Rate_Charged",
        "Tax_Type",
        "Invoice_File_Name_1",
        "Invoice_File_Name_2",
        "Line_Item_Description",
    ]

    df = df[input_columns + output_columns]

    # Save to Excel
    output_file = Path("test_data/Master_Claim_Sheet_Comprehensive.xlsx")
    output_file.parent.mkdir(exist_ok=True)

    df.to_excel(output_file, index=False)

    print(f"✅ Created comprehensive master Excel: {output_file}")
    print(f"   Total rows: {len(df)}")
    print(f"   Total invoices: {df['Invoice_Number'].nunique()}")
    print(f"   Total POs: {df['Purchase_Order_Number'].nunique()}")
    print(f"   Sales Tax rows: {len(df[df['Tax_Type'] == 'Sales Tax'])}")
    print(f"   Use Tax rows: {len(df[df['Tax_Type'] == 'Use Tax'])}")

    # Print summary by scenario
    print("\n📊 Breakdown by Purchase Order:")
    for po in df["Purchase_Order_Number"].unique():
        po_data = df[df["Purchase_Order_Number"] == po]
        print(
            f"   {po}: {
                len(po_data)} rows, {
                po_data['Invoice_Number'].nunique()} invoices, Vendor: {
                po_data.iloc[0]['Vendor_Name']}"
        )

    return df


if __name__ == "__main__":
    create_master_excel()
