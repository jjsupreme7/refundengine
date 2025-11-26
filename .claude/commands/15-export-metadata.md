# Export Knowledge Base Metadata

Pulls document metadata from Supabase into an Excel file for review or editing. First step in the metadata editing workflow.

## What Gets Exported

Depending on `--type`:

**Tax Law (`--type tax_law`):**
- Document ID, title, citation (WAC/RCW)
- Document type (statute, rule, decision)
- Effective date, file URL
- Chunk count, embedding status

**Vendor (`--type vendor`):**
- Vendor name, industry
- Products/services
- Tax classification
- Research status

## How It Fits In The System

```
[Supabase Database]
        |
        v (SELECT * FROM documents/vendors)
    /15-export-metadata
        |
        v
[Excel file with all metadata]
        |
        v
    /14-edit-kb-metadata (optional editing)
        |
        v
    /16-import-metadata (push changes back)
```

## Arguments

$ARGUMENTS (required)
- `--type <tax_law|vendor>` - What to export
- `--export-metadata <path>` - Output file path

## Examples

```bash
/15-export-metadata --type tax_law --export-metadata outputs/Tax_Metadata.xlsx
/15-export-metadata --type vendor --export-metadata outputs/Vendor_Metadata.xlsx
```

## Success Looks Like

```
Exporting tax_law documents...
Found 847 documents
Writing to outputs/Tax_Metadata.xlsx...
Export complete. 847 rows written.
```

## What The Excel Contains

| Column | Description |
|--------|-------------|
| id | Database ID (don't modify) |
| title | Document title |
| citation | WAC/RCW number |
| doc_type | statute, rule, determination, etc. |
| effective_date | When law took effect |
| file_url | Link to source document |
| chunk_count | Number of text chunks |
| status | Processing status |

## When To Use

- Auditing what's in the knowledge base
- Bulk editing metadata
- Creating reports on document coverage
- Identifying gaps in tax law coverage

```bash
python core/ingest_documents.py $ARGUMENTS
```
