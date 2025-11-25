---
description: Format and lint code (black, isort, flake8)
---

Format and lint the codebase:

1. **Format with Black:**
   ```bash
   black .
   ```

2. **Sort imports with isort:**
   ```bash
   isort . --profile black
   ```

3. **Lint with flake8:**
   ```bash
   flake8 . --max-line-length=88 --extend-ignore=E203,W503
   ```

4. **Report results:**
   - Show any formatting changes made
   - List any linting errors that need manual attention
   - Suggest fixes for common issues

Optional: Run mypy type checking if `$ARGUMENTS` includes `--types`:
```bash
mypy core/ scripts/ analysis/
```
