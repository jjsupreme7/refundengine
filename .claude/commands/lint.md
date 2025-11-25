Run code formatting and linting checks.

Arguments: $ARGUMENTS
- Optional: Specific file or directory to lint
- No argument lints the entire project

Examples:
- /lint (entire project)
- /lint analysis/
- /lint core/rag.py

```bash
isort ${ARGUMENTS:-.} && black ${ARGUMENTS:-.} && flake8 ${ARGUMENTS:-.} --max-line-length=120 --ignore=E501,W503
```
