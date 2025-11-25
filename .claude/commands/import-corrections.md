---
description: Import human corrections to learn from
---

Import human corrections from reviewed Excel files:

1. **Identify the Excel file:**
   - If `$ARGUMENTS` provided, use that file path
   - Otherwise, ask user which reviewed Excel file to import

2. **Ask for reviewer email:**
   - This is required for tracking who made corrections

3. **Run the import:**
   ```bash
   python analysis/import_corrections.py "<excel_file>" --reviewer "<email>"
   ```

4. **Report results:**
   - Number of corrections imported
   - Patterns learned from corrections
   - Any errors encountered

5. **Explain what happens next:**
   - System learns from approved/rejected decisions
   - Future analyses will benefit from these patterns
