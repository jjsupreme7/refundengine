# Washington State Tax Refund Engine - Complete Workflow

## 📋 STEP-BY-STEP GUIDE

### STEP 1: UPLOAD YOUR DOCUMENTS

#### A. Legal Documents (Knowledge Base)
Put your Washington State legal documents in these folders:

```
knowledge_base/statutes/rcw/     ← RCW documents (PDF, DOCX, TXT)
knowledge_base/statutes/wac/     ← WAC regulations
knowledge_base/guidance/wtd/     ← Written Tax Determinations
knowledge_base/guidance/eta/     ← Excise Tax Advisories
knowledge_base/case_law/         ← Court cases (optional)
```

**Supported formats**: PDF, DOCX, DOC, TXT, XLSX, XLS

#### B. Client Documents
Put ALL client documents in ONE folder:

```
client_documents/uploads/        ← Dump everything here!
```

**What to upload**:
- Invoices (any format)
- Purchase orders
- Statements of work
- Contracts
- Receipts
- Any client billing documents

**The AI will automatically**:
- Detect document type
- Extract all data
- Move to organized folders

---

### STEP 2: FIRST TIME SETUP (Run Once)

Open Terminal and navigate to project:
```bash
cd ~/Desktop/refund-engine
source venv/bin/activate
```

Initialize the database:
```bash
python scripts/db_setup.py
```

**What this does**:
✅ Creates SQLite database
✅ Creates all tables
✅ Seeds 5 sample legal rules
✅ Initializes ChromaDB vector database
✅ Creates test client (client_id=1)

---

### STEP 3: INGEST LEGAL DOCUMENTS

After uploading legal docs to knowledge_base/ folders:

```bash
python scripts/ingest_legal_docs.py --folder knowledge_base/
```

**What this does**:
✅ Scans all folders (rcw/, wac/, wtd/, eta/)
✅ Classifies each document (AI verifies folder hints)
✅ Extracts citations and metadata
✅ Creates text chunks
✅ Generates vector embeddings
✅ Stores in searchable database

**Output**: 
- Legal documents in database
- Vector embeddings in vector_db/chroma/
- Processing log in logs/

**Time**: ~30 seconds per document

---

### STEP 4: PROCESS CLIENT DOCUMENTS

After uploading client docs to client_documents/uploads/:

#### Option A: Full Pipeline (Recommended)

```bash
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/
```

**What this does**:
1. ✅ Classifies all documents (invoice, PO, SOW, etc.)
2. ✅ Extracts all invoice data and line items
3. ✅ Identifies products (digital, service, primarily human effort)
4. ✅ Analyzes refund eligibility using vector search
5. ✅ Generates all 3 Excel reports

**Output**:
- `outputs/reports/` - Client report
- `outputs/dor_filings/` - DOR worksheet
- `outputs/analysis/` - Internal analysis

**Time**: ~2-3 minutes per invoice

#### Option B: Step-by-Step

If you want to run each step individually:

**4a. Ingest client documents**:
```bash
python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1
```

**4b. Identify products**:
```bash
python scripts/identify_product.py --invoice_id 1
```

**4c. Analyze refunds**:
```bash
python scripts/analyze_refund.py --invoice_id 1
```

**4d. Generate reports**:
```bash
python scripts/generate_client_report.py --client_id 1
python scripts/generate_dor_filing.py --client_id 1
python scripts/generate_internal_workbook.py --client_id 1
```

---

### STEP 5: REVIEW OUTPUTS

Check the generated reports:

```bash
# Client report
open outputs/reports/

# DOR filing
open outputs/dor_filings/

# Internal analysis
open outputs/analysis/
```

---

## 🔄 PROCESSING ADDITIONAL CLIENTS

For each new client:

1. **Create client in database** (optional - or modify scripts):
   ```sql
   INSERT INTO clients (client_name, business_entity_type, ubi_number, contact_email, industry_classification)
   VALUES ('New Client LLC', 'LLC', '987-654-321', 'client@example.com', 'Manufacturing');
   ```

2. **Get new client_id**:
   ```bash
   # Check database for client_id
   ```

3. **Upload their documents** to `client_documents/uploads/`

4. **Run pipeline**:
   ```bash
   python scripts/process_pipeline.py --client_id 2 --invoices client_documents/uploads/
   ```

---

## 📊 UNDERSTANDING THE ANALYSIS

### Vector Search Approach

The system does NOT use hardcoded rules. Instead:

1. **For each invoice line item**:
   - Creates search query: "product_category description Washington sales tax exemption"
   
2. **Searches ALL legal documents**:
   - Uses semantic similarity
   - Retrieves top 10 most relevant legal sections
   
3. **AI analyzes** against retrieved documents:
   - Manufacturing equipment → finds manufacturing exemptions
   - Consulting services → finds "primarily human effort" test
   - Resale items → finds reseller permit exemptions
   - Agricultural products → finds farm exemptions

4. **Different products get different laws automatically**!

### Confidence Scores

- **90-100%**: Very confident, ready for filing
- **70-89%**: Confident, minimal review needed
- **50-69%**: Review recommended
- **<50%**: Manual review required (flagged automatically)

---

## 🔧 TROUBLESHOOTING

### "No legal documents found"
- Check you ran: `python scripts/ingest_legal_docs.py --folder knowledge_base/`
- Verify legal docs are in correct folders (rcw/, wac/, etc.)

### "No invoices found"
- Check you placed files in `client_documents/uploads/`
- Verify file formats are supported (PDF, XLSX, DOCX)

### Low confidence scores
- Add more legal documents to knowledge base
- Check product descriptions are clear
- Review flagged items manually

### Import errors in IDE
- Make sure IDE is using: `./venv/bin/python`
- In VS Code: Cmd+Shift+P → "Python: Select Interpreter"

---

## 📁 FOLDER SUMMARY

### YOU UPLOAD TO:
✅ `knowledge_base/statutes/rcw/` - RCW documents
✅ `knowledge_base/statutes/wac/` - WAC documents
✅ `knowledge_base/guidance/wtd/` - WTD documents
✅ `knowledge_base/guidance/eta/` - ETA documents
✅ `client_documents/uploads/` - ALL client documents

### SYSTEM MANAGES:
🤖 `client_documents/invoices/` - Auto-organized invoices
🤖 `client_documents/purchase_orders/` - Auto-organized POs
🤖 `client_documents/statements_of_work/` - Auto-organized SOWs
🤖 `outputs/reports/` - Generated client reports
🤖 `outputs/dor_filings/` - Generated DOR worksheets
🤖 `outputs/analysis/` - Generated internal analysis
🤖 `logs/` - Processing logs
🤖 `vector_db/chroma/` - Vector embeddings database

---

## 🎯 QUICK REFERENCE

```bash
# 1. First time setup
python scripts/db_setup.py

# 2. Ingest legal docs (after uploading to knowledge_base/)
python scripts/ingest_legal_docs.py --folder knowledge_base/

# 3. Full pipeline (after uploading to client_documents/uploads/)
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/

# 4. Check outputs
open outputs/reports/
```

That's it! 🚀
