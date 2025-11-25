"""
Excel Column Definitions
========================

Defines which columns are INPUT (user provides) vs OUTPUT (AI generates).

This is used to determine when rows need re-analysis:
- INPUT column changes → Re-analyze the row
- OUTPUT column changes → Feedback/correction only, no re-analysis needed

Usage:
    from core.excel_column_definitions import INPUT_COLUMNS, OUTPUT_COLUMNS, is_input_column

    if is_input_column("Invoice_File_Name_1"):
        # This change requires re-analysis
        mark_for_reanalysis(row_index)
"""

# ============================================================================
# INPUT COLUMNS - User Provides (Changes trigger re-analysis)
# ============================================================================

INPUT_COLUMNS = [
    # Identification
    "Vendor_ID",
    "Vendor_Name",
    "Invoice_Number",
    "Purchase_Order_Number",

    # Financial Data
    "Total_Amount",
    "Tax_Amount",
    "Tax_Remitted",
    "Tax_Rate_Charged",

    # Document References (KEY: Changes here need re-analysis)
    "Invoice_File_Name_1",       # Vendor invoice PDF
    "Invoice_File_Name_2",       # Internal invoice PDF
    "Purchase_Order_File_Name",  # PO PDF

    # Additional Context
    "Line_Item_Description",
    "Tax_Type",  # sales_tax or use_tax

    # Location/Dates (if present)
    "STATE",
    "Invoice_Date",
    "PO_Date",
]

# ============================================================================
# OUTPUT COLUMNS - AI Generates (Changes are feedback/corrections)
# ============================================================================

OUTPUT_COLUMNS = [
    # Analysis Results
    "Analysis_Notes",
    "Final_Decision",

    # Classification
    "Tax_Category",
    "Additional_Info",

    # Refund Determination
    "Refund_Basis",
    "Estimated_Refund",

    # Legal Support
    "Legal_Citation",

    # Confidence/Metadata
    "AI_Confidence",
    "Anomalies_Detected",
    "Patterns_Applied",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_input_column(column_name: str) -> bool:
    """
    Check if a column is an INPUT column (user-provided data).

    Args:
        column_name: Name of the column to check

    Returns:
        True if column is an INPUT column, False otherwise

    Example:
        >>> is_input_column("Invoice_File_Name_1")
        True
        >>> is_input_column("Analysis_Notes")
        False
    """
    return column_name in INPUT_COLUMNS


def is_output_column(column_name: str) -> bool:
    """
    Check if a column is an OUTPUT column (AI-generated).

    Args:
        column_name: Name of the column to check

    Returns:
        True if column is an OUTPUT column, False otherwise

    Example:
        >>> is_output_column("Analysis_Notes")
        True
        >>> is_output_column("Invoice_File_Name_1")
        False
    """
    return column_name in OUTPUT_COLUMNS


def get_column_type(column_name: str) -> str:
    """
    Get the type of a column.

    Args:
        column_name: Name of the column to check

    Returns:
        "input", "output", or "unknown"

    Example:
        >>> get_column_type("Invoice_File_Name_1")
        'input'
        >>> get_column_type("Analysis_Notes")
        'output'
        >>> get_column_type("Some_Random_Column")
        'unknown'
    """
    if is_input_column(column_name):
        return "input"
    elif is_output_column(column_name):
        return "output"
    else:
        return "unknown"


def triggers_reanalysis(column_name: str) -> bool:
    """
    Check if changing this column should trigger row re-analysis.

    Currently, only INPUT column changes trigger re-analysis.
    OUTPUT column changes are treated as feedback/corrections.

    Args:
        column_name: Name of the column to check

    Returns:
        True if changes to this column should trigger re-analysis

    Example:
        >>> triggers_reanalysis("Invoice_File_Name_2")  # New invoice file added
        True
        >>> triggers_reanalysis("Tax_Category")  # Human corrected AI's classification
        False
    """
    return is_input_column(column_name)


def get_input_document_columns():
    """
    Get list of INPUT columns that reference documents (invoices, POs).

    These are especially important because adding a new document
    means there's new information to analyze.

    Returns:
        List of document reference column names

    Example:
        >>> get_input_document_columns()
        ['Invoice_File_Name_1', 'Invoice_File_Name_2', 'Purchase_Order_File_Name']
    """
    return [
        "Invoice_File_Name_1",
        "Invoice_File_Name_2",
        "Purchase_Order_File_Name",
    ]


# ============================================================================
# VALIDATION
# ============================================================================

def validate_excel_structure(df_columns: list) -> dict:
    """
    Validate that an Excel DataFrame has the expected structure.

    Args:
        df_columns: List of column names from DataFrame

    Returns:
        Dict with validation results:
            - has_all_input: bool
            - has_all_output: bool
            - missing_input: list
            - missing_output: list
            - extra_columns: list

    Example:
        >>> import pandas as pd
        >>> df = pd.read_excel("Master_Sheet.xlsx")
        >>> validation = validate_excel_structure(df.columns.tolist())
        >>> if not validation['has_all_input']:
        ...     print(f"Missing columns: {validation['missing_input']}")
    """
    df_columns_set = set(df_columns)
    input_set = set(INPUT_COLUMNS)
    output_set = set(OUTPUT_COLUMNS)
    expected_set = input_set | output_set

    missing_input = input_set - df_columns_set
    missing_output = output_set - df_columns_set
    extra_columns = df_columns_set - expected_set

    return {
        "has_all_input": len(missing_input) == 0,
        "has_all_output": len(missing_output) == 0,
        "missing_input": list(missing_input),
        "missing_output": list(missing_output),
        "extra_columns": list(extra_columns),
    }


# ============================================================================
# EXPORT FOR EXTERNAL USE
# ============================================================================

__all__ = [
    "INPUT_COLUMNS",
    "OUTPUT_COLUMNS",
    "is_input_column",
    "is_output_column",
    "get_column_type",
    "triggers_reanalysis",
    "get_input_document_columns",
    "validate_excel_structure",
]
