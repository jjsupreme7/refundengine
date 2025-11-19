---
name: root-docs
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: ^[^/]+\.md$
  - field: file_path
    operator: not_contains
    pattern: README.md
  - field: file_path
    operator: not_contains
    pattern: CHANGELOG.md
  - field: file_path
    operator: not_contains
    pattern: PRODUCT_ROADMAP.md
---

⚠️ **Adding documentation to root directory**

You're creating a markdown file in the root directory.

**Current standard:**
- Only `README.md`, `CHANGELOG.md`, and `PRODUCT_ROADMAP.md` should be in root
- Other docs belong in `docs/` directory

**Consider:**
- Is this a guide? → `docs/guides/`
- Is this planning? → `docs/planning/` or `docs/active/`
- Is this deployment notes? → `docs/deployment/`

**Why this matters:**
- We recently cleaned up root from 21 docs to 3
- Keep root professional and uncluttered
- Other engineers expect docs in `docs/` folder
