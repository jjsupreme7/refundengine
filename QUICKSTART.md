# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup (First Time Only)

```bash
cd refund-engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/db_setup.py
```

### 2. Add Legal Documents

```bash
# Place your Washington State legal documents in:
knowledge_base/statutes/rcw/    # RCW files
knowledge_base/statutes/wac/    # WAC files
knowledge_base/guidance/wtd/    # WTD files
knowledge_base/guidance/eta/    # ETA files

# Then ingest them:
python scripts/ingest_legal_docs.py --folder knowledge_base/
```

### 3. Process Client Invoices

```bash
# Place ALL client documents in:
client_documents/uploads/

# Run the full pipeline:
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/
```

### 4. Get Your Reports

Reports are automatically generated in:
- `outputs/reports/` - Client-facing report
- `outputs/dor_filings/` - DOR submission worksheet
- `outputs/analysis/` - Internal analysis

## 🎯 What It Does

1. **Classifies** all your documents automatically (invoices, POs, SOWs)
2. **Identifies** products and determines taxability characteristics
3. **Searches** across ALL legal documents for relevant exemptions
4. **Analyzes** each line item for refund eligibility
5. **Generates** professional Excel reports

## 💡 Key Features

- **Vector Search**: Automatically finds relevant tax laws for each product
- **AI Classification**: No manual sorting needed
- **Comprehensive Coverage**: Analyzes HUNDREDS of exemptions, not just a few
- **Professional Reports**: Ready for client presentation and DOR filing

## ⚡ Commands Cheat Sheet

```bash
# Initialize
python scripts/db_setup.py

# Ingest legal docs
python scripts/ingest_legal_docs.py --folder knowledge_base/

# Process client docs
python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1

# Full pipeline
python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/

# Individual analysis
python scripts/analyze_refund.py --invoice_id 1

# Generate reports
python scripts/generate_client_report.py --client_id 1
python scripts/generate_dor_filing.py --client_id 1
python scripts/generate_internal_workbook.py --client_id 1
```

## 📞 Need Help?

See the full README.md for detailed documentation.
