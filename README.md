# Refund Engine

A local-first refund analysis system for Washington sales/use tax workbooks.

It helps a reviewer:
- Upload workbooks and track version history.
- Upload invoice PDFs/images used as supporting evidence.
- Run row-level AI analysis with OCR and legal/vendor retrieval context.
- Save analyzed output as a new workbook version.

The system is designed for 2023-2024 transaction analysis and pre-October 1, 2025 Washington law assumptions.

## What Works Today

- Local Streamlit web app: `apps/refund_webapp.py`
- Workbook version repository: `refund_engine/workbook_repository.py`
- OCR-enabled invoice extraction: `refund_engine/invoice_text.py`
- OpenAI-based row analysis: `refund_engine/analysis/openai_analyzer.py`
- Supabase-backed RAG retrieval for legal/vendor context: `refund_engine/rag.py`
- Validation and retry/fallback logic: `refund_engine/validation_rules.py`
- CLI pipeline for dataset-driven runs: `scripts/refund_cli.py`

## High-Level Flow

1. Upload workbook (`.xlsx` or `.xlsb`).
2. Upload invoices (`.pdf` or image formats).
3. Select sheet, map columns, choose rows.
4. Analyze selected rows.
5. Review events/results.
6. Save analyzed workbook as a new version.

Pipeline used by analysis:

`row data -> invoice text/OCR -> RAG retrieval -> OpenAI analysis -> validation -> output columns`

## Repository Layout

- `apps/` - Streamlit app.
- `refund_engine/` - Core analysis modules.
- `scripts/` - CLI entrypoints and utility scripts.
- `tests/` - Pytest coverage for core modules.
- `config/datasets.yaml` - Dataset definitions for CLI runs.
- `knowledge_base/` - Local law/vendor reference assets.
- `webapp_data/` - Local runtime data (versions/uploads, not source logic).

## Quick Start (Local Web App)

### 1. Install and Configure

```bash
cd refund-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Required environment values:
- `OPENAI_API_KEY`
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (for RAG)

Recommended:
- Install Tesseract for OCR fallback (`brew install tesseract` on macOS).

### 2. Run App

```bash
PYTHONPATH=$PWD venv/bin/streamlit run apps/refund_webapp.py \
  --server.address localhost \
  --server.port 8765 \
  --server.headless true \
  --server.fileWatcherType none
```

Open:
- `http://localhost:8765`

### 3. Use App

1. `Upload / Versions` tab:
- Upload workbook.
- Upload invoice files.

2. `Analyze Rows` tab:
- Select workbook version and sheet.
- Map required columns.
- Enter row indices/ranges (example: `12,15,20-25`).
- Click `Analyze Selected Rows`.
- Click `Save Analyzed Rows as New Version` to persist output.

## CLI Usage

Use the CLI when you want batch runs against configured datasets.

```bash
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py list-datasets
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py preflight --dataset use_tax_2024
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py analyze --dataset use_tax_2024 --limit 5 --dry-run
```

## Testing

```bash
PYTHONPATH=$PWD venv/bin/pytest -q
```

## Persistence Model

By default, the web app stores runtime artifacts under `webapp_data/`:
- `webapp_data/workbooks/` - workbook versions and change summaries.
- `webapp_data/invoices/` - uploaded invoice files.

This data is operational and local-state oriented.

## Troubleshooting

### "Connection error" / "Site can't be reached"
- Ensure Streamlit is still running in a terminal.
- Verify listener:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
```

- Hard refresh browser (`Cmd+Shift+R`) after restart.

### Upload button disabled
- The page is disconnected from backend (`CONNECTING` state).
- Restart Streamlit and reload.

### RAG warnings in analysis metadata
- Confirm Supabase credentials and network access.
- Confirm RPC names exist in your Supabase project:
- `search_tax_law`
- `search_vendor_background`

## Project Context

Business context and system goals are documented in:
- `PROJECT_OVERVIEW.md`

Contributor rules and commit hygiene are documented in:
- `CONTRIBUTING.md`
