"""
XLSB Excel Processor
====================

Handles loading and processing of binary Excel (.xlsb) files.

These files are larger/faster versions of .xlsx used by Excel for big datasets.

Usage:
    from analysis.xlsb_processor import load_xlsb, filter_sales_tax_rows

    # Load the file
    df = load_xlsb("path/to/file.xlsb", sheet_name="TestRun")

    # Apply filters
    filtered = filter_sales_tax_rows(df)
"""

from pathlib import Path
from typing import Optional

import pandas as pd


def column_letter_to_index(letter: str) -> int:
    """
    Convert Excel column letter to 0-based index.

    Examples:
        A -> 0
        B -> 1
        Z -> 25
        AA -> 26
        AB -> 27
        AZ -> 51
        BA -> 52
    """
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def index_to_column_letter(index: int) -> str:
    """
    Convert 0-based index to Excel column letter.

    Examples:
        0 -> A
        25 -> Z
        26 -> AA
        27 -> AB
    """
    result = ""
    index += 1  # Convert to 1-based
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord('A') + remainder) + result
    return result


def load_xlsb(filepath: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Load an Excel binary (.xlsb) file.

    Args:
        filepath: Path to the .xlsb file
        sheet_name: Sheet to load (None = first sheet)

    Returns:
        DataFrame with the sheet data
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if path.suffix.lower() != ".xlsb":
        raise ValueError(f"Expected .xlsb file, got: {path.suffix}")

    print(f"Loading {path.name}...")

    # pyxlsb is used via pandas engine
    df = pd.read_excel(filepath, sheet_name=sheet_name, engine="pyxlsb")

    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def get_sheet_names(filepath: str) -> list:
    """Get list of sheet names from .xlsb file."""
    from pyxlsb import open_workbook

    with open_workbook(filepath) as wb:
        return wb.sheets


def get_column_by_letter(df: pd.DataFrame, letter: str):
    """
    Get a column from DataFrame by Excel column letter.

    Args:
        df: DataFrame
        letter: Excel column letter (e.g., "A", "AA", "CT")

    Returns:
        The column (Series)
    """
    idx = column_letter_to_index(letter)
    if idx >= len(df.columns):
        raise IndexError(f"Column {letter} (index {idx}) out of range. DataFrame has {len(df.columns)} columns.")
    return df.iloc[:, idx]


def filter_sales_tax_rows(
    df: pd.DataFrame,
    paid_column: str = "AW",
    analysis_column: str = "U",
    invoice_column: str = "AA",
    quadrant_column: str = "CT",
    quadrant_value: Optional[str] = None,
) -> pd.DataFrame:
    """
    Filter sales tax rows based on criteria.

    Default filters:
    - Column AW = "PAID"
    - Column U = empty
    - Column AA = not empty (has invoice)

    Args:
        df: Source DataFrame
        paid_column: Column with payment status (default AW)
        analysis_column: Column that should be empty (default U)
        invoice_column: Column that should have invoice (default AA)
        quadrant_column: Column with quadrant/comment (default CT)
        quadrant_value: If specified, filter to this quadrant value

    Returns:
        Filtered DataFrame
    """
    # Get column indices
    paid_idx = column_letter_to_index(paid_column)
    analysis_idx = column_letter_to_index(analysis_column)
    invoice_idx = column_letter_to_index(invoice_column)
    quadrant_idx = column_letter_to_index(quadrant_column)

    # Validate indices
    max_cols = len(df.columns)
    for name, idx in [("paid", paid_idx), ("analysis", analysis_idx),
                      ("invoice", invoice_idx), ("quadrant", quadrant_idx)]:
        if idx >= max_cols:
            raise IndexError(f"{name} column index {idx} out of range (max {max_cols})")

    # Build filters
    paid_col = df.iloc[:, paid_idx]
    analysis_col = df.iloc[:, analysis_idx]
    invoice_col = df.iloc[:, invoice_idx]

    # Filter: Paid = "PAID"
    paid_mask = paid_col.astype(str).str.upper().str.strip() == "PAID"

    # Filter: Analysis column is empty
    empty_mask = analysis_col.isna() | (analysis_col.astype(str).str.strip() == "")

    # Filter: Invoice column is not empty
    has_invoice_mask = invoice_col.notna() & (invoice_col.astype(str).str.strip() != "")

    # Combine filters
    combined_mask = paid_mask & empty_mask & has_invoice_mask

    # Optional: Filter by quadrant value
    if quadrant_value:
        quadrant_col = df.iloc[:, quadrant_idx]
        # Use exact phrase matching to distinguish "In WA" from "NOT in WA"
        if "not" in quadrant_value.lower():
            # Match "NOT in WA" - look for "NOT" in the value
            quadrant_mask = quadrant_col.astype(str).str.upper().str.contains("NOT", na=False)
        else:
            # Match "In WA" but NOT "NOT in WA"
            quadrant_mask = (
                quadrant_col.astype(str).str.upper().str.contains("IN WA", na=False) &
                ~quadrant_col.astype(str).str.upper().str.contains("NOT", na=False)
            )
        combined_mask = combined_mask & quadrant_mask

    filtered = df[combined_mask].copy()
    print(f"  Filtered to {len(filtered):,} rows (from {len(df):,})")

    return filtered


# Column name constants for the Denodo sales tax file
class DenodoColumns:
    """Column letter mappings for Denodo Sales Tax files."""
    # Filter columns
    PAID = "AW"            # Column 48 - Payment status
    ANALYSIS = "U"         # Column 20 - Recon Analysis (filter: empty)
    INVOICE_1 = "AA"       # Column 26 - Inv 1
    INVOICE_2 = "AB"       # Column 27 - Inv 2

    # Key data columns
    RATE = "AF"            # Column 31 - Tax rate charged
    TAX_BASE = "AG"        # Column 32 - Tax base amount
    TAX_AMOUNT = "AH"      # Column 33 - Tax amount
    VENDOR_NAME = "AY"     # Column 50 - Vendor name
    JURISDICTION = "BU"    # Column 72 - Tax jurisdiction state
    QUADRANT = "CT"        # Column 97 - "Yes Tax, in WA" or "Yes Tax, NOT in WA"
    INV_FILE_PATH = "AD"   # Column 29 - Invoice file path

    # For "in WA" analysis - rate lookup and exemption checking
    VENDOR_CITY = "BB"     # Column 53 - ort01_po_vendor_city
    VENDOR_ZIP = "BF"      # Column 57 - pstlz_po_vendor_zip
    DESCRIPTION = "CE"     # Column 82 - txz01_po_description


def extract_sales_tax_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract key columns from sales tax DataFrame for analysis.

    Returns DataFrame with named columns for easier access.
    """
    cols = DenodoColumns

    result = pd.DataFrame({
        "rate": get_column_by_letter(df, cols.RATE),
        "tax_base": get_column_by_letter(df, cols.TAX_BASE),
        "tax_amount": get_column_by_letter(df, cols.TAX_AMOUNT),
        "vendor_name": get_column_by_letter(df, cols.VENDOR_NAME),
        "jurisdiction_state": get_column_by_letter(df, cols.JURISDICTION),
        "quadrant": get_column_by_letter(df, cols.QUADRANT),
        "inv_file_path": get_column_by_letter(df, cols.INV_FILE_PATH),
        "invoice_1": get_column_by_letter(df, cols.INVOICE_1),
        "invoice_2": get_column_by_letter(df, cols.INVOICE_2),
        "paid_status": get_column_by_letter(df, cols.PAID),
    })

    # Keep original index for reference
    result.index = df.index

    return result


# ============================================================================
# Real Run Sheet Format (Final 2024)
# ============================================================================

class RealRunColumns:
    """Column letter mappings for 'Real Run' sheet (Final 2024 format)."""
    # Filter columns
    PAID = "R"              # Column R - Paid? = "PAID"
    ANALYSIS = "D"          # Column D - Recon Analysis (filter: empty)
    INVOICE_1 = "J"         # Column J - Inv 1
    INVOICE_2 = "K"         # Column K - Inv 2

    # Key data columns
    INV_FILE_PATH = "L"     # Column L - Invoice File Path
    RATE = "M"              # Column M - Tax rate charged
    TAX_BASE = "N"          # Column N - hwbas_tax_base_lc
    TAX_AMOUNT = "O"        # Column O - hwste_tax_amount_lc
    DESCRIPTION_1 = "Q"     # Column Q - matk1_po_material_group_desc
    DESCRIPTION_2 = "V"     # Column V - txz01_po_description
    VENDOR_NAME = "S"       # Column S - name1_po_vendor_name
    JURISDICTION = "U"      # Column U - tax_jurisdiction_state
    QUADRANT = "Y"          # Column Y - "Yes Tax, In WA" or "Yes Tax, NOT in WA"


def filter_real_run_rows(
    df: pd.DataFrame,
    quadrant_value: Optional[str] = None,
) -> pd.DataFrame:
    """
    Filter rows from 'Real Run' sheet based on criteria.

    Filters:
    - Column R (Paid?) = "PAID"
    - Column D (Recon Analysis) = empty
    - Column J (Inv 1) = not empty (has invoice)

    Args:
        df: Source DataFrame
        quadrant_value: If specified, filter to this quadrant value
                       e.g., "In WA" or "NOT in WA"

    Returns:
        Filtered DataFrame
    """
    cols = RealRunColumns

    # Get column indices
    paid_idx = column_letter_to_index(cols.PAID)
    analysis_idx = column_letter_to_index(cols.ANALYSIS)
    invoice_idx = column_letter_to_index(cols.INVOICE_1)
    quadrant_idx = column_letter_to_index(cols.QUADRANT)

    # Validate indices
    max_cols = len(df.columns)
    for name, idx in [("paid", paid_idx), ("analysis", analysis_idx),
                      ("invoice", invoice_idx), ("quadrant", quadrant_idx)]:
        if idx >= max_cols:
            raise IndexError(f"{name} column index {idx} out of range (max {max_cols})")

    # Build filters
    paid_col = df.iloc[:, paid_idx]
    analysis_col = df.iloc[:, analysis_idx]
    invoice_col = df.iloc[:, invoice_idx]

    # Filter: Paid = "PAID"
    paid_mask = paid_col.astype(str).str.upper().str.strip() == "PAID"

    # Filter: Analysis column is empty
    empty_mask = analysis_col.isna() | (analysis_col.astype(str).str.strip() == "")

    # Filter: Invoice column is not empty
    has_invoice_mask = invoice_col.notna() & (invoice_col.astype(str).str.strip() != "")

    # Combine filters
    combined_mask = paid_mask & empty_mask & has_invoice_mask

    # Optional: Filter by quadrant value
    if quadrant_value:
        quadrant_col = df.iloc[:, quadrant_idx]
        # Use exact phrase matching to distinguish "In WA" from "NOT in WA"
        if "not" in quadrant_value.lower():
            # Match "NOT in WA" - look for "NOT" in the value
            quadrant_mask = quadrant_col.astype(str).str.upper().str.contains("NOT", na=False)
        else:
            # Match "In WA" but NOT "NOT in WA"
            quadrant_mask = (
                quadrant_col.astype(str).str.upper().str.contains("IN WA", na=False) &
                ~quadrant_col.astype(str).str.upper().str.contains("NOT", na=False)
            )
        combined_mask = combined_mask & quadrant_mask

    filtered = df[combined_mask].copy()
    print(f"  Filtered to {len(filtered):,} rows (from {len(df):,})")

    return filtered


def extract_real_run_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract key columns from Real Run sheet for analysis.

    Returns DataFrame with named columns matching the standard analysis format.
    """
    cols = RealRunColumns

    # Get both descriptions and combine them
    desc1 = get_column_by_letter(df, cols.DESCRIPTION_1)
    desc2 = get_column_by_letter(df, cols.DESCRIPTION_2)

    result = pd.DataFrame({
        "rate": get_column_by_letter(df, cols.RATE),
        "tax_base": get_column_by_letter(df, cols.TAX_BASE),
        "tax_amount": get_column_by_letter(df, cols.TAX_AMOUNT),
        "vendor_name": get_column_by_letter(df, cols.VENDOR_NAME),
        "jurisdiction_state": get_column_by_letter(df, cols.JURISDICTION),
        "quadrant": get_column_by_letter(df, cols.QUADRANT),
        "inv_file_path": get_column_by_letter(df, cols.INV_FILE_PATH),
        "invoice_1": get_column_by_letter(df, cols.INVOICE_1),
        "invoice_2": get_column_by_letter(df, cols.INVOICE_2),
        "paid_status": get_column_by_letter(df, cols.PAID),
        "description_1": desc1,
        "description_2": desc2,
        # Combined description for analysis
        "description": desc1.fillna("") + " | " + desc2.fillna(""),
    })

    # Keep original index for reference
    result.index = df.index

    return result
