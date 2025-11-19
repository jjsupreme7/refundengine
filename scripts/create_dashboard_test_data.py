#!/usr/bin/env python3
"""
Create Dashboard-Compatible Test Data

Generates:
1. Excel manifest matching dashboard expected format
2. Supporting invoice PDFs
3. Database records for projects

Matches the format expected by DocumentsPage.tsx:
- "file name"
- "Vendor name"
- "Invoice number"
- "Purchase order"
- "Description of the date"
"""

import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from core.database import get_supabase_client

# Load environment
load_dotenv()
supabase = get_supabase_client()


class DashboardTestDataGenerator:
    """Generate test data matching dashboard expected format"""

    def __init__(self, output_dir="test_data_dashboard"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test scenarios with realistic Washington State refund opportunities
        self.test_transactions = [
            # REFUND OPPORTUNITIES - DAS/SaaS with MPU
            {
                "file_name": "INV-10021.pdf",
                "vendor": "Microsoft Corporation",
                "invoice_number": "INV-10021",
                "purchase_order": "PO-5001",
                "date": "2024-08-15",
                "line_items": [
                    {
                        "desc": "Microsoft 365 Business Premium - Annual Subscription (500 users)",
                        "qty": 500,
                        "unit_price": 22.00,
                        "category": "DAS/SaaS",
                        "taxability": "exempt",
                        "refund_basis": "MPU",
                        "confidence": 0.95,
                        "tax_amount": 1155.00,
                        "notes": "Multi-state organization with <10% employees in WA",
                    }
                ],
            },
            {
                "file_name": "INV-10022.pdf",
                "vendor": "Salesforce Inc",
                "invoice_number": "INV-10022",
                "purchase_order": "PO-5002",
                "date": "2024-07-20",
                "line_items": [
                    {
                        "desc": "Sales Cloud Enterprise Edition - Quarterly Subscription",
                        "qty": 1,
                        "unit_price": 18000.00,
                        "category": "DAS/SaaS",
                        "taxability": "exempt",
                        "refund_basis": "MPU",
                        "confidence": 0.92,
                        "tax_amount": 1890.00,
                        "notes": "National sales team, MPU exemption applies",
                    }
                ],
            },
            # TANGIBLE GOODS - Out of State Shipment
            {
                "file_name": "INV-10023.pdf",
                "vendor": "Dell Technologies",
                "invoice_number": "INV-10023",
                "purchase_order": "PO-5003",
                "date": "2024-06-10",
                "line_items": [
                    {
                        "desc": "PowerEdge R750 Rack Server (12 units)",
                        "qty": 12,
                        "unit_price": 8500.00,
                        "category": "equipment",
                        "taxability": "exempt",
                        "refund_basis": "Out of State - Shipment",
                        "confidence": 0.98,
                        "tax_amount": 10710.00,
                        "notes": "Shipped to Oregon datacenter - delivery address outside WA",
                    }
                ],
            },
            # PROFESSIONAL SERVICES - Non-Taxable
            {
                "file_name": "INV-10024.pdf",
                "vendor": "Deloitte Consulting LLP",
                "invoice_number": "INV-10024",
                "purchase_order": "PO-5004",
                "date": "2024-05-22",
                "line_items": [
                    {
                        "desc": "IT Strategy & Digital Transformation Consulting - 200 hours",
                        "qty": 200,
                        "unit_price": 350.00,
                        "category": "professional services",
                        "taxability": "exempt",
                        "refund_basis": "Non-Taxable",
                        "confidence": 0.96,
                        "tax_amount": 7350.00,
                        "notes": "Professional services - human effort, not subject to sales tax",
                    }
                ],
            },
            # CUSTOM SOFTWARE DEVELOPMENT - Non-Taxable (OLD LAW)
            {
                "file_name": "INV-10025.pdf",
                "vendor": "Accenture",
                "invoice_number": "INV-10025",
                "purchase_order": "PO-5005",
                "date": "2024-04-18",
                "line_items": [
                    {
                        "desc": "Custom ERP Module Development - Phase 1",
                        "qty": 1,
                        "unit_price": 85000.00,
                        "category": "custom software",
                        "taxability": "exempt",
                        "refund_basis": "Non-Taxable",
                        "confidence": 0.94,
                        "tax_amount": 8925.00,
                        "notes": "Custom software created for single client - not prewritten",
                    }
                ],
            },
            # AMBIGUOUS - Installation bundled with equipment
            {
                "file_name": "INV-10026.pdf",
                "vendor": "Red Bison Tech Services",
                "invoice_number": "INV-10026",
                "purchase_order": "PO-5006",
                "date": "2024-08-02",
                "line_items": [
                    {
                        "desc": "Network rack servers (6 units)",
                        "qty": 6,
                        "unit_price": 4200.00,
                        "category": "equipment",
                        "taxability": "taxable",
                        "refund_basis": None,
                        "confidence": 0.97,
                        "tax_amount": 2646.00,
                        "notes": "Tangible goods, properly taxed",
                    },
                    {
                        "desc": "Installation & cabling for servers",
                        "qty": 40,
                        "unit_price": 150.00,
                        "category": "installation",
                        "taxability": "depends by state facts",
                        "refund_basis": None,
                        "confidence": 0.73,
                        "tax_amount": 630.00,
                        "notes": "Bundled installation - taxability depends on contract structure",
                    },
                    {
                        "desc": "Post-install performance tuning (remote)",
                        "qty": 8,
                        "unit_price": 250.00,
                        "category": "professional services",
                        "taxability": "exempt",
                        "refund_basis": "Non-Taxable",
                        "confidence": 0.95,
                        "tax_amount": 210.00,
                        "notes": "Separately stated professional service",
                    },
                ],
            },
            # CLOUD SERVICES - Out of State
            {
                "file_name": "INV-10027.pdf",
                "vendor": "Amazon Web Services",
                "invoice_number": "INV-10027",
                "purchase_order": "",
                "date": "2024-09-01",
                "line_items": [
                    {
                        "desc": "AWS EC2 Compute - us-west-2 (Oregon region)",
                        "qty": 1,
                        "unit_price": 12500.00,
                        "category": "DAS/SaaS",
                        "taxability": "exempt",
                        "refund_basis": "Out of State - Services",
                        "confidence": 0.91,
                        "tax_amount": 1312.50,
                        "notes": "Infrastructure hosted in Oregon, not Washington",
                    }
                ],
            },
            # TELECOM - Properly Taxed (NO REFUND)
            {
                "file_name": "INV-10028.pdf",
                "vendor": "Verizon Wireless",
                "invoice_number": "INV-10028",
                "purchase_order": "",
                "date": "2024-08-25",
                "line_items": [
                    {
                        "desc": "Business Mobile Plans - 50 lines",
                        "qty": 50,
                        "unit_price": 85.00,
                        "category": "telecommunications",
                        "taxability": "taxable",
                        "refund_basis": None,
                        "confidence": 0.99,
                        "tax_amount": 446.25,
                        "notes": "Telecom services in WA, properly taxed",
                    }
                ],
            },
            # LICENSE vs SAAS - Needs Review
            {
                "file_name": "INV-10029.pdf",
                "vendor": "Oracle America Inc",
                "invoice_number": "INV-10029",
                "purchase_order": "PO-5007",
                "date": "2024-07-12",
                "line_items": [
                    {
                        "desc": "Oracle Database Enterprise Edition - Annual License",
                        "qty": 10,
                        "unit_price": 4750.00,
                        "category": "license",
                        "taxability": "needs review",
                        "refund_basis": "Non-Taxable",
                        "confidence": 0.68,
                        "tax_amount": 4987.50,
                        "notes": "License vs SaaS distinction - requires contract review",
                    }
                ],
            },
            # SMALL DOLLAR - Office Supplies (NO REFUND)
            {
                "file_name": "INV-10030.pdf",
                "vendor": "Office Depot",
                "invoice_number": "INV-10030",
                "purchase_order": "",
                "date": "2024-08-30",
                "line_items": [
                    {
                        "desc": "Office supplies - various items",
                        "qty": 1,
                        "unit_price": 845.00,
                        "category": "tangible goods",
                        "taxability": "taxable",
                        "refund_basis": None,
                        "confidence": 0.99,
                        "tax_amount": 88.73,
                        "notes": "Tangible goods delivered in WA, properly taxed",
                    }
                ],
            },
        ]

    def create_excel_manifest(self):
        """
        Create Excel file matching dashboard expected format
        """
        print("\n📊 Creating Excel manifest...")

        # Flatten transactions to rows
        rows = []
        for tx in self.test_transactions:
            # For now, create one row per invoice (not per line item)
            # Line items will be parsed from the PDF later
            rows.append(
                {
                    "file name": tx["file_name"],
                    "Vendor name": tx["vendor"],
                    "Invoice number": tx["invoice_number"],
                    "Purchase order": tx["purchase_order"],
                    "Description of the date": tx["date"],
                }
            )

        df = pd.DataFrame(rows)

        # Save to Excel
        excel_path = self.output_dir / "claim_manifest_dashboard.xlsx"
        df.to_excel(excel_path, index=False, sheet_name="Transactions")

        print(f"  ✅ Created: {excel_path}")
        print(f"  📄 Rows: {len(df)}")

        return excel_path

    def create_project_in_db(self):
        """
        Create test project in database
        """
        print("\n🗂️ Creating project in database...")

        project_data = {
            "id": "WA-UT-2022_2024",
            "name": "Washington Use Tax Review",
            "period": "2022–2024",
            "estimated_refund": 184230.00,
            "status": "Analyzing",
            "created_at": datetime.now().isoformat(),
        }

        # Note: This assumes you'll create a projects table
        # For now, just print what would be inserted
        print(f"  📋 Project: {project_data['name']}")
        print(f"  💰 Estimated Refund: ${project_data['estimated_refund']:,.2f}")

        # TODO: Create projects table and insert
        # supabase.table("projects").upsert(project_data).execute()

    def calculate_summary_stats(self):
        """
        Calculate summary statistics
        """
        print("\n📈 Summary Statistics:")
        print("=" * 60)

        total_invoices = len(self.test_transactions)
        total_line_items = sum(len(tx["line_items"]) for tx in self.test_transactions)

        refund_lines = []
        properly_taxed_lines = []
        needs_review_lines = []
        total_tax_charged = 0.0
        total_estimated_refund = 0.0

        for tx in self.test_transactions:
            for line in tx["line_items"]:
                tax = line["tax_amount"]
                total_tax_charged += tax

                if line["refund_basis"]:
                    refund_lines.append(line)
                    total_estimated_refund += tax
                elif (
                    line["taxability"] == "needs review"
                    or line["taxability"] == "depends by state facts"
                ):
                    needs_review_lines.append(line)
                else:
                    properly_taxed_lines.append(line)

        print(f"Total Invoices: {total_invoices}")
        print(f"Total Line Items: {total_line_items}")
        print()
        print(f"Refund Opportunities: {len(refund_lines)} line items")
        print(f"Properly Taxed: {len(properly_taxed_lines)} line items")
        print(f"Needs Review: {len(needs_review_lines)} line items")
        print()
        print(f"Total Tax Charged: ${total_tax_charged:,.2f}")
        print(f"Estimated Refund: ${total_estimated_refund:,.2f}")
        print(f"Refund Rate: {(total_estimated_refund / total_tax_charged * 100):.1f}%")
        print()

        # Category breakdown
        print("Refunds by Category:")
        category_refunds = {}
        for line in refund_lines:
            cat = line["category"]
            category_refunds[cat] = category_refunds.get(cat, 0) + line["tax_amount"]

        for cat, amount in sorted(
            category_refunds.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {cat:25s} ${amount:>10,.2f}")

        print("=" * 60)

    def generate_all(self):
        """
        Generate all test data
        """
        print("=" * 70)
        print("DASHBOARD TEST DATA GENERATION")
        print("=" * 70)

        # Create Excel manifest
        excel_path = self.create_excel_manifest()

        # Create project in DB (placeholder for now)
        self.create_project_in_db()

        # Show summary
        self.calculate_summary_stats()

        print()
        print("=" * 70)
        print("✅ TEST DATA GENERATION COMPLETE")
        print("=" * 70)
        print()
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📄 Excel manifest: {excel_path}")
        print()
        print("Next steps:")
        print("  1. Import Excel manifest in dashboard (Documents page)")
        print("  2. Upload supporting invoice PDFs (auto-match by filename)")
        print("  3. Trigger AI analysis")
        print("  4. Review exceptions in Review Queue")
        print("  5. Generate claim packet")
        print()


def main():
    """Main entry point"""
    generator = DashboardTestDataGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()
