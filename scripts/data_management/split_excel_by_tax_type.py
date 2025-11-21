#!/usr/bin/env python3
"""
Split a combined Excel sheet into separate Sales Tax and Use Tax sheets.

Usage:
    python scripts/split_excel_by_tax_type.py <input_excel_file>

Example:
    python scripts/split_excel_by_tax_type.py test_data/All_Transactions.xlsx
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


def classify_tax_type(row: pd.Series) -> str:
    """
    Classify a single row as sales_tax, use_tax, or NEEDS_REVIEW.

    Detection Logic:
        - Sales Tax: Vendor collected and remitted tax (Tax_Remitted > 0)
        - Use Tax: Purchaser self-assessed tax (Tax_Remitted = 0, Tax_Amount > 0)
        - Needs Review: Cannot determine automatically

    Args:
        row: Pandas Series representing a single transaction row

    Returns:
        'sales_tax', 'use_tax', or 'NEEDS_REVIEW'
    """
    tax_remitted = row.get("Tax_Remitted", 0)
    tax_amount = row.get("Tax_Amount", 0)

    # Handle NaN/None values
    if pd.isna(tax_remitted):
        tax_remitted = 0
    if pd.isna(tax_amount):
        tax_amount = 0

    # Convert to float for comparison
    try:
        tax_remitted = float(tax_remitted)
        tax_amount = float(tax_amount)
    except (ValueError, TypeError):
        return "NEEDS_REVIEW"

    # SALES TAX: Vendor collected and remitted tax
    if tax_remitted > 0 and tax_amount > 0:
        return "sales_tax"

    # USE TAX: No vendor tax collected, but tax amount present (self-assessed)
    if tax_remitted == 0 and tax_amount > 0:
        return "use_tax"

    # NO TAX: Should not be in refund claim
    if tax_amount == 0:
        return "NEEDS_REVIEW"

    # EDGE CASE: Cannot determine
    return "NEEDS_REVIEW"


def get_classification_summary(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get summary statistics of classification results.

    Args:
        df: DataFrame with 'Tax_Type' column

    Returns:
        Dictionary with counts by tax type
    """
    return {
        "sales_tax": len(df[df["Tax_Type"] == "sales_tax"]),
        "use_tax": len(df[df["Tax_Type"] == "use_tax"]),
        "needs_review": len(df[df["Tax_Type"] == "NEEDS_REVIEW"]),
        "total": len(df),
    }


def split_excel_by_tax_type(
    input_file: str, output_dir: str = "test_data"
) -> Tuple[str, str, str]:
    """
    Split combined Excel into separate Sales Tax and Use Tax sheets.

    Creates three output files:
        1. Master_Sales_Tax_Claim_Sheet.xlsx - Sales tax refunds
        2. Master_Use_Tax_Claim_Sheet.xlsx - Use tax refunds
        3. Needs_Manual_Classification.xlsx - Unclear transactions

    Args:
        input_file: Path to input Excel file with combined transactions
        output_dir: Directory to write output files (default: test_data/)

    Returns:
        Tuple of (sales_tax_file, use_tax_file, needs_review_file) paths
    """
    print(f"📂 Reading input file: {input_file}")
    df = pd.read_excel(input_file)

    print(f"📊 Loaded {len(df)} transactions")

    # Validate required columns
    required_columns = [
        "Vendor_Name",
        "Invoice_Number",
        "Total_Amount",
        "Tax_Amount",
        "Tax_Remitted",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Classify each row
    print("🔍 Classifying transactions by tax type...")
    df["Tax_Type"] = df.apply(classify_tax_type, axis=1)

    # Get summary
    summary = get_classification_summary(df)
    print("\n📈 Classification Summary:")
    print(
        f"   Sales Tax:    {
            summary['sales_tax']:>4} transactions ({
            summary['sales_tax'] /
            summary['total'] *
            100:.1f}%)"
    )
    print(
        f"   Use Tax:      {
            summary['use_tax']:>4} transactions ({
            summary['use_tax'] /
            summary['total'] *
            100:.1f}%)"
    )
    print(
        f"   Needs Review: {
            summary['needs_review']:>4} transactions ({
            summary['needs_review'] /
            summary['total'] *
            100:.1f}%)"
    )
    print(f"   Total:        {summary['total']:>4} transactions\n")

    # Split into separate DataFrames
    sales_df = df[df["Tax_Type"] == "sales_tax"].copy()
    use_df = df[df["Tax_Type"] == "use_tax"].copy()
    needs_review_df = df[df["Tax_Type"] == "NEEDS_REVIEW"].copy()

    # Create output directory if needed
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Define output file paths
    sales_file = output_path / "Master_Sales_Tax_Claim_Sheet.xlsx"
    use_file = output_path / "Master_Use_Tax_Claim_Sheet.xlsx"
    review_file = output_path / "Needs_Manual_Classification.xlsx"

    # Write to separate Excel files
    print("💾 Writing output files...")
    if len(sales_df) > 0:
        sales_df.to_excel(sales_file, index=False)
        print(f"   ✅ Sales Tax: {len(sales_df)} transactions → {sales_file}")
    else:
        print("   ⚠️  No sales tax transactions found")

    if len(use_df) > 0:
        use_df.to_excel(use_file, index=False)
        print(f"   ✅ Use Tax: {len(use_df)} transactions → {use_file}")
    else:
        print("   ⚠️  No use tax transactions found")

    if len(needs_review_df) > 0:
        needs_review_df.to_excel(review_file, index=False)
        print(
            f"   ⚠️  Needs Review: {len(needs_review_df)} transactions → {review_file}"
        )
        print(
            f"\n⚠️  WARNING: {
                len(needs_review_df)} transactions require manual classification"
        )
    else:
        print("   ✅ No transactions need manual review")

    print("\n✅ Split complete!")

    return str(sales_file), str(use_file), str(review_file)


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("❌ Error: Missing input file")
        print("\nUsage:")
        print(
            "    python scripts/split_excel_by_tax_type.py <input_excel_file> [output_dir]"
        )
        print("\nExample:")
        print(
            "    python scripts/split_excel_by_tax_type.py test_data/All_Transactions.xlsx"
        )
        print(
            "    python scripts/split_excel_by_tax_type.py uploads/claim_data.xlsx test_data"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "test_data"

    # Validate input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    try:
        split_excel_by_tax_type(input_file, output_dir)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
