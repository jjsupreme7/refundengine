"""
Fast Batch Refund Analyzer

Ultra-fast invoice analysis using:
- Smart caching (vendor DB, invoice extraction, RAG results)
- Batch AI analysis (20 items per API call)
- Async processing where possible
- State-aware legal research

Usage:
    python scripts/5_fast_batch_analyzer.py --excel "Master Refunds.xlsx" --state washington
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client
from scripts.utils.smart_cache import SmartCache

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Initialize cache
cache = SmartCache()


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
        import pdfplumber
        from PIL import Image
        import base64
        from io import BytesIO

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
    Search legal documents for category (with caching)
    """
    # Check cache
    if cached := cache.get_rag_results(category, state):
        return cached

    print(f"  📚 Searching legal docs for: {category}")

    try:
        # Create query based on category
        category_queries = {
            "saas_subscription": "Washington tax law cloud services SaaS multi-point use digital products",
            "professional_services": "Washington tax law professional services primarily human effort consulting",
            "iaas_paas": "Washington tax law cloud infrastructure IaaS PaaS allocation",
            "software_license": "Washington tax law software licenses prewritten custom",
            "tangible_personal_property": "Washington tax tangible personal property exemptions",
        }

        query_text = category_queries.get(category, f"Washington tax law {category}")

        # Get embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002", input=query_text
        )
        query_embedding = response.data[0].embedding

        # Search Supabase (state-aware)
        results = supabase.rpc(
            "match_documents_by_state",
            {
                "query_embedding": query_embedding,
                "target_state": state,
                "match_threshold": 0.7,
                "match_count": 10,
            },
        ).execute()

        legal_docs = results.data or []

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
    # Load state tax rules
    tax_rules_path = Path(f"knowledge_base/states/{state.lower()}/tax_rules.json")
    if tax_rules_path.exists():
        with open(tax_rules_path, "r") as f:
            tax_rules = json.load(f)
    else:
        tax_rules = {}

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
                legal_text += f"  - {doc.get('document_title', 'Unknown')} ({doc.get('citation', 'N/A')})\n"

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
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Washington State tax expert. Provide accurate analysis with legal citations.",
                },
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
    if args.limit:
        df = df.head(args.limit)
    print(f"✓ Loaded {len(df)} rows")

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

    # Prepare analysis queue
    print("\n🔍 Matching line items...")
    analysis_queue = []

    for idx, row in df.iterrows():
        inv_file = row.get("Inv_1_File")
        if pd.isna(inv_file) or inv_file not in invoice_data:
            continue

        inv_data = invoice_data[inv_file]
        if "error" in inv_data:
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

    print(f"✓ Matched {len(analysis_queue)} line items")

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
        batch = analysis_queue[i : i + batch_size]
        print(f"  Batch {i//batch_size + 1}/{(len(analysis_queue)-1)//batch_size + 1}")

        analyses = analyze_batch(batch, legal_context, args.state.upper())
        all_analyses.extend(analyses)

    # Write results back to DataFrame
    print("\n📝 Writing results...")
    for i, analysis in enumerate(all_analyses):
        if i < len(analysis_queue):
            idx = analysis_queue[i]["excel_row_idx"]
            line_item = analysis_queue[i]["line_item"]

            df.loc[idx, "Product_Desc"] = line_item.get("description", "")
            df.loc[idx, "Product_Type"] = analysis.get("product_classification", "")
            df.loc[idx, "Refund_Basis"] = analysis.get("refund_basis", "")
            df.loc[idx, "Citation"] = ", ".join(analysis.get("legal_citations", []))
            df.loc[idx, "Confidence"] = f"{analysis.get('confidence_score', 0)}%"
            df.loc[idx, "Estimated_Refund"] = (
                f"${analysis.get('estimated_refund_amount', 0):,.2f}"
            )
            df.loc[idx, "Explanation"] = analysis.get("explanation", "")

    # Save output
    if not args.output:
        base_name = Path(args.excel).stem
        args.output = str(Path(args.excel).parent / f"{base_name} - Analyzed.xlsx")

    df.to_excel(args.output, index=False)

    print("\n✅ ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"Output: {args.output}")
    print(f"Analyzed: {len(all_analyses)} items")
    print("\n💡 Open the Excel file to review results!")


if __name__ == "__main__":
    main()
