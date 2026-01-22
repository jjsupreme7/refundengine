---
name: knowledge-base-docs
enabled: true
event: file
action: warn
pattern: knowledge_base/.*\.(pdf|docx|txt)$
---

**Knowledge Base Document Warning**

You're about to modify a tax law reference document.

**These files are used for:**
- RAG (Retrieval-Augmented Generation) searches
- Legal reasoning and citation
- Tax law reference lookups

**Before modifying:**
1. Verify this is intentional (not accidental)
2. Consider if a new document should be added instead
3. Remember that chunks may need to be regenerated after changes

**After modifying:**
- Run `/verify-chunks` to ensure RAG is updated
- Consider running `/import-metadata` if document metadata changed

