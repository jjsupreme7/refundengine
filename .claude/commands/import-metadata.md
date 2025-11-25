Import edited Excel metadata back to Supabase database.

Arguments: $ARGUMENTS
- Required: Excel file path
- Optional: --yes (auto-confirm), --force (ignore Status column)

Examples:
- /import-metadata outputs/Tax_Metadata.xlsx
- /import-metadata outputs/Vendor_Metadata.xlsx --yes --force

```bash
python core/ingest_documents.py --import-metadata $ARGUMENTS
```
