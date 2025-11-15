# Washington State Tax Refund Engine

AI-powered system with **human-in-the-loop learning** for identifying sales/use tax refund opportunities for Washington State businesses.

## ✨ What's New - Production Ready! 🚀

- 🧪 **Full Test Coverage** - pytest with 70%+ coverage ensuring financial accuracy
- ⚡ **Async Processing** - Process 100K invoices in 4 hours (was 9 days!)
- 🐳 **Docker Ready** - One command deploys entire stack
- 🔄 **CI/CD Pipeline** - Automated testing and deployment via GitHub Actions
- 📊 **Excel-Based Review Workflow** - AI analyzes, you review in Excel, system learns from corrections
- 🧠 **Dual Knowledge Base** - Separate Tax Law (RCW/WAC) and Vendor Background documents
- 🤖 **Smart Invoice Matching** - AI reads PDFs and matches line items to Excel rows by amount
- 👤 **Human-in-the-Loop** - Approve/correct AI decisions, system gets smarter over time
- 🔄 **Vendor Learning System** - Builds product patterns from your corrections

## 🚀 Quick Start

### Option 1: Docker (Recommended - 30 seconds)

```bash
# Clone repository
git clone https://github.com/yourusername/refund-engine.git
cd refund-engine

# Create .env file with your API keys
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY, SUPABASE_URL, etc.

# Start everything (Redis + Workers + Monitoring)
docker-compose up -d

# Run tests to verify setup
docker-compose run test

# Process invoices (async, parallel processing!)
docker-compose run app python scripts/async_analyzer.py --excel Master_Refunds.xlsx

# Monitor progress at: http://localhost:5555
```

**That's it! You're processing invoices in parallel.** 🎉

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Start Celery workers (in another terminal)
celery -A tasks worker --loglevel=info --concurrency=10

# Queue invoices for processing
python scripts/async_analyzer.py --excel Master_Refunds.xlsx
```

## 📚 Documentation

### 🚀 Getting Started
- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Get running in 15 minutes
- **[Simple Explanation](docs/guides/SIMPLE_EXPLANATION.md)** - How the system works
- **[Local Setup](docs/setup/LOCAL_ENVIRONMENT_SETUP.md)** - Set up your development environment
- **[Quick Reference](docs/guides/QUICK_REFERENCE.md)** - Command cheatsheet

### 📖 Core Workflows
- **[Excel Workflow Guide](docs/guides/EXCEL_WORKFLOW_GUIDE.md)** - Complete analysis workflow
- **[Knowledge Base Guide](docs/guides/KNOWLEDGE_BASE_GUIDE.md)** - Managing tax law documents
- **[Testing Guide](docs/guides/TESTING_GUIDE.md)** - Running tests for accuracy

### 🏗️ Deployment & Scaling
- **[Production Setup](docs/setup/PRODUCTION_SETUP.md)** - Deploy to production
- **[Docker Guide](docs/setup/DOCKER_GUIDE.md)** - Containerized deployment
- **[Async Processing](docs/guides/ASYNC_PROCESSING_GUIDE.md)** - Scale to 100K+ invoices

### 🔧 Technical Deep Dives
- **[Architecture](docs/technical/ARCHITECTURE.md)** - Business & workflow architecture
- **[System Architecture](docs/technical/SYSTEM_ARCHITECTURE.md)** - Technical & database design
- **[Enhanced RAG](docs/technical/ENHANCED_RAG_GUIDE.md)** - AI retrieval system

### 📂 Complete Documentation Index
➡️ **[See all 47 documentation files](docs/README.md)** - Master documentation index

### 🔗 Project Resources
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and recent changes
- **[PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md)** - Strategic roadmap 2025-2026

### 3. Review & Correct in Excel

Open `input_analyzed.xlsx` and fill in review columns:
- **Review_Status**: Approved / Needs Correction / Rejected
- **Corrected_Product_Type**: Fix if AI got it wrong
- **Corrected_Estimated_Refund**: Fix amount if wrong
- **Reviewer_Notes**: Your reasoning (helps system learn!)

### 4. Import Corrections & System Learns

```bash
# Import your corrections
python scripts/7_import_corrections.py "input_analyzed.xlsx" --reviewer "your.email@company.com"

# System learns from corrections and gets smarter!
```

**📚 Detailed Guides:**
- Excel Workflow: [docs/guides/EXCEL_WORKFLOW_GUIDE.md](docs/guides/EXCEL_WORKFLOW_GUIDE.md)
- Knowledge Base: [docs/guides/KNOWLEDGE_BASE_GUIDE.md](docs/guides/KNOWLEDGE_BASE_GUIDE.md)

---

## 📁 Project Structure

```
refund-engine/
├── client_documents/
│   └── invoices/                    # Your invoice PDFs go here
│
├── knowledge_base/
│   ├── vendors/
│   │   └── vendor_database.json     # 200+ pre-populated vendors
│   ├── taxonomy/
│   │   └── product_types.json       # Product classification rules
│   └── states/
│       └── washington/
│           ├── legal_documents/     # WA tax law PDFs
│           └── tax_rules.json       # WA tax logic
│
├── scripts/
│   ├── 1_setup_supabase.py         # Database setup
│   ├── 2_ingest_legal_docs.py      # Ingest legal docs
│   ├── 5_fast_batch_analyzer.py    # Main analyzer (NEW!)
│   └── utils/
│       └── smart_cache.py           # Caching system
│
└── database/
    └── supabase_schema.sql          # Database schema
```

---

## 🎯 How It Works

### The Analysis Pipeline

```
Excel → Extract Invoices → Match Line Items → Categorize Products
                                                      ↓
  ← Write Results ← AI Analysis ← Legal Research ← Search Laws
```

### 1. Invoice Extraction (GPT-4 Vision)
- Reads invoice PDFs
- Extracts vendor, line items, amounts, tax
- **Cached** for 30 days (instant on re-runs)

### 2. Vendor Lookup
- Checks pre-populated vendor database (200+ vendors)
- Instant lookup (no API calls)
- Auto-learns new vendors

### 3. Product Categorization
- Classifies products: SaaS, Professional Services, Hardware, etc.
- Uses keyword matching + vendor context

### 4. Legal Research (RAG)
- Searches WA legal documents (RCW, WAC, WTD)
- Category-based (one search per category, not per item)
- **Cached** for 7 days

### 5. AI Analysis (Batched)
- Analyzes 20 items per API call (vs 1 item per call)
- Applies WA tax rules
- Determines refund eligibility
- Provides legal citations

---

## 💰 Performance & Cost

### Speed
- **100 invoices, 250 line items: ~2-3 minutes**
- First run: ~3 min
- Subsequent runs (cached): ~1 min

### Cost (per 100 invoices)
- Invoice extraction: $0.30 (20 new invoices, 80 cached)
- Legal research: $0.00 (cached)
- AI analysis: $0.78 (13 batched calls)
- **Total: ~$1.08**

### Caching Benefits
- Invoice cache: 80%+ hit rate after first run
- Vendor database: 100% hit rate
- RAG cache: 100% hit rate (category-based)

---

## 📊 Excel Format

### Required Columns (You Fill)

| Vendor | Invoice_Number | Date | Amount | Tax | Inv_1_File |
|--------|----------------|------|--------|-----|------------|
| Microsoft | INV-001 | 2024-01-15 | 50,000 | 5,000 | microsoft-jan.pdf |

### AI-Filled Columns

| Product_Desc | Refund_Basis | Citation | Confidence | Estimated_Refund | Explanation |
|--------------|--------------|----------|------------|------------------|-------------|
| Microsoft 365 E5 | MPU | WAC 458-20-15502 | 88% | $4,250 | Digital service, allocate by user location... |

---

## 🔧 Configuration

### .env File

```bash
OPENAI_API_KEY=sk-...              # Required
SUPABASE_URL=https://...           # Required
SUPABASE_SERVICE_ROLE_KEY=...      # Required
```

### State Support

Currently: **Washington only**

Future: Add more states by:
1. Creating `knowledge_base/states/[state]/`
2. Adding legal documents
3. Creating `tax_rules.json`
4. Running: `--state california`

---

## 📚 Key Concepts

### Multi-Point Use (MPU)
- WA law: Tax allocated based on where services/products are used
- Example: 100 Microsoft 365 users, 85 outside WA → 85% refund
- Citation: WAC 458-20-15502

### Primarily Human Effort
- Services requiring human expertise are NOT taxable
- Example: Consulting, professional services
- Citation: RCW 82.04.050(6)

### Digital Automated Services
- Cloud/SaaS services are taxable in WA
- BUT: MPU allocation applies if multi-state usage
- Example: Salesforce, AWS, Azure

---

## 🎓 Common Refund Scenarios

| Scenario | Refund Basis | Typical Recovery |
|----------|--------------|------------------|
| Multi-state SaaS (users distributed) | MPU | 70-90% |
| Consulting services taxed incorrectly | Non-taxable | 100% |
| Cloud infrastructure (multi-region) | MPU | 80-95% |
| Hardware shipped out-of-state | OOS Shipment | 100% |
| Manufacturing equipment | Exemption | 100% |

---

## ⚙️ Advanced Usage

### Test Mode (First 10 Rows)
```bash
python scripts/5_fast_batch_analyzer.py \
    --excel "Master Refunds.xlsx" \
    --state washington \
    --limit 10
```

### Custom Output Path
```bash
python scripts/5_fast_batch_analyzer.py \
    --excel "Master Refunds.xlsx" \
    --output "Results Q1 2024.xlsx"
```

### Cache Management
```python
from scripts.utils.smart_cache import SmartCache

cache = SmartCache()
stats = cache.get_cache_stats()
print(stats)

# Clean expired entries
cache.cleanup_expired()
```

---

## 🔍 Troubleshooting

### "Invoice file not found"
- Ensure PDFs are in `client_documents/invoices/`
- Check Excel `Inv_1_File` column has correct filenames

### "No legal documents found"
- Run: `python scripts/2_ingest_legal_docs.py --state washington --folder knowledge_base/states/washington/legal_documents/`

### Low confidence scores (<60%)
- Review explanation column
- May need more legal documents
- Or product description is ambiguous

### API rate limits
- System automatically batches requests
- Uses caching to minimize API calls
- Adjust batch size if needed (edit script)

---

## 📝 Next Steps

1. **Process historical invoices** - Build your refund database
2. **Review high-confidence items** (>80%) - Quick wins
3. **Investigate medium-confidence** (60-80%) - Verify assumptions
4. **Manual review low-confidence** (<60%) - Complex cases
5. **Submit refund claims** - Use output as supporting documentation

---

## 🤝 Support

**Documentation:**
- 📖 **[Documentation Index](docs/README.md)** - Complete guide to all 47 documentation files
- 📁 **Module READMEs** - Each folder has detailed documentation:
  - [scripts/README.md](scripts/README.md) - All utility scripts
  - [analysis/README.md](analysis/README.md) - Analysis modules
  - [knowledge_base/README.md](knowledge_base/README.md) - Knowledge base organization
  - [tests/README.md](tests/README.md) - Testing information
  - [core/README.md](core/README.md) - Core ingestion pipeline
  - [chatbot/README.md](chatbot/README.md) - Chatbot usage

**Database:**
- Supabase dashboard: https://supabase.com/dashboard
- Schema documentation: [database/README.md](database/README.md)

---

## ⚖️ Legal Disclaimer

This system provides automated analysis for informational purposes only. All refund claims should be reviewed by qualified tax professionals before submission to the Washington State Department of Revenue.

---

**Built with:** OpenAI GPT-4o, Supabase, pgvector, Python
