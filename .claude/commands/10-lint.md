# Format and Lint Code

Runs three code quality tools in sequence to format and check your Python code:
1. **isort** - Organizes imports alphabetically and by type
2. **black** - Formats code to consistent style
3. **flake8** - Checks for errors and style violations

## Why This Matters

Consistent code formatting:
- Makes code reviews easier
- Prevents merge conflicts from whitespace changes
- Catches common bugs (unused imports, undefined variables)
- Keeps the codebase professional

## How It Fits In The System

```
[You write code]
        |
        v
    /10-lint
        |
        +--> isort: Fixes import order
        |
        +--> black: Formats code style
        |
        +--> flake8: Reports remaining issues
        |
        v
[Clean, consistent code ready to commit]
```

## Arguments

$ARGUMENTS (optional)
- No args → Lint entire project
- Path → Lint specific file or directory

## Examples

```bash
/10-lint                    # Lint everything
/10-lint analysis/          # Lint analysis folder
/10-lint core/enhanced_rag.py    # Lint one file
```

## Success Looks Like

```
Fixing /Users/.../core/enhanced_rag.py
Fixing /Users/.../analysis/fast_batch_analyzer.py
reformatted 2 files

All done! ✨ 🍰 ✨
2 files reformatted, 45 files left unchanged.
```

(No flake8 output = no errors)

## Common Issues

- `E501 line too long` → We ignore this (--ignore=E501)
- `F401 imported but unused` → Remove the unused import
- `E999 SyntaxError` → You have a Python syntax error. Fix it.

## When To Run

- Before every git commit
- After writing new code
- Before code review

## What Each Tool Does

| Tool | Purpose | Modifies Files? |
|------|---------|-----------------|
| isort | Sort imports | Yes |
| black | Format code | Yes |
| flake8 | Report issues | No (just reports) |

```bash
isort ${ARGUMENTS:-.} && black ${ARGUMENTS:-.} && flake8 ${ARGUMENTS:-.} --max-line-length=120 --ignore=E501,W503
```
