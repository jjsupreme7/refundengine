# Project Overview

## Purpose

`refund-engine` is a local-first analysis system for identifying potential Washington sales/use tax refund opportunities from invoice-backed workbook rows.

It exists to make tax review work faster without hiding evidence from the reviewer.

## Primary Goals

- Reduce manual effort for large workbook reviews.
- Keep analysis traceable to invoice evidence and citations.
- Preserve reviewer control with explicit save/version steps.
- Support repeatable workflows across years/datasets.

## Core Problem It Solves

A reviewer often has:
- One or more Excel workbooks.
- Invoice documents (PDF or scanned image-like PDFs).
- Need to decide refund/no-refund/review row-by-row.

This project links those inputs, runs analysis consistently, and stores auditable outputs as versioned workbook artifacts.

## Current Product Surface

### Web App (Primary)

Entry point:
- `apps/refund_webapp.py`

Capabilities:
- Upload workbook (`.xlsx`, `.xlsb`).
- Track workbook versions and sampled diffs.
- Upload invoice files in-app.
- Select specific rows to analyze.
- Save analyzed results as a new version.

### CLI (Batch)

Entry point:
- `scripts/refund_cli.py`

Capabilities:
- Dataset preflight checks.
- Controlled row selection and batch analysis.
- Optional dry-run and output validation.

## Analysis Architecture

Main modules:
- `refund_engine/web_analysis.py` - row orchestration for UI flow.
- `refund_engine/analysis/openai_analyzer.py` - OpenAI call + prompt + output mapping.
- `refund_engine/invoice_text.py` - PDF text extraction with OCR fallback.
- `refund_engine/rag.py` - Supabase RAG retrieval for legal/vendor context.
- `refund_engine/validation_rules.py` - output validation and safe fallback behavior.
- `refund_engine/workbook_repository.py` - versioned storage for workbooks and invoices.

Runtime pipeline:

`worksheet row -> invoice extraction/OCR -> RAG context -> OpenAI analysis -> validation -> output columns`

## Data and State

Default local repository root:
- `webapp_data/`

Stored artifacts:
- `webapp_data/workbooks/<workbook_id>/versions/...`
- `webapp_data/workbooks/<workbook_id>/metadata.yaml`
- `webapp_data/workbooks/<workbook_id>/changes/...`
- `webapp_data/invoices/...`

Important behavior:
- Workbook upload is persisted immediately when imported.
- Analysis results are temporary until user explicitly saves as a new version.

## Legal and Policy Context

This workflow currently assumes 2023-2024 transaction review under pre-October 1, 2025 Washington law.

If transaction periods expand, rules and prompt assumptions need to be updated and tested.

## What "Done" Looks Like for a Row

A row is considered operationally complete when:
- Invoice evidence was attempted.
- Analysis output passes validation (or deterministic REVIEW fallback applied).
- Decision and reasoning are written to output columns.
- User saves to a new version when ready.

## Known Limitations

- No auth/multi-user isolation in the local web app.
- Row targeting is numeric index-based (not natural language yet).
- RAG quality depends on Supabase connectivity and RPC schema consistency.
- Long-running server process management is manual in local environments.

## Near-Term Improvements

- Natural-language row targeting and saved filters.
- Better server lifecycle tooling for local operators.
- Improved diagnostics panel for RAG and OCR evidence quality.
- Optional background job queue for larger row batches.
