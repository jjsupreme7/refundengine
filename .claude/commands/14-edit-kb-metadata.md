# Open Knowledge Base Metadata for Editing

Opens an exported metadata Excel file in your default spreadsheet application (Excel/Numbers). This is the middle step in the metadata editing workflow.

## The Workflow

```
Step 1: /15-export-metadata outputs/kb.xlsx    # Pull data from Supabase
        |
        v
Step 2: /14-edit-kb-metadata outputs/kb.xlsx   # Open in Excel, make changes
        |
        v
Step 3: [You edit in Excel and save]
        |
        v
Step 4: /16-import-metadata outputs/kb.xlsx    # Push changes back to Supabase
```

## Why Edit Metadata?

The knowledge base stores documents with metadata like:
- Document title and type
- WAC/RCW citation
- Effective date
- Summary/description
- Tags and categories

Sometimes you need to:
- Fix incorrect citations
- Add missing effective dates
- Correct document titles
- Bulk update categories

Editing in Excel is faster than updating one record at a time.

## Arguments

$ARGUMENTS (optional)
- File path to open
- Default: `outputs/metadata.xlsx`

## Examples

```bash
/14-edit-kb-metadata                           # Opens default file
/14-edit-kb-metadata outputs/Tax_Metadata.xlsx # Opens specific file
```

## Success Looks Like

Your default spreadsheet app opens with the file.

## Tips for Editing

1. **Don't change the ID column** - This links rows to database records
2. **Use consistent values** - Check existing values before adding new ones
3. **Save as .xlsx** - Keep the Excel format (not .csv)
4. **Close file before import** - Excel locks files when open

## Common Issues

- "File not found" → Run `/15-export-metadata` first
- File won't open → Check you have Excel/Numbers installed
- Changes not taking effect → Make sure you saved and ran `/16-import-metadata`

```bash
open "${ARGUMENTS:-outputs/metadata.xlsx}"
```
