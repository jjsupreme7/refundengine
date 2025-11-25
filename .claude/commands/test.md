---
description: Run tests with coverage
---

Run the project test suite:

1. **Run pytest with coverage:**
   ```bash
   pytest tests/ --cov=core --cov=scripts --cov=analysis --cov-report=term-missing -v
   ```

2. **Report results:**
   - Show any failing tests with details
   - Report overall coverage percentage
   - Highlight any modules below 70% coverage

3. **If tests fail:**
   - Analyze the failure messages
   - Suggest fixes if the cause is clear
   - Ask before making changes

Optional arguments:
- `$ARGUMENTS` can be used to pass additional pytest flags (e.g., `-m unit` for unit tests only, `-k test_name` for specific tests)
