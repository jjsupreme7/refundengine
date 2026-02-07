# Setup

This guide covers the current local setup for the `refund-engine` code on this repository.

## Prerequisites

Required:
- Python 3.10+
- OpenAI API key

Recommended:
- Supabase project with service-role access (for RAG retrieval)
- Tesseract OCR binary (`brew install tesseract` on macOS)

## 1. Clone and Install

```bash
git clone https://github.com/jjsupreme7/refundengine.git
cd refund-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure Environment

```bash
cp .env.example .env
```

Minimum required values:
- `OPENAI_API_KEY`

Recommended for RAG-enabled analysis:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Optional tuning knobs are documented in `.env.example`.

## 3. Verify Install

```bash
PYTHONPATH=$PWD venv/bin/pytest -q
```

## 4. Run Local Web App

```bash
PYTHONPATH=$PWD venv/bin/streamlit run apps/refund_webapp.py \
  --server.address localhost \
  --server.port 8765 \
  --server.headless true \
  --server.fileWatcherType none
```

Open:
- `http://localhost:8765`

## 5. Run CLI (Optional)

```bash
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py list-datasets
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py preflight --dataset use_tax_2024
PYTHONPATH=$PWD venv/bin/python scripts/refund_cli.py analyze --dataset use_tax_2024 --limit 5 --dry-run
```

## Troubleshooting

### Web app shows connection error
- Ensure Streamlit process is still running.
- Check listener:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
```

- Hard refresh browser (`Cmd+Shift+R`).

### OCR fallback not working
- Verify tesseract is installed:

```bash
tesseract --version
```

### RAG warnings in analysis metadata
- Check Supabase credentials in `.env`.
- Confirm your project has RPCs named:
- `search_tax_law`
- `search_vendor_background`
