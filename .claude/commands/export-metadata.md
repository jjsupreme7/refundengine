Export knowledge base metadata to Excel for review and editing.

Arguments: $ARGUMENTS
- --type <tax_law|vendor> (required)
- --export-metadata <output_path> (required)
- --folder <source_folder> (optional)

Examples:
- /export-metadata --type tax_law --export-metadata outputs/Tax_Metadata.xlsx
- /export-metadata --type vendor --export-metadata outputs/Vendor_Metadata.xlsx

```bash
python core/ingest_documents.py $ARGUMENTS
```
