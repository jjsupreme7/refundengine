from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from pathlib import Path

import pandas as pd

from refund_engine.analysis.openai_analyzer import (
    InvoiceEvidence,
    OpenAIAnalyzer,
    RowEvidence,
)
from refund_engine.constants import AI_OUTPUT_COLUMNS
from refund_engine.datasets import coerce_float
from refund_engine.invoice_text import extract_invoice_text
from refund_engine.validation_rules import ensure_process_token, validate_output_row


@dataclass(frozen=True)
class ColumnMapping:
    vendor: str
    tax_amount: str
    description: str
    invoice_1: str
    analysis_col: str
    invoice_2: str | None = None
    tax_base: str | None = None
    invoice_number: str | None = None
    po_number: str | None = None


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_row_selection(text: str, max_rows: int) -> list[int]:
    text = (text or "").strip()
    if not text:
        return []

    indices: set[int] = set()
    parts = [part.strip() for part in text.split(",") if part.strip()]
    for part in parts:
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text.strip())
            end = int(end_text.strip())
            if start > end:
                start, end = end, start
            for idx in range(start, end + 1):
                if 0 <= idx < max_rows:
                    indices.add(idx)
        else:
            idx = int(part)
            if 0 <= idx < max_rows:
                indices.add(idx)

    return sorted(indices)


def suggest_column_mapping(columns: list[str]) -> dict[str, str | None]:
    lower_map = {col.lower(): col for col in columns}

    def pick(*candidates: str) -> str | None:
        for candidate in candidates:
            if candidate.lower() in lower_map:
                return lower_map[candidate.lower()]
        for col in columns:
            if any(candidate.lower() in col.lower() for candidate in candidates):
                return col
        return None

    return {
        "vendor": pick("Vendor Name", "Vendor", "name1_po_vendor_name"),
        "tax_amount": pick("Tax Remit", "Tax_Remit", "hwste_tax_amount_lc"),
        "description": pick("Description", "txz01_po_description"),
        "invoice_1": pick("Inv-1PDF", "Inv_1_File", "Inv 1"),
        "invoice_2": pick("Inv-2 PDF", "Inv_2_File", "Inv 2"),
        "analysis_col": pick("AI_Reasoning", "KOM Analysis & Notes", "Recon Analysis"),
        "tax_base": pick("hwbas_tax_base_lc"),
        "invoice_number": pick("INVNO", "Invoice_Number", "belnr_max_document_number"),
        "po_number": pick("PO Number", "PO_Number", "ebeln_po_number"),
    }


def _invoice_evidence(invoice_dir: str, filename: str, max_invoice_pages: int) -> InvoiceEvidence | None:
    if not filename:
        return None
    invoice_path = Path(invoice_dir).expanduser() / filename
    result = extract_invoice_text(invoice_path, max_pages=max_invoice_pages)
    return InvoiceEvidence(
        filename=filename,
        path=result.pdf_path,
        extraction_method=result.method,
        text_preview=result.preview(max_chars=2400),
        warnings=result.warnings,
    )


def _fallback_review_row(row: pd.Series, mapping: ColumnMapping, reason: str) -> dict[str, Any]:
    tax_amount = coerce_float(row.get(mapping.tax_amount)) or 0.0
    invoice_number = _safe_str(row.get(mapping.invoice_number)) if mapping.invoice_number else "UNKNOWN"
    description = _safe_str(row.get(mapping.description))

    lines = [
        f"INVOICE VERIFIED: Invoice #{invoice_number} dated UNKNOWN",
        "SHIP-TO: UNKNOWN",
        f"MATCHED LINE ITEM: {description or 'UNKNOWN'} @ ${tax_amount:,.2f}",
        "---",
        "",
        "VENDOR RESEARCH (from web search):",
        "Automated analysis did not complete.",
        "",
        "PRODUCT/SERVICE ANALYSIS:",
        description or "No description provided.",
        "",
        "WHY THIS IS/ISN'T TAXABLE:",
        "Manual review required due to analysis failure.",
        "",
        "TAX ANALYSIS:",
        "- Product Type: Unknown",
        "- Exemption Basis: Unknown",
        "- Citation: N/A",
        "",
        "DECISION: REVIEW",
        "ESTIMATED REFUND: $0.00",
        f"EXPLANATION: {reason}",
    ]

    return {
        "Product_Desc": description,
        "Product_Type": "",
        "Service_Classification": "",
        "Refund_Basis": "",
        "Citation": "",
        "Citation_Source": "",
        "Confidence": 0.0,
        "Estimated_Refund": 0.0,
        "Refund_Source": "",
        "Final_Decision": "REVIEW",
        "Explanation": reason,
        "Needs_Review": "Yes",
        "Follow_Up_Questions": "Manual verification needed",
        "AI_Reasoning": ensure_process_token("\n".join(lines)),
        "Tax_Category": "",
        "Methodology": "",
        "Sales_Use_Tax": "",
    }


def analyze_rows_dataframe(
    df: pd.DataFrame,
    *,
    mapping: ColumnMapping,
    row_indices: list[int],
    invoice_dir: str,
    model: str | None = None,
    reasoning_effort: str | None = None,
    verbosity: str | None = None,
    max_invoice_pages: int = 4,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    out_df = df.copy()
    analyzer = OpenAIAnalyzer(
        model=model,
        reasoning_effort=reasoning_effort,
        verbosity=verbosity,
    )
    events: list[dict[str, Any]] = []

    for col in AI_OUTPUT_COLUMNS:
        if col not in out_df.columns:
            out_df[col] = None

    for idx in row_indices:
        if idx not in out_df.index:
            events.append(
                {"row_index": idx, "status": "skipped", "reason": "row not in dataframe"}
            )
            continue

        row = out_df.loc[idx]
        vendor = _safe_str(row.get(mapping.vendor))
        description = _safe_str(row.get(mapping.description))
        invoice_1_name = _safe_str(row.get(mapping.invoice_1))
        invoice_2_name = _safe_str(row.get(mapping.invoice_2)) if mapping.invoice_2 else ""

        evidence = RowEvidence(
            dataset_id="webapp",
            row_index=int(idx),
            vendor=vendor,
            description=description,
            tax_amount=coerce_float(row.get(mapping.tax_amount)),
            tax_base=coerce_float(row.get(mapping.tax_base)) if mapping.tax_base else None,
            invoice_number=_safe_str(row.get(mapping.invoice_number)) if mapping.invoice_number else "",
            po_number=_safe_str(row.get(mapping.po_number)) if mapping.po_number else "",
            invoice_1=_invoice_evidence(invoice_dir, invoice_1_name, max_invoice_pages),
            invoice_2=_invoice_evidence(invoice_dir, invoice_2_name, max_invoice_pages),
        )

        status = "ok"
        validation_errors: list[str] = []
        metadata: dict[str, Any] = {}

        try:
            result, metadata = analyzer.analyze_row(evidence)
            validation_errors = validate_output_row(result)
            if validation_errors:
                guidance = (
                    "Previous output failed validation. Return corrected JSON only. "
                    f"Issues: {validation_errors}"
                )
                result, metadata = analyzer.analyze_row(evidence, guidance=guidance)
                validation_errors = validate_output_row(result)
                if validation_errors:
                    status = "fallback_review"
                    result = _fallback_review_row(
                        row,
                        mapping,
                        f"Validation failed after retry: {validation_errors}",
                    )
                else:
                    status = "retry_ok"
        except Exception as exc:
            status = "error_review"
            validation_errors = [str(exc)]
            result = _fallback_review_row(row, mapping, f"Analysis error: {exc}")

        for key, value in result.items():
            if key in out_df.columns:
                out_df.at[idx, key] = value

        if mapping.analysis_col in out_df.columns:
            out_df.at[idx, mapping.analysis_col] = result.get("AI_Reasoning")

        events.append(
            {
                "row_index": int(idx),
                "status": status,
                "vendor": vendor,
                "final_decision": result.get("Final_Decision"),
                "confidence": result.get("Confidence"),
                "citation": result.get("Citation"),
                "invoice_1_method": evidence.invoice_1.extraction_method if evidence.invoice_1 else "none",
                "invoice_2_method": evidence.invoice_2.extraction_method if evidence.invoice_2 else "none",
                "validation_errors": validation_errors,
                "metadata": metadata,
            }
        )

    return out_df, events
