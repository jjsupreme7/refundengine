---
name: root-scripts
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: ^[^/]+\.(py|sh)$
  - field: file_path
    operator: not_contains
    pattern: tasks.py
---

⚠️ **Adding script to root directory**

You're creating a Python or shell script in the root directory.

**Current standard:**
- Scripts belong in `scripts/` directory and subdirectories
- Only `tasks.py` (Celery) should be in root

**Organize scripts by purpose:**
- Utilities → `scripts/utils/`
- Setup scripts → `scripts/setup/`
- Deployment → `scripts/deployment/`
- Analysis → `scripts/analysis/`

**Why this matters:**
- We recently cleaned up root directory
- Keep root organized and professional
- Easier for other engineers to find scripts

**If this is truly a top-level script:**
- Confirm it needs to be in root
- Consider if it should be in scripts/ instead
