#!/usr/bin/env python3
"""
Excel Processors for Tax Data Files
Specialized processors for Denodo Sales Tax and Use Tax Excel files

Handles the specific schemas of:
- Denodo Sales Tax files (109 columns from SAP)
- Use Tax Phase 3 files (32 columns for research)

Usage:
    from analysis.excel_processors import DenodoSalesTaxProcessor, UseTaxProcessor

    # Process Sales Tax file
    processor = DenodoSalesTaxProcessor()
    df = processor.load_file("2023 Records in Denodo not in Master_2-2-24.xlsx")
    analysis_ready_df = processor.extract_key_fields(df)

    # Process Use Tax file
    processor = UseTaxProcessor()
    df = processor.load_file("Phase_3_2023_Use Tax_10-17-25.xlsx")
"""

import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


class DenodoSalesTaxProcessor:
    """
    Process Denodo Sales Tax Excel files (109-column SAP extracts)

    These files contain comprehensive SAP transaction data with:
    - Financial amounts (tax amount, tax base)
    - Purchase order details
    - Vendor information
    - Tax codes and jurisdictions
    - Analysis and decision fields

    Enhanced features:
    - WIP sheet auto-detection
    - Row ID generation (DEN_1, DEN_2, etc.)
    - Combined description field
    - Tax type determination (Sales/Use/Both)
    - Standardized Tax column
    """

    # Slimmed down columns for analysis (16 essential columns)
    # Identification
    IDENTIFICATION_COLUMNS = [
        "name1_po_vendor_name",      # Vendor name
        "xblnr_invoice_number",      # Invoice ID
    ]

    # Financial
    FINANCIAL_COLUMNS = [
        "hwste_tax_amount_lc",       # Original tax amount (for reference)
        "sales_tax_line",            # For tax type determination
        "use_tax_line",              # For tax type determination
    ]

    # Decision/Analysis
    DECISION_COLUMNS = [
        "Final Decision",            # Skip if already done
        "Refund Basis",              # Existing determination
        "Tax Category",              # Classification
    ]

    # Date
    DATE_COLUMNS = ["bldat_document_date"]

    # Tax Classification
    TAX_CLASSIFICATION_COLUMNS = [
        "tax_jurisdiction_state",    # Jurisdiction
        "mwskz_tax_code",            # Tax code
    ]

    # Product (used for Combined_Description)
    PRODUCT_COLUMNS = [
        "txz01_po_description",
        "maktx_material_description",
        "txt50_account_description",
    ]

    # Document paths
    DOCUMENT_COLUMNS = [
        "Invoice Folder Path",
        "Inv 1 File Name",
        "Inv 2 File Name",
    ]

    def __init__(self):
        """Initialize the Denodo Sales Tax processor"""
        pass

    def load_file(
        self, filepath: str, sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load Denodo sales tax Excel file

        Args:
            filepath: Path to Excel file
            sheet_name: Specific sheet to load (None = auto-detect main data sheet)

        Returns:
            DataFrame with sales tax data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If expected columns are missing
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Read Excel file
        excel_file = pd.ExcelFile(filepath)

        # Auto-detect data sheet if not specified
        if sheet_name is None:
            # Priority 1: Look for WIP sheet
            for sheet in excel_file.sheet_names:
                if "wip" in sheet.lower():
                    sheet_name = sheet
                    break
            # Priority 2: Look for sheet with "tax items" or quarter
            if sheet_name is None:
                for sheet in excel_file.sheet_names:
                    if (
                        "tax items" in sheet.lower()
                        or "q1" in sheet.lower()
                        or "q2" in sheet.lower()
                    ):
                        sheet_name = sheet
                        break
            # Priority 3: Use first sheet
            if sheet_name is None:
                sheet_name = excel_file.sheet_names[0]

        print(f"Loading sheet: {sheet_name}")
        df = pd.read_excel(filepath, sheet_name=sheet_name)

        # Validate structure
        self._validate_denodo_structure(df)

        print(f"[OK] Loaded {len(df)} rows with {len(df.columns)} columns")
        return df

    def _validate_denodo_structure(self, df: pd.DataFrame):
        """Validate that the DataFrame has expected Denodo structure"""
        # Check for some key columns
        key_columns_to_check = ["xblnr_invoice_number", "vendor", "Final Decision"]

        missing = [col for col in key_columns_to_check if col not in df.columns]

        if len(missing) == len(key_columns_to_check):
            warnings.warn(
                "This doesn't look like a Denodo sales tax file. "
                f"Missing expected columns: {missing}\n"
                f"Available columns: {list(df.columns[:10])}..."
            )

    def _combine_descriptions(self, df: pd.DataFrame) -> pd.Series:
        """Combine PO, Material, and GL descriptions into one field"""
        col_prefix_map = [
            ("txz01_po_description", "PO"),
            ("maktx_material_description", "Material"),
            ("txt50_account_description", "GL"),
        ]

        def combine_row(row):
            parts = []
            for col, prefix in col_prefix_map:
                if col in df.columns:
                    val = row.get(col, "")
                    if pd.notna(val) and str(val).strip():
                        parts.append(f"{prefix}: {val}")
            return " | ".join(parts) if parts else ""

        return df.apply(combine_row, axis=1)

    def _determine_tax_type(self, df: pd.DataFrame) -> pd.Series:
        """Determine tax type based on sales_tax_line and use_tax_line values"""
        sales_tax = df.get("sales_tax_line", pd.Series([0] * len(df))).fillna(0)
        use_tax = df.get("use_tax_line", pd.Series([0] * len(df))).fillna(0)

        def classify(idx):
            s = float(sales_tax.iloc[idx]) if idx < len(sales_tax) else 0
            u = float(use_tax.iloc[idx]) if idx < len(use_tax) else 0
            if s > 0 and u > 0:
                return "Both"
            elif s > 0:
                return "Sales"
            elif u > 0:
                return "Use"
            return "Unknown"

        return pd.Series([classify(i) for i in range(len(df))], index=df.index)

    def _calculate_tax(self, df: pd.DataFrame) -> pd.Series:
        """Calculate standardized Tax column with priority-based selection"""
        if "hwste_tax_amount_lc" in df.columns:
            return df["hwste_tax_amount_lc"].fillna(0)
        elif "total_tax_amount" in df.columns:
            return df["total_tax_amount"].fillna(0)
        else:
            sales = df.get("sales_tax_line", pd.Series([0] * len(df))).fillna(0)
            use = df.get("use_tax_line", pd.Series([0] * len(df))).fillna(0)
            return sales + use

    def extract_key_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the key fields needed for refund analysis

        Args:
            df: Full Denodo DataFrame

        Returns:
            DataFrame with key analysis columns plus enhanced fields:
            - Row_ID: Unique identifier (DEN_1, DEN_2, etc.)
            - Combined_Description: Merged PO/Material/GL descriptions
            - Tax_Type: Sales, Use, Both, or Unknown
            - Tax: Standardized tax amount
        """
        # Combine all key column lists
        key_columns = (
            self.IDENTIFICATION_COLUMNS
            + self.FINANCIAL_COLUMNS
            + self.DECISION_COLUMNS
            + self.DATE_COLUMNS
            + self.TAX_CLASSIFICATION_COLUMNS
            + self.PRODUCT_COLUMNS
            + self.DOCUMENT_COLUMNS
        )

        # Filter to only columns that exist in the DataFrame
        available_columns = [col for col in key_columns if col in df.columns]

        result = df[available_columns].copy()

        # Add enhanced columns
        result.insert(0, "Row_ID", [f"DEN_{i+1}" for i in range(len(df))])
        result["Combined_Description"] = self._combine_descriptions(df)
        result["Tax_Type"] = self._determine_tax_type(df)
        result["Tax"] = self._calculate_tax(df)

        return result

    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get summary statistics for the dataset

        Returns:
            Dictionary with key statistics
        """
        stats = {
            "total_rows": len(df),
            "total_tax_amount": (
                df["hwste_tax_amount_lc"].sum()
                if "hwste_tax_amount_lc" in df.columns
                else 0
            ),
            "unique_vendors": df["vendor"].nunique() if "vendor" in df.columns else 0,
            "unique_invoices": (
                df["xblnr_invoice_number"].nunique()
                if "xblnr_invoice_number" in df.columns
                else 0
            ),
            "decision_breakdown": (
                df["Final Decision"].value_counts().to_dict()
                if "Final Decision" in df.columns
                else {}
            ),
        }
        return stats

    def filter_for_refund_opportunities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to only rows that might be refund opportunities

        Args:
            df: Full DataFrame

        Returns:
            Filtered DataFrame with potential refund opportunities
        """
        filtered = df.copy()

        # Remove rows already marked as "NO OPP" or similar
        if "Final Decision" in filtered.columns:
            filtered = filtered[
                ~filtered["Final Decision"]
                .str.upper()
                .str.contains("NO OPP|PASS", na=False)
            ]

        # Filter for non-zero tax amounts
        if "hwste_tax_amount_lc" in filtered.columns:
            filtered = filtered[filtered["hwste_tax_amount_lc"] > 0]

        print(
            f"Filtered to {
                len(filtered)} potential refund opportunities (from {
                len(df)} total)"
        )
        return filtered


class UseTaxProcessor:
    """
    Process Use Tax Phase 3 Excel files (32-column research files)

    These files contain:
    - Vendor and invoice identifiers
    - Tax amounts and rates
    - Research status and analysis
    - Decision and categorization fields

    Enhanced features:
    - WIP sheet auto-detection
    - Row ID generation (USE_P3_1, USE_P3_2, etc.)
    - Standardized Tax column
    """

    # Slimmed down columns for analysis (13 essential columns)
    # Identification
    IDENTIFICATION_COLUMNS = [
        "Vendor Name",               # Who sold it
        "INVNO",                     # Invoice ID
    ]

    # Financial
    FINANCIAL_COLUMNS = [
        "Total Tax",                 # The money
    ]

    # Location
    LOCATION_COLUMNS = ["STATE"]     # Jurisdiction

    # Decision/Analysis
    DECISION_COLUMNS = [
        "Final Decision",            # Skip if already done
        "Refund Basis",              # Existing determination
        "Tax Category",              # Classification
    ]

    # Classification
    CLASSIFICATION_COLUMNS = [
        "Vertex Category",           # Product classification
        "Description",               # What was purchased
    ]

    # Document paths
    DOCUMENT_COLUMNS = [
        "Invoice Folder Path",
        "Inv-1 File Name",
        "Inv-2 File Name",
    ]

    def __init__(self):
        """Initialize the Use Tax processor"""
        pass

    def load_file(
        self, filepath: str, sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load Use Tax Excel file

        Args:
            filepath: Path to Excel file
            sheet_name: Specific sheet to load (None = auto-detect or first sheet)

        Returns:
            DataFrame with use tax data
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Read Excel file
        excel_file = pd.ExcelFile(filepath)

        # Auto-detect data sheet if not specified
        if sheet_name is None:
            # Priority 1: Look for WIP sheet
            for sheet in excel_file.sheet_names:
                if "wip" in sheet.lower():
                    sheet_name = sheet
                    break
            # Priority 2: Look for year sheet (e.g., "2023")
            if sheet_name is None:
                for sheet in excel_file.sheet_names:
                    if sheet.isdigit():
                        sheet_name = sheet
                        break
            # Priority 3: Use first sheet
            if sheet_name is None:
                sheet_name = excel_file.sheet_names[0]

        print(f"Loading sheet: {sheet_name}")
        df = pd.read_excel(filepath, sheet_name=sheet_name)

        # Validate structure
        self._validate_use_tax_structure(df)

        print(f"[OK] Loaded {len(df)} rows with {len(df.columns)} columns")
        return df

    def _validate_use_tax_structure(self, df: pd.DataFrame):
        """Validate that the DataFrame has expected Use Tax structure"""
        key_columns_to_check = ["Vendor Name", "INVNO", "Total Tax"]

        missing = [col for col in key_columns_to_check if col not in df.columns]

        if len(missing) == len(key_columns_to_check):
            warnings.warn(
                "This doesn't look like a Use Tax file. "
                f"Missing expected columns: {missing}\n"
                f"Available columns: {list(df.columns[:10])}..."
            )

    def _calculate_tax(self, df: pd.DataFrame) -> pd.Series:
        """Calculate standardized Tax column"""
        if "Total Tax" in df.columns:
            return df["Total Tax"].fillna(0)
        return pd.Series([0] * len(df), index=df.index)

    def extract_key_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the key fields needed for refund analysis

        Returns:
            DataFrame with key columns plus enhanced fields:
            - Row_ID: Unique identifier (USE_P3_1, USE_P3_2, etc.)
            - Tax: Standardized tax amount
        """
        key_columns = (
            self.IDENTIFICATION_COLUMNS
            + self.FINANCIAL_COLUMNS
            + self.LOCATION_COLUMNS
            + self.DECISION_COLUMNS
            + self.CLASSIFICATION_COLUMNS
            + self.DOCUMENT_COLUMNS
        )

        available_columns = [col for col in key_columns if col in df.columns]
        result = df[available_columns].copy()

        # Add enhanced columns
        result.insert(0, "Row_ID", [f"USE_P3_{i+1}" for i in range(len(df))])
        result["Tax"] = self._calculate_tax(df)

        return result

    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics for the use tax dataset"""
        stats = {
            "total_rows": len(df),
            "total_tax_amount": (
                df["Total Tax"].sum() if "Total Tax" in df.columns else 0
            ),
            "unique_vendors": (
                df["Vendor Name"].nunique() if "Vendor Name" in df.columns else 0
            ),
            "unique_invoices": df["INVNO"].nunique() if "INVNO" in df.columns else 0,
            "status_breakdown": (
                df["Status"].value_counts().to_dict() if "Status" in df.columns else {}
            ),
            "decision_breakdown": (
                df["Final Decision"].value_counts().to_dict()
                if "Final Decision" in df.columns
                else {}
            ),
        }
        return stats

    def filter_for_research(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to rows that need research

        Returns:
            DataFrame with rows marked for research
        """
        filtered = df.copy()

        if "Invoices to Research" in filtered.columns:
            filtered = filtered[
                filtered["Invoices to Research"]
                .str.upper()
                .str.contains("RESEARCH", na=False)
            ]

        if "Status" in filtered.columns:
            # Keep rows without final status
            filtered = filtered[
                ~filtered["Status"]
                .str.upper()
                .str.contains("COMPLETE|DONE|CLOSED", na=False)
            ]

        print(
            f"Filtered to {len(filtered)} items needing research (from {len(df)} total)"
        )
        return filtered


def auto_detect_file_type(filepath: str) -> str:
    """
    Auto-detect whether a file is Denodo Sales Tax or Use Tax format

    Args:
        filepath: Path to Excel file

    Returns:
        String: 'denodo_sales_tax', 'use_tax', or 'unknown'
    """
    try:
        # Read first few rows
        df = pd.read_excel(filepath, nrows=1)

        # Check for Denodo columns
        if "xblnr_invoice_number" in df.columns or "hwste_tax_amount_lc" in df.columns:
            return "denodo_sales_tax"

        # Check for Use Tax columns
        if (
            "Vendor Name" in df.columns
            and "INVNO" in df.columns
            and "Total Tax" in df.columns
        ):
            return "use_tax"

        return "unknown"

    except Exception as e:
        print(f"Error auto-detecting file type: {e}")
        return "unknown"


if __name__ == "__main__":
    # Self-test
    import sys

    print("Excel Processors Module - Self Test")
    print("=" * 70)

    # Check if test data path provided
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"Testing with file: {test_file}")

        # Auto-detect type
        file_type = auto_detect_file_type(test_file)
        print(f"Detected file type: {file_type}")

        # Process based on type
        if file_type == "denodo_sales_tax":
            processor = DenodoSalesTaxProcessor()
            df = processor.load_file(test_file)
            print("\nSummary Statistics:")
            stats = processor.get_summary_stats(df)
            for key, value in stats.items():
                print(f"  {key}: {value}")

        elif file_type == "use_tax":
            processor = UseTaxProcessor()
            df = processor.load_file(test_file)
            print("\nSummary Statistics:")
            stats = processor.get_summary_stats(df)
            for key, value in stats.items():
                print(f"  {key}: {value}")

        else:
            print("Unable to determine file type")

    else:
        print("\nUsage: python excel_processors.py <path_to_excel_file>")
        print("\nExample:")
        print(
            '  python excel_processors.py "Test Data/2023 Records in Denodo not in Master_2-2-24.xlsx"'
        )
        print(
            '  python excel_processors.py "Test Data/Phase_3_2023_Use Tax_10-17-25.xlsx"'
        )
