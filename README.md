# Washington State Tax Refund Engine

An AI-powered system for identifying and analyzing potential sales/use tax refunds for Washington State businesses. The system ingests legal documents (RCW, WAC, WTD, ETA) and client invoices, uses vector search to find relevant exemptions, and generates professional Excel reports.

## 🎯 Key Features

- **AI-Powered Document Classification**: Automatically detects and classifies legal documents and client invoices
- **Vector Search Technology**: Searches across ALL uploaded legal documents using semantic similarity
- **Comprehensive Tax Law Coverage**: Analyzes HUNDREDS of Washington State tax exemptions, not just specific examples
- **Automated Product Identification**: Determines product type, digital vs physical, service vs product, and "primarily human effort" classification
- **Professional Excel Reports**: Generates client-facing reports, DOR filing worksheets, and internal analysis workbooks
- **Intelligent Processing Pipeline**: End-to-end automation from document ingestion to final reports

## 🧠 Comprehensive Tax Law Coverage

### CRITICAL UNDERSTANDING

This system is designed to analyze **ALL Washington State tax laws and exemptions**, not just specific examples.

The "primarily human effort" test (for digital services under ESSB 5814) is **ONE** example among **HUNDREDS** of Washington State tax rules.

### System Intelligence Approach

1. **Ingests ALL legal documents** uploaded into a searchable vector database
2. **For EACH invoice line item**, searches across ALL legal documents using semantic similarity
3. **Retrieves the 10 most relevant** legal sections based on product description and context
4. **Analyzes the transaction** against ALL retrieved legal authorities
5. **Applies whichever exemptions** are most relevant to that specific product/service
6. **Different products automatically trigger different exemptions** based on vector search results

### Example Analysis Scenarios

#### Scenario 1: Industrial Manufacturing Equipment
- **Line item**: "CNC milling machine for metal fabrication"
- **System searches** ALL legal documents
- **Top results**: RCW 82.08.02565 (manufacturing equipment exemption), WAC 458-20-13601
- **AI analyzes**: Is equipment used directly in manufacturing operations? Yes.
- **Result**: Eligible for refund under manufacturing exemption
- **Citation**: RCW 82.08.02565
- **Note**: "Primarily human effort" is NOT relevant here - different exemption applies

#### Scenario 2: Automated Software Subscription
- **Line item**: "Salesforce CRM annual subscription"
- **System searches** ALL legal documents
- **Top results**: ESSB 5814, RCW 82.04.050 (digital service taxation), WTD decisions on SaaS
- **AI analyzes**: Is this primarily human effort? No, it's automated software platform.
- **Result**: Properly taxed under ESSB 5814, no refund
- **Citation**: RCW 82.04.050
- **Note**: "Primarily human effort" IS relevant here - this is the right test for this product

#### Scenario 3: Agricultural Equipment
- **Line item**: "John Deere tractor for wheat farming operations"
- **System searches** ALL legal documents
- **Top results**: RCW 82.08.0259 (agricultural exemption), WAC 458-20-101
- **AI analyzes**: Used in farming? Yes. Qualifying agricultural equipment? Yes.
- **Result**: Eligible for refund under agricultural exemption
- **Citation**: RCW 82.08.0259

#### Scenario 4: Professional Consulting Services
- **Line item**: "Strategic management consulting - 40 hours at $250/hr"
- **System searches** ALL legal documents
- **Top results**: RCW 82.04.050 (service taxation), ESSB 5814, ETA on professional services
- **AI analyzes**: Is this primarily human effort? Yes, consulting requires human expertise and judgment.
- **Result**: Should not have been taxed, eligible for refund
- **Citation**: RCW 82.04.050 primarily human effort exemption

### Exemption Categories Covered

The system analyzes ALL exemptions found in uploaded documents, including but not limited to:

- **Manufacturing exemptions** (RCW 82.08.02565, 82.08.02566, etc.)
- **Resale exemptions** (RCW 82.08.0251, 82.08.0252, etc.)
- **Interstate/foreign commerce** (RCW 82.08.0264, 82.08.0265, etc.)
- **Agricultural exemptions** (RCW 82.08.0259, 82.08.02745, etc.)
- **Digital products and services** (ESSB 5814, RCW 82.04.050, etc.)
- **Service taxability rules** (including "primarily human effort" test)
- **Construction exemptions** (RCW 82.08.02785, etc.)
- **Nonprofit exemptions** (RCW 82.08.02573, etc.)
- **Government exemptions** (RCW 82.08.0259, etc.)
- **Research & development** (RCW 82.63.045, etc.)
- **Food products** (RCW 82.08.0293, etc.)
- **Prescription drugs** (RCW 82.08.0281, etc.)
- **Energy** (RCW 82.08.956, etc.)
- **Transportation** (RCW 82.08.0266, etc.)
- **And HUNDREDS of other specific exemptions**

### Key Principles

1. **Vector Search Drives Analysis**:
   - Product description → semantic embedding → search across ALL legal docs
   - Top 10 most similar legal sections are retrieved
   - Analysis is based on THESE retrieved documents, not hardcoded rules
   - Different products naturally retrieve different relevant laws

2. **Comprehensive Coverage**:
   - Do NOT only look for "primarily human effort" cases
   - Do NOT only apply the 5 sample legal_rules seeded in database
   - DO search across ALL uploaded legal documents for EVERY line item
   - DO apply ANY relevant exemption found in the knowledge base

3. **Adaptive Analysis**:
   - Manufacturing equipment → manufacturing exemption analysis
   - Resale items → reseller permit analysis
   - Services → primarily human effort test
   - Agricultural products → agricultural exemption analysis
   - The AI adapts its analysis based on what legal documents are retrieved

## 📁 Document Organization

### LEGAL DOCUMENTS (knowledge_base/)

Folder names provide **HINTS**, AI verifies content.

**How to organize**:
1. RCW documents → `knowledge_base/statutes/rcw/`
2. WAC documents → `knowledge_base/statutes/wac/`
3. WTD documents → `knowledge_base/guidance/wtd/`
4. ETA documents → `knowledge_base/guidance/eta/`

**The AI will**:
- Use folder name as hint
- Read content to confirm type
- Extract citation automatically
- Extract metadata (dates, topics, concepts)
- Create searchable vector database

### CLIENT DOCUMENTS (client_documents/)

**Two approaches** - choose what's easier:

**OPTION A (Recommended): Single Upload Folder**
- Put ALL documents in: `client_documents/uploads/`
- AI detects type automatically (invoice/PO/SOW/contract)
- AI moves to organized folders after processing

**OPTION B: Pre-Organize**
- Manually sort into `invoices/`, `purchase_orders/`, etc.
- AI still verifies classification

### File Format Support

✅ **PDF, Excel, Word, PNG, TIFF, JPG** - all handled automatically

### Metadata Auto-Extraction

**For Legal Documents**: citation, dates, topics, key concepts, referenced statutes
**For Invoices**: vendor info, line items, tax amounts, locations
**For SOWs**: service description, primarily_human_effort determination

## 🚀 Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

1. **Navigate to project directory**:
   ```bash
   cd refund-engine
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

5. **Initialize database**:
   ```bash
   python scripts/db_setup.py
   ```

## 📖 Usage

### Quick Start: Full Pipeline

Process everything in one command:

```bash
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/
```

This will:
1. Ingest and classify all client documents
2. Identify all products/services
3. Analyze refund eligibility using vector search
4. Generate all three Excel reports

### Step-by-Step Workflow

#### 1. Ingest Legal Documents

Place your legal documents in the appropriate folders:

```bash
knowledge_base/statutes/rcw/       # RCW files
knowledge_base/statutes/wac/       # WAC files
knowledge_base/guidance/wtd/       # WTD files
knowledge_base/guidance/eta/       # ETA files
```

Then run:

```bash
python scripts/ingest_legal_docs.py --folder knowledge_base/
```

#### 2. Process Client Documents

Place all client documents in:

```bash
client_documents/uploads/
```

Then run:

```bash
python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1
```

#### 3. Identify Products

For a single invoice:

```bash
python scripts/identify_product.py --invoice_id 1
```

For a specific line item:

```bash
python scripts/identify_product.py --line_item_id 1
```

#### 4. Analyze Refunds

For a single invoice:

```bash
python scripts/analyze_refund.py --invoice_id 1
```

For a specific line item:

```bash
python scripts/analyze_refund.py --line_item_id 1
```

#### 5. Generate Reports

**Client-facing report**:
```bash
python scripts/generate_client_report.py --client_id 1
```

**DOR filing worksheet**:
```bash
python scripts/generate_dor_filing.py --client_id 1
```

**Internal analysis workbook**:
```bash
python scripts/generate_internal_workbook.py --client_id 1
```

### Individual Utilities

**Classify a document**:
```bash
python scripts/document_classifier.py --file path/to/document.pdf
```

**Extract metadata**:
```bash
python scripts/metadata_extractor.py --file path/to/invoice.pdf --type invoice
```

## 📊 Outputs

All generated reports are saved to the `outputs/` directory:

- `outputs/reports/` - Client-facing Excel reports (4 sheets)
- `outputs/dor_filings/` - DOR submission worksheets (2 sheets)
- `outputs/analysis/` - Internal analysis workbooks (6 sheets)

## 🔍 How It Works

### Vector Search Technology

The system uses **sentence-transformers** to create semantic embeddings of all legal documents. When analyzing an invoice line item:

1. Creates a search query from: product category + description + tax context
2. Searches the vector database for the 10 most semantically similar legal document chunks
3. Passes these retrieved documents to Claude for analysis
4. Claude evaluates which exemptions apply based on the retrieved legal authorities

This means the system **automatically finds relevant laws** without hardcoding every possible exemption.

### "Primarily Human Effort" Test

Under Washington State law (ESSB 5814 / RCW 82.04.050), services that are "primarily human effort" are NOT subject to sales tax, even if delivered digitally.

**Primarily Human Effort = TRUE** if:
- Custom services requiring human expertise, judgment, or creativity
- Consulting, professional services, manual labor
- Human-driven analysis, design, or problem-solving

**Primarily Human Effort = FALSE** if:
- Automated software platforms or SaaS subscriptions
- Pre-built digital products or tools
- Standardized automated services

The system automatically determines this classification for all service line items.

## 🗄️ Database Schema

The system uses SQLite with the following main tables:

- **clients** - Client information
- **legal_documents** - All legal documents with metadata
- **document_chunks** - Text chunks for vector search
- **invoices** - Invoice headers
- **invoice_line_items** - Individual line items
- **product_identifications** - AI product classifications
- **refund_analysis** - Refund eligibility determinations
- **legal_rules** - Sample exemption rules

## ⚙️ Configuration

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_key_here
DATABASE_URL=sqlite:///database/refund_engine.db
```

### Model Configuration

The system uses:
- **Claude Sonnet 4.5** (`claude-sonnet-4-20250514`) for all AI analysis
- **sentence-transformers/all-MiniLM-L6-v2** for vector embeddings

## 🚨 Troubleshooting

### API Key Error
- Check that `.env` file exists and contains valid Anthropic API key

### File Not Processing
- Verify file format is supported (PDF, DOCX, XLSX, PNG, JPG, TIFF)
- Check file is not corrupted

### Low Confidence Scores
- System may need more legal documents in knowledge base
- Product description may be ambiguous
- Consider manual review for confidence < 60%

### No Vector Search Results
- Ensure legal documents have been ingested: `python scripts/ingest_legal_docs.py --folder knowledge_base/`
- Check ChromaDB collection exists in `vector_db/chroma/`

## 📝 Logs

Detailed logs are saved to `logs/` directory:

- `ingestion_YYYYMMDD_HHMMSS.log` - Legal document ingestion
- `client_ingestion_YYYYMMDD_HHMMSS.log` - Client document processing

## 🤝 Contributing

This is a production system for KOM Consulting. Code quality, accuracy, and legal analysis precision are critical.

## 📄 License

Proprietary - KOM Consulting

## ⚖️ Legal Disclaimer

This system provides automated analysis for informational purposes only. All refund claims should be reviewed by qualified tax professionals before submission to the Washington State Department of Revenue.

---

**Built with**:
- Anthropic Claude Sonnet 4.5
- ChromaDB Vector Database
- Python 3.10+
- OpenPyXL for Excel generation
- Sentence Transformers for embeddings

**For support**: Contact KOM Consulting
