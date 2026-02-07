# Workflows

## Web App Workflow (Primary)

1. Start app:

```bash
PYTHONPATH=$PWD venv/bin/streamlit run apps/refund_webapp.py --server.address localhost --server.port 8765
```

2. Open `http://localhost:8765`.
3. In `Upload / Versions`:
- Upload workbook (`.xlsx` or `.xlsb`).
- Upload invoice files (`.pdf` or image formats).
4. In `Analyze Rows`:
- Select workbook version and sheet.
- Map required columns.
- Enter rows to analyze (`12,15,20-25`).
- Run analysis.
5. Save results:
- Click `Save Analyzed Rows as New Version`.

## CLI Workflow (Batch)

1. List datasets:

```bash
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py list-datasets
```

2. Run preflight:

```bash
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py preflight --dataset use_tax_2024
```

3. Dry-run analysis:

```bash
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py analyze --dataset use_tax_2024 --limit 10 --dry-run
```

4. Real run:

```bash
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py analyze --dataset use_tax_2024 --limit 10
```

## Saved Artifacts

Web app data is written under `webapp_data/` by default:
- `webapp_data/workbooks/` - versioned workbook artifacts.
- `webapp_data/invoices/` - uploaded invoice files.

## Operational Notes

- Analysis includes OCR fallback for scanned invoices.
- Analysis includes RAG retrieval when Supabase is configured.
- Unsaved in-session analysis is lost if the session closes.
- Persisted output requires explicit save action.
