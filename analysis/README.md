# Analysis Modules

This folder contains the core analysis modules for processing tax refund data, analyzing invoices, and learning from corrections.

## Overview

The analysis system processes Excel files with invoice data, extracts information from PDF invoices, queries the knowledge base, and determines refund eligibility using AI.

## Module Descriptions

### Core Analysis Engines

#### `analyze_refunds.py`
**Purpose**: Standard refund analysis engine

**What it does**:
- Reads Excel file with invoice line items
- Extracts product descriptions from invoice PDFs
- Queries tax law knowledge base
- Determines refund eligibility
- Outputs Excel with AI analysis columns

**Usage**:
```bash
python -m analysis.analyze_refunds input.xlsx --output results.xlsx
```

**Input**: Excel with columns (Row_ID, Vendor, Invoice_Number, Amount, Tax, etc.)
**Output**: Same Excel + AI_Product_Desc, AI_Refund_Eligible, AI_Citation, etc.

---

#### `analyze_refunds_enhanced.py`
**Purpose**: Enhanced analysis with advanced RAG features

**What it does**:
- Everything analyze_refunds.py does, plus:
- Corrective RAG (self-verification)
- Query expansion for better search
- Advanced filtering by law category
- Vendor background integration

**Usage**:
```bash
python -m analysis.analyze_refunds_enhanced input.xlsx --enhanced-rag
```

**When to use**:
Use enhanced version for complex cases requiring deeper analysis. Standard version is faster for straightforward cases.

---

#### `fast_batch_analyzer.py`
**Purpose**: High-performance batch processing

**What it does**:
- Processes large Excel files (10,000+ rows)
- Parallel processing for speed
- Progress tracking
- Checkpoint/resume support

**Usage**:
```bash
python -m analysis.fast_batch_analyzer large_file.xlsx --workers 4
```

**When to use**:
Processing very large datasets where speed is critical.

---

### Supporting Modules

#### `excel_processors.py`
**Purpose**: Excel file parsing and processing utilities

**Contains**:
- `DenodoSalesTaxProcessor` - Processes Denodo sales tax exports
- `UseTaxProcessor` - Processes use tax Phase 3 files
- `auto_detect_file_type()` - Automatically detects Excel format
- Column mapping and validation functions

**Usage**: Imported by analysis scripts
```python
from analysis.excel_processors import DenodoSalesTaxProcessor
processor = DenodoSalesTaxProcessor()
df = processor.load_file("sales_tax.xlsx")
```

---

#### `invoice_lookup.py`
**Purpose**: Extract line item details from invoice PDFs

**What it does**:
- Opens invoice PDF
- Finds line item matching specific amount
- Extracts product description, SKU, details
- Handles multiple invoice formats

**Usage**: Called internally by analysis engines
```python
from analysis.invoice_lookup import extract_line_item
desc = extract_line_item(pdf_path, amount=8000.00)
```

---

#### `import_corrections.py`
**Purpose**: Import human corrections and learn from them

**What it does**:
- Reads reviewed Excel with correction columns
- Stores reviews in `analysis_reviews` table
- Creates/updates vendor product catalog
- Generates pattern matching rules
- Logs all changes to audit trail

**Usage**:
```bash
python -m analysis.import_corrections reviewed.xlsx --reviewer email@company.com
```

**Input**: Excel with Review_Status, Corrected_* columns filled in
**Output**: Updates database with learnings

---

#### `invoice_pattern_learning.py`
**Purpose**: Learn patterns from historical corrections

**What it does**:
- Analyzes correction history
- Identifies recurring patterns
- Creates matching rules
- Improves future accuracy

**Usage**: Called automatically by import_corrections
```python
from analysis.invoice_pattern_learning import learn_from_correction
learn_from_correction(vendor="Nokia", product="5G Radio", correct_type="Hardware")
```

---

## How Modules Work Together

### Standard Workflow

```
Excel Input
     ↓
[analyze_refunds.py]
     ├→ Uses excel_processors.py to read Excel
     ├→ Uses invoice_lookup.py to extract from PDFs
     ├→ Queries knowledge base (core/enhanced_rag.py)
     └→ Outputs Excel with AI columns

Excel with AI Results
     ↓
(Human reviews and corrects)
     ↓
[import_corrections.py]
     ├→ Uses invoice_pattern_learning.py to learn
     └→ Updates database with patterns

Next Analysis
     ↓
[analyze_refunds.py]
     └→ Uses learned patterns for better accuracy!
```

### Fast Batch Workflow

```
Large Excel (100,000 rows)
     ↓
[fast_batch_analyzer.py]
     ├→ Splits into chunks
     ├→ Processes in parallel (4-8 workers)
     ├→ Saves checkpoints every 1000 rows
     └→ Merges results
```

---

## Input/Output Formats

### Input Excel Format
Required columns:
- `Row_ID` - Unique identifier
- `Vendor` - Vendor name
- `Invoice_Number` - Invoice #
- `PO Number` - Purchase order #
- `Date` - Transaction date
- `Inv_1_File` - Invoice PDF filename
- `Amount` - Line item amount
- `Tax` - Tax paid

### Output Excel Format
Input columns + these AI-generated columns:
- `AI_Product_Desc` - Product description
- `AI_Product_Type` - Category (Hardware/Software/Service)
- `AI_Refund_Eligible` - True/False
- `AI_Refund_Basis` - Legal reasoning
- `AI_Citation` - RCW/WAC reference
- `AI_Confidence` - 0-100%
- `AI_Estimated_Refund` - Dollar amount
- `AI_Explanation` - Detailed explanation

### Review Excel Format
Output columns + these human-filled columns:
- `Review_Status` - Approved/Needs Correction/Rejected (**required**)
- `Corrected_Product_Desc` - Fixed description (if wrong)
- `Corrected_Product_Type` - Fixed type (if wrong)
- `Corrected_Refund_Basis` - Fixed reasoning (if wrong)
- `Reviewer_Notes` - Your explanation (**recommended**)

---

## Configuration

Most analysis modules use these environment variables:
```bash
OPENAI_API_KEY=sk-...           # For AI analysis
SUPABASE_URL=https://...        # Database connection
SUPABASE_SERVICE_ROLE_KEY=...  # Database auth
DOCS_FOLDER=client_docs         # Where PDFs are stored
```

---

## Performance Tips

### For Speed
1. Use `fast_batch_analyzer.py` for large files
2. Increase workers: `--workers 8` (if you have the cores)
3. Use standard `analyze_refunds.py` instead of enhanced version

### For Accuracy
1. Use `analyze_refunds_enhanced.py` with `--enhanced-rag`
2. Ensure knowledge base is comprehensive
3. Import corrections regularly to improve learning
4. Review and correct low-confidence results (<50%)

### For Cost Optimization
1. Don't re-analyze rows that are already correct
2. Use smaller batches for testing
3. Review high-confidence results (>90%) less rigorously

---

## Troubleshooting

### "No text extracted from PDF"
- PDF may be scanned (no OCR)
- Use `pdftotext` to check if text is extractable
- Consider using OCR tool first

### "Product not found in invoice"
- Invoice format may be unusual
- Amount might not match exactly
- Check `invoice_lookup.py` logic for your invoice format

### Low confidence scores
- Insufficient knowledge base
- Ambiguous product descriptions
- Novel scenarios not seen before
- **Solution**: Add more documents to knowledge base

### "Database connection failed"
- Check `.env` file has correct Supabase credentials
- Verify network connectivity
- Check Supabase project status

---

## Adding New Analysis Modules

When creating new analysis modules:

1. **Follow naming convention**: `verb_noun.py` (e.g., `analyze_expenses.py`)
2. **Import from core**: Use `core.enhanced_rag` for KB queries
3. **Use excel_processors**: Don't reinvent Excel parsing
4. **Support command-line**: Use argparse for flexibility
5. **Add progress tracking**: For long-running operations
6. **Update this README**: Document your module

---

## Related Documentation

- [Excel Workflow Guide](../docs/guides/EXCEL_WORKFLOW_GUIDE.md) - Complete workflow
- [Enhanced RAG Guide](../docs/technical/ENHANCED_RAG_GUIDE.md) - RAG system details
- [Scripts](../scripts/README.md) - Supporting scripts
- [Core Modules](../core/README.md) - Core functionality

---

**Last Updated**: 2025-11-13
