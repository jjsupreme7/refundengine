---
name: client-documents
enabled: true
event: file
action: block
pattern: client_documents/.*
---

**Client Documents Protection**

This folder contains original invoice PDFs from clients. These are source documents that should not be modified.

**Why this is blocked:**
- Invoice PDFs are legal records
- Modifications could affect audit trails
- Original files should remain untouched for reference

**What you should do instead:**
- Read files for analysis (allowed)
- Create copies in a working directory if needed
- Use the analysis pipeline to process invoices

