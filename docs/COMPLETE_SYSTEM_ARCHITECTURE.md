# Complete System Architecture
## Washington State Tax Refund Analysis Engine

**Version**: 1.0
**Last Updated**: 2025-11-15
**Author**: Tax Refund Engine Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Components](#architecture-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [File Structure](#file-structure)
9. [Deployment Architecture](#deployment-architecture)
10. [Security & Compliance](#security--compliance)
11. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

The Washington State Tax Refund Analysis Engine is an AI-powered system designed to analyze historical invoices and purchase orders to identify sales tax and use tax refund opportunities. The system applies **OLD LAW** (pre-October 1, 2025) to historical transactions and uses a human-in-the-loop learning approach to continuously improve accuracy.

### Key Features

- **Dual Tax Type Processing**: Separate workflows for Sales Tax vs Use Tax refunds
- **AI-Powered Analysis**: Enhanced RAG (Retrieval Augmented Generation) using GPT-4 with tax law knowledge base
- **Active Learning System**: Captures human corrections and extracts patterns for future improvements
- **Anomaly Detection**: 15 research-backed detectors for identifying hidden refund opportunities
- **90% Confidence Threshold**: Auto-approve high-confidence, flag low-confidence for human review
- **Dashboard Interface**: Professional UI for exception handling and claim building
- **Excel Integration**: Auto-detect file changes and process incrementally

### Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| AI Confidence Accuracy | >85% | TBD (initial deployment) |
| Auto-Approval Rate | >70% | TBD |
| Human Override Rate | 15-25% | TBD |
| Avg Review Time | 3-5 min | TBD |
| Pattern Learning Rate | 50+ patterns in 500 reviews | TBD |

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Excel Upload    │    Dashboard UI    │   Power BI Analytics   │
│  (Master Sheet)  │  (React TypeScript)│   (Reporting Layer)    │
└────────┬─────────┴──────────┬─────────┴────────────┬───────────┘
         │                     │                       │
         ▼                     ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API LAYER (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│ /api/excel/upload    │ /api/analysis/run  │ /api/reviews/submit │
│ /api/documents/ocr   │ /api/patterns/list │ /api/claims/generate│
└────────┬─────────────┴──────────┬──────────┴──────────┬─────────┘
         │                         │                      │
         ▼                         ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Tax Type        │   AI Analysis   │  Pattern      │  Anomaly   │
│  Classifier      │   Engine        │  Learning     │  Detection │
│                  │   (GPT-4 + RAG) │  System       │  Framework │
└────────┬─────────┴──────────┬─────┴───────┬────────┴─────┬──────┘
         │                     │             │              │
         ▼                     ▼             ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  Supabase PostgreSQL   │   Supabase Storage  │  Vector Store   │
│  (Transactions, Reviews│   (PDF Invoices,    │  (Tax Law       │
│   Patterns, Analysis)  │    Purchase Orders) │   Documents)    │
└────────────────────────┴─────────────────────┴─────────────────┘
```

---

## Architecture Components

### 1. Excel Processing Layer

**Purpose**: Ingest master Excel sheets and split by tax type

**Components**:
- `scripts/split_excel_by_tax_type.py`: Classify transactions as Sales Tax vs Use Tax
- `analysis/excel_processors.py`: Parse Excel data and validate structure
- `database/schema/migration_excel_file_tracking.sql`: Track file versions with MD5 hashing

**Process**:
```python
# Step 1: Upload Excel file
upload_excel('Master_Claim_Data.xlsx')

# Step 2: Classify by tax type
classify_tax_type(transactions)
# → Master_Sales_Tax_Claim_Sheet.xlsx
# → Master_Use_Tax_Claim_Sheet.xlsx
# → Needs_Manual_Classification.xlsx

# Step 3: Detect changes (incremental processing)
detect_excel_changes('Master_Sales_Tax_Claim_Sheet.xlsx')
# → Only process new/changed rows
```

**Key Data Structure**:
```python
ExcelRow = {
    # INPUT COLUMNS (User provides)
    'Vendor_ID': str,
    'Vendor_Name': str,
    'Invoice_Number': str,
    'Purchase_Order_Number': str,
    'Total_Amount': float,
    'Tax_Amount': float,
    'Tax_Remitted': float,  # KEY: >0 = sales tax, =0 = use tax
    'Tax_Rate_Charged': str,
    'Invoice_File_Name_1': str,  # Vendor invoice PDF
    'Invoice_File_Name_2': str,  # Internal invoice PDF

    # OUTPUT COLUMNS (AI populates)
    'Analysis_Notes': str,
    'Final_Decision': str,
    'Tax_Category': str,
    'Additional_Info': str,
    'Refund_Basis': str,
    'Estimated_Refund': float,
    'Legal_Citation': str,
    'AI_Confidence': float,  # 0-100

    # METADATA (System adds)
    'Tax_Type': str,  # 'sales_tax' or 'use_tax'
}
```

---

### 2. AI Analysis Engine

**Purpose**: Analyze invoices using GPT-4 with enhanced RAG

**Components**:
- `analysis/analyze_refunds_enhanced.py`: Main analysis logic
- `core/law_version_handler.py`: OLD LAW vs NEW LAW selection
- `core/rag_query_engine.py`: Retrieve relevant tax law chunks
- `analysis/invoice_lookup.py`: PDF OCR and text extraction

**Analysis Pipeline**:
```python
def analyze_invoice_enhanced(
    invoice_file: str,
    vendor_name: str,
    tax_amount: float,
    law_version: str = 'OLD',
    tax_type: str = 'sales_tax'
) -> Dict:
    """
    Full analysis pipeline.
    """
    # Step 1: Extract text from invoice PDF
    invoice_text = extract_pdf_text(invoice_file)

    # Step 2: Retrieve vendor background metadata
    vendor_metadata = get_vendor_metadata(vendor_name)

    # Step 3: RAG query for relevant tax law
    relevant_laws = query_tax_law_rag(
        description=invoice_text,
        law_version=law_version,
        tax_type=tax_type
    )

    # Step 4: Run GPT-4 analysis with context
    base_result = run_gpt4_analysis(
        invoice_text=invoice_text,
        vendor_metadata=vendor_metadata,
        tax_laws=relevant_laws,
        tax_type=tax_type
    )

    # Step 5: Run anomaly detection
    anomalies = detect_anomalies(
        invoice_text=invoice_text,
        tax_amount=tax_amount,
        vendor_metadata=vendor_metadata,
        base_result=base_result
    )

    # Step 6: Apply learned patterns
    adjusted_result = apply_learned_patterns(
        base_result=base_result,
        invoice_text=invoice_text,
        vendor_name=vendor_name
    )

    # Step 7: Calculate final confidence
    final_confidence = calculate_confidence(
        base_confidence=base_result['confidence'],
        anomalies=anomalies,
        pattern_adjustments=adjusted_result['pattern_boosts']
    )

    return {
        'analysis_notes': adjusted_result['rationale'],
        'final_decision': adjusted_result['determination'],
        'tax_category': adjusted_result['category'],
        'additional_info': adjusted_result['additional_info'],
        'refund_basis': adjusted_result['refund_basis'],
        'estimated_refund': calculate_refund(tax_amount, adjusted_result),
        'legal_citation': adjusted_result['citations'],
        'ai_confidence': final_confidence,
        'anomalies_detected': [a['type'] for a in anomalies],
        'patterns_applied': adjusted_result['patterns_applied']
    }
```

**Confidence Calculation**:
```python
def calculate_confidence(
    base_confidence: float,
    anomalies: List[Dict],
    pattern_adjustments: List[Dict]
) -> float:
    """
    Adjust base AI confidence with anomalies and patterns.
    """
    adjusted = base_confidence

    # Anomalies reduce confidence
    for anomaly in anomalies:
        if anomaly['severity'] == 'CRITICAL':
            adjusted -= 30
        elif anomaly['severity'] == 'HIGH':
            adjusted -= 15
        elif anomaly['severity'] == 'MEDIUM':
            adjusted -= 8
        else:  # LOW
            adjusted -= 3

    # Learned patterns boost confidence
    for pattern in pattern_adjustments:
        adjusted += pattern['confidence_boost']

    # Cap at 0-100
    return max(0, min(100, adjusted))
```

---

### 3. Anomaly Detection Framework

**Purpose**: Identify red flags and refund opportunities AI might miss

**Detectors** (15 total - see `docs/ANOMALY_DETECTION_FRAMEWORK.md`):

1. **Odd Dollar Amount Detector**: Identifies hidden tax on exempt services
2. **High Exempt Ratio**: Flags unusually high exempt percentage
3. **Use Tax Pattern**: Detects likely self-assessed use tax
4. **Construction Retainage Tracker**: Finds tax timing errors on progress payments
5. **Missing Documentation**: Alerts when supporting docs are absent
6. **In-State Vendor Credibility**: Boosts confidence for WA vendors
7. **Revenue Fluctuation**: Detects unusual spending patterns
8. **Duplicate Tax**: Finds sales + use tax on same item
9. **Wrong Tax Rate**: Validates rate against location
10. **Bundled Services**: Identifies mixed taxable/exempt
11. **Stair-Stepping Pattern**: Detects potential fraud
12. **Exempt Certificate**: Validates resale/MPU claims
13. **Service Location**: Checks if service performed out-of-state
14. **Professional Services Tax**: Flags taxed professional services
15. **Digital Goods Classification**: Validates pre/post-2009 treatment

**Example Output**:
```python
anomalies = [
    {
        'type': 'odd_dollar_amount',
        'severity': 'HIGH',
        'confidence_impact': -15,
        'reason': 'Amount $5,525 suggests $5,000 base + 10.5% tax on exempt professional services',
        'refund_potential': 525.00
    },
    {
        'type': 'construction_retainage',
        'severity': 'HIGH',
        'confidence_impact': -20,
        'reason': 'PO for $100K taxed upfront, but only $80K delivered (20% retainage)',
        'refund_potential': 2100.00  # 10.5% of $20K retainage
    }
]
```

---

### 4. Learning System

**Purpose**: Capture human corrections and improve AI over time

**Components**:
- `database/schema/analysis_reviews.sql`: Review records
- `database/schema/learned_patterns.sql`: Extracted patterns
- `core/pattern_extraction.py`: Auto-extract patterns from explanations
- `core/similar_case_detection.py`: Find similar past cases

**Learning Flow**:
```
Human Override
    ↓
Capture Explanation (REQUIRED)
    ↓
Extract Pattern
    ↓
Save to learned_patterns table
    ↓
Find Similar Unreviewed Cases
    ↓
Apply Pattern (if "apply to similar" checked)
    ↓
Track Pattern Accuracy
    ↓
Adjust Future Analyses
```

**Pattern Types**:
1. **Vendor-Specific**: "Microsoft always provides custom software"
2. **Category Rules**: "Professional services + odd $ = hidden tax"
3. **Keyword Triggers**: "Hosting" → exempt digital goods
4. **Anomaly Responses**: Construction retainage → timing error

**Example Pattern**:
```json
{
  "pattern_id": "PAT-2024-0042",
  "pattern_type": "vendor_specific",
  "pattern_name": "microsoft_custom_software_development",
  "trigger_conditions": {
    "vendor_name": "Microsoft Corporation",
    "keywords": ["development", "custom", "configuration", "API integration"]
  },
  "confidence_adjustment": +20,
  "override_determination": null,
  "learned_from_count": 5,
  "times_applied": 23,
  "accuracy_rate": 0.91,
  "is_active": true
}
```

---

### 5. Human Review Workflow

**Purpose**: Analysts review flagged transactions and provide corrections

**Review Queues**:
| Queue | Confidence | Tax Amount | Priority | SLA |
|-------|-----------|------------|----------|-----|
| Critical | < 50% | > $10K | P1 | 24h |
| High | 50-70% | > $5K | P2 | 3d |
| Standard | 70-90% | Any | P3 | 1w |
| Auto-Approved | ≥ 90% | Any | N/A | Spot check only |

**Review Actions**:
1. **Accept**: AI correct (→ approved)
2. **Override**: AI wrong (→ requires explanation → pattern learning)
3. **Send to Client**: Need clarification (→ email client)
4. **Escalate**: Complex case (→ senior analyst)
5. **No Refund**: Correctly taxed (→ remove from claim)

**UI Components** (from Google AI Studio dashboard):
- Exception queue table (left panel)
- Detail panel (right panel) with:
  - Parsed invoice text
  - AI suggestion + confidence
  - Anomalies detected
  - Similar past cases
  - Action buttons

---

### 6. Sales Tax vs Use Tax Separation

**Purpose**: Separate claims for different tax types (required by WA DOR)

**Classification Logic**:
```python
def classify_tax_type(row: Dict) -> str:
    tax_remitted = row['Tax_Remitted']
    tax_amount = row['Tax_Amount']

    # SALES TAX: Vendor collected and remitted
    if tax_remitted > 0 and tax_amount > 0:
        return 'sales_tax'

    # USE TAX: Self-assessed by purchaser
    if tax_remitted == 0 and tax_amount > 0:
        return 'use_tax'

    # UNCLEAR: Needs human review
    return 'NEEDS_REVIEW'
```

**Output Files**:
- `Master_Sales_Tax_Claim_Sheet.xlsx` → Sales tax refund claim
- `Master_Use_Tax_Claim_Sheet.xlsx` → Use tax refund claim
- `Needs_Manual_Classification.xlsx` → Human intervention required

**Claim Packet Generation**:
- Separate PDF packets for each tax type
- Different cover letter templates
- Different legal citations
- Different schedules of transactions

---

### 7. Dashboard UI (React + TypeScript)

**Purpose**: Professional interface for tax analysts

**Pages**:
1. **Dashboard** (`/`): Overview, stats, quick actions
2. **Projects** (`/projects`): Project management
3. **Documents** (`/documents`): Upload invoices, import Excel
4. **Review Queue** (`/review`): Exception handling (CORE PAGE)
5. **Claims** (`/claims`): Claim builder, packet generation
6. **Pattern Library** (`/patterns`): View learned patterns

**Key Features**:
- Exception-driven workflow
- AI transparency (show rationale, citations)
- Split-view review (table + detail panel)
- Feedback capture with explanation requirement
- Similar case suggestions
- Keyboard shortcuts for efficiency

---

### 8. Analytics & Reporting (Power BI)

**Purpose**: Track progress, accuracy, and identify gaps

**Dashboards**:
1. **Executive Summary**: Total refunds, claims status, timeline
2. **Analysis Accuracy**: AI confidence vs human override rate
3. **Learning Progress**: Patterns learned, accuracy improvement
4. **Vendor Analysis**: Top vendors, industries, refund opportunities
5. **Anomaly Insights**: Most common anomalies, refund potential

**Key DAX Measures**:
```dax
TotalEstimatedRefund = SUM(analysis_results[estimated_refund])

AutoApprovalRate =
DIVIDE(
    COUNTROWS(FILTER(analysis_results, [ai_confidence] >= 90)),
    COUNTROWS(analysis_results)
)

OverrideRate =
DIVIDE(
    COUNTROWS(FILTER(analysis_reviews, [correction_type] <> 'accept')),
    COUNTROWS(analysis_reviews)
)

PatternAccuracy =
AVERAGE(learned_patterns[accuracy_rate])

AvgReviewTime =
AVERAGE(analysis_reviews[review_duration_seconds]) / 60
```

---

## Data Flow

### End-to-End Flow: Excel Upload → Refund Packet

```
1. USER UPLOADS EXCEL
   ↓
2. CLASSIFY TAX TYPE
   → Master_Sales_Tax_Claim_Sheet.xlsx
   → Master_Use_Tax_Claim_Sheet.xlsx
   ↓
3. DETECT FILE CHANGES (MD5 hash)
   → Process only new/changed rows
   ↓
4. FOR EACH ROW:
   a. Extract invoice PDF text (OCR)
   b. Get vendor metadata
   c. Query tax law RAG
   d. Run GPT-4 analysis
   e. Run anomaly detection
   f. Apply learned patterns
   g. Calculate confidence
   h. Populate OUTPUT columns
   ↓
5. TRIAGE BY CONFIDENCE
   → ≥90%: Auto-approve (spot check 10%)
   → <90%: Send to review queue
   ↓
6. HUMAN REVIEW (for <90%)
   a. Analyst reviews AI determination
   b. Accepts OR overrides with explanation
   c. System extracts pattern from explanation
   d. Pattern applied to similar cases
   ↓
7. FINALIZE MASTER SHEETS
   → All rows have OUTPUT columns populated
   → Reviewed and approved
   ↓
8. GENERATE CLAIM PACKETS
   → Sales_Tax_Refund_Packet.pdf
   → Use_Tax_Refund_Packet.pdf
   ↓
9. ANALYST REVIEWS PACKETS
   → Download, sign, submit to WA DOR
```

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Database**: Supabase PostgreSQL
- **Storage**: Supabase Storage (PDFs)
- **Vector DB**: pgvector (for RAG)
- **AI Model**: OpenAI GPT-4o
- **OCR**: pdftotext, Tesseract (fallback)

### Frontend
- **Framework**: React 18 + TypeScript
- **Routing**: React Router v6
- **State**: React Context API
- **UI Components**: Tailwind CSS
- **Icons**: Google Material Icons
- **Build**: Vite

### Analytics
- **Platform**: Power BI Desktop
- **Data Source**: Supabase PostgreSQL (DirectQuery)
- **Refresh**: Real-time

### DevOps
- **Hosting**: TBD (AWS, Vercel, or Railway)
- **CI/CD**: GitHub Actions
- **Secrets**: Environment variables
- **Monitoring**: TBD (Sentry, LogRocket)

---

## Database Schema

### Core Tables

#### `knowledge_documents`
```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type TEXT NOT NULL,  -- 'tax_law', 'vendor_background', 'guidance'
    title TEXT NOT NULL,
    state_code TEXT,
    law_version TEXT,  -- 'OLD' or 'NEW'
    effective_date DATE,
    vendor_name TEXT,
    industry TEXT,
    business_model TEXT,
    primary_products TEXT[],
    confidence_score FLOAT,
    source_file_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `analysis_results`
```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id TEXT NOT NULL,
    vendor_name TEXT,
    invoice_file_url TEXT,

    -- Analysis Output
    analysis_notes TEXT,
    final_decision TEXT,
    tax_category TEXT,
    additional_info TEXT,
    refund_basis TEXT,
    estimated_refund DECIMAL(10, 2),
    legal_citation TEXT,
    ai_confidence FLOAT,

    -- Metadata
    tax_type TEXT,  -- 'sales_tax' or 'use_tax'
    tax_amount DECIMAL(10, 2),
    anomalies_detected TEXT[],
    patterns_applied TEXT[],
    review_status TEXT,  -- 'pending', 'accepted', 'overridden', 'awaiting_client'

    analyzed_at TIMESTAMP DEFAULT NOW()
);
```

#### `analysis_reviews`
```sql
CREATE TABLE analysis_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analysis_results(id),

    -- Original AI
    ai_taxability TEXT,
    ai_confidence FLOAT,

    -- Human Correction
    human_taxability TEXT,
    human_explanation TEXT NOT NULL,
    correction_type TEXT,

    -- Learning
    pattern_extracted BOOLEAN,
    pattern_id UUID REFERENCES learned_patterns(id),
    apply_to_similar BOOLEAN,

    reviewed_by TEXT,
    reviewed_at TIMESTAMP DEFAULT NOW()
);
```

#### `learned_patterns`
```sql
CREATE TABLE learned_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type TEXT NOT NULL,
    pattern_name TEXT UNIQUE NOT NULL,
    trigger_conditions JSONB NOT NULL,
    confidence_adjustment FLOAT,

    -- Learning Stats
    learned_from_count INTEGER DEFAULT 1,
    times_applied INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    accuracy_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN times_applied > 0
        THEN CAST(times_correct AS FLOAT) / times_applied
        ELSE NULL END
    ) STORED,

    is_active BOOLEAN DEFAULT TRUE,
    requires_validation BOOLEAN DEFAULT TRUE
);
```

#### `excel_file_tracking`
```sql
CREATE TABLE excel_file_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,  -- MD5 or SHA256
    tax_type TEXT,
    row_count INTEGER,
    processed_count INTEGER,
    upload_date TIMESTAMP DEFAULT NOW(),
    last_processed_at TIMESTAMP
);
```

---

## API Endpoints

### Excel Processing
- `POST /api/excel/upload` - Upload master Excel file
- `POST /api/excel/classify` - Classify by tax type
- `GET /api/excel/changes` - Detect file changes

### Analysis
- `POST /api/analysis/run` - Run AI analysis on invoice
- `POST /api/analysis/batch` - Batch analyze multiple invoices
- `GET /api/analysis/{id}` - Get analysis result
- `POST /api/analysis/{id}/rationale` - Request AI rationale

### Reviews
- `GET /api/reviews/queue` - Get review queue
- `POST /api/reviews/submit` - Submit human review
- `GET /api/reviews/{id}/similar` - Find similar cases
- `POST /api/reviews/override` - Override AI determination

### Patterns
- `GET /api/patterns` - List learned patterns
- `POST /api/patterns/{id}/validate` - Validate pattern
- `POST /api/patterns/apply-to-similar` - Apply pattern to similar cases

### Claims
- `POST /api/claims/generate` - Generate claim packet PDF
- `GET /api/claims/{id}` - Get claim packet
- `POST /api/claims/{id}/finalize` - Mark as filed

---

## File Structure

```
refund-engine/
├── analysis/
│   ├── analyze_refunds_enhanced.py      # Main analysis logic
│   ├── excel_processors.py              # Excel parsing
│   ├── fast_batch_analyzer.py           # Batch processing
│   └── invoice_lookup.py                # PDF OCR
├── core/
│   ├── law_version_handler.py           # OLD vs NEW law
│   ├── rag_query_engine.py              # Tax law RAG
│   ├── pattern_extraction.py            # Learn from reviews
│   ├── similar_case_detection.py        # Find similar cases
│   └── feedback_system.py               # Feedback capture
├── database/
│   ├── schema/
│   │   ├── migration_excel_file_tracking.sql
│   │   ├── migration_vendor_metadata.sql
│   │   ├── analysis_reviews.sql
│   │   └── learned_patterns.sql
│   └── migrations/
├── scripts/
│   ├── split_excel_by_tax_type.py       # Tax type classifier
│   ├── create_master_excel_sheet.py     # Test data generator
│   ├── ingest_vendor_background.py      # Vendor metadata ingest
│   └── deploy_feedback_schema.py        # DB deployment
├── docs/
│   ├── ANOMALY_DETECTION_FRAMEWORK.md   # 15 anomaly detectors
│   ├── SALES_USE_TAX_SEPARATION.md      # Tax type separation
│   ├── LEARNING_SYSTEM_ARCHITECTURE.md  # Active learning
│   ├── HUMAN_REVIEW_WORKFLOW.md         # Review process
│   └── COMPLETE_SYSTEM_ARCHITECTURE.md  # This document
├── test_data/
│   ├── Master_Sales_Tax_Claim_Sheet.xlsx
│   ├── Master_Use_Tax_Claim_Sheet.xlsx
│   ├── invoices/
│   └── purchase_orders/
└── knowledge_base/
    └── states/washington/
        ├── legal_documents/
        └── essb_5814_oct_2025/
```

---

## Deployment Architecture

### Option A: Full Cloud (AWS)

```
┌─────────────────────────────────────────────┐
│              CloudFront CDN                 │
│         (Static React Frontend)             │
└─────────────────┬───────────────────────────┘
                  │
         ┌────────▼─────────┐
         │   API Gateway    │
         └────────┬─────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Lambda Functions (Python) │
    │   - Excel processing       │
    │   - AI analysis            │
    │   - Pattern learning       │
    └──────────┬─────────────────┘
               │
    ┌──────────▼──────────┐
    │  Supabase Cloud     │
    │  - PostgreSQL       │
    │  - Storage (PDFs)   │
    │  - Vector Store     │
    └─────────────────────┘
```

### Option B: Hybrid (Supabase + Vercel)

```
┌──────────────────────────┐
│   Vercel (Frontend)      │
│   - React App            │
│   - API Routes (Next.js) │
└──────────┬───────────────┘
           │
    ┌──────▼───────┐
    │  Supabase    │
    │  - Database  │
    │  - Storage   │
    │  - Functions │
    └──────────────┘
```

### Option C: Self-Hosted (Railway)

```
┌─────────────────────────┐
│   Railway Container     │
│   - FastAPI Backend     │
│   - React Frontend      │
│   - Worker Queue        │
└──────────┬──────────────┘
           │
    ┌──────▼───────┐
    │  Supabase    │
    │  (DB only)   │
    └──────────────┘
```

---

## Security & Compliance

### Data Security
- **Encryption at Rest**: Supabase provides AES-256 encryption
- **Encryption in Transit**: TLS 1.3 for all API calls
- **Access Control**: Row-Level Security (RLS) in Supabase
- **API Authentication**: JWT tokens with expiration

### Compliance
- **Tax Data Sensitivity**: All invoice data considered confidential
- **Retention Policy**: Keep analysis data for 7 years (IRS requirement)
- **Audit Trail**: All human reviews logged with timestamps
- **Client Data Handling**: Separate storage per client project

### Security Best Practices
```python
# Environment variables (never commit)
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Row-Level Security policy example
CREATE POLICY "Users can only see their own projects"
ON analysis_results
FOR SELECT
USING (auth.uid() = user_id);
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [x] Design architecture
- [x] Create documentation
- [x] Design database schema
- [ ] Deploy Supabase tables
- [ ] Implement tax type classifier
- [ ] Create test data (invoices, Excel)

### Phase 2: Core Analysis (Weeks 3-5)
- [ ] Build enhanced RAG system
- [ ] Implement GPT-4 analysis pipeline
- [ ] Create anomaly detection framework
- [ ] Test with 50 sample invoices
- [ ] Validate accuracy against expert reviews

### Phase 3: Learning System (Weeks 6-7)
- [ ] Implement review capture forms
- [ ] Build pattern extraction algorithm
- [ ] Create similar case detection
- [ ] Deploy pattern application logic
- [ ] Test with 20 human corrections

### Phase 4: Dashboard UI (Weeks 8-10)
- [ ] Build Review Queue page
- [ ] Create override forms with explanations
- [ ] Implement keyboard shortcuts
- [ ] Add similar case display
- [ ] Build Pattern Library page

### Phase 5: Excel Integration (Week 11)
- [ ] Implement file change detection
- [ ] Build incremental processing
- [ ] Create OUTPUT column population
- [ ] Test with full client dataset

### Phase 6: Claim Generation (Week 12)
- [ ] Build claim packet PDF generator
- [ ] Create separate sales/use tax templates
- [ ] Implement cover letter generation
- [ ] Test end-to-end workflow

### Phase 7: Analytics & Reporting (Week 13)
- [ ] Design Power BI data model
- [ ] Create DAX measures
- [ ] Build 5 dashboard pages
- [ ] Connect to Supabase

### Phase 8: Testing & Refinement (Week 14-15)
- [ ] User acceptance testing with tax analysts
- [ ] Fix bugs and edge cases
- [ ] Optimize performance
- [ ] Finalize documentation

### Phase 9: Deployment (Week 16)
- [ ] Deploy to production
- [ ] Train analysts on system
- [ ] Monitor initial results
- [ ] Iterate based on feedback

---

## Success Criteria

### Technical
- [ ] ≥ 90% uptime
- [ ] < 5 second average response time for analysis
- [ ] Zero data loss
- [ ] All PDFs readable via OCR (> 95% accuracy)

### Accuracy
- [ ] AI confidence accuracy > 85% (high confidence = correct)
- [ ] Auto-approval rate > 70% (≥90% confidence)
- [ ] Human override rate 15-25%
- [ ] Pattern accuracy > 85%

### Efficiency
- [ ] Average review time < 5 minutes
- [ ] 50+ patterns learned in first 500 reviews
- [ ] Analysts complete 20-40 reviews/day

### User Satisfaction
- [ ] Tax analysts rate system 4/5 or higher
- [ ] Claim generation time reduced by 50%
- [ ] Refund discovery rate increased by 20%

---

## Appendix

### Related Documents
- [ANOMALY_DETECTION_FRAMEWORK.md](./ANOMALY_DETECTION_FRAMEWORK.md) - 15 anomaly detectors
- [SALES_USE_TAX_SEPARATION.md](./SALES_USE_TAX_SEPARATION.md) - Tax type separation logic
- [LEARNING_SYSTEM_ARCHITECTURE.md](./LEARNING_SYSTEM_ARCHITECTURE.md) - Active learning system
- [HUMAN_REVIEW_WORKFLOW.md](./HUMAN_REVIEW_WORKFLOW.md) - Step-by-step review process
- [COMPLETE_WORKFLOW_GUIDE.md](./COMPLETE_WORKFLOW_GUIDE.md) - End-to-end user guide

### Glossary
- **DAS**: Digital Automated Services (new WA tax category)
- **MPU**: Multiple Points of Use (exemption for multi-state businesses)
- **OLD LAW**: Pre-Oct 1, 2025 tax law
- **NEW LAW**: ESSB 5814 (effective Oct 1, 2025)
- **RAG**: Retrieval Augmented Generation (AI technique)
- **RLS**: Row-Level Security (Supabase feature)

### Contact
For questions about this architecture:
- Technical Lead: [Contact Info]
- Tax Expert: [Contact Info]
- Project Manager: [Contact Info]

---

**End of Document**
