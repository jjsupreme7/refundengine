"""
Excel Masking Module

Masks PII in Excel exports for safe sharing with reviewers.
"""

from typing import Dict, List

import pandas as pd

from .encryption import EncryptionService, PIIFieldMapper


class ExcelMasker:
    """
    Masks PII fields in Excel exports.

    Ensures that exported Excel files don't contain sensitive data
    while preserving enough information for review and audit.
    """

    def __init__(self):
        """Initialize Excel masker"""
        # Encryption service is optional for masking (only used for mask_value static method)
        pass

    def mask_dataframe(
        self, df: pd.DataFrame, column_mapping: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        Mask PII columns in a DataFrame.

        Args:
            df: DataFrame to mask
            column_mapping: Optional dict mapping column names to mask types
                          If None, uses default field mapping

        Returns:
            DataFrame with masked columns
        """
        if df.empty:
            return df

        masked_df = df.copy()

        # Get columns to mask
        if column_mapping is None:
            column_mapping = {}
            for col in df.columns:
                if PIIFieldMapper.should_mask(col):
                    column_mapping[col] = PIIFieldMapper.get_mask_type(col)

        # Mask each column
        for col, mask_type in column_mapping.items():
            if col in masked_df.columns:
                masked_df[col] = masked_df[col].apply(
                    lambda x: self._mask_value(x, mask_type)
                )

        return masked_df

    def _mask_value(self, value, mask_type: str):
        """
        Mask a single value.

        Args:
            value: Value to mask
            mask_type: Type of masking

        Returns:
            Masked value
        """
        if pd.isna(value) or value == "" or value is None:
            return value

        if not isinstance(value, str):
            value = str(value)

        return EncryptionService.mask_value(value, mask_type)

    def mask_excel_export(
        self, input_file: str, output_file: str, columns_to_mask: List[str] = None
    ):
        """
        Mask PII in an Excel file and save to new file.

        Args:
            input_file: Path to input Excel file
            output_file: Path to output masked Excel file
            columns_to_mask: List of column names to mask (None = auto-detect)
        """
        # Read Excel
        df = pd.read_excel(input_file)

        # Build column mapping
        column_mapping = {}
        if columns_to_mask:
            for col in columns_to_mask:
                if col in df.columns:
                    column_mapping[col] = PIIFieldMapper.get_mask_type(col) or "generic"
        else:
            # Auto-detect from field mapper
            for col in df.columns:
                if PIIFieldMapper.should_mask(col):
                    column_mapping[col] = PIIFieldMapper.get_mask_type(col)

        # Mask DataFrame
        masked_df = self.mask_dataframe(df, column_mapping)

        # Save to new file
        masked_df.to_excel(output_file, index=False)

        return {
            "input_file": input_file,
            "output_file": output_file,
            "rows_processed": len(masked_df),
            "columns_masked": list(column_mapping.keys()),
        }

    @staticmethod
    def get_safe_export_columns() -> Dict[str, str]:
        """
        Get recommended column configuration for safe exports.

        Returns:
            Dictionary of column names with their masking strategy
        """
        return {
            # Keep as-is (business data)
            "vendor": "keep",
            "invoice_number": "keep",
            "po_number": "keep",
            "date": "keep",
            "amount": "keep",
            "tax": "keep",
            "product_desc": "keep",
            "product_type": "keep",
            "ai_refund_basis": "keep",
            "ai_citation": "keep",
            "ai_confidence": "keep",
            "ai_estimated_refund": "keep",
            "ai_explanation": "keep",
            # Mask (sensitive)
            "contact_email": "email",
            "contact_phone": "phone",
            "approver_name": "name",
            "approver_email": "email",
            "bank_account": "account",
            "routing_number": "account",
            "tax_id": "tax_id",
            # Remove completely (highly sensitive)
            "ssn": "remove",
            "credit_card": "remove",
        }

    def apply_safe_export_policy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply safe export policy to DataFrame.

        Implements the recommended column strategy:
        - Keep business data
        - Mask PII
        - Remove highly sensitive fields

        Args:
            df: DataFrame to process

        Returns:
            Safe DataFrame for export
        """
        safe_df = df.copy()
        policy = self.get_safe_export_columns()

        columns_to_mask = {}
        columns_to_remove = []

        for col in safe_df.columns:
            col_lower = col.lower()

            # Check if column matches any policy
            strategy = None
            for policy_col, policy_strategy in policy.items():
                if policy_col in col_lower or col_lower in policy_col:
                    strategy = policy_strategy
                    break

            if strategy == "remove":
                columns_to_remove.append(col)
            elif strategy and strategy != "keep":
                columns_to_mask[col] = strategy

        # Remove highly sensitive columns
        if columns_to_remove:
            safe_df = safe_df.drop(columns=columns_to_remove)

        # Mask PII columns
        if columns_to_mask:
            safe_df = self.mask_dataframe(safe_df, columns_to_mask)

        return safe_df
