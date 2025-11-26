# Check Database Schema

Inspects Supabase database tables to verify schema is correct. Use this after migrations, when queries fail, or to understand what tables exist.

## What It Shows

For each table in the database:
- Table name
- Row count
- Column names and types
- Sample data (first few rows)

## How It Fits In The System

```
"Query failed: column 'vendor_id' does not exist"
        |
        v
    /20-check-schema
        |
        v
Shows actual columns:
  vendors table:
    - id (uuid)
    - name (text)        <-- No 'vendor_id' column!
    - industry (text)
        |
        v
Now you know to use 'id' not 'vendor_id'
```

## Key Tables

| Table | Purpose |
|-------|---------|
| documents | Tax law documents (WAC, RCW, decisions) |
| document_chunks | Text chunks with embeddings for RAG |
| vendor_products | Vendor information and tax classification |
| analysis_results | Saved analysis outputs |
| projects | User projects/batches |
| excel_versions | Excel file version tracking |

## Arguments

None

## Example

```bash
/20-check-schema
```

## Success Looks Like

```
=== Supabase Schema Inspection ===

Connected to: https://xxxxx.supabase.co

Tables found: 12

Table: documents
  Rows: 847
  Columns:
    - id (uuid, primary key)
    - title (text)
    - doc_type (text)
    - citation (text)
    - effective_date (date)
    - file_url (text)
    - created_at (timestamp)

Table: document_chunks
  Rows: 24,891
  Columns:
    - id (uuid, primary key)
    - document_id (uuid, foreign key → documents)
    - content (text)
    - embedding (vector)
    - chunk_index (integer)

Table: vendor_products
  Rows: 465
  Columns:
    - id (uuid)
    - vendor_name (text)
    - industry (text)
    - products (text)
    - tax_classification (text)
    - researched (boolean)

[... more tables ...]
```

## When To Use

- After running database migrations
- When queries fail with column errors
- To understand database structure
- Debugging data issues
- Verifying migration applied correctly

## Related Commands

- `/06-verify-chunks` - Deeper check on document chunks specifically
- `/09-verify-setup` - Checks database connection is working

```bash
python scripts/utils/check_supabase_tables.py
```
