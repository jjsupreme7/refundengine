from __future__ import annotations

import argparse
import json
from pathlib import Path

from refund_engine.pipeline import (
    AnalyzeOptions,
    analyze_dataset,
    list_datasets,
    preflight_dataset,
    validate_dataset_output,
)


def _print_json(data):
    print(json.dumps(data, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refund Engine CLI")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to datasets config yaml (default: config/datasets.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-datasets", help="List configured datasets")

    preflight = subparsers.add_parser("preflight", help="Run dataset preflight checks")
    preflight.add_argument("--dataset", required=True, help="Dataset id")
    preflight.add_argument(
        "--sample-rows",
        type=int,
        default=25,
        help="How many candidate rows to inspect for invoice file existence",
    )

    analyze = subparsers.add_parser("analyze", help="Run OpenAI analysis pipeline")
    analyze.add_argument("--dataset", required=True, help="Dataset id")
    analyze.add_argument("--limit", type=int, default=10, help="Max rows to process")
    analyze.add_argument("--row", type=int, default=None, help="Analyze one row index")
    analyze.add_argument("--vendor", type=str, default=None, help="Filter by vendor substring")
    analyze.add_argument(
        "--min-amount",
        type=float,
        default=None,
        help="Minimum tax amount filter",
    )
    analyze.add_argument(
        "--max-invoice-pages",
        type=int,
        default=4,
        help="Max pages to read/OCR per invoice",
    )
    analyze.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without OpenAI calls or output writes",
    )
    analyze.add_argument(
        "--no-write",
        action="store_true",
        help="Run analysis but skip writing updates to output workbook",
    )
    analyze.add_argument("--model", type=str, default=None, help="Override analysis model")
    analyze.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high"],
        default=None,
        help="Override reasoning effort",
    )
    analyze.add_argument(
        "--verbosity",
        choices=["low", "medium", "high"],
        default=None,
        help="Override text verbosity",
    )

    validate = subparsers.add_parser("validate", help="Validate output workbook rows")
    validate.add_argument("--dataset", required=True, help="Dataset id")
    validate.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional row limit for validation scan",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_path = args.config

    if args.command == "list-datasets":
        _print_json({"datasets": list_datasets(config_path=config_path)})
        return 0

    if args.command == "preflight":
        report = preflight_dataset(
            args.dataset,
            sample_rows=args.sample_rows,
            config_path=config_path,
        )
        _print_json(report)
        return 0 if report.get("ok") else 1

    if args.command == "analyze":
        options = AnalyzeOptions(
            dataset_id=args.dataset,
            limit=args.limit,
            row_index=args.row,
            vendor=args.vendor,
            min_amount=args.min_amount,
            max_invoice_pages=args.max_invoice_pages,
            dry_run=args.dry_run,
            write_output=not args.no_write,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            verbosity=args.verbosity,
            config_path=config_path,
        )
        summary = analyze_dataset(options)
        _print_json(summary)
        return 0 if summary.get("ok") else 1

    if args.command == "validate":
        report = validate_dataset_output(
            args.dataset,
            max_rows=args.max_rows,
            config_path=config_path,
        )
        _print_json(report)
        return 0 if report.get("ok") else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
