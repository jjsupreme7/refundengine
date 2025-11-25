---
description: Run invoice analysis on Excel files
---

Run the invoice analysis pipeline:

1. **Identify the Excel file:**
   - If `$ARGUMENTS` provided, use that file path
   - Otherwise, ask user which Excel file to analyze

2. **Run the fast batch analyzer:**
   ```bash
   python analysis/fast_batch_analyzer.py --excel "<excel_file>" --state washington
   ```

3. **Monitor and report:**
   - Show progress as invoices are processed
   - Report any errors encountered
   - Summarize results when complete:
     - Number of rows analyzed
     - Number skipped (already processed)
     - Number with refund opportunities found

4. **Next steps:**
   - Remind user to review output in Excel
   - Mention `/import-corrections` for importing human corrections
