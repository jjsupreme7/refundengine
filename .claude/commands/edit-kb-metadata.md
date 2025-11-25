Open the knowledge base metadata Excel file for editing.

This is the middle step between /export-metadata and /import-metadata.

Workflow:
1. /export-metadata outputs/kb_metadata.xlsx
2. /edit-kb-metadata (opens the file)
3. Make changes in Excel, save
4. /import-metadata outputs/kb_metadata.xlsx

Arguments: $ARGUMENTS
- Optional: Specific file path (default: outputs/metadata.xlsx)

```bash
open "${ARGUMENTS:-outputs/metadata.xlsx}"
```
