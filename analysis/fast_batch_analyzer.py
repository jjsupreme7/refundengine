"""
Fast Batch Refund Analyzer (Enhanced)

High-quality, efficient invoice analysis using:
- EnhancedRAG: Corrective RAG + reranking + query expansion
- ExcelFileWatcher: Intelligent row-level change tracking
- Smart caching (vendor DB, invoice extraction, RAG results)
- Batch AI analysis (20 items per API call)
- State-aware legal research

Key Features:
- Only analyzes new/changed rows (skips already-analyzed data)
- Database-backed tracking using file and row hashes
- Higher quality legal research with AI-powered reranking
- Maintains fast batch processing for efficiency

INTELLIGENT CHANGE DETECTION (NEW):
- INPUT column changes (new invoice file, new PO, changed amounts) → Re-analyze
- OUTPUT column changes (corrections to AI analysis) → Skip re-analysis (feedback only)
- Uses excel_cell_changes table if file is in versioning system
- Falls back to row-level hash checking for non-versioned files

Usage:
    # Analyze only changed rows
    python analysis/fast_batch_analyzer.py \\
        --excel "Master Refunds.xlsx" --state washington

    # Test mode (force re-analysis of first N rows)
    python analysis/fast_batch_analyzer.py \\
        --excel "Master Refunds.xlsx" --state washington --limit 10
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports
from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

from core.database import get_supabase_client  # noqa: E402
from core.enhanced_rag import EnhancedRAG  # noqa: E402
from core.excel_file_watcher import ExcelFileWatcher  # noqa: E402
from core.excel_column_definitions import INPUT_COLUMNS, is_input_column  # noqa: E402
from core.model_router import ModelRouter  # noqa: E402
from scripts.utils.smart_cache import SmartCache  # noqa: E402

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()

# Initialize multi-model router
# Routes tasks to optimal models:
#   - GPT-5 for extraction/vision (best document understanding)
#   - Claude Sonnet 4.5 for tax analysis & legal reasoning
#   - Claude Opus 4.5 for high-stakes decisions ($25k+)
#   - GPT-4o-mini for validation tasks
router = ModelRouter()

# Initialize cache
cache = SmartCache()

# Initialize EnhancedRAG (also uses the router internally)
enhanced_rag = EnhancedRAG()


# ==========================================
# PATTERN QUERY FUNCTIONS
# ==========================================

def get_vendor_pattern(vendor_name: str, tax_type: str) -> Optional[Dict]:
    """Get historical vendor pattern from Supabase"""
    try:
        result = supabase.table("vendor_products") \
            .select("*") \
            .eq("vendor_name", vendor_name) \
            .eq("tax_type", tax_type) \
            .maybe_single() \
            .execute()
        return result.data
    except Exception as e:
        print(f"  ⚠️  Vendor pattern lookup failed for {vendor_name}: {e}")
        return None


def get_refund_basis_patterns(tax_type: str, limit: int = 10) -> List[Dict]:
    """Get top refund basis patterns for tax type"""
    try:
        result = supabase.table("refund_citations") \
            .select("*") \
            .eq("tax_type", tax_type) \
            .order("usage_count", desc=True) \
            .limit(limit) \
            .execute()
        return result.data
    except Exception as e:
        print(f"  ⚠️  Refund basis pattern lookup failed: {e}")
        return []


def get_keyword_patterns(tax_type: str) -> Dict[str, List[str]]:
    """Get all keyword patterns as dict by category"""
    try:
        result = supabase.table("keyword_patterns") \
            .select("*") \
            .eq("tax_type", tax_type) \
            .execute()

        # Convert to dict: {"tax_categories": [...], "product_types": [...]}
        return {
            row["category"]: row["keywords"]
            for row in result.data
        }
    except Exception as e:
        print(f"  ⚠️  Keyword pattern lookup failed: {e}")
        return {}


def _extract_pdf_image(file_path: str) -> str:
    """Extract first page of PDF as base64 image"""
    import base64
    from io import BytesIO
    import pdfplumber

    with pdfplumber.open(file_path) as pdf:
        if len(pdf.pages) == 0:
            return None

        first_page = pdf.pages[0]
        img = first_page.to_image(resolution=150)

        buffered = BytesIO()
        img.original.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


def _extract_image(file_path: str) -> str:
    """Extract JPG/PNG image as base64"""
    import base64

    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _extract_excel_invoice(file_path: str) -> Dict[str, Any]:
    """
    Extract invoice data from Excel file

    Expected columns: Vendor, Invoice Number, Date, Line Item, Amount, Tax
    """
    try:
        df = pd.read_excel(file_path)

        # Try to find common column patterns
        vendor_col = next((col for col in df.columns if 'vendor' in col.lower()), None)
        invoice_col = next((col for col in df.columns if 'invoice' in col.lower() and 'number' in col.lower()), None)
        date_col = next((col for col in df.columns if 'date' in col.lower()), None)
        amount_col = next((col for col in df.columns if 'amount' in col.lower() or 'total' in col.lower()), None)
        tax_col = next((col for col in df.columns if 'tax' in col.lower()), None)
        desc_col = next((col for col in df.columns if 'description' in col.lower() or 'item' in col.lower()), None)

        # Extract line items
        line_items = []
        for idx, row in df.iterrows():
            line_items.append({
                "description": row.get(desc_col, "Unknown") if desc_col else "Unknown",
                "amount": float(row.get(amount_col, 0)) if amount_col else 0,
                "tax": float(row.get(tax_col, 0)) if tax_col else 0
            })

        return {
            "vendor_name": df[vendor_col].iloc[0] if vendor_col and len(df) > 0 else "Unknown",
            "invoice_number": df[invoice_col].iloc[0] if invoice_col and len(df) > 0 else "Unknown",
            "invoice_date": str(df[date_col].iloc[0]) if date_col and len(df) > 0 else None,
            "total_amount": sum(item['amount'] for item in line_items),
            "tax_amount": sum(item['tax'] for item in line_items),
            "line_items": line_items
        }
    except Exception as e:
        return {"error": f"Excel extraction failed: {str(e)}"}


def _extract_word_invoice(file_path: str) -> Dict[str, Any]:
    """
    Extract invoice data from Word document

    Uses python-docx to parse tables, then GPT-5 (via router) for text extraction.
    GPT-5 excels at document understanding and structured data extraction.
    """
    try:
        from docx import Document

        doc = Document(file_path)

        # Extract all text
        full_text = '\n'.join([para.text for para in doc.paragraphs])

        # Try to extract tables (invoices often have tables)
        tables_text = []
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join([cell.text for cell in row.cells])
                tables_text.append(row_text)

        combined_text = full_text + '\n\n' + '\n'.join(tables_text)

        # Use router for extraction task (routes to GPT-5)
        prompt = f"""Extract invoice data from this Word document text and return JSON:

{combined_text}

Return format:
{{
  "vendor_name": "Company Name",
  "invoice_number": "INV-123",
  "invoice_date": "2024-01-15",
  "total_amount": 100.00,
  "tax_amount": 10.00,
  "line_items": [
    {{
      "description": "Product/service description",
      "amount": 100.00,
      "tax": 10.00
    }}
  ]
}}"""

        result = router.execute(
            task="extraction",
            prompt=prompt,
            stakes=0,  # Extraction is a preliminary task
        )

        return json.loads(result["content"])

    except ImportError:
        return {"error": "python-docx not installed. Run: pip install python-docx"}
    except Exception as e:
        return {"error": f"Word extraction failed: {str(e)}"}


def extract_invoice_with_vision(file_path: str) -> Dict[str, Any]:
    """
    Extract invoice data using GPT-5 Vision (via router) or structured parsing.

    GPT-5 has improved visual perception and 45% fewer hallucinations than GPT-4o,
    making it ideal for document extraction tasks.

    Supports:
    - PDF files (GPT-5 Vision)
    - Images: JPG, PNG (GPT-5 Vision)
    - Excel files: .xlsx, .xls (pandas parsing)
    - Word docs: .docx (python-docx parsing)

    With caching support
    """
    # Check cache first
    if cached := cache.get_invoice_data(file_path):
        return cached

    print(f"  📄 Extracting: {Path(file_path).name}")

    file_ext = Path(file_path).suffix.lower()

    try:
        import base64  # noqa: E402
        from io import BytesIO  # noqa: E402

        # Route to appropriate extraction method based on file type
        if file_ext == '.pdf':
            img_base64 = _extract_pdf_image(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            img_base64 = _extract_image(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return _extract_excel_invoice(file_path)
        elif file_ext == '.docx':
            return _extract_word_invoice(file_path)
        else:
            return {"error": f"Unsupported file format: {file_ext}"}

        if not img_base64:
            return {"error": "Failed to extract image from file"}

        # Use router for extraction task with vision (routes to GPT-5)
        prompt = """Extract invoice data and return JSON:
{
  "vendor_name": "Company Name",
  "invoice_number": "INV-123",
  "invoice_date": "2024-01-15",
  "total_amount": 100.00,
  "tax_amount": 10.00,
  "line_items": [
    {
      "description": "Product/service description",
      "amount": 100.00,
      "tax": 10.00
    }
  ]
}"""

        result = router.execute(
            task="extraction",
            prompt=prompt,
            stakes=0,
            images=[img_base64],  # Pass image for vision extraction
        )

        invoice_data = json.loads(result["content"])

        # Cache result
        cache.set_invoice_data(file_path, invoice_data)

        return invoice_data

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"error": str(e)}


def categorize_product(description: str, vendor_info: Optional[Dict] = None) -> str:
    """
    Categorize product based on description and vendor info
    """
    desc_lower = description.lower()

    # Check keywords
    if any(
        kw in desc_lower for kw in ["saas", "subscription", "cloud", "365", "workspace"]
    ):
        return "saas_subscription"
    elif any(
        kw in desc_lower
        for kw in ["consulting", "professional services", "advisory", "hours"]
    ):
        return "professional_services"
    elif any(
        kw in desc_lower
        for kw in ["ec2", "vm", "virtual machine", "infrastructure", "iaas"]
    ):
        return "iaas_paas"
    elif any(kw in desc_lower for kw in ["license", "software license"]):
        return "software_license"
    elif any(kw in desc_lower for kw in ["hardware", "equipment", "device"]):
        return "tangible_personal_property"
    else:
        return "other"


def search_legal_docs(category: str, state: str = "WA") -> List[Dict]:
    """
    Search legal documents for category using EnhancedRAG (with caching)

    Uses corrective RAG + reranking for higher quality results.
    """
    # Check cache
    if cached := cache.get_rag_results(category, state):
        return cached

    print(f"  📚 Searching legal docs for: {category}")

    try:
        # Create query based on category
        category_queries = {
            "saas_subscription": (
                "Washington tax law cloud services SaaS "
                "multi-point use digital products"
            ),
            "professional_services": (
                "Washington tax law professional services "
                "primarily human effort consulting"
            ),
            "iaas_paas": (
                "Washington tax law cloud infrastructure "
                "IaaS PaaS allocation"
            ),
            "software_license": (
                "Washington tax law software licenses prewritten custom"
            ),
            "tangible_personal_property": (
                "Washington tax tangible personal property exemptions"
            ),
        }

        query_text = category_queries.get(category, f"Washington tax law {category}")

        # Use Agentic RAG: Intelligently decides whether/how to retrieve
        # - Checks for cached results (high confidence) → USE_CACHED (10ms, $0)
        # - Checks for structured rules → USE_RULES (50ms, $0.01)
        # - Simple queries → RETRIEVE_SIMPLE (1.5s, $0.008)
        # - Complex queries → RETRIEVE_ENHANCED (8-12s, $0.010)
        # This saves 60-80% on repeated vendor analysis
        result = enhanced_rag.search_with_decision(
            query=query_text,
            context={
                "product_type": category,
            }
        )

        # Extract results from decision response
        legal_docs = result.get("results", [])

        # Log the decision made by agentic RAG
        action = result.get("action", "UNKNOWN")
        cost_saved = result.get("cost_saved", 0)
        confidence = result.get("confidence", 0)
        print(f"    🤖 Agentic RAG decision: {action} (confidence: {confidence:.2f}, saved: ${cost_saved:.4f})")

        # Cache results
        cache.set_rag_results(category, legal_docs, state)

        return legal_docs

    except Exception as e:
        print(f"  ⚠️  RAG search failed: {e}")
        return []


def analyze_batch(
    items: List[Dict], legal_context: Dict[str, List], state: str = "WA", tax_type: str = "sales_tax"
) -> List[Dict]:
    """
    Batch analyze multiple line items at once
    Now with historical pattern intelligence!
    """
    # Get unique vendors in this batch
    vendors_in_batch = list(set(item['vendor'] for item in items))

    # Query vendor patterns for this batch
    vendor_patterns = {}
    for vendor_name in vendors_in_batch:
        pattern = get_vendor_pattern(vendor_name, tax_type)
        if pattern:
            vendor_patterns[vendor_name] = pattern

    # Query top refund basis patterns for this tax type
    refund_basis_patterns = get_refund_basis_patterns(tax_type, limit=10)

    # Build prompt for batch analysis
    items_text = ""
    for i, item in enumerate(items, 1):
        vendor_info = item.get("vendor_info", {})
        line_item = item.get("line_item", {})
        category = item.get("category", "other")
        vendor_name = item['vendor']

        items_text += f"\n{i}. Vendor: {vendor_name}\n"
        items_text += f"   Product: {line_item.get('description', 'Unknown')}\n"
        items_text += f"   Amount: ${item['amount']:,.2f}\n"
        items_text += f"   Tax Charged: ${item['tax']:,.2f}\n"
        items_text += f"   Category: {category}\n"

        # Add vendor pattern info if available
        if vendor_name in vendor_patterns:
            vp = vendor_patterns[vendor_name]
            items_text += f"   📊 Historical Pattern: {vp.get('historical_sample_count', 0)} transactions, "
            items_text += f"typical refund: {vp.get('typical_refund_basis', 'Unknown')}\n"

        if vendor_info:
            items_text += (
                f"   Vendor Type: {vendor_info.get('business_model', 'Unknown')}\n"
            )

    # Build legal context
    legal_text = ""
    for category, docs in legal_context.items():
        if docs:
            legal_text += f"\n{category.upper()} - Relevant Laws:\n"
            for doc in docs[:3]:  # Top 3 per category
                doc_title = doc.get('document_title', 'Unknown')
                doc_citation = doc.get('citation', 'N/A')
                legal_text += f"  - {doc_title} ({doc_citation})\n"

    # Build pattern context
    pattern_text = ""
    if refund_basis_patterns:
        pattern_text += f"\nTOP REFUND BASIS PATTERNS ({tax_type.upper().replace('_', ' ')}):\n"
        for pattern in refund_basis_patterns[:5]:
            refund_basis = pattern.get('refund_basis', 'Unknown')
            usage_count = pattern.get('usage_count', 0)
            percentage = pattern.get('percentage', 0)
            pattern_text += f"  - {refund_basis}: {usage_count} uses ({percentage:.1f}%)\n"

    prompt = f"""You are a Washington State tax refund expert analyzing {tax_type.replace('_', ' ')} transactions.

Analyze these {len(items)} transactions for refund eligibility.

PRIMARY SOURCE - WASHINGTON TAX LAW (80-90% weight):
{legal_text}

SECONDARY SOURCE - HISTORICAL PATTERNS (10-20% weight):
{pattern_text}

DECISION HIERARCHY:
1. Base recommendations primarily on Washington State tax law (WAC/RCW)
2. Use historical patterns to:
   - Confirm your legal interpretation (high confidence when they align)
   - Flag potential inconsistencies (review needed when they conflict)
   - Provide context for vendor-specific behavior
3. If law and patterns conflict, law takes precedence (but note the discrepancy)
4. Always cite legal authority (WAC/RCW) when available

TRANSACTIONS:
{items_text}

For EACH transaction, analyze:
1. Product classification
2. Is it taxable in Washington?
3. Refund basis (MPU, Non-taxable, OOS Services, No Refund, etc.)
4. Legal citations
5. Confidence (0-100%)
6. Estimated refund amount
7. Brief explanation

Return JSON array:
{{
  "analyses": [
    {{
      "transaction_id": 1,
      "product_classification": "...",
      "is_taxable_in_wa": true/false,
      "refund_basis": "MPU" | "Non-taxable" | "OOS Services" | "No Refund",
      "legal_citations": ["WAC 458-20-15502"],
      "confidence_score": 85,
      "estimated_refund_amount": 4250.00,
      "refund_percentage": 85,
      "explanation": "..."
    }}
  ]
}}"""

    try:
        system_msg = """You are a Washington State tax refund expert analyzing invoices and purchase orders.

YOUR ANALYSIS MUST:
1. **Apply Washington State tax law** (WAC/RCW) as primary authority
2. **Reference historical patterns** for consistency and confidence
3. **Prioritize legal correctness** over historical precedent
4. **Flag discrepancies** when your analysis differs from typical patterns

KNOWLEDGE SOURCES:
- Tax Law Context: Legal citations and rules (PRIMARY - 80-90% weight)
- Historical Patterns: Vendor behavior, refund basis precedent (SECONDARY - 10-20% weight)

When analyzing each transaction:
- Determine legal taxability FIRST (based on WAC/RCW)
- Check historical patterns SECOND (for consistency)
- If they align: High confidence
- If they conflict: Flag for review, recommend legal answer

Provide accurate analysis with legal citations and confidence scores."""

        # Calculate stakes for this batch (sum of tax amounts)
        batch_stakes = sum(item.get('tax', 0) for item in items)

        # Use router for analysis task (routes to Claude Sonnet 4.5 for legal reasoning)
        # Claude excels at careful, methodical reasoning through complex tax rules
        # For high-stakes batches ($25k+), router automatically escalates to Claude Opus 4.5
        result = router.execute(
            task="analysis",
            prompt=prompt,
            system_prompt=system_msg,
            stakes=batch_stakes,
            temperature=0.2,
        )

        parsed = json.loads(result["content"])
        print(f"    📊 Model used: {result['model']} (stakes: ${batch_stakes:,.0f})")
        return parsed.get("analyses", [])

    except Exception as e:
        print(f"  ❌ Batch analysis error: {e}")
        return []


def get_rows_with_input_changes(file_id: str, hours_lookback: int = 24) -> set:
    """
    Query excel_cell_changes table to find rows where INPUT columns changed.

    This identifies rows that need re-analysis because new data was added
    (e.g., new invoice file, new PO, changed tax amount).

    OUTPUT column changes (like corrections to Analysis_Notes) are ignored
    since those are feedback, not new data requiring re-analysis.

    Args:
        file_id: UUID of the Excel file in excel_file_tracking
        hours_lookback: How far back to check for changes (default: 24 hours)

    Returns:
        Set of row indices that have INPUT column changes
    """
    from datetime import datetime, timedelta

    try:
        # Calculate cutoff time
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours_lookback)).isoformat()

        # Query recent cell changes for this file
        result = supabase.table('excel_cell_changes')\
            .select('row_index, column_name, old_value, new_value, changed_at')\
            .eq('file_id', file_id)\
            .gte('changed_at', cutoff_time)\
            .execute()

        if not result.data:
            return set()

        # Filter to INPUT column changes only
        rows_needing_reanalysis = set()
        input_changes_count = 0
        output_changes_count = 0

        for change in result.data:
            column_name = change['column_name']
            row_index = change['row_index']

            if is_input_column(column_name):
                rows_needing_reanalysis.add(row_index)
                input_changes_count += 1
            else:
                output_changes_count += 1

        print(f"  📊 Cell changes in last {hours_lookback} hours:")
        print(f"     INPUT columns (triggers re-analysis): {input_changes_count}")
        print(f"     OUTPUT columns (feedback only): {output_changes_count}")
        print(f"  📝 Rows needing re-analysis: {len(rows_needing_reanalysis)}")

        return rows_needing_reanalysis

    except Exception as e:
        print(f"  ⚠️  Could not check excel_cell_changes: {e}")
        print(f"     Falling back to standard change detection")
        return set()


def main():
    parser = argparse.ArgumentParser(description="Fast Batch Refund Analyzer")
    parser.add_argument("--excel", required=True, help="Path to Excel file")
    parser.add_argument(
        "--state",
        default="washington",
        help="State to analyze for (default: washington)",
    )
    parser.add_argument(
        "--tax-type",
        choices=["sales_tax", "use_tax"],
        default="sales_tax",
        help="Tax type: sales_tax or use_tax (default: sales_tax)",
    )
    parser.add_argument("--limit", type=int, help="Limit to first N rows (testing)")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    print("🚀 FAST BATCH REFUND ANALYZER")
    print("=" * 70)
    print(f"Excel: {args.excel}")
    print(f"State: {args.state.upper()}")
    print(f"Tax Type: {args.tax_type.replace('_', ' ').title()}")
    print("=" * 70)

    # Load Excel
    print("\n📂 Loading Excel...")
    df = pd.read_excel(args.excel)
    original_row_count = len(df)

    # Initialize ExcelFileWatcher for intelligent row tracking
    print("\n🔍 Checking for changes...")

    # Try to find file_id from versioning system first
    file_id = None
    try:
        # Check if this file is tracked in the versioning system
        abs_path = str(Path(args.excel).resolve())
        result = supabase.table('excel_file_tracking')\
            .select('id')\
            .or_(f'file_path.eq.{abs_path},file_name.eq.{Path(args.excel).name}')\
            .limit(1)\
            .execute()

        if result.data:
            file_id = result.data[0]['id']
            print(f"  ✓ Found file in versioning system (ID: {file_id[:8]}...)")
    except Exception as e:
        print(f"  ⚠️  Could not check versioning system: {e}")

    # Get changed rows (new or modified rows only)
    if not args.limit:
        # Option 1: Use versioning system if available (more intelligent)
        if file_id:
            print(f"  🔍 Checking INPUT column changes (versioning-aware)...")
            rows_with_input_changes = get_rows_with_input_changes(file_id, hours_lookback=72)

            if rows_with_input_changes:
                # Filter DataFrame to only rows with INPUT column changes
                df = df.loc[df.index.isin(rows_with_input_changes)]
                print(f"✓ Found {len(df)} rows with INPUT column changes out of {original_row_count} total")
                print(f"  Skipping {original_row_count - len(df)} rows (no INPUT changes)")
            else:
                print("✓ No INPUT column changes detected!")
                print("  💡 OUTPUT column changes (corrections) don't trigger re-analysis")
                print("  💡 Use --limit flag to force re-analysis for testing")
                sys.exit(0)

        # Option 2: Fallback to row-level hash checking (less intelligent)
        else:
            print(f"  🔍 Checking row-level changes (hash-based)...")
            watcher = ExcelFileWatcher()
            changed_rows = watcher.get_changed_rows(args.excel, df)

            if changed_rows:
                changed_indices = [idx for idx, _, _ in changed_rows]
                df = df.loc[changed_indices]
                print(f"✓ Found {len(changed_rows)} changed/new rows out of {original_row_count} total")
                print(f"  Skipping {original_row_count - len(changed_rows)} already-analyzed rows")
            else:
                print("✓ No changes detected - all rows already analyzed!")
                print("\n💡 Tip: Use --limit flag to force re-analysis for testing")
                sys.exit(0)
    else:
        df = df.head(args.limit)
        print(f"✓ Test mode: Processing first {args.limit} rows (change tracking disabled)")

    print(f"✓ Analyzing {len(df)} rows")

    # Get unique invoices
    invoice_files = df["Inv_1_File"].dropna().unique()
    print(f"\n📄 Found {len(invoice_files)} unique invoices")

    # Extract invoices
    print("\n📄 Extracting invoices...")
    invoice_data = {}
    for inv_file in tqdm(invoice_files, desc="Extracting"):
        file_path = Path("client_documents/invoices") / inv_file
        if file_path.exists():
            invoice_data[inv_file] = extract_invoice_with_vision(str(file_path))

    # Prepare analysis queue with skip tracking
    print("\n🔍 Matching line items...")
    analysis_queue = []
    skipped_rows = {
        "no_invoice_file": [],
        "extraction_failed": [],
        "no_line_item_match": [],
    }

    for idx, row in df.iterrows():
        inv_file = row.get("Inv_1_File")
        if pd.isna(inv_file):
            skipped_rows["no_invoice_file"].append(idx)
            continue

        if inv_file not in invoice_data:
            skipped_rows["no_invoice_file"].append(idx)
            continue

        inv_data = invoice_data[inv_file]
        if "error" in inv_data:
            skipped_rows["extraction_failed"].append(
                (idx, inv_data.get("error", "Unknown error"))
            )
            continue

        # Match line item by amount
        amount = row.get("Amount", 0)
        line_items = inv_data.get("line_items", [])

        matched_item = None
        for item in line_items:
            if abs(item.get("amount", 0) - amount) < 1.0:
                matched_item = item
                break

        if matched_item:
            vendor = row.get("Vendor", "Unknown")
            vendor_info = cache.get_vendor_info(vendor)
            category = categorize_product(
                matched_item.get("description", ""), vendor_info
            )

            analysis_queue.append(
                {
                    "excel_row_idx": idx,
                    "vendor": vendor,
                    "vendor_info": vendor_info or {},
                    "line_item": matched_item,
                    "amount": amount,
                    "tax": row.get("Tax", 0),
                    "category": category,
                }
            )
        else:
            skipped_rows["no_line_item_match"].append((idx, amount))

    # Report matching results
    total_rows = len(df)
    total_skipped = sum(
        (
            len(v)
            if isinstance(v, list) and not isinstance(v[0] if v else None, tuple)
            else len(v)
        )
        for v in skipped_rows.values()
    )

    print("\n📊 MATCHING SUMMARY:")
    print(f"   Total rows: {total_rows}")
    print(f"   ✓ Matched: {len(analysis_queue)}")
    print(f"   ✗ Skipped: {total_skipped}")

    if total_skipped > 0:
        print("\n⚠️  SKIPPED ROWS BREAKDOWN:")
        if skipped_rows["no_invoice_file"]:
            no_inv_count = len(skipped_rows['no_invoice_file'])
            print(f"   • No invoice file: {no_inv_count} rows")
            if no_inv_count <= 10:
                print(f"     Rows: {skipped_rows['no_invoice_file']}")
        if skipped_rows["extraction_failed"]:
            extract_fail_count = len(skipped_rows['extraction_failed'])
            print(
                "   • Invoice extraction failed: "
                f"{extract_fail_count} rows"
            )
            if extract_fail_count <= 5:
                for idx, error in skipped_rows["extraction_failed"]:
                    print(f"     Row {idx}: {error}")
        if skipped_rows["no_line_item_match"]:
            no_match_count = len(skipped_rows['no_line_item_match'])
            print(f"   • No line item match: {no_match_count} rows")
            if no_match_count <= 10:
                for idx, amount in skipped_rows["no_line_item_match"]:
                    print(f"     Row {idx}: ${amount:,.2f}")

    if total_skipped > len(analysis_queue):
        analyzed_count = len(analysis_queue)
        print(
            f"\n🚨 WARNING: More rows skipped ({total_skipped}) "
            f"than analyzed ({analyzed_count})!"
        )
        print("   You may want to review your invoice files and data.")

    if len(analysis_queue) == 0:
        print("\n❌ ERROR: No rows matched for analysis!")
        print("   Check that your invoice files exist and amounts match.")
        sys.exit(1)

    # Get unique categories and search legal docs
    print("\n📚 Researching legal context...")
    categories = set(item["category"] for item in analysis_queue)
    legal_context = {}

    for category in categories:
        legal_context[category] = search_legal_docs(category, args.state.upper())

    # Batch analysis
    print(f"\n🤖 Analyzing {len(analysis_queue)} items...")
    batch_size = 20
    all_analyses = []

    for i in range(0, len(analysis_queue), batch_size):
        batch = analysis_queue[i: i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(analysis_queue) - 1) // batch_size + 1
        print(f"  Batch {batch_num}/{total_batches}")

        analyses = analyze_batch(batch, legal_context, args.state.upper(), args.tax_type)
        all_analyses.extend(analyses)

    # Write results back to DataFrame
    print("\n📝 Writing results...")

    # Validate analysis count
    if len(all_analyses) != len(analysis_queue):
        analyses_count = len(all_analyses)
        queue_count = len(analysis_queue)
        print(
            f"⚠️  WARNING: Got {analyses_count} analyses "
            f"for {queue_count} items"
        )
        print("   Some results may be missing or duplicated!")

    # Create mapping by transaction_id for safe alignment
    analysis_map = {}
    for analysis in all_analyses:
        tid = analysis.get("transaction_id")
        if tid is not None:
            analysis_map[tid] = analysis

    # Write results using transaction_id matching
    matched_count = 0
    for i, queue_item in enumerate(analysis_queue):
        # Try to match by transaction_id (1-indexed in the prompt)
        transaction_id = i + 1
        analysis = analysis_map.get(transaction_id)

        if analysis is None:
            row_idx = queue_item['excel_row_idx']
            print(
                "⚠️  No analysis found for transaction "
                f"{transaction_id} (row {row_idx})"
            )
            continue

        idx = queue_item["excel_row_idx"]
        line_item = queue_item["line_item"]

        df.loc[idx, "Product_Desc"] = line_item.get("description", "")
        df.loc[idx, "Product_Type"] = analysis.get("product_classification", "")
        df.loc[idx, "Refund_Basis"] = analysis.get("refund_basis", "")
        df.loc[idx, "Citation"] = ", ".join(analysis.get("legal_citations", []))
        df.loc[idx, "Confidence"] = f"{analysis.get('confidence_score', 0)}%"
        df.loc[idx, "Estimated_Refund"] = (
            f"${analysis.get('estimated_refund_amount', 0):,.2f}"
        )
        df.loc[idx, "Explanation"] = analysis.get("explanation", "")
        matched_count += 1

    if matched_count < len(analysis_queue):
        queue_count = len(analysis_queue)
        print(
            f"⚠️  Only matched {matched_count}/{queue_count} items - "
            "some rows may be incomplete!"
        )

    # Save output
    if not args.output:
        base_name = Path(args.excel).stem
        args.output = str(Path(args.excel).parent / f"{base_name} - Analyzed.xlsx")

    df.to_excel(args.output, index=False)

    # Update tracking database if not in test mode
    if not args.limit:
        print("\n📊 Updating tracking database...")
        watcher.update_file_tracking(args.excel)

        # Update row tracking for successfully analyzed rows
        for i, queue_item in enumerate(analysis_queue):
            if i < matched_count:  # Only update successfully analyzed rows
                idx = queue_item["excel_row_idx"]
                if idx in df.index:
                    row_data = df.loc[idx].to_dict()
                    watcher.update_row_tracking(args.excel, idx, row_data)

        print("✓ Tracking database updated")

    print("\n✅ ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"Output: {args.output}")
    print("\n📊 FINAL SUMMARY:")
    print(f"   Total rows in Excel: {total_rows}")
    print(f"   ✓ Analyzed successfully: {matched_count}")
    print(f"   ✗ Skipped: {total_skipped}")
    if total_skipped > 0:
        coverage_pct = (matched_count / total_rows * 100) if total_rows > 0 else 0
        print(f"   Coverage: {coverage_pct:.1f}%")
        if coverage_pct < 80:
            print(
                "\n⚠️  Low coverage! "
                "Review skipped rows above to improve results."
            )
    print("\n💡 Open the Excel file to review results!")


if __name__ == "__main__":
    main()
