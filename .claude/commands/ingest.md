---
description: Ingest documents into knowledge base
---

Ingest documents into the RAG knowledge base:

1. **Determine document type:**
   - If `$ARGUMENTS` contains "tax" or "legal": `--type tax_law`
   - If `$ARGUMENTS` contains "vendor": `--type vendor`
   - Otherwise, ask user which type

2. **Determine folder:**
   - Tax law default: `knowledge_base/states/washington/legal_documents`
   - Vendor default: `knowledge_base/vendors`
   - Or use path from `$ARGUMENTS`

3. **Run ingestion:**
   ```bash
   python core/ingest_documents.py --type <type> --folder <folder>
   ```

4. **Report results:**
   - Number of documents processed
   - Number of chunks created
   - Any errors encountered

5. **Verify ingestion:**
   - Run a quick test query to confirm documents are searchable
