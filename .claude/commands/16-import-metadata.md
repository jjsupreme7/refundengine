# Import Metadata from Excel

Pushes edited metadata from an Excel file back to Supabase. Final step in the metadata editing workflow.

## What It Does

1. Reads Excel file with metadata
2. Matches rows to database records by ID
3. Updates changed fields in Supabase
4. Reports what was updated

## How It Fits In The System

```
[Excel file with your edits]
        |
        v
    /16-import-metadata
        |
        +--> Compare with database
        |
        +--> Update changed records
        |
        v
[Supabase database updated]
        |
        v
[RAG system uses new metadata]
```

## Arguments

$ARGUMENTS (required)
- Excel file path (required)
- `--yes` - Skip confirmation prompt
- `--force` - Ignore Status column, update all rows

## Examples

```bash
/16-import-metadata outputs/Tax_Metadata.xlsx
/16-import-metadata outputs/Vendor_Metadata.xlsx --yes
/16-import-metadata outputs/Tax_Metadata.xlsx --yes --force
```

## Success Looks Like

```
Loading outputs/Tax_Metadata.xlsx...
Found 847 rows

Changes detected:
  - Row 23: title "WAC 458-20-102" → "WAC 458-20-102 - Reseller Permits"
  - Row 156: effective_date NULL → "2020-01-01"
  - Row 298: doc_type "rule" → "determination"

3 records will be updated. Proceed? [y/N]
> y

Updating records...
✓ Updated 3 records
Import complete.
```

## Safety Features

- **Preview before update** - Shows what will change
- **ID matching** - Only updates existing records (won't create new ones)
- **Confirmation prompt** - Asks before making changes (use --yes to skip)

## Common Issues

- "ID not found" → That document was deleted from database
- "File locked" → Close Excel before importing
- "No changes detected" → Your edits might not have been saved

## When To Use

- After editing metadata in `/14-edit-kb-metadata`
- Bulk updates to document properties
- Fixing data quality issues
- Restoring from backup

```bash
python core/ingest_documents.py --import-metadata $ARGUMENTS
```
