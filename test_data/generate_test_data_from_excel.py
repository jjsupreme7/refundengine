#!/usr/bin/env python3
"""
Generate test data documents from TestClaimSheet_JJ.xlsx

Reads the user's Excel file with pre-filled amounts and dates,
fills in missing columns (Vendor, filenames, etc.),
then generates matching invoice and PO documents (Excel + PDF).

Usage:
    python test_data/generate_test_data_from_excel.py
"""

import random
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("Warning: reportlab not installed. PDF generation will be skipped.")
    print("Install with: pip install reportlab")


# =============================================================================
# VENDOR POOLS
# =============================================================================

# Use Tax vendors - mix of software, hardware, network, and services
USE_TAX_VENDORS = [
    {"id": "V-UT001", "name": "Salesforce Inc", "products": ["CRM Implementation", "Server Hardware", "Network Installation", "Technical Support"]},
    {"id": "V-UT002", "name": "Amazon Web Services", "products": ["EC2 Compute Services", "Network Equipment", "Storage Arrays", "Data Center Hardware"]},
    {"id": "V-UT003", "name": "ServiceNow Inc", "products": ["ITSM Platform", "Server Maintenance", "Network Monitoring Hardware", "IT Asset Management"]},
    {"id": "V-UT004", "name": "Ericsson Inc", "products": ["Network Installation", "5G Radio Units", "Core Network Equipment", "Technical Support Services"]},
    {"id": "V-UT005", "name": "Nokia Solutions", "products": ["AirScale Radio", "Network Hardware", "Optical Networking Equipment", "Installation Services"]},
    {"id": "V-UT006", "name": "Cisco Systems", "products": ["Network Switches", "Router Equipment", "Firewall Hardware", "Network Installation"]},
    {"id": "V-UT007", "name": "MongoDB Inc", "products": ["Database License", "Technical Support", "Server Configuration", "Cloud Database Services"]},
    {"id": "V-UT008", "name": "Palo Alto Networks", "products": ["Firewall Hardware", "Security Appliances", "Network Security Services", "Threat Prevention"]},
    {"id": "V-UT009", "name": "Juniper Networks", "products": ["Network Switches", "Router Hardware", "Security Equipment", "Network Services"]},
    {"id": "V-UT010", "name": "Arista Networks", "products": ["Data Center Switches", "Network Hardware", "Cloud Networking", "Technical Support"]},
    {"id": "V-UT011", "name": "F5 Networks", "products": ["Load Balancer Hardware", "Application Delivery", "Network Equipment", "Support Services"]},
    {"id": "V-UT012", "name": "NetApp Inc", "products": ["Storage Arrays", "Data Management Hardware", "Cloud Storage Services", "Technical Support"]},
    {"id": "V-UT013", "name": "Splunk Inc", "products": ["Security Software", "Server Hardware", "Infrastructure Monitoring", "Professional Services"]},
    {"id": "V-UT014", "name": "Fortinet Inc", "products": ["Firewall Hardware", "Security Appliances", "Network Equipment", "FortiGate Devices"]},
    {"id": "V-UT015", "name": "CommScope Inc", "products": ["Network Cabling", "Infrastructure Hardware", "Antenna Equipment", "Installation Services"]},
]

# Sales Tax vendors - mix of software, hardware, network, and services
SALES_TAX_VENDORS = [
    {"id": "V-ST001", "name": "Microsoft Corporation", "products": ["Office 365 Licenses", "Surface Devices", "Server Hardware", "Windows Server License"]},
    {"id": "V-ST002", "name": "Oracle Corporation", "products": ["Database License", "Server Hardware", "Exadata Systems", "Technical Support"]},
    {"id": "V-ST003", "name": "Dell Technologies", "products": ["PowerEdge Servers", "Laptop Computers", "Storage Arrays", "Network Switches"]},
    {"id": "V-ST004", "name": "Cisco Systems", "products": ["Network Switches", "Routers", "Security Appliances", "Cisco Phones"]},
    {"id": "V-ST005", "name": "Zones Inc", "products": ["Cisco Switches", "Server Hardware", "IT Equipment Bundle", "Network Installation"]},
    {"id": "V-ST006", "name": "CDW Corporation", "products": ["Computer Hardware", "Network Equipment", "Server Systems", "Printers"]},
    {"id": "V-ST007", "name": "HP Inc", "products": ["Desktop Computers", "Printers", "Server Hardware", "Network Equipment"]},
    {"id": "V-ST008", "name": "Lenovo Group", "products": ["ThinkPad Laptops", "Server Hardware", "ThinkCentre Desktops", "Monitors"]},
    {"id": "V-ST009", "name": "VMware Inc", "products": ["vSphere License", "Server Software", "NSX Networking", "Hardware Support"]},
    {"id": "V-ST010", "name": "Citrix Systems", "products": ["NetScaler ADC", "Virtual Desktop License", "Network Hardware", "Technical Support"]},
    {"id": "V-ST011", "name": "Ericsson Inc", "products": ["Network Equipment", "5G Infrastructure", "Radio Units", "Installation Services"]},
    {"id": "V-ST012", "name": "Nokia Solutions", "products": ["Network Hardware", "5G Equipment", "AirScale Radio", "Core Network"]},
    {"id": "V-ST013", "name": "Motorola Solutions", "products": ["Radio Equipment", "Communication Devices", "Network Infrastructure", "Technical Services"]},
    {"id": "V-ST014", "name": "Zebra Technologies", "products": ["Barcode Scanners", "Mobile Computers", "Printers", "RFID Equipment"]},
    {"id": "V-ST015", "name": "Honeywell Inc", "products": ["Scanning Equipment", "Mobile Devices", "Safety Equipment", "Technical Support"]},
]

# WA Location tax rates (approximate)
WA_LOCATIONS = [
    {"city": "Seattle", "zip": "98101", "rate": 0.1025},
    {"city": "Bellevue", "zip": "98004", "rate": 0.1025},
    {"city": "Tacoma", "zip": "98401", "rate": 0.102},
    {"city": "Redmond", "zip": "98052", "rate": 0.1025},
    {"city": "Spokane", "zip": "99201", "rate": 0.089},
    {"city": "Vancouver", "zip": "98660", "rate": 0.084},
    {"city": "Wenatchee", "zip": "98801", "rate": 0.084},
    {"city": "Olympia", "zip": "98501", "rate": 0.092},
    {"city": "Everett", "zip": "98201", "rate": 0.099},
    {"city": "Kent", "zip": "98032", "rate": 0.102},
]


def generate_invoice_number(prefix: str, index: int) -> str:
    """Generate a realistic invoice number."""
    return f"{prefix}-INV-2024-{index:04d}"


def generate_po_number(index: int) -> str:
    """Generate a realistic PO number."""
    return f"PO-490{random.randint(1000000, 9999999)}"


def get_document_mix(total_rows: int) -> list:
    """
    Determine document availability for each row.
    Returns list of tuples: (has_invoice, has_invoice2, has_po)
    """
    mix = []
    # Invoice only: ~52%
    for _ in range(int(total_rows * 0.52)):
        mix.append((True, False, False))
    # Invoice + PO: ~28%
    for _ in range(int(total_rows * 0.28)):
        mix.append((True, False, True))
    # PO only: ~13%
    for _ in range(int(total_rows * 0.13)):
        mix.append((False, False, True))
    # Invoice + Invoice2 + PO: ~7%
    remaining = total_rows - len(mix)
    for _ in range(remaining):
        mix.append((True, True, True))

    random.shuffle(mix)
    return mix


def fill_use_tax_data(df: pd.DataFrame) -> pd.DataFrame:
    """Fill in missing columns for Use Tax tab."""
    rows = len(df)
    doc_mix = get_document_mix(rows)

    # Track which vendors are used to distribute evenly
    vendor_indices = list(range(len(USE_TAX_VENDORS)))
    random.shuffle(vendor_indices)

    for i in range(rows):
        vendor = USE_TAX_VENDORS[vendor_indices[i % len(USE_TAX_VENDORS)]]
        product = random.choice(vendor["products"])
        has_inv, has_inv2, has_po = doc_mix[i]

        df.at[i, "Vendor ID"] = vendor["id"]
        df.at[i, "Vendor"] = vendor["name"]
        df.at[i, "Description"] = product

        inv_num = generate_invoice_number(vendor["name"].split()[0].upper()[:3], i + 1)
        po_num = generate_po_number(i + 1) if has_po else None

        df.at[i, "Inv No"] = inv_num if has_inv else None
        df.at[i, "PO No"] = po_num

        # File names
        vendor_prefix = vendor["name"].replace(" ", "_").replace(",", "").replace(".", "")
        if has_inv:
            df.at[i, "Inv-1 FileName"] = f"{vendor_prefix}_{inv_num}.xlsx"
        if has_inv2:
            df.at[i, "Inv-2 FileName"] = f"{vendor_prefix}_{inv_num}_internal.xlsx"
        if has_po:
            df.at[i, "PO_FileName"] = f"{vendor_prefix}_{po_num}.xlsx"

    return df


def fill_sales_tax_data(df: pd.DataFrame) -> pd.DataFrame:
    """Fill in missing columns for Sales Tax tab."""
    rows = len(df)
    doc_mix = get_document_mix(rows)

    vendor_indices = list(range(len(SALES_TAX_VENDORS)))
    random.shuffle(vendor_indices)

    for i in range(rows):
        vendor = SALES_TAX_VENDORS[vendor_indices[i % len(SALES_TAX_VENDORS)]]
        product = random.choice(vendor["products"])
        has_inv, has_inv2, has_po = doc_mix[i]

        df.at[i, "Vendor ID"] = vendor["id"]
        df.at[i, "Vendor"] = vendor["name"]
        df.at[i, "Description"] = product

        inv_num = generate_invoice_number(vendor["name"].split()[0].upper()[:3], i + 100)
        po_num = generate_po_number(i + 100) if has_po else None

        df.at[i, "Inv No"] = inv_num if has_inv else None
        df.at[i, "PO No"] = po_num

        vendor_prefix = vendor["name"].replace(" ", "_").replace(",", "").replace(".", "")
        if has_inv:
            df.at[i, "Inv-1 FileName"] = f"{vendor_prefix}_{inv_num}.xlsx"
        if has_inv2:
            df.at[i, "Inv-2 FileName"] = f"{vendor_prefix}_{inv_num}_internal.xlsx"
        if has_po:
            df.at[i, "PO_FileName"] = f"{vendor_prefix}_{po_num}.xlsx"

    return df


def create_invoice_excel(
    output_path: Path,
    invoice_number: str,
    vendor_name: str,
    date,
    subtotal: float,
    tax: float,
    total: float,
    product: str,
    is_use_tax: bool = False,
    ship_to_location: dict = None,
    show_tax_on_invoice: bool = None,
) -> None:
    """Create an invoice Excel file."""
    if ship_to_location is None:
        ship_to_location = random.choice(WA_LOCATIONS)

    # Determine if we show tax on the invoice
    if show_tax_on_invoice is None:
        show_tax_on_invoice = not is_use_tax

    # Calculate reasonable quantity and unit price
    if subtotal > 0:
        quantity = random.randint(1, 10)
        unit_price = round(subtotal / quantity, 2)
    else:
        quantity = 1
        unit_price = 0

    displayed_tax = tax if show_tax_on_invoice else 0
    displayed_total = total if show_tax_on_invoice else subtotal

    # Format date
    if isinstance(date, datetime):
        date_str = date.strftime("%m/%d/%Y")
    elif hasattr(date, 'strftime'):
        date_str = date.strftime("%m/%d/%Y")
    else:
        date_str = str(date)

    invoice_data = {
        "invoice_number": [invoice_number],
        "vendor": [vendor_name],
        "customer": ["JJ INC"],
        "ship_to_city": [ship_to_location.get("city", "Seattle")],
        "ship_to_state": ["WA"],
        "ship_to_zip": [ship_to_location.get("zip", "98101")],
        "date": [date_str],
        "product": [product],
        "quantity": [quantity],
        "unit_price": [unit_price],
        "subtotal": [subtotal],
        "tax": [displayed_tax],
        "total": [displayed_total],
    }

    df = pd.DataFrame(invoice_data)
    df.to_excel(output_path, index=False)


def create_po_excel(
    output_path: Path,
    po_number: str,
    vendor_name: str,
    date,
    amount: float,
    product: str,
) -> None:
    """Create a PO Excel file."""
    # Format date
    if isinstance(date, datetime):
        date_str = date.strftime("%m/%d/%Y")
    elif hasattr(date, 'strftime'):
        date_str = date.strftime("%m/%d/%Y")
    else:
        date_str = str(date)

    po_data = {
        "po_number": [po_number],
        "vendor": [vendor_name],
        "customer": ["JJ INC"],
        "date": [date_str],
        "description": [product],
        "amount": [amount],
        "status": ["Approved"],
    }

    df = pd.DataFrame(po_data)
    df.to_excel(output_path, index=False)


def create_invoice_pdf(
    output_path: Path,
    invoice_number: str,
    vendor_name: str,
    date,
    subtotal: float,
    tax: float,
    total: float,
    product: str,
    is_use_tax: bool = False,
    ship_to_location: dict = None,
    show_tax_on_invoice: bool = None,
) -> None:
    """Create a professional-looking invoice PDF."""
    if not HAS_REPORTLAB:
        return

    if ship_to_location is None:
        ship_to_location = random.choice(WA_LOCATIONS)

    # Determine if we show tax on the invoice
    if show_tax_on_invoice is None:
        show_tax_on_invoice = not is_use_tax

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.darkblue,
    )
    elements.append(Paragraph(vendor_name, header_style))
    elements.append(Spacer(1, 0.25 * inch))

    # Invoice details
    elements.append(Paragraph("<b>INVOICE</b>", styles["Heading2"]))
    elements.append(Paragraph(f"Invoice #: {invoice_number}", styles["Normal"]))

    # Format date
    if isinstance(date, datetime):
        date_str = date.strftime("%B %d, %Y")
    elif hasattr(date, 'strftime'):
        date_str = date.strftime("%B %d, %Y")
    else:
        date_str = str(date)

    elements.append(Paragraph(f"Date: {date_str}", styles["Normal"]))
    elements.append(Spacer(1, 0.25 * inch))

    # Bill To
    elements.append(Paragraph("<b>Bill To:</b>", styles["Normal"]))
    elements.append(Paragraph("JJ INC", styles["Normal"]))
    elements.append(Paragraph(f"{ship_to_location.get('city', 'Seattle')}, WA {ship_to_location.get('zip', '98101')}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))

    # Line items table
    quantity = random.randint(1, 10)
    unit_price = round(subtotal / quantity, 2) if subtotal > 0 else 0
    displayed_tax = tax if show_tax_on_invoice else 0
    displayed_total = total if show_tax_on_invoice else subtotal

    data = [
        ["Description", "Qty", "Unit Price", "Amount"],
        [product, str(quantity), f"${unit_price:,.2f}", f"${subtotal:,.2f}"],
        ["", "", "Subtotal:", f"${subtotal:,.2f}"],
        ["", "", "Tax:", f"${displayed_tax:,.2f}"],
        ["", "", "TOTAL:", f"${displayed_total:,.2f}"],
    ]

    table = Table(data, colWidths=[3.5 * inch, 0.75 * inch, 1.25 * inch, 1.25 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, 1), 1, colors.black),
                ("FONTNAME", (2, -3), (3, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)


def create_po_pdf(
    output_path: Path,
    po_number: str,
    vendor_name: str,
    date,
    amount: float,
    product: str,
) -> None:
    """Create a professional-looking PO PDF."""
    if not HAS_REPORTLAB:
        return

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.darkgreen,
    )
    elements.append(Paragraph("JJ INC", header_style))
    elements.append(Spacer(1, 0.25 * inch))

    # PO details
    elements.append(Paragraph("<b>PURCHASE ORDER</b>", styles["Heading2"]))
    elements.append(Paragraph(f"PO #: {po_number}", styles["Normal"]))

    # Format date
    if isinstance(date, datetime):
        date_str = date.strftime("%B %d, %Y")
    elif hasattr(date, 'strftime'):
        date_str = date.strftime("%B %d, %Y")
    else:
        date_str = str(date)

    elements.append(Paragraph(f"Date: {date_str}", styles["Normal"]))
    elements.append(Spacer(1, 0.25 * inch))

    # Vendor
    elements.append(Paragraph("<b>Vendor:</b>", styles["Normal"]))
    elements.append(Paragraph(vendor_name, styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))

    # Line items
    data = [
        ["Description", "Amount"],
        [product, f"${amount:,.2f}"],
        ["", ""],
        ["TOTAL:", f"${amount:,.2f}"],
    ]

    table = Table(data, colWidths=[5 * inch, 1.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, 1), 1, colors.black),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)


def generate_documents(
    df: pd.DataFrame,
    output_dir: Path,
    is_use_tax: bool = False,
    tax_column: str = "Tax Remitted",
) -> int:
    """Generate invoice and PO documents for each row. Returns count of documents created."""
    invoice_dir = output_dir / "invoices"
    po_dir = output_dir / "purchase_orders"
    invoice_dir.mkdir(parents=True, exist_ok=True)
    po_dir.mkdir(parents=True, exist_ok=True)

    doc_count = 0

    for i, row in df.iterrows():
        vendor_name = row.get("Vendor", "Unknown Vendor")
        if pd.isna(vendor_name):
            continue

        date_val = row.get("Date", datetime.now())
        initial_amount = row.get("Initial Amount", 0)
        tax_amount = row.get(tax_column, 0)
        total_amount = row.get("Total Amount", initial_amount + tax_amount)
        product = row.get("Description", "Product/Service")

        # Edge case: Row 27 (index 26) in Use Tax - vendor incorrectly charged tax
        is_dual_tax_case = is_use_tax and i == 26
        show_tax = is_dual_tax_case or not is_use_tax

        # Wrong rate scenario: pick one Sales Tax row to use Wenatchee location
        ship_location = None
        if not is_use_tax and i == 5:  # Row 6 in Sales Tax
            ship_location = {"city": "Wenatchee", "zip": "98801", "rate": 0.084}

        # Generate invoice if we have a filename
        inv_filename = row.get("Inv-1 FileName")
        if pd.notna(inv_filename) and inv_filename:
            inv_path_xlsx = invoice_dir / inv_filename
            inv_path_pdf = invoice_dir / inv_filename.replace(".xlsx", ".pdf")
            inv_number = row.get("Inv No", "INV-0000")

            create_invoice_excel(
                inv_path_xlsx,
                inv_number,
                vendor_name,
                date_val,
                initial_amount,
                tax_amount,
                total_amount,
                product,
                is_use_tax=is_use_tax,
                ship_to_location=ship_location,
                show_tax_on_invoice=show_tax,
            )
            doc_count += 1

            create_invoice_pdf(
                inv_path_pdf,
                inv_number,
                vendor_name,
                date_val,
                initial_amount,
                tax_amount,
                total_amount,
                product,
                is_use_tax=is_use_tax,
                ship_to_location=ship_location,
                show_tax_on_invoice=show_tax,
            )
            doc_count += 1

        # Generate secondary invoice if exists
        inv2_filename = row.get("Inv-2 FileName")
        if pd.notna(inv2_filename) and inv2_filename:
            inv2_path_xlsx = invoice_dir / inv2_filename
            inv_number = row.get("Inv No", "INV-0000")
            create_invoice_excel(
                inv2_path_xlsx,
                f"{inv_number}-2",
                vendor_name,
                date_val,
                initial_amount,
                tax_amount,
                total_amount,
                f"{product} - Internal Copy",
                is_use_tax=is_use_tax,
                show_tax_on_invoice=show_tax,
            )
            doc_count += 1

        # Generate PO if we have a filename
        po_filename = row.get("PO_FileName")
        if pd.notna(po_filename) and po_filename:
            po_path_xlsx = po_dir / po_filename
            po_path_pdf = po_dir / po_filename.replace(".xlsx", ".pdf")
            po_number = row.get("PO No", "PO-0000")

            create_po_excel(
                po_path_xlsx,
                po_number,
                vendor_name,
                date_val,
                initial_amount,
                product,
            )
            doc_count += 1

            create_po_pdf(
                po_path_pdf,
                po_number,
                vendor_name,
                date_val,
                initial_amount,
                product,
            )
            doc_count += 1

    return doc_count


def main():
    """Main function to generate test data."""
    # Input/output paths - SAME FILE, updated in place
    excel_file = Path("/Users/jacoballen/Desktop/TestClaimSheet_JJ.xlsx")
    output_base = Path(__file__).parent  # test_data folder

    print(f"Reading Excel file: {excel_file}")

    # Read both sheets
    df_use_tax = pd.read_excel(excel_file, sheet_name="Use Tax")
    df_sales_tax = pd.read_excel(excel_file, sheet_name="Sales Tax")

    print(f"Use Tax rows: {len(df_use_tax)}")
    print(f"Sales Tax rows: {len(df_sales_tax)}")

    # Fill in missing data
    print("\nFilling Use Tax data...")
    df_use_tax = fill_use_tax_data(df_use_tax)

    print("Filling Sales Tax data...")
    df_sales_tax = fill_sales_tax_data(df_sales_tax)

    # Create output directories
    use_tax_dir = output_base / "use_tax"
    sales_tax_dir = output_base / "sales_tax"

    # Generate documents
    print("\nGenerating Use Tax documents...")
    use_doc_count = generate_documents(df_use_tax, use_tax_dir, is_use_tax=True, tax_column="Tax Remitted")

    print("Generating Sales Tax documents...")
    sales_doc_count = generate_documents(df_sales_tax, sales_tax_dir, is_use_tax=False, tax_column="Tax Paid")

    # Save back to the SAME Excel file (update existing tabs)
    print(f"\nSaving updated data back to: {excel_file}")
    with pd.ExcelWriter(excel_file, engine="openpyxl", mode="w") as writer:
        df_use_tax.to_excel(writer, sheet_name="Use Tax", index=False)
        df_sales_tax.to_excel(writer, sheet_name="Sales Tax", index=False)

    print(f"\n{'='*60}")
    print("TEST DATA GENERATION COMPLETE!")
    print(f"{'='*60}")
    print(f"\nExcel updated: {excel_file}")
    print(f"\nUse Tax documents: {use_tax_dir}")
    print(f"  - Invoices: {use_tax_dir / 'invoices'}")
    print(f"  - POs: {use_tax_dir / 'purchase_orders'}")
    print(f"\nSales Tax documents: {sales_tax_dir}")
    print(f"  - Invoices: {sales_tax_dir / 'invoices'}")
    print(f"  - POs: {sales_tax_dir / 'purchase_orders'}")

    print(f"\nTotal documents created: {use_doc_count + sales_doc_count}")
    print(f"  - Use Tax: {use_doc_count}")
    print(f"  - Sales Tax: {sales_doc_count}")

    # Edge case notes
    print(f"\nEdge cases included:")
    print(f"  - Row 27 (Use Tax): Vendor incorrectly charged sales tax (shows tax on invoice)")
    print(f"  - Row 6 (Sales Tax): Wrong Rate - Wenatchee location with higher rate charged")


if __name__ == "__main__":
    main()
