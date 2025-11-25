Verify knowledge base chunks are properly formatted and complete.

Arguments: $ARGUMENTS (optional)
- --limit N (verify only first N chunks)
- --fix (attempt automatic repairs)

Examples:
- /verify-chunks
- /verify-chunks --limit 100
- /verify-chunks --fix

```bash
python scripts/utils/verify_chunks.py $ARGUMENTS
```
