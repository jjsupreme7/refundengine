#!/usr/bin/env python3
"""
Enforced Analysis Workflow - Guarantees thorough analysis by forcing the process.

This script walks through each analysis step and won't proceed until all
required fields are filled. Output is marked with a process token that
the validation hook checks for.

Usage:
    python scripts/analyze_row.py --file "Use Tax 2024" --row 5
    python scripts/analyze_row.py --file "Sales Tax 2024" --limit 10
    python scripts/analyze_row.py --file "Use Tax 2023" --vendor "ACME"
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from refund_engine.invoice_text import InvoiceTextResult, extract_invoice_text
from scripts.validate_analysis import validate_row, is_valid_citation


# =============================================================================
# DATASET CONFIGURATIONS
# =============================================================================

DATASETS = {
    "Sales Tax 2024": {
        "source_file": "~/Desktop/Files/Files to be Analyzed/Final 2024 Denodo Review.xlsx",
        "output_file": "~/Desktop/Files/Analyzed_Output/Final 2024 Denodo Review - Analyzed.xlsx",
        "sheet_name": "Real Run",
        "columns": {
            "vendor": "name1_po_vendor_name",
            "tax_amount": "hwste_tax_amount_lc",
            "tax_base": "hwbas_tax_base_lc",
            "description": "txz01_po_description",
            "invoice_1": "Inv 1",
            "invoice_2": "Inv 2",
            "analysis_col": "Recon Analysis",  # Empty means not analyzed
        },
        "filters": {
            "Paid?": "PAID",
        },
        "invoice_path": "~/Desktop/Invoices/",
    },
    "Use Tax 2023": {
        "source_file": "~/Desktop/Files/Files to be Analyzed/Use Tax Phase 3 2023.xlsx",
        "output_file": "~/Desktop/Files/Analyzed_Output/Phase_3_2023_Use Tax - Analyzed.xlsx",
        "sheet_name": None,  # First sheet
        "columns": {
            "vendor": "Vendor Name",
            "tax_amount": "Tax Remit",
            "description": "Description",
            "invoice_1": "Inv-1PDF",
            "invoice_2": "Inv-2PDF",
            "analysis_col": "KOM Analysis & Notes",
        },
        "filters": {
            "INDICATOR": "Remit",
        },
        "invoice_path": "~/Desktop/Invoices/",
    },
    "Use Tax 2024": {
        "source_file": "~/Desktop/Files/Files to be Analyzed/Use Tax Phase 3 2024 Oct 17.xlsx",
        "output_file": "~/Desktop/Files/Analyzed_Output/Phase_3_2024_Use Tax - Analyzed.xlsx",
        "sheet_name": None,
        "columns": {
            "vendor": "Vendor Name",
            "tax_amount": "Tax Remit",
            "description": "Description",
            "invoice_1": "Inv-1PDF",
            "invoice_2": "Inv-2PDF",
            "analysis_col": "KOM Analysis & Notes",
        },
        "filters": {
            "INDICATOR": "Remit",
        },
        "invoice_path": "~/Desktop/Invoices/",
    },
}


# =============================================================================
# PROCESS TOKEN - Proves analysis went through enforced workflow
# =============================================================================

def generate_process_token():
    """Generate a unique token proving this went through the enforced process."""
    timestamp = datetime.now().isoformat()
    return f"ENFORCED_PROCESS|{timestamp}|v1"


def has_process_token(reasoning: str) -> bool:
    """Check if AI_Reasoning contains a valid process token."""
    return "ENFORCED_PROCESS|" in str(reasoning)


# =============================================================================
# ANALYSIS FORM - The enforced structure
# =============================================================================

class AnalysisForm:
    """
    Structured form that MUST be filled for each row.
    Cannot generate output until all required fields are filled.
    """

    def __init__(self):
        # Invoice Verification (REQUIRED)
        self.invoice_number = None
        self.invoice_date = None
        self.pdf_filename = None
        self.invoice_text_preview = None  # First 500 chars as proof of read

        # Delivery Location (REQUIRED)
        self.ship_to_address = None
        self.city_state_zip = None

        # Line Item Matching (REQUIRED)
        self.excel_description = None
        self.excel_amount = None
        self.matched_invoice_line = None
        self.invoice_line_text = None
        self.amount_matches = None

        # Vendor Research (REQUIRED)
        self.vendor_description = None  # What does vendor do?
        self.vendor_business_model = None  # Products/services they sell
        self.vendor_size_location = None  # Company size, HQ location
        self.vendor_research_url = None  # Source URL
        self.research_source = None  # Source used for citation output

        # Product/Service Analysis (REQUIRED)
        self.product_description = None  # What is T-Mobile buying?
        self.product_how_it_works = None  # How does product/service function?
        self.product_category = None  # Physical goods / Software / Human labor / Construction
        self.how_determined = None  # "invoice_clear", "web_search", "vendor_known"

        # Tax Reasoning (REQUIRED)
        self.is_retail_sale = None  # Yes/No
        self.why_taxable_or_not = None  # Explanation of tax treatment
        self.exemption_category = None  # If exempt, what category?

        # Tax Determination (REQUIRED)
        self.product_type = None  # DAS, TPP, Service, Construction, Custom Software
        self.exemption_basis = None  # MPU, OOS, Professional Services, etc.
        self.citation = None
        self.citation_valid = None

        # Decision (REQUIRED)
        self.final_decision = None  # REFUND, NO REFUND, REVIEW
        self.review_reason = None  # If REVIEW, what needs checking
        self.confidence = None
        self.estimated_refund = None

        # Process token
        self.process_token = None

    def get_missing_fields(self) -> list:
        """Return list of required fields that are still empty."""
        required = [
            # Invoice verification
            ("invoice_number", self.invoice_number),
            ("invoice_date", self.invoice_date),
            ("pdf_filename", self.pdf_filename),
            ("ship_to_address", self.ship_to_address),
            ("matched_invoice_line", self.matched_invoice_line),
            # Vendor research
            ("vendor_description", self.vendor_description),
            ("vendor_business_model", self.vendor_business_model),
            # Product analysis
            ("product_description", self.product_description),
            ("product_how_it_works", self.product_how_it_works),
            # Tax reasoning
            ("why_taxable_or_not", self.why_taxable_or_not),
            # Tax determination
            ("product_type", self.product_type),
            ("citation", self.citation),
            ("final_decision", self.final_decision),
            ("confidence", self.confidence),
        ]
        return [name for name, value in required if not value]

    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        return len(self.get_missing_fields()) == 0

    def generate_ai_reasoning(self) -> str:
        """Generate AI_Reasoning from the filled form."""
        if not self.is_complete():
            missing = self.get_missing_fields()
            raise ValueError(f"Cannot generate output - missing fields: {missing}")

        # Generate process token
        self.process_token = generate_process_token()

        # Build the reasoning with all required sections
        lines = [
            f"INVOICE VERIFIED: Invoice #{self.invoice_number} dated {self.invoice_date}",
            f"SHIP-TO: {self.ship_to_address}",
            f"MATCHED LINE ITEM: {self.invoice_line_text or self.matched_invoice_line} @ ${self.excel_amount:,.2f}",
            "---",
            "",
            "VENDOR RESEARCH (from web search):",
            f"{self.vendor_description} {self.vendor_business_model}",
        ]

        if self.vendor_size_location:
            lines.append(f"{self.vendor_size_location}")
        if self.vendor_research_url:
            lines.append(f"Source: {self.vendor_research_url}")

        lines.append("")
        lines.append("PRODUCT/SERVICE ANALYSIS:")
        lines.append(f"{self.product_description}")
        if self.product_how_it_works:
            lines.append(f"{self.product_how_it_works}")

        lines.append("")
        lines.append("WHY THIS IS/ISN'T TAXABLE:")
        lines.append(f"{self.why_taxable_or_not}")
        if self.exemption_category:
            lines.append(f"Exemption category: {self.exemption_category}")

        lines.append("")
        lines.append("TAX ANALYSIS:")
        lines.append(f"- Product Type: {self.product_type}")
        lines.append(f"- Exemption Basis: {self.exemption_basis or 'N/A - taxable'}")
        lines.append(f"- Citation: {self.citation}")

        lines.append("")
        lines.append(f"DECISION: {self.final_decision}")
        if self.final_decision == "REVIEW" and self.review_reason:
            lines.append(f"REVIEW NEEDED: {self.review_reason}")
        if self.estimated_refund:
            lines.append(f"ESTIMATED REFUND: ${self.estimated_refund:,.2f}")

        # Add process token (proves this went through enforced workflow)
        lines.append("")
        lines.append(f"[{self.process_token}]")

        return "\n".join(lines)

    def to_output_row(self) -> dict:
        """Convert form to output row dict."""
        return {
            "Product_Desc": self.product_description,
            "Product_Type": self.product_type,
            "Service_Classification": self.product_type,
            "Refund_Basis": self.exemption_basis,
            "Citation": self.citation,
            "Citation_Source": self.research_source or self.vendor_research_url or "",
            "Confidence": self.confidence,
            "Estimated_Refund": self.estimated_refund or 0,
            "Final_Decision": self.final_decision,
            "AI_Reasoning": self.generate_ai_reasoning(),
            "Needs_Review": "Yes" if self.final_decision == "REVIEW" else "No",
        }


# =============================================================================
# ROW CONTEXT - Data needed for analysis
# =============================================================================

class RowContext:
    """All context needed to analyze a single row."""

    def __init__(self, row_data: pd.Series, dataset_config: dict):
        self.row_data = row_data
        self.config = dataset_config
        self.cols = dataset_config["columns"]

        # Extract key fields
        self.vendor = row_data.get(self.cols["vendor"], "Unknown")
        self.tax_amount = row_data.get(self.cols["tax_amount"], 0)
        self.tax_base = row_data.get(self.cols.get("tax_base", ""), 0) or 0
        self.description = row_data.get(self.cols.get("description", ""), "")

        # Invoice files
        self.invoice_1 = row_data.get(self.cols["invoice_1"], "")
        self.invoice_2 = row_data.get(self.cols.get("invoice_2", ""), "")

        # Invoice path
        self.invoice_dir = os.path.expanduser(dataset_config["invoice_path"])

    def get_invoice_path(self, invoice_num: int = 1) -> str:
        """Get full path to invoice PDF."""
        filename = self.invoice_1 if invoice_num == 1 else self.invoice_2
        if pd.isna(filename) or not filename:
            return None
        return os.path.join(self.invoice_dir, filename)

    def extract_invoice_text(
        self,
        invoice_num: int = 1,
        *,
        max_pages: int = 4,
    ) -> InvoiceTextResult | None:
        """Extract invoice text using PDF text extraction with OCR fallback."""
        invoice_path = self.get_invoice_path(invoice_num)
        if not invoice_path:
            return None
        return extract_invoice_text(invoice_path, max_pages=max_pages)

    def display_summary(self):
        """Print summary of this row."""
        print("\n" + "="*60)
        print("ROW TO ANALYZE")
        print("="*60)
        print(f"Vendor:      {self.vendor}")
        print(f"Tax Amount:  ${self.tax_amount:,.2f}")
        if self.tax_base:
            print(f"Tax Base:    ${self.tax_base:,.2f}")
        if self.description and not pd.isna(self.description):
            print(f"Description: {self.description[:100]}...")
        print(f"Invoice 1:   {self.invoice_1}")
        if self.invoice_2 and not pd.isna(self.invoice_2):
            print(f"Invoice 2:   {self.invoice_2}")
        print("="*60)


# =============================================================================
# MAIN ANALYSIS WORKFLOW
# =============================================================================

def load_dataset(dataset_name: str) -> tuple:
    """Load source data and return (dataframe, config)."""
    if dataset_name not in DATASETS:
        print(f"Unknown dataset: {dataset_name}")
        print(f"Available: {list(DATASETS.keys())}")
        sys.exit(1)

    config = DATASETS[dataset_name]
    source_path = os.path.expanduser(config["source_file"])

    print(f"Loading: {source_path}")

    if config["sheet_name"]:
        df = pd.read_excel(source_path, sheet_name=config["sheet_name"])
    else:
        df = pd.read_excel(source_path)

    return df, config


def filter_unanalyzed(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Filter to rows that haven't been analyzed yet."""
    cols = config["columns"]

    # Apply dataset-specific filters
    mask = pd.Series([True] * len(df))

    for col, value in config.get("filters", {}).items():
        if col in df.columns:
            mask &= (df[col] == value)

    # Must have invoice
    if cols["invoice_1"] in df.columns:
        mask &= df[cols["invoice_1"]].notna()

    # Analysis column must be empty (not yet analyzed)
    if cols["analysis_col"] in df.columns:
        analysis_series = df[cols["analysis_col"]]
        mask &= analysis_series.isna() | (analysis_series.astype(str).str.strip() == "")

    return df[mask]


def display_form_status(form: AnalysisForm):
    """Display current state of the analysis form."""
    print("\n" + "-"*40)
    print("ANALYSIS FORM STATUS")
    print("-"*40)

    fields = [
        ("Invoice #", form.invoice_number),
        ("Invoice Date", form.invoice_date),
        ("Ship-To", form.ship_to_address),
        ("Line Match", form.matched_invoice_line),
        ("Product", form.product_description),
        ("Type", form.product_type),
        ("Citation", form.citation),
        ("Decision", form.final_decision),
        ("Confidence", form.confidence),
    ]

    for name, value in fields:
        status = "✓" if value else "○"
        display_value = str(value)[:40] if value else "(empty)"
        print(f"  {status} {name}: {display_value}")

    missing = form.get_missing_fields()
    if missing:
        print(f"\nMissing {len(missing)} required field(s)")
    else:
        print("\n✓ ALL REQUIRED FIELDS FILLED")


def display_invoice_text_preview(
    label: str,
    result: InvoiceTextResult | None,
    *,
    max_chars: int = 1000,
):
    """Print invoice text extraction status and a preview block."""
    if result is None:
        return

    print("\n" + "-" * 60)
    print(f"{label.upper()} TEXT PREVIEW")
    print("-" * 60)
    print(f"Source: {result.pdf_path}")
    print(f"Method: {result.method}")
    print(f"Pages processed: {result.pages_processed}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    preview = result.preview(max_chars=max_chars)
    if preview:
        print("\nExtracted text preview:")
        print(preview)
    else:
        print("\nNo extractable text found.")
    print("-" * 60)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Enforced Analysis Workflow")
    parser.add_argument("--file", "-f", required=True,
                        choices=list(DATASETS.keys()),
                        help="Dataset to analyze")
    parser.add_argument("--row", "-r", type=int,
                        help="Specific row index to analyze")
    parser.add_argument("--limit", "-l", type=int, default=1,
                        help="Number of rows to analyze")
    parser.add_argument("--vendor", "-v", type=str,
                        help="Filter to specific vendor")
    parser.add_argument("--min-amount", type=float,
                        help="Minimum tax amount filter")
    parser.add_argument("--list", action="store_true",
                        help="List available rows without analyzing")
    parser.add_argument(
        "--max-invoice-pages",
        type=int,
        default=4,
        help="Max pages to read/OCR per invoice when generating previews",
    )

    args = parser.parse_args()

    # Load data
    df, config = load_dataset(args.file)
    print(f"Loaded {len(df)} total rows")

    # Filter to unanalyzed
    df_filtered = filter_unanalyzed(df, config)
    print(f"Found {len(df_filtered)} unanalyzed rows")

    # Apply additional filters
    cols = config["columns"]

    if args.vendor:
        vendor_col = cols["vendor"]
        df_filtered = df_filtered[
            df_filtered[vendor_col].str.contains(args.vendor, case=False, na=False)
        ]
        print(f"Filtered to {len(df_filtered)} rows matching vendor '{args.vendor}'")

    if args.min_amount:
        amount_col = cols["tax_amount"]
        df_filtered = df_filtered[df_filtered[amount_col] >= args.min_amount]
        print(f"Filtered to {len(df_filtered)} rows with tax >= ${args.min_amount:,.2f}")

    if args.list:
        print("\n" + "="*80)
        print("AVAILABLE ROWS FOR ANALYSIS")
        print("="*80)
        for idx, row in df_filtered.head(20).iterrows():
            vendor = row.get(cols["vendor"], "Unknown")
            amount = row.get(cols["tax_amount"], 0)
            inv = row.get(cols["invoice_1"], "No invoice")
            print(f"Row {idx}: {vendor[:30]:<30} ${amount:>12,.2f}  {inv}")
        if len(df_filtered) > 20:
            print(f"... and {len(df_filtered) - 20} more rows")
        return

    if len(df_filtered) == 0:
        print("No rows to analyze!")
        return

    # Select rows to analyze
    if args.row is not None:
        if args.row in df_filtered.index:
            rows_to_analyze = df_filtered.loc[[args.row]]
        else:
            print(f"Row {args.row} not found in filtered data")
            return
    else:
        rows_to_analyze = df_filtered.head(args.limit)

    print(f"\nWill analyze {len(rows_to_analyze)} row(s)")
    print("\n" + "="*60)
    print("ENFORCED ANALYSIS WORKFLOW")
    print("="*60)
    print("""
This workflow FORCES thorough analysis by requiring you to:
1. READ the invoice PDF (content will be displayed)
2. FILL IN all required form fields
3. VERIFY your citations are valid
4. Only THEN can output be generated

You cannot skip steps. Incomplete forms are rejected.
""")

    for idx, row in rows_to_analyze.iterrows():
        context = RowContext(row, config)
        context.display_summary()

        form = AnalysisForm()
        form.excel_description = context.description
        form.excel_amount = context.tax_base or context.tax_amount
        form.pdf_filename = context.invoice_1

        inv1_result = context.extract_invoice_text(1, max_pages=args.max_invoice_pages)
        display_invoice_text_preview("Invoice 1", inv1_result)
        if inv1_result and inv1_result.text:
            form.invoice_text_preview = inv1_result.preview(max_chars=500)

        inv2_result = context.extract_invoice_text(2, max_pages=args.max_invoice_pages)
        display_invoice_text_preview("Invoice 2", inv2_result)

        display_form_status(form)

        print("\n>>> NEXT STEP: Read the invoice PDF and fill in the form fields")
        print(f">>> Invoice path: {context.get_invoice_path()}")
        print("\nUse this script interactively or call from Claude Code.")
        print("The form must be completed before output can be written.")


if __name__ == "__main__":
    main()
