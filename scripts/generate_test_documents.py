#!/usr/bin/env python3
"""
Generate Fictional Test Invoices and Purchase Orders

Creates realistic test documents for refund engine testing including:
- Invoices from various vendors
- Corresponding purchase orders
- Sample claim sheet Excel file
- Variety of tax scenarios (refund opportunities and non-opportunities)

Output:
- test_data/invoices/XXXX.pdf (sequential numbered invoices)
- test_data/purchase_orders/PO_XXXXX_VENDOR.pdf
- test_data/Refund_Claim_Sheet_Test.xlsx (master claim sheet)
"""

import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Excel generation
import pandas as pd
from reportlab.lib import colors

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDocumentGenerator:
    """Generate fictional invoices, POs, and claim sheets for testing"""

    def __init__(self, output_dir="test_data"):
        self.output_dir = Path(output_dir)
        self.invoices_dir = self.output_dir / "invoices"
        self.pos_dir = self.output_dir / "purchase_orders"

        # Create directories
        self.invoices_dir.mkdir(parents=True, exist_ok=True)
        self.pos_dir.mkdir(parents=True, exist_ok=True)

        # Test scenarios - mix of refund opportunities and non-opportunities
        self.test_scenarios = [
            # REFUND OPPORTUNITIES
            {
                "vendor": "Microsoft Corporation",
                "vendor_number": "V-10001",
                "product": "Microsoft 365 Business Premium - Annual Subscription",
                "amount": 9000.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "DAS",
                "expected_basis": "MPU",
                "expected_refund": "100%",
                "notes": "Multi-state usage, <10% in WA",
            },
            {
                "vendor": "Salesforce Inc",
                "vendor_number": "V-10002",
                "product": "Sales Cloud Enterprise Edition - Q3 2024",
                "amount": 15000.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "DAS",
                "expected_basis": "MPU",
                "expected_refund": "100%",
                "notes": "SaaS with national user base",
            },
            {
                "vendor": "Dell Technologies",
                "vendor_number": "V-10003",
                "product": "PowerEdge R750 Server - Shipped to Oregon datacenter",
                "amount": 25000.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "Tangible Goods",
                "expected_basis": "Out of State - Shipment",
                "expected_refund": "100%",
                "notes": "Shipped to out-of-state location",
            },
            {
                "vendor": "Deloitte Consulting LLP",
                "vendor_number": "V-10004",
                "product": "IT Strategy Consulting Services - September 2024",
                "amount": 45000.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "Services",
                "expected_basis": "Non-Taxable",
                "expected_refund": "100%",
                "notes": "Professional services - human effort, not taxable",
            },
            {
                "vendor": "Adobe Systems Inc",
                "vendor_number": "V-10005",
                "product": "Creative Cloud Enterprise - 50 User Licenses",
                "amount": 12500.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "DAS",
                "expected_basis": "MPU",
                "expected_refund": "100%",
                "notes": "Digital automated service, multi-state users",
            },
            {
                "vendor": "AWS Inc",
                "vendor_number": "V-10006",
                "product": "EC2 Compute Instances - August 2024 (us-west-2)",
                "amount": 8500.00,
                "tax_rate": 0.105,
                "has_po": False,
                "expected_category": "DAS",
                "expected_basis": "Out of State - Services",
                "expected_refund": "100%",
                "notes": "Infrastructure hosted outside Washington",
            },
            {
                "vendor": "Zoom Video Communications",
                "vendor_number": "V-10007",
                "product": "Zoom Enterprise - 500 Users - Annual",
                "amount": 18000.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "DAS",
                "expected_basis": "MPU",
                "expected_refund": "100%",
                "notes": "Digital automated service, multi-state users",
            },
            # SMALLER ITEMS (< $20,000) - Auto "Add to Claim"
            {
                "vendor": "Slack Technologies",
                "vendor_number": "V-10008",
                "product": "Slack Business+ Plan - 100 Users",
                "amount": 6000.00,
                "tax_rate": 0.105,
                "has_po": False,
                "expected_category": "DAS",
                "expected_basis": "MPU",
                "expected_refund": "100%",
                "notes": "Small dollar amount, auto-add to claim sample",
            },
            {
                "vendor": "Oracle Corporation",
                "vendor_number": "V-10009",
                "product": "Oracle Database Standard Edition - License Renewal",
                "amount": 11000.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "License",
                "expected_basis": "Non-Taxable",
                "expected_refund": "100%",
                "notes": "Software license, not prewritten software",
            },
            {
                "vendor": "Workday Inc",
                "vendor_number": "V-10010",
                "product": "Workday HCM Subscription - Q2 2024",
                "amount": 14500.00,
                "tax_rate": 0.105,
                "has_po": True,
                "expected_category": "DAS",
                "expected_basis": "MPU",
                "expected_refund": "100%",
                "notes": "HR SaaS, multi-state employees",
            },
            # NO REFUND OPPORTUNITIES
            {
                "vendor": "Staples Business Advantage",
                "vendor_number": "V-10011",
                "product": "Office Supplies - Various Items",
                "amount": 2500.00,
                "tax_rate": 0.105,
                "has_po": False,
                "expected_category": "Tangible Goods",
                "expected_basis": None,
                "expected_refund": "0%",
                "notes": "Tangible goods delivered in WA, properly taxed",
            },
            {
                "vendor": "Comcast Business",
                "vendor_number": "V-10012",
                "product": "Internet Service - Seattle Office - September 2024",
                "amount": 850.00,
                "tax_rate": 0.105,
                "has_po": False,
                "expected_category": "Telecommunications",
                "expected_basis": None,
                "expected_refund": "0%",
                "notes": "Telecom services in WA, properly taxed",
            },
        ]

        self.claim_sheet_data = []

    def generate_invoice(self, scenario: dict, invoice_number: int):
        """Generate a realistic invoice PDF"""

        # Generate invoice date (random date in 2024, before Oct 1 2025)
        days_ago = random.randint(30, 365)
        invoice_date = datetime(2024, 9, 1) - timedelta(days=days_ago)
        due_date = invoice_date + timedelta(days=30)

        # Calculate amounts
        subtotal = scenario["amount"]
        tax_rate = scenario["tax_rate"]
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        # Generate PDF
        invoice_filename = f"{invoice_number:04d}.pdf"
        invoice_path = self.invoices_dir / invoice_filename

        doc = SimpleDocTemplate(str(invoice_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Company header
        header = Paragraph(
            f"<b>{scenario['vendor']}</b><br/>123 Business Way<br/>Business City, ST 12345<br/>Phone: (555) 123-4567",
            styles["Normal"],
        )
        story.append(header)
        story.append(Spacer(1, 0.3 * inch))

        # Invoice title
        title = Paragraph(f"<b>INVOICE</b>", styles["Title"])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Invoice details
        invoice_info = [
            ["Invoice Number:", f"INV-2024-{invoice_number:04d}"],
            ["Invoice Date:", invoice_date.strftime("%B %d, %Y")],
            ["Due Date:", due_date.strftime("%B %d, %Y")],
            ["Vendor Number:", scenario["vendor_number"]],
        ]
        invoice_table = Table(invoice_info, colWidths=[2 * inch, 3 * inch])
        invoice_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(invoice_table)
        story.append(Spacer(1, 0.3 * inch))

        # Bill to
        bill_to = Paragraph(
            "<b>Bill To:</b><br/>Acme Corporation<br/>456 Client Street<br/>Seattle, WA 98101",
            styles["Normal"],
        )
        story.append(bill_to)
        story.append(Spacer(1, 0.3 * inch))

        # Line items
        line_items = [
            ["#", "Description", "Quantity", "Unit Price", "Amount"],
            ["1", scenario["product"], "1", f"${subtotal:,.2f}", f"${subtotal:,.2f}"],
        ]

        items_table = Table(
            line_items,
            colWidths=[0.5 * inch, 3.5 * inch, 1 * inch, 1.2 * inch, 1.2 * inch],
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 0.3 * inch))

        # Totals
        totals = [
            ["", "", "", "Subtotal:", f"${subtotal:,.2f}"],
            ["", "", "", f"Sales Tax ({tax_rate*100:.2f}%):", f"${tax_amount:,.2f}"],
            ["", "", "", "Total Due:", f"${total:,.2f}"],
        ]

        totals_table = Table(
            totals, colWidths=[0.5 * inch, 3.5 * inch, 1 * inch, 1.2 * inch, 1.2 * inch]
        )
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                    ("ALIGN", (4, 0), (4, -1), "RIGHT"),
                    ("FONTNAME", (3, -1), (4, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (3, -1), (4, -1), 12),
                    ("LINEABOVE", (3, -1), (4, -1), 2, colors.black),
                ]
            )
        )
        story.append(totals_table)
        story.append(Spacer(1, 0.3 * inch))

        # Payment terms
        terms = Paragraph(
            "<b>Payment Terms:</b> Net 30 days<br/><b>Notes:</b> Thank you for your business!",
            styles["Normal"],
        )
        story.append(terms)

        # Build PDF
        doc.build(story)

        print(f"  ✅ Generated invoice: {invoice_filename}")
        return invoice_filename, invoice_date, tax_amount, total

    def generate_purchase_order(self, scenario: dict, po_number: int):
        """Generate a realistic purchase order PDF"""

        if not scenario.get("has_po"):
            return None

        # Generate PO date (before invoice)
        days_ago = random.randint(380, 400)
        po_date = datetime(2024, 9, 1) - timedelta(days=days_ago)

        # PO filename includes vendor name
        vendor_short = (
            scenario["vendor"].split()[0].upper().replace(",", "").replace(".", "")
        )
        po_filename = f"PO_{po_number:05d}_{vendor_short}.pdf"
        po_path = self.pos_dir / po_filename

        doc = SimpleDocTemplate(str(po_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Company header
        header = Paragraph(
            "<b>ACME CORPORATION</b><br/>456 Client Street<br/>Seattle, WA 98101<br/>Phone: (555) 987-6543",
            styles["Normal"],
        )
        story.append(header)
        story.append(Spacer(1, 0.3 * inch))

        # PO title
        title = Paragraph(f"<b>PURCHASE ORDER</b>", styles["Title"])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # PO details
        po_info = [
            ["PO Number:", f"PO-{po_number:05d}"],
            ["PO Date:", po_date.strftime("%B %d, %Y")],
            ["Vendor Number:", scenario["vendor_number"]],
            ["Buyer:", "Jane Procurement"],
        ]
        po_table = Table(po_info, colWidths=[2 * inch, 3 * inch])
        po_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(po_table)
        story.append(Spacer(1, 0.3 * inch))

        # Vendor info
        vendor_info = Paragraph(
            f"<b>Vendor:</b><br/>{scenario['vendor']}<br/>123 Business Way<br/>Business City, ST 12345",
            styles["Normal"],
        )
        story.append(vendor_info)
        story.append(Spacer(1, 0.3 * inch))

        # Line items
        line_items = [
            ["Line", "Description", "Quantity", "Unit Price", "Total"],
            [
                "1",
                scenario["product"],
                "1",
                f"${scenario['amount']:,.2f}",
                f"${scenario['amount']:,.2f}",
            ],
        ]

        items_table = Table(
            line_items,
            colWidths=[0.5 * inch, 3.8 * inch, 1 * inch, 1.2 * inch, 1.2 * inch],
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 0.3 * inch))

        # Total
        total_table = Table(
            [["", "", "", "Total:", f"${scenario['amount']:,.2f}"]],
            colWidths=[0.5 * inch, 3.8 * inch, 1 * inch, 1.2 * inch, 1.2 * inch],
        )
        total_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (3, 0), (4, 0), "RIGHT"),
                    ("FONTNAME", (3, 0), (4, 0), "Helvetica-Bold"),
                    ("LINEABOVE", (3, 0), (4, 0), 2, colors.black),
                ]
            )
        )
        story.append(total_table)
        story.append(Spacer(1, 0.3 * inch))

        # Terms
        terms = Paragraph(
            "<b>Terms & Conditions:</b><br/>• Payment: Net 30 days<br/>• Delivery: As specified in contract<br/>• This PO authorizes the vendor to proceed with order",
            styles["Normal"],
        )
        story.append(terms)

        # Build PDF
        doc.build(story)

        print(f"  ✅ Generated PO: {po_filename}")
        return po_filename

    def generate_claim_sheet(self):
        """Generate master claim sheet Excel file"""

        claim_sheet_path = self.output_dir / "Refund_Claim_Sheet_Test.xlsx"

        df = pd.DataFrame(self.claim_sheet_data)

        # Column order
        columns = [
            "Vendor_Number",
            "Vendor_Name",
            "Invoice_Number",
            "PO_Number",
            "Line_Item_Number",
            "Tax_Remitted",
            "Tax_Percentage_Charged",
            "Line_Item_Amount",
            "Total_Amount",
            "Invoice_Files",
            "PO_Files",
            "Invoice_Date",
            "Transaction_Date",
            "Product_Description",
            "Expected_Tax_Category",
            "Expected_Refund_Basis",
            "Expected_Refund_Percentage",
            "Test_Notes",
        ]

        df = df[columns]

        # Write to Excel
        with pd.ExcelWriter(claim_sheet_path, engine="openpyxl") as writer:
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
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"\n✅ Generated claim sheet: {claim_sheet_path}")
        print(f"   Total rows: {len(df)}")

    def generate_all(self):
        """Generate all test documents"""

        print("=" * 70)
        print("GENERATING TEST DOCUMENTS")
        print("=" * 70)
        print()

        for idx, scenario in enumerate(self.test_scenarios, start=1):
            print(f"\n[{idx}/{len(self.test_scenarios)}] {scenario['vendor']}")

            # Generate invoice
            invoice_file, invoice_date, tax_amount, total = self.generate_invoice(
                scenario, idx
            )

            # Generate PO if applicable
            po_file = (
                self.generate_purchase_order(scenario, 49000 + idx)
                if scenario.get("has_po")
                else ""
            )

            # Add to claim sheet
            self.claim_sheet_data.append(
                {
                    "Vendor_Number": scenario["vendor_number"],
                    "Vendor_Name": scenario["vendor"],
                    "Invoice_Number": f"INV-2024-{idx:04d}",
                    "PO_Number": (
                        f"PO-{49000 + idx:05d}" if scenario.get("has_po") else ""
                    ),
                    "Line_Item_Number": 1,
                    "Tax_Remitted": tax_amount,
                    "Tax_Percentage_Charged": f"{scenario['tax_rate']*100:.1f}%",
                    "Line_Item_Amount": scenario["amount"],
                    "Total_Amount": total,
                    "Invoice_Files": invoice_file,
                    "PO_Files": po_file,
                    "Invoice_Date": invoice_date.strftime("%Y-%m-%d"),
                    "Transaction_Date": (invoice_date - timedelta(days=5)).strftime(
                        "%Y-%m-%d"
                    ),
                    "Product_Description": scenario["product"],
                    "Expected_Tax_Category": scenario["expected_category"],
                    "Expected_Refund_Basis": scenario["expected_basis"],
                    "Expected_Refund_Percentage": scenario["expected_refund"],
                    "Test_Notes": scenario["notes"],
                }
            )

        # Generate claim sheet
        self.generate_claim_sheet()

        print()
        print("=" * 70)
        print("✅ TEST DOCUMENT GENERATION COMPLETE")
        print("=" * 70)
        print()
        print(f"📁 Output directory: {self.output_dir}")
        print(
            f"📄 Invoices: {len([s for s in self.test_scenarios])} files in {self.invoices_dir}"
        )
        print(
            f"📄 Purchase Orders: {len([s for s in self.test_scenarios if s.get('has_po')])} files in {self.pos_dir}"
        )
        print(f"📊 Claim Sheet: {self.output_dir / 'Refund_Claim_Sheet_Test.xlsx'}")
        print()
        print("Summary:")
        refund_opps = len(
            [s for s in self.test_scenarios if s["expected_refund"] != "0%"]
        )
        no_refund = len(
            [s for s in self.test_scenarios if s["expected_refund"] == "0%"]
        )
        print(f"  • Refund Opportunities: {refund_opps}")
        print(f"  • No Refund (Properly Taxed): {no_refund}")
        print()


def main():
    """Main entry point"""
    generator = TestDocumentGenerator(output_dir="test_data")
    generator.generate_all()


if __name__ == "__main__":
    main()
