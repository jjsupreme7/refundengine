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
from scripts.utils.smart_cache import SmartCache  # noqa: E402

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()

# Initialize cache
cache = SmartCache()

# Initialize EnhancedRAG
enhanced_rag = EnhancedRAG()


def extract_invoice_with_vision(file_path: str) -> Dict[str, Any]:
    """
    Extract invoice data using GPT-4 Vision
    With caching support
    """
    # Check cache first
    if cached := cache.get_invoice_data(file_path):
        return cached

    print(f"  📄 Extracting: {Path(file_path).name}")

    try:
        import base64  # noqa: E402
        from io import BytesIO  # noqa: E402

        import pdfplumber  # noqa: E402

        # Convert first page to image
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                return {"error": "Empty PDF"}

            first_page = pdf.pages[0]
            img = first_page.to_image(resolution=150)

            # Convert to base64
            buffered = BytesIO()
            img.original.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # GPT-4 Vision extraction
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract invoice data and return JSON:
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
}""",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
        )

        invoice_data = json.loads(response.choices[0].message.content)

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
    items: List[Dict], legal_context: Dict[str, List], state: str = "WA"
) -> List[Dict]:
    """
    Batch analyze multiple line items at once
    """
    # Build prompt for batch analysis
    items_text = ""
    for i, item in enumerate(items, 1):
        vendor_info = item.get("vendor_info", {})
        line_item = item.get("line_item", {})
        category = item.get("category", "other")

        items_text += f"\n{i}. Vendor: {item['vendor']}\n"
        items_text += f"   Product: {line_item.get('description', 'Unknown')}\n"
        items_text += f"   Amount: ${item['amount']:,.2f}\n"
        items_text += f"   Tax Charged: ${item['tax']:,.2f}\n"
        items_text += f"   Category: {category}\n"
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

    prompt = f"""You are a Washington State tax refund expert.

Analyze these {len(items)} transactions for refund eligibility.

WASHINGTON TAX LAW CONTEXT:
{legal_text}

STATE TAX RULES:
- SaaS/Cloud services: Taxable but may qualify for MPU (multi-point use) allocation
- Professional services: Not taxable if "primarily human effort"
- Hardware: Taxable unless shipped out-of-state or other exemptions apply

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
        system_msg = (
            "You are a Washington State tax expert. "
            "Provide accurate analysis with legal citations."
        )
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("analyses", [])

    except Exception as e:
        print(f"  ❌ Batch analysis error: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Fast Batch Refund Analyzer")
    parser.add_argument("--excel", required=True, help="Path to Excel file")
    parser.add_argument(
        "--state",
        default="washington",
        help="State to analyze for (default: washington)",
    )
    parser.add_argument("--limit", type=int, help="Limit to first N rows (testing)")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    print("🚀 FAST BATCH REFUND ANALYZER")
    print("=" * 70)
    print(f"Excel: {args.excel}")
    print(f"State: {args.state.upper()}")
    print("=" * 70)

    # Load Excel
    print("\n📂 Loading Excel...")
    df = pd.read_excel(args.excel)
    original_row_count = len(df)

    # Initialize ExcelFileWatcher for intelligent row tracking
    print("\n🔍 Checking for changes...")
    watcher = ExcelFileWatcher()

    # Get changed rows (new or modified rows only)
    if not args.limit:
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

        analyses = analyze_batch(batch, legal_context, args.state.upper())
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
