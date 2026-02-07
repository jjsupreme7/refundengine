from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from refund_engine.analysis.openai_analyzer import (
    InvoiceEvidence,
    OpenAIAnalyzer,
    RowEvidence,
)
from refund_engine.constants import RUNS_DIR
from refund_engine.datasets import (
    DatasetConfig,
    coerce_float,
    filter_unanalyzed_rows,
    get_dataset_config,
    is_blank,
    load_datasets_config,
    read_excel_dataframe,
    read_source_dataframe,
    select_rows,
)
from refund_engine.invoice_text import extract_invoice_text
from refund_engine.output_writer import apply_updates_to_output
from refund_engine.validation_rules import ensure_process_token, validate_output_row


@dataclass(frozen=True)
class AnalyzeOptions:
    dataset_id: str
    limit: int = 10
    row_index: int | None = None
    vendor: str | None = None
    min_amount: float | None = None
    max_invoice_pages: int = 4
    dry_run: bool = False
    write_output: bool = True
    model: str | None = None
    reasoning_effort: str | None = None
    verbosity: str | None = None
    config_path: str | Path | None = None


def list_datasets(config_path: str | Path | None = None) -> dict[str, str]:
    datasets = load_datasets_config(config_path=config_path)
    return {dataset_id: cfg.description for dataset_id, cfg in datasets.items()}


def _safe_text(value: Any) -> str:
    if is_blank(value):
        return ""
    return str(value).strip()


def _resolve_invoice_path(invoice_dir: Path, filename: str | None) -> Path | None:
    if not filename:
        return None
    raw = Path(filename).expanduser()
    if raw.is_absolute():
        return raw
    return invoice_dir / filename


def _build_invoice_evidence(
    invoice_dir: Path,
    filename: str | None,
    *,
    max_pages: int,
) -> InvoiceEvidence | None:
    if not filename:
        return None
    path = _resolve_invoice_path(invoice_dir, filename)
    if path is None:
        return None

    result = extract_invoice_text(path, max_pages=max_pages)
    return InvoiceEvidence(
        filename=filename,
        path=str(path),
        extraction_method=result.method,
        text_preview=result.preview(max_chars=1600),
        warnings=result.warnings,
    )


def _build_row_evidence(
    dataset_id: str,
    config: DatasetConfig,
    row_index: int,
    row: pd.Series,
    *,
    max_invoice_pages: int,
) -> RowEvidence:
    cols = config.columns
    invoice_1_name = _safe_text(row.get(cols.invoice_1))
    invoice_2_name = _safe_text(row.get(cols.invoice_2)) if cols.invoice_2 else ""

    tax_amount = coerce_float(row.get(cols.tax_amount))
    tax_base = coerce_float(row.get(cols.tax_base)) if cols.tax_base else None

    return RowEvidence(
        dataset_id=dataset_id,
        row_index=row_index,
        vendor=_safe_text(row.get(cols.vendor)),
        description=_safe_text(row.get(cols.description)) if cols.description else "",
        tax_amount=tax_amount,
        tax_base=tax_base,
        invoice_number=_safe_text(row.get(cols.invoice_number)) if cols.invoice_number else "",
        po_number=_safe_text(row.get(cols.po_number)) if cols.po_number else "",
        invoice_1=_build_invoice_evidence(
            config.invoice_path,
            invoice_1_name,
            max_pages=max_invoice_pages,
        ),
        invoice_2=_build_invoice_evidence(
            config.invoice_path,
            invoice_2_name,
            max_pages=max_invoice_pages,
        ),
    )


def _fallback_review_result(evidence: RowEvidence, reason: str) -> dict[str, Any]:
    lines = [
        f"INVOICE VERIFIED: Invoice #{evidence.invoice_number or 'UNKNOWN'} dated UNKNOWN",
        "SHIP-TO: UNKNOWN",
        f"MATCHED LINE ITEM: {evidence.description or 'UNKNOWN'} @ "
        f"${(evidence.tax_base if evidence.tax_base is not None else evidence.tax_amount or 0.0):,.2f}",
        "---",
        "",
        "VENDOR RESEARCH (from web search):",
        "Automated analysis could not complete this row.",
        "",
        "PRODUCT/SERVICE ANALYSIS:",
        evidence.description or "No description provided.",
        "",
        "WHY THIS IS/ISN'T TAXABLE:",
        "Manual review required due to processing or validation error.",
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
        "Product_Desc": evidence.description,
        "Product_Type": "",
        "Service_Classification": "",
        "Refund_Basis": "",
        "Citation": "",
        "Citation_Source": "",
        "Confidence": 0.0,
        "Estimated_Refund": 0.0,
        "Final_Decision": "REVIEW",
        "Explanation": reason,
        "Needs_Review": "Yes",
        "Follow_Up_Questions": "Please inspect invoice manually.",
        "AI_Reasoning": ensure_process_token("\n".join(lines)),
    }


def _write_run_log(dataset_id: str, events: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    RUNS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RUNS_DIR / f"{stamp}_{dataset_id}.jsonl"
    with open(path, "w") as f:
        for event in events:
            f.write(json.dumps(event, default=str) + "\n")
        f.write(json.dumps({"type": "summary", **summary}, default=str) + "\n")
    return str(path)


def preflight_dataset(
    dataset_id: str,
    *,
    sample_rows: int = 25,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    config = get_dataset_config(dataset_id, config_path=config_path)
    report: dict[str, Any] = {
        "dataset_id": dataset_id,
        "description": config.description,
        "source_file": str(config.source_file),
        "output_file": str(config.output_file),
        "invoice_path": str(config.invoice_path),
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    if not config.source_file.exists():
        report["errors"].append(f"Source file missing: {config.source_file}")
    if not config.invoice_path.exists():
        report["errors"].append(f"Invoice directory missing: {config.invoice_path}")

    if shutil.which("tesseract") is None:
        report["warnings"].append(
            "tesseract binary not found; OCR fallback is unavailable for scanned PDFs"
        )

    source_df = None
    if not report["errors"]:
        try:
            source_df = read_source_dataframe(config)
        except Exception as exc:
            report["errors"].append(f"Failed to read source file: {exc}")

    if source_df is not None:
        required_columns = [
            config.columns.vendor,
            config.columns.tax_amount,
            config.columns.invoice_1,
            config.columns.analysis_col,
        ]
        if config.columns.description:
            required_columns.append(config.columns.description)
        missing_columns = [col for col in required_columns if col not in source_df.columns]
        if missing_columns:
            report["errors"].append(f"Missing required columns: {missing_columns}")
        else:
            filtered = filter_unanalyzed_rows(source_df, config)
            report["stats"]["source_rows"] = int(len(source_df))
            report["stats"]["unanalyzed_rows"] = int(len(filtered))

            sample = filtered.head(sample_rows)
            missing_invoice_files = 0
            for _, row in sample.iterrows():
                invoice_name = _safe_text(row.get(config.columns.invoice_1))
                path = _resolve_invoice_path(config.invoice_path, invoice_name)
                if not path or not path.exists():
                    missing_invoice_files += 1
            report["stats"]["sample_rows_checked"] = int(len(sample))
            report["stats"]["sample_missing_invoice_files"] = int(missing_invoice_files)

    report["ok"] = len(report["errors"]) == 0
    return report


def analyze_dataset(options: AnalyzeOptions) -> dict[str, Any]:
    config = get_dataset_config(options.dataset_id, config_path=options.config_path)
    preflight = preflight_dataset(
        options.dataset_id,
        sample_rows=max(5, min(25, options.limit)),
        config_path=options.config_path,
    )
    if not preflight["ok"]:
        return {
            "ok": False,
            "aborted": True,
            "reason": "preflight_failed",
            "preflight": preflight,
        }

    source_df = read_source_dataframe(config)
    filtered = filter_unanalyzed_rows(source_df, config)
    selected = select_rows(
        filtered,
        config,
        limit=options.limit,
        row_index=options.row_index,
        vendor=options.vendor,
        min_amount=options.min_amount,
    )

    if len(selected) == 0:
        summary = {
            "ok": True,
            "aborted": False,
            "dataset_id": options.dataset_id,
            "selected_rows": 0,
            "updated_rows": 0,
            "dry_run": options.dry_run,
            "message": "No rows selected for analysis.",
            "preflight": preflight,
        }
        summary["run_log"] = _write_run_log(options.dataset_id, [], summary)
        return summary

    analyzer = None
    if not options.dry_run:
        analyzer = OpenAIAnalyzer(
            model=options.model,
            reasoning_effort=options.reasoning_effort,
            verbosity=options.verbosity,
        )

    updates: dict[int, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    status_counts = {"ok": 0, "retry_ok": 0, "fallback_review": 0, "error_review": 0, "dry_run": 0}

    for idx, row in selected.iterrows():
        evidence = _build_row_evidence(
            options.dataset_id,
            config,
            int(idx),
            row,
            max_invoice_pages=options.max_invoice_pages,
        )
        result: dict[str, Any]
        metadata: dict[str, Any] = {}
        validation_errors: list[str] = []
        status = "ok"

        if options.dry_run:
            result = _fallback_review_result(
                evidence,
                "dry-run mode: no API call executed",
            )
            status = "dry_run"
        else:
            try:
                assert analyzer is not None
                result, metadata = analyzer.analyze_row(evidence)
                validation_errors = validate_output_row(result)

                if validation_errors:
                    guidance = (
                        "Your previous output failed validation. "
                        f"Fix these issues and return corrected JSON only: {validation_errors}"
                    )
                    result, metadata = analyzer.analyze_row(evidence, guidance=guidance)
                    validation_errors = validate_output_row(result)
                    if validation_errors:
                        status = "fallback_review"
                        result = _fallback_review_result(
                            evidence,
                            f"Validation failed after retry: {validation_errors}",
                        )
                    else:
                        status = "retry_ok"
            except Exception as exc:
                status = "error_review"
                result = _fallback_review_result(evidence, f"Analysis error: {exc}")
                validation_errors = [f"Analysis exception: {exc}"]

        updates[int(idx)] = result
        status_counts[status] = status_counts.get(status, 0) + 1
        events.append(
            {
                "type": "row",
                "dataset_id": options.dataset_id,
                "row_index": int(idx),
                "vendor": evidence.vendor,
                "status": status,
                "invoice_1_method": evidence.invoice_1.extraction_method if evidence.invoice_1 else "none",
                "invoice_2_method": evidence.invoice_2.extraction_method if evidence.invoice_2 else "none",
                "final_decision": result.get("Final_Decision"),
                "confidence": result.get("Confidence"),
                "estimated_refund": result.get("Estimated_Refund"),
                "validation_errors": validation_errors,
                "metadata": metadata,
            }
        )

    write_result = None
    if options.write_output and not options.dry_run:
        write_result = apply_updates_to_output(config, updates)

    summary = {
        "ok": True,
        "aborted": False,
        "dataset_id": options.dataset_id,
        "selected_rows": int(len(selected)),
        "updated_rows": int(len(updates)),
        "dry_run": options.dry_run,
        "write_output": options.write_output and not options.dry_run,
        "status_counts": status_counts,
        "preflight": preflight,
        "write_result": write_result,
    }
    summary["run_log"] = _write_run_log(options.dataset_id, events, summary)
    return summary


def validate_dataset_output(
    dataset_id: str,
    *,
    max_rows: int | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    config = get_dataset_config(dataset_id, config_path=config_path)
    if not config.output_file.exists():
        return {
            "ok": False,
            "dataset_id": dataset_id,
            "error": f"Output file not found: {config.output_file}",
        }

    df = read_excel_dataframe(config.output_file, config.sheet_name)
    rows = df if max_rows is None else df.head(max_rows)

    errors_by_row: dict[int, list[str]] = {}
    for idx, row in rows.iterrows():
        reasoning = row.get("AI_Reasoning")
        if is_blank(reasoning):
            continue
        row_errors = validate_output_row(row.to_dict())
        if row_errors:
            errors_by_row[int(idx)] = row_errors

    return {
        "ok": len(errors_by_row) == 0,
        "dataset_id": dataset_id,
        "checked_rows": int(len(rows)),
        "rows_with_errors": len(errors_by_row),
        "errors_by_row": errors_by_row,
    }
