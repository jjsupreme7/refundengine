#!/usr/bin/env python3
"""
Enhanced Refund Analysis Script with Improved RAG
Integrates Corrective RAG, Reranking, Query Expansion, and Hybrid Search
"""

from core.enhanced_rag import EnhancedRAG
from core.database import get_supabase_client
from openai import OpenAI
import PyPDF2
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import centralized database client

# Import enhanced RAG

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()


class EnhancedRefundAnalyzer:
    """
    Refund Analyzer with Enhanced RAG capabilities

    Improvements over basic version:
    - Corrective RAG for legal citation validation
    - Reranking for better legal relevance
    - Query expansion with tax terminology
    - Hybrid search (vector + keyword)
    """

    def __init__(
        self, docs_folder: str = "client_docs", enable_dynamic_models: bool = True
    ):
        self.docs_folder = Path(docs_folder)
        self.embedding_model = "text-embedding-3-small"
        self.analysis_model = "gpt-4o"

        # Initialize Enhanced RAG with dynamic model selection
        self.rag = EnhancedRAG(supabase, enable_dynamic_models=enable_dynamic_models)

        print("✅ Enhanced Refund Analyzer initialized")
        print("   - Corrective RAG: ON")
        print("   - Reranking: ON")
        print("   - Query Expansion: ON")
        print("   - Hybrid Search: ON")
        if enable_dynamic_models:
            print("   - Dynamic Model Selection: ON")
            print(
                f"     • High stakes (>${
                    self.rag.stakes_threshold_high:,                }): Claude Sonnet 4.5"
            )
            print(
                f"     • Medium stakes (${
                    self.rag.stakes_threshold_medium:,}-${self.rag.stakes_threshold_high:,}): GPT-4o"
            )
            print(
                f"     • Low stakes (<${
                    self.rag.stakes_threshold_medium:,}): gpt-4o-mini"
            )
        else:
            print("   - Dynamic Model Selection: OFF")
        print()

    # ==================== PDF & EXTRACTION ====================

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def find_line_item_in_invoice(
        self, invoice_text: str, amount: float, tax: float
    ) -> Dict:
        """Use AI to find the specific line item in invoice text"""
        prompt = """You are analyzing an invoice to find a specific line item.

Invoice Text:
{invoice_text[:4000]}

Find the line item with:
- Amount: ${amount:,.2f}
- Tax: ${tax:,.2f}

Extract:
1. Product/Service Description
2. Product Type/Category
3. Any relevant details (model, SKU, quantity, etc.)

Return JSON:
{{
    "product_desc": "exact description from invoice",
    "product_type": "category (e.g., Hardware, Software, Services)",
    "details": "additional details",
    "line_item_found": true/false,
    "confidence": 0-100
}}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error extracting line item: {e}")
            return {
                "product_desc": "Unknown",
                "product_type": "Unknown",
                "details": "",
                "line_item_found": False,
                "confidence": 0,
            }

    # ==================== VENDOR LEARNING ====================

    def check_vendor_learning(
        self, vendor_name: str, product_desc: str
    ) -> Optional[Dict]:
        """Check if we've seen this vendor/product before and learned anything"""
        try:
            # Check vendor_products table
            response = (
                supabase.table("vendor_products")
                .select("*")
                .eq("vendor_name", vendor_name)
                .ilike("product_description", f"%{product_desc[:50]}%")
                .execute()
            )

            if response.data:
                return response.data[0]

            # Check vendor_product_patterns
            response = (
                supabase.table("vendor_product_patterns")
                .select("*")
                .eq("vendor_name", vendor_name)
                .eq("is_active", True)
                .execute()
            )

            if response.data:
                for pattern in response.data:
                    if pattern["product_keyword"].lower() in product_desc.lower():
                        return pattern

            return None
        except Exception as e:
            print(f"Error checking vendor learning: {e}")
            return None

    # ==================== ENHANCED REFUND ANALYSIS ====================

    def analyze_refund_eligibility(
        self,
        vendor: str,
        product_desc: str,
        product_type: str,
        amount: float,
        tax: float,
        invoice_text: str = "",
        po_text: str = "",
        rag_method: str = "agentic",
        # agentic (RECOMMENDED), enhanced, basic, corrective, reranking, expansion, hybrid
    ) -> Dict:
        """
        Main analysis: Determine if tax refund is eligible
        Uses Enhanced RAG with selectable method

        Args:
            rag_method: Which RAG method to use
                - "agentic": Intelligent decision layer (RECOMMENDED) - auto-decides cache/rules/retrieval
                - "enhanced": All RAG improvements - always retrieves with full validation
                - "basic": Standard vector search
                - "corrective": With validation/correction
                - "reranking": With AI reranking
                - "expansion": With query expansion
                - "hybrid": Vector + keyword search
        """

        print(f"\n{'=' * 80}")
        print("Analyzing Refund Eligibility")
        print(f"Vendor: {vendor}")
        print(f"Product: {product_desc[:100]}")
        print(f"RAG Method: {rag_method.upper()}")
        print(f"{'=' * 80}\n")

        # Check if we've learned about this vendor/product
        learned_info = self.check_vendor_learning(vendor, product_desc)

        if learned_info:
            print(f"💡 Found prior learning for {vendor}")

        # Build query for legal knowledge base
        query = """
Vendor: {vendor}
Product: {product_desc}
Product Type: {product_type}
Amount: ${amount:,.2f}
Tax Paid: ${tax:,.2f}

Determine if Washington State use tax refund is eligible.
Consider:
- Multi-point use (MPU) allocation
- Professional services exemption
- Digital automated services rules
- Manufacturing exemptions
- Out-of-state delivery

IMPORTANT - Check for common errors:
1. DOUBLE-CHARGING: Was sales tax charged (invoice total not round) AND use tax accrued?
   → If in-state vendor charged sales tax, use tax should NOT be accrued (100% refund of use tax)
2. WRONG JURISDICTION RATE: Does tax rate match service/ship-to location for the invoice date?
   → Check if location indicators (city, site IDs, facility codes) suggest different jurisdiction
3. CONSTRUCTION RETAINAGE (WA): Is this construction with retainage billing?
   → WA requires tax on full contract amount upfront, not progressive billing
"""

        # Use Agentic RAG decision layer for intelligent retrieval
        # This will automatically decide whether to use cached results, structured rules,
        # or perform actual retrieval based on context and confidence
        if rag_method == "agentic":
            print("\n🤖 Using Agentic RAG (intelligent decision-making)...\n")

            # Assess query complexity for dynamic model selection
            complexity = self.rag._assess_query_complexity(query, {})

            # Build context for decision-making (includes stakes for dynamic models)
            context = {
                "vendor": vendor,
                "product": product_desc,
                "product_type": product_type,
                "amount": amount,
                "tax_paid": tax,
                "complexity": complexity,  # For stakes calculation
                "prior_analysis": learned_info if learned_info else None,
            }

            # Let the agent decide how to retrieve
            decision_result = self.rag.search_with_decision(
                query, context=context, top_k=5
            )

            # Extract results and add decision metadata
            legal_chunks = decision_result.get("results", [])
            decision_action = decision_result.get("action", "UNKNOWN")
            decision_confidence = decision_result.get("confidence", 0.0)
            cost_saved = decision_result.get("cost_saved", 0.0)

            print(f"\n✅ Decision: {decision_action}")
            print(f"   Confidence: {decision_confidence:.2f}")
            print(f"   Cost Saved: ${cost_saved:.4f}")
            print(f"   Retrieved {len(legal_chunks)} chunks\n")

        else:
            # Traditional RAG methods (backward compatibility)
            print(f"\n🔍 Searching legal knowledge base ({rag_method} method)...\n")

            if rag_method == "basic":
                legal_chunks = self.rag.basic_search(query, top_k=5)
            elif rag_method == "corrective":
                legal_chunks = self.rag.search_with_correction(query, top_k=5)
            elif rag_method == "reranking":
                legal_chunks = self.rag.search_with_reranking(query, top_k=5)
            elif rag_method == "expansion":
                legal_chunks = self.rag.search_with_expansion(query, top_k=5)
            elif rag_method == "hybrid":
                legal_chunks = self.rag.search_hybrid(query, top_k=5)
            else:  # enhanced (default)
                legal_chunks = self.rag.search_enhanced(
                    query, top_k=5, vendor_name=vendor
                )

            print(f"\n✅ Retrieved {len(legal_chunks)} legal chunks\n")

        # Build context from legal knowledge
        legal_context = self._build_legal_context(legal_chunks)

        # Build context from vendor learning
        learning_context = ""
        if learned_info:
            learning_context = """
PRIOR LEARNING:
This vendor/product has been analyzed before:
- Product Type: {learned_info.get('product_type', 'N/A')}
- Tax Treatment: {learned_info.get('tax_treatment', 'N/A')}
- Confidence: {learned_info.get('confidence_score', 'N/A')}
"""

        # Extract vendor background from legal chunks if available
        vendor_background_context = ""
        if legal_chunks and len(legal_chunks) > 0:
            first_chunk = legal_chunks[0]
            if "vendor_background" in first_chunk and first_chunk["vendor_background"]:
                vb = first_chunk["vendor_background"]
                products_str = (
                    ", ".join(vb.get("primary_products", [])[:3])
                    if vb.get("primary_products")
                    else "N/A"
                )
                vendor_background_context = """
VENDOR BACKGROUND:
Understanding the vendor's business helps interpret ambiguous descriptions:
- Company: {vb.get('vendor_name', vendor)}
- Industry: {vb.get('industry', 'Unknown')}
- Business Model: {vb.get('business_model', 'Unknown')}
- Primary Offerings: {products_str}
- Research Confidence: {vb.get('confidence_score', 0)}%

Context: This vendor typically provides services/products in the {vb.get('industry', 'technology')} sector.
Understanding their typical offerings helps determine if this transaction matches their standard
patterns (e.g., custom development vs. licenses, professional services vs. tangible goods).
"""

        # Build comprehensive analysis prompt
        analysis_prompt = """You are a Washington State tax law expert analyzing use tax refund eligibility.

TRANSACTION DETAILS:
- Vendor: {vendor}
- Product: {product_desc}
- Product Type: {product_type}
- Amount: ${amount:,.2f}
- Tax Paid: ${tax:,.2f}

{vendor_background_context}

{learning_context}

RELEVANT LEGAL CONTEXT:
{legal_context}

ANALYSIS REQUIRED:

1. **Taxability**: Is this product/service subject to Washington use tax?

2. **Exemptions/Exclusions**: Does any exemption or exclusion apply?
   - Professional services (primarily human effort)
   - Manufacturing equipment
   - Resale
   - Agricultural use
   - Other exemptions

3. **Multi-Point Use (MPU)**: If taxable, should tax be allocated based on usage location?
   - Is this used in multiple states?
   - What allocation methodology applies?

4. **Refund Eligibility**: Can a refund be claimed?
   - If yes, what is the refund basis?
   - What percentage/amount should be refunded?

5. **COMMON TAX ERRORS** - Check for these specific scenarios:

   a) **Double-Charging (Sales + Use Tax)**:
      - Does invoice total suggest sales tax was charged (not a round number)?
      - Is vendor in-state (same state as buyer)?
      - If YES to both: Use tax should NOT be accrued (sales tax already collected)
      - Refund opportunity: 100% of use tax if double-charged

   b) **Wrong Jurisdiction Rate**:
      - Does the tax rate match the service location or ship-to address?
      - Look for location indicators: city, county, site IDs, facility codes
      - Check if rate is appropriate for invoice date (rates change by year/quarter)
      - Refund opportunity: Difference between charged rate and correct rate

   c) **Construction Retainage** (Washington specific):
      - Is this construction industry with retainage/percentage completion billing?
      - WA law requires tax on FULL contract amount upfront, not progressive
      - Check if vendor charged tax progressively (wrong) vs. upfront full amount (correct)
      - Risk: Potential underpayment (not refund), or overcharge if wrong rate used

6. **Legal Citations**: Which RCW/WAC sections apply?

7. **Confidence**: How confident are you in this analysis (0-100)?

8. **Information Gaps**: Identify specific information needed to improve confidence or determine refund eligibility

   CRITICAL: If confidence < 70% OR refund eligibility is uncertain, you MUST identify information gaps.

   For each gap, specify:
   - **Category**: SERVICE_LOCATION|MPU_USERS|DELIVERY_ADDRESS|CUSTOM_VS_PREWRITTEN|VENDOR_STATE|CONTRACT_TERMS|OTHER
   - **Description**: What specific information is missing (be specific!)
   - **Impact**: How this affects the refund determination
   - **Refund Potential**: HIGH (>$5K potential)|MEDIUM ($1K-$5K)|LOW (<$1K) if information found
   - **Example Query**: Specific question to ask the client

   Common scenarios requiring additional information:
   - **Out-of-state services**: Need service location (construction, installation performed where?)
   - **MPU allocation**: Need user distribution, usage data by location, equipment locations
   - **Custom vs. prewritten software**: Need SOW, contract terms, uniqueness of deliverable
   - **Wrong jurisdiction rate**: Need delivery address, facility codes, project site locations
   - **Professional services classification**: Need to verify "primarily human effort" vs. automated
   - **Vendor location**: If vendor state unknown, affects sales/use tax determination

9. **Next Steps**: Quick action items based on current information

Return JSON:
{{
    "is_taxable": true/false,
    "refund_eligible": "YES|NO|UNCERTAIN",
    "refund_basis": "MPU|Non-taxable|Exemption|OOS Delivery|Double-Charge|Wrong-Rate|None",
    "refund_percentage": 0-100,
    "estimated_refund": dollar amount,
    "primary_citation": "RCW/WAC",
    "supporting_citations": ["citation1", "citation2"],
    "mpu_required": true/false,
    "allocation_method": "User location|Equipment location|N/A",
    "confidence": 0-100,
    "reasoning": "detailed explanation",
    "information_needed": {{
        "has_gaps": true/false,
        "gap_severity": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
        "gaps": [
            {{
                "category": "SERVICE_LOCATION|MPU_USERS|DELIVERY_ADDRESS|CUSTOM_VS_PREWRITTEN|VENDOR_STATE|CONTRACT_TERMS|OTHER",
                "description": "specific information missing",
                "impact": "how this affects refund determination",
                "refund_potential_if_found": "HIGH|MEDIUM|LOW",
                "example_query": "exact question to ask client"
            }}
        ]
    }},
    "next_steps": ["action1", "action2"],
    "common_errors_detected": {{
        "double_charging": {{
            "detected": true/false,
            "explanation": "If detected, explain why",
            "refund_amount": dollar amount
        }},
        "wrong_jurisdiction": {{
            "detected": true/false,
            "expected_rate": percentage,
            "actual_rate": percentage,
            "location_indicators": ["city", "site_id", etc],
            "refund_or_risk": "refund|underpayment"
        }},
        "construction_retainage": {{
            "detected": true/false,
            "issue": "progressive_billing|correct_upfront|unclear"
        }}
    }}
}}
"""

        # Get AI analysis
        print("🤖 Running AI analysis...\n")

        try:
            response = client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": analysis_prompt}],
                response_format={"type": "json_object"},
            )

            analysis_result = json.loads(response.choices[0].message.content)

            # Add metadata
            analysis_result["rag_method"] = rag_method
            analysis_result["legal_chunks_found"] = len(legal_chunks)
            analysis_result["vendor_learning_used"] = learned_info is not None

            # Add chunk details for transparency
            analysis_result["legal_sources"] = [
                {
                    "citation": chunk.get("citation", "N/A"),
                    "relevance_score": chunk.get("relevance_score"),
                    "preview": chunk.get("chunk_text", "")[:200],
                }
                for chunk in legal_chunks
            ]

            print("✅ Analysis complete!")
            print(f"   Refund Eligible: {analysis_result.get('refund_eligible')}")
            print(f"   Refund Basis: {analysis_result.get('refund_basis')}")
            print(f"   Confidence: {analysis_result.get('confidence')}%")
            print(f"{'=' * 80}\n")

            return analysis_result

        except Exception as e:
            print(f"❌ Error in analysis: {e}")
            return {"error": str(e), "refund_eligible": False, "confidence": 0}

    def _build_legal_context(self, chunks: List[Dict]) -> str:
        """Build formatted legal context from chunks"""
        if not chunks:
            return "No relevant legal documents found."

        context = ""
        for i, chunk in enumerate(chunks):
            citation = chunk.get("citation", "N/A")
            text = chunk.get("chunk_text", "")
            relevance = chunk.get("relevance_score", "N/A")

            context += f"\n[Source {i + 1}] {citation}"
            if relevance != "N/A":
                context += f" (Relevance: {relevance:.2f})"
            context += f"\n{text[:800]}\n"

        return context

    # ==================== COMPARISON & TESTING ====================

    def compare_rag_methods(
        self,
        vendor: str,
        product_desc: str,
        product_type: str,
        amount: float,
        tax: float,
    ) -> Dict:
        """
        Compare all RAG methods side-by-side for the same query
        Useful for testing which method works best
        """

        query = """
Vendor: {vendor}
Product: {product_desc}
Product Type: {product_type}
Amount: ${amount:,.2f}
Tax Paid: ${tax:,.2f}

Determine if Washington State use tax refund is eligible.
"""

        print(f"\n{'=' * 80}")
        print("📊 COMPARING ALL RAG METHODS")
        print(f"Vendor: {vendor}")
        print(f"Product: {product_desc[:100]}")
        print(f"{'=' * 80}\n")

        # Use the RAG comparison method
        rag_results = self.rag.compare_methods(query, top_k=5)

        # Summarize comparison
        summary = {"query": query, "methods_compared": len(rag_results), "results": {}}

        for method, chunks in rag_results.items():
            summary["results"][method] = {
                "chunks_found": len(chunks),
                "citations": [c.get("citation", "N/A") for c in chunks[:3]],
                "avg_relevance": (
                    sum(c.get("relevance_score", 0) for c in chunks) / len(chunks)
                    if chunks
                    else 0
                ),
            }

        return summary


def main():
    """Main entry point for enhanced refund analysis"""

    parser = argparse.ArgumentParser(
        description="Enhanced Refund Analysis with Improved RAG"
    )

    parser.add_argument("--vendor", required=True, help="Vendor name")
    parser.add_argument("--product", required=True, help="Product description")
    parser.add_argument("--product-type", default="Unknown", help="Product type")
    parser.add_argument("--amount", type=float, required=True, help="Invoice amount")
    parser.add_argument("--tax", type=float, required=True, help="Tax paid")
    parser.add_argument(
        "--method",
        choices=["basic", "corrective", "reranking", "expansion", "hybrid", "enhanced"],
        default="enhanced",
        help="RAG method to use (default: enhanced)",
    )
    parser.add_argument(
        "--compare", action="store_true", help="Compare all RAG methods"
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = EnhancedRefundAnalyzer()

    if args.compare:
        # Compare all methods
        comparison = analyzer.compare_rag_methods(
            args.vendor, args.product, args.product_type, args.amount, args.tax
        )

        print("\n📊 COMPARISON SUMMARY:")
        print(json.dumps(comparison, indent=2))
    else:
        # Run single analysis
        result = analyzer.analyze_refund_eligibility(
            args.vendor,
            args.product,
            args.product_type,
            args.amount,
            args.tax,
            rag_method=args.method,
        )

        print("\n📄 ANALYSIS RESULT:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
