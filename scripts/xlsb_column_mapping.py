"""
Column mapping for Sales Tax 2024 xlsb files (106-column format).

This maps the full Denodo export columns to the standard analysis columns.
"""

# Column positions in the 106-column xlsb format (0-indexed)
XLSB_COLUMNS = {
    # Key identifiers
    "belnr_max_document_number": 7,      # Invoice number
    "ebeln_po_number": 20,               # PO number

    # Vendor info
    "name1_po_vendor_name": 55,
    "lifnr_po_vendor": 41,
    "ort01_po_vendor_city": 58,
    "regio_po_vendor_state": 64,
    "pstlz_po_vendor_zip": 62,
    "stras_po_vendor_address": 76,
    "landl_po_vendor_country": 40,

    # Tax amounts
    "hwbas_tax_base_lc": 37,
    "hwste_tax_amount_lc": 38,
    "fwbas_tax_base_dc": 23,
    "fwste_tax_amount_dc": 24,

    # Invoice files (primary - use these)
    "Inv 1": 34,
    "Inv 2": 35,
    # Note: Duplicates exist at 100, 101 - ignore those

    # Tax info
    "rate": 36,
    "sales_tax_state": 69,
    "tax_jurisdiction_state": 77,
    "mwskz_tax_code": 50,
    "derived_tax_code": 18,

    # Product info
    "txz01_po_description": 87,
    "matk1_po_material_group_desc": 47,
    "maktx_material_description": 44,

    # Status
    "Paid?": 53,
    "Previous Refund?": 54,
    "quadrant": 102,
    "score": 103,
    "reasons": 104,
    "buckets": 105,

    # Human review columns (NEVER overwrite if populated)
    "Assigned": 27,
    "Recon Analysis": 28,
    "Notes": 29,
    "Final Decision": 30,
    "Tax Category": 31,
    "Add'l info": 32,
    "Refund Basis": 33,

    # Additional context
    "bukrs_company_code": 15,
    "bukrs_company_code_desc": 16,
    "kost1_cost_center": 39,
    "ltext_cost_center_description": 42,
    "prctr_profit_center": 60,
    "ltext_profit_center_description": 43,
}

# Columns that contain human-entered data - NEVER overwrite
HUMAN_COLUMNS = [
    "Assigned",
    "Recon Analysis",
    "Notes",
    "Final Decision",
    "Tax Category",
    "Add'l info",
    "Refund Basis",
]

# Columns for the standard 27-column xlsx format
XLSX_STANDARD_COLUMNS = [
    "name1_po_vendor_name",
    "hwbas_tax_base_lc",
    "hwste_tax_amount_lc",
    "Inv 1",
    "Inv 2",
    "rate",
    "txz01_po_description",
    "matk1_po_material_group_desc",
    "sales_tax_state",
    "tax_jurisdiction_state",
    "quadrant",
    "Invoice_Number",  # mapped from belnr_max_document_number
    "PO_Number",       # mapped from ebeln_po_number
]

# Standard filters for Sales Tax 2024 analysis
DEFAULT_FILTERS = {
    "Paid?": "PAID",
    "Recon Analysis": "",  # Must be empty (not yet analyzed)
    "Inv 1": "NOT_EMPTY",  # Must have invoice
}

# Map xlsb column names to output column names
OUTPUT_COLUMN_MAP = {
    "belnr_max_document_number": "Invoice_Number",
    "ebeln_po_number": "PO_Number",
}


def get_column_index(column_name: str) -> int:
    """Get the 0-indexed column position for a column name."""
    return XLSB_COLUMNS.get(column_name, -1)


def is_human_column(column_name: str) -> bool:
    """Check if a column contains human-entered data."""
    return column_name in HUMAN_COLUMNS


def get_row_key(row_data: dict) -> str:
    """Generate a unique key for a row based on invoice/PO/vendor."""
    invoice = row_data.get("belnr_max_document_number", "")
    po = row_data.get("ebeln_po_number", "")
    vendor = row_data.get("name1_po_vendor_name", "")
    return f"{invoice}|{po}|{vendor}"
