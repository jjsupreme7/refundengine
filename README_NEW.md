# Washington Tax Refund Engine

AI-powered system for analyzing invoices against Washington State tax law to identify refund opportunities.

## ✅ What's Been Set Up

### 1. **Clean Project Structure**
```
refund-engine/
├── database/
│   └── supabase_schema.sql          (Complete schema with pgvector)
├── scripts/
│   ├── 1_setup_supabase.py          (Database setup)
│   └── 2_ingest_legal_docs.py       (AI-powered doc ingestion)
├── client_documents/
│   └── invoices/                    (Put your invoice PDFs here)
├── knowledge_base/
│   └── wa_tax_law/                  (Put WA tax law PDFs here)
├── outputs/
│   └── analyzed_sheets/             (Output Excel files go here)
├── .env                             (API keys configured)
└── requirements.txt                 (Dependencies updated)
```

### 2. **Supabase Database**
- ✅ Complete schema with 14 tables
- ✅ pgvector extension for RAG search
- ✅ Rich metadata fields for filtering
- ✅ Helper functions for semantic search
- ✅ Optimized indexes

### 3. **High-Level Document Ingestion**
- ✅ GPT-4 powered metadata extraction
- ✅ Interactive review & confirmation
- ✅ OpenAI embeddings (ada-002)
- ✅ Automatic chunking & storage

### 4. **Excel Integration** (Documented)
- ✅ Complete workflow explained in `EXCEL_INTEGRATION_EXPLAINED.md`
- ✅ Handles multiple line items per invoice
- ✅ Matches documents by filename
- ✅ Fills analysis columns automatically

---

## 🚀 Getting Started

### Step 1: Install Dependencies

```bash
cd ~/Desktop/refund-engine
pip install -r requirements.txt
```

### Step 2: Setup Database

**Option A: Manual (Recommended)**
1. Go to https://supabase.com/dashboard/project/yzycrptfkxszeutvhuhm/sql
2. Open `database/supabase_schema.sql`
3. Copy entire SQL
4. Paste into Supabase SQL Editor
5. Click "Run"

**Option B: Automatic**
```bash
python scripts/1_setup_supabase.py --auto
```

### Step 3: Ingest Legal Documents (20-30 PDFs)

```bash
python scripts/2_ingest_legal_docs.py \
  --folder ~/Desktop/"WA Tax Law" \
  --limit 10
```

This will:
- Extract text from PDFs
- Use GPT-4 to suggest metadata
- Show you suggestions for review
- Generate embeddings
- Store in Supabase

**Cost**: ~$0.01 per 10 documents

---

## 📊 Excel Workflow

### Your Excel Structure

**Input Columns (You Fill)**:
- Vendor Name
- Invoice #
- PO #
- Date
- Inv 1, Inv 2
- File Path ← **Matches invoice filename**
- PO File Name

**Output Columns (AI Fills)**:
- Product Description
- Background
- Type
- Additional Info
- Refund Basis
- Citation
- Location
- Explanation

### How It Works

1. **Prepare Excel**: Fill input columns with invoice info
2. **Add PDFs**: Place invoices in `client_documents/invoices/`
3. **Run Analysis**: `python scripts/3_analyze_from_excel.py --excel "Test Refund Sheet.xlsx"`
4. **Review Output**: Get analyzed Excel with all columns filled

**Key Feature**: Multiple rows with same filename = Multiple line items from one invoice ✓

**See `EXCEL_INTEGRATION_EXPLAINED.md` for complete details**

---

## 🏗️ Architecture

### Technology Stack

- **Database**: Supabase (PostgreSQL + pgvector)
- **AI Models**:
  - GPT-4o (document analysis, invoice extraction)
  - OpenAI ada-002 (embeddings)
  - Anthropic Claude (optional analysis)
- **RAG**: Semantic search via pgvector
- **PDF Processing**: pdfplumber, PyPDF2
- **Excel**: pandas, openpyxl

### Data Flow

```
Excel Sheet → Match Documents → Extract Data → RAG Search → AI Analysis → Fill Excel
     ↓              ↓                ↓              ↓             ↓            ↓
  (Input)    (Find PDFs)    (OCR/Vision)   (Legal DB)   (Determine)   (Output)
```

### Database Tables

**Legal Knowledge**:
- `legal_documents` - Document metadata
- `document_chunks` - Text chunks with embeddings
- `document_metadata` - Rich tagging

**Invoice Data**:
- `invoices` - Invoice headers
- `invoice_line_items` - Line item details
- `refund_analysis` - Analysis results

---

## 🔍 RAG Search Explained

### How It Works

1. **Question**: "Is cloud hosting taxable in WA?"
2. **Convert to embedding**: `[0.023, -0.891, 0.445, ...]` (1536 numbers)
3. **Search database**: Find document chunks with similar embeddings
4. **Get results**: Top 5 most relevant legal sections
5. **AI analyzes**: Based on retrieved context
6. **Generate answer**: With citations

### Filtering

Search with filters:
```python
# Only search WACs from 2015-2020 about digital services
results = search_with_filters(
    query_embedding=embedding,
    source_types=["WAC"],
    year_from=2015,
    year_to=2020,
    topic_tags_filter=["digital services"]
)
```

---

## 💡 Key Concepts

### 1. **Metadata-Driven Filtering**

Every legal document has rich metadata:
- `source_type`: RCW, WAC, Determination, etc.
- `year_issued`: For date range filtering
- `topic_tags`: ["digital products", "exemptions"]
- `tax_types`: ["sales tax", "use tax"]
- `industries`: ["technology", "SaaS"]

**Use case**: "Show me only RCWs from 2013-2017 about digital products"

### 2. **Multiple Line Items per Invoice**

Your Excel has multiple rows for same invoice:
```
Row 1: Invoice-001.pdf | Line item 1
Row 2: Invoice-001.pdf | Line item 2
Row 3: Invoice-001.pdf | Line item 3
```

System:
- Processes PDF once
- Extracts all 3 line items
- Matches each to correct Excel row
- Analyzes each independently

### 3. **Confidence Scoring**

Every analysis includes confidence:
- **90-100%**: Very strong case
- **80-89%**: Strong case, likely eligible
- **70-79%**: Good case, minor gaps
- **60-69%**: Moderate case, needs review
- **<60%**: Weak case, requires investigation

---

## 📈 Next Steps

### Immediate (Today)

1. ✅ Review cleaned folder structure
2. ✅ Run database setup
3. ✅ Test with 10 legal documents
4. ✅ Read `EXCEL_INTEGRATION_EXPLAINED.md`

### Soon (This Week)

1. ⏳ Ingest 20-30 curated legal documents
2. ⏳ Build script #3: `analyze_from_excel.py`
3. ⏳ Test with sample Excel sheet
4. ⏳ Review results

### Later (Optional)

1. ⏳ Build chatbot interface (Streamlit)
2. ⏳ Add pattern learning
3. ⏳ Expand to 100+ legal documents
4. ⏳ Create reporting dashboard

---

## 🔐 Security Notes

- ✅ API keys in `.env` (not committed to git)
- ✅ `.gitignore` configured
- ✅ Service role key for server-side only
- ✅ No credentials in code

---

## 💰 Cost Estimates

### One-Time Setup
- Legal doc ingestion (30 docs): ~$0.30
- Database setup: Free

### Per Invoice Analysis
- OCR/extraction: ~$0.01 per invoice
- Embedding search: ~$0.001 per query
- Analysis: ~$0.01 per line item

**Example**: 100 invoices with 250 line items = ~$3.50

---

## 📞 Support

**Documentation**:
- `EXCEL_INTEGRATION_EXPLAINED.md` - Complete Excel workflow
- `database/supabase_schema.sql` - Database schema reference

**Environment**:
- `.env` - API keys and configuration

**Next Script to Build**: `3_analyze_from_excel.py`

---

## ✨ What Makes This Different

1. **AI-First**: GPT-4 Vision reads invoices like a human
2. **RAG-Powered**: Searches ALL legal documents, not just hardcoded rules
3. **Metadata Rich**: Filter by date, type, topic, industry
4. **Excel Native**: Works with your existing workflow
5. **Transparent**: See exactly which laws apply and why
6. **Scalable**: 10 invoices or 10,000 invoices

---

**Built with**: OpenAI GPT-4, Supabase, pgvector, Python
