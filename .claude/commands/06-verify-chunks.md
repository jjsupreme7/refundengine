# Verify Knowledge Base Integrity

Checks that your Supabase knowledge base is healthy - documents are properly chunked, embeddings exist, and data is consistent. Run this when RAG responses seem wrong or after ingesting new documents.

## What It Checks

1. **Document counts** - How many tax law docs, vendor docs, etc.
2. **Chunk counts** - Each document should have multiple chunks
3. **Embedding coverage** - Every chunk should have a vector embedding
4. **Orphan detection** - Chunks without parent documents (bad)
5. **Format validation** - Chunk metadata is properly structured

## How It Fits In The System

The knowledge base powers the RAG (Retrieval Augmented Generation) system:

```
User Question: "Is software taxable in Washington?"
         |
         v
    [RAG Search] --> tax_law_chunks table
         |              |
         |              +--> /06-verify-chunks checks this is healthy
         v
    [Relevant chunks returned]
         |
         v
    [AI generates answer with citations]
```

If chunks are missing or corrupted, RAG gives bad answers.

## Arguments

$ARGUMENTS (optional)
- No args → Standard verification (recommended)
- `--quick` → Fast summary only (counts, no deep checks)
- `--full` → Exhaustive check (slow but thorough)

## Examples

```bash
/06-verify-chunks              # Standard check
/06-verify-chunks --quick      # Just counts
/06-verify-chunks --full       # Deep inspection
```

## Success Looks Like

```
=== Knowledge Base Verification ===

Documents:
  - Tax Law: 847 documents
  - Vendor: 465 documents
  - Total: 1,312 documents

Chunks:
  - Total chunks: 24,891
  - With embeddings: 24,891 (100%)
  - Orphaned: 0

Format Check: PASSED
Embedding Check: PASSED

Knowledge base is healthy.
```

## Red Flags

- `With embeddings: 20,000 (80%)` → Missing embeddings. Re-run ingestion.
- `Orphaned: 150` → Chunks without documents. Run cleanup.
- `Format Check: FAILED` → Corrupted metadata. May need re-ingestion.

## When To Run

- After `/04-analyze` gives weird results
- After ingesting new documents
- After database migrations
- Weekly health check

```bash
python scripts/utils/verify_chunks.py $ARGUMENTS
```
