# Contributing

## Development Setup

```bash
cd refund-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run tests:

```bash
PYTHONPATH=$PWD venv/bin/pytest -q
```

Run web app:

```bash
PYTHONPATH=$PWD venv/bin/streamlit run apps/refund_webapp.py --server.address localhost --server.port 8765
```

## Standards

- Keep changes focused by feature.
- Prefer module-level code in `refund_engine/` over large ad-hoc scripts.
- Add or update tests for behavior changes.
- Maintain clear fallback behavior for analysis failures.

## Commit Hygiene

Do not commit:
- Secrets (`.env`, credentials, tokens, keys).
- Local runtime artifacts (`webapp_data/`, `runs/`, temporary outputs).
- Personal local tool settings unless intentionally shared.

Before commit:
1. Run tests.
2. Review `git status` for unrelated files.
3. Stage only relevant files.

## Pull Request Expectations

Include:
- What changed.
- Why it changed.
- How to validate it.
- Any migration or environment requirements.

If behavior changes user workflow, update:
- `README.md`
- `PROJECT_OVERVIEW.md`
- `SETUP.md` when setup instructions change.
