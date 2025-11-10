#!/usr/bin/env python3
"""
Enhanced Refund Analysis Script with Improved RAG
Integrates Corrective RAG, Reranking, Query Expansion, and Hybrid Search
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from supabase import create_client, Client
import PyPDF2

# Import enhanced RAG
from core.enhanced_rag import EnhancedRAG

# Initialize clients
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)


class EnhancedRefundAnalyzer:
    """
    Refund Analyzer with Enhanced RAG capabilities

    Improvements over basic version:
    - Corrective RAG for legal citation validation
    - Reranking for better legal relevance
    - Query expansion with tax terminology
    - Hybrid search (vector + keyword)
    """

    def __init__(self, docs_folder: str = "client_docs"):
        self.docs_folder = Path(docs_folder)
        self.embedding_model = "text-embedding-3-small"
        self.analysis_model = "gpt-4o"

        # Initialize Enhanced RAG
        self.rag = EnhancedRAG(supabase)

        print("✅ Enhanced Refund Analyzer initialized")
        print("   - Corrective RAG: ON")
        print("   - Reranking: ON")
        print("   - Query Expansion: ON")
        print("   - Hybrid Search: ON\n")

    # ==================== PDF & EXTRACTION ====================

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def find_line_item_in_invoice(self, invoice_text: str, amount: float, tax: float) -> Dict:
        """Use AI to find the specific line item in invoice text"""
        prompt = f"""You are analyzing an invoice to find a specific line item.

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
                response_format={"type": "json_object"}
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
                "confidence": 0
            }

    # ==================== VENDOR LEARNING ====================

    def check_vendor_learning(self, vendor_name: str, product_desc: str) -> Optional[Dict]:
        """Check if we've seen this vendor/product before and learned anything"""
        try:
            # Check vendor_products table
            response = supabase.table('vendor_products').select('*').eq(
                'vendor_name', vendor_name
            ).ilike('product_description', f'%{product_desc[:50]}%').execute()

            if response.data:
                return response.data[0]

            # Check vendor_product_patterns
            response = supabase.table('vendor_product_patterns').select('*').eq(
                'vendor_name', vendor_name
            ).eq('is_active', True).execute()

            if response.data:
                for pattern in response.data:
                    if pattern['product_keyword'].lower() in product_desc.lower():
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
        rag_method: str = "enhanced"  # basic, corrective, reranking, expansion, hybrid, enhanced
    ) -> Dict:
        """
        Main analysis: Determine if tax refund is eligible
        Uses Enhanced RAG with selectable method

        Args:
            rag_method: Which RAG method to use
                - "basic": Standard vector search
                - "corrective": With validation/correction
                - "reranking": With AI reranking
                - "expansion": With query expansion
                - "hybrid": Vector + keyword search
                - "enhanced": All improvements (RECOMMENDED)
        """

        print(f"\n{'='*80}")
        print(f"Analyzing Refund Eligibility")
        print(f"Vendor: {vendor}")
        print(f"Product: {product_desc[:100]}")
        print(f"RAG Method: {rag_method.upper()}")
        print(f"{'='*80}\n")

        # Check if we've learned about this vendor/product
        learned_info = self.check_vendor_learning(vendor, product_desc)

        if learned_info:
            print(f"💡 Found prior learning for {vendor}")

        # Build query for legal knowledge base
        query = f"""
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
"""

        # Search legal knowledge using selected RAG method
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
            legal_chunks = self.rag.search_enhanced(query, top_k=5)

        print(f"\n✅ Retrieved {len(legal_chunks)} legal chunks\n")

        # Build context from legal knowledge
        legal_context = self._build_legal_context(legal_chunks)

        # Build context from vendor learning
        learning_context = ""
        if learned_info:
            learning_context = f"""
PRIOR LEARNING:
This vendor/product has been analyzed before:
- Product Type: {learned_info.get('product_type', 'N/A')}
- Tax Treatment: {learned_info.get('tax_treatment', 'N/A')}
- Confidence: {learned_info.get('confidence_score', 'N/A')}
"""

        # Build comprehensive analysis prompt
        analysis_prompt = f"""You are a Washington State tax law expert analyzing use tax refund eligibility.

TRANSACTION DETAILS:
- Vendor: {vendor}
- Product: {product_desc}
- Product Type: {product_type}
- Amount: ${amount:,.2f}
- Tax Paid: ${tax:,.2f}

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

5. **Legal Citations**: Which RCW/WAC sections apply?

6. **Confidence**: How confident are you in this analysis (0-100)?

7. **Next Steps**: What additional information is needed?

Return JSON:
{{
    "is_taxable": true/false,
    "refund_eligible": true/false,
    "refund_basis": "MPU|Non-taxable|Exemption|OOS Delivery|None",
    "refund_percentage": 0-100,
    "estimated_refund": dollar amount,
    "primary_citation": "RCW/WAC",
    "supporting_citations": ["citation1", "citation2"],
    "mpu_required": true/false,
    "allocation_method": "User location|Equipment location|N/A",
    "confidence": 0-100,
    "reasoning": "detailed explanation",
    "next_steps": ["action1", "action2"]
}}
"""

        # Get AI analysis
        print("🤖 Running AI analysis...\n")

        try:
            response = client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": analysis_prompt}],
                response_format={"type": "json_object"}
            )

            analysis_result = json.loads(response.choices[0].message.content)

            # Add metadata
            analysis_result['rag_method'] = rag_method
            analysis_result['legal_chunks_found'] = len(legal_chunks)
            analysis_result['vendor_learning_used'] = learned_info is not None

            # Add chunk details for transparency
            analysis_result['legal_sources'] = [
                {
                    'citation': chunk.get('citation', 'N/A'),
                    'relevance_score': chunk.get('relevance_score'),
                    'preview': chunk.get('chunk_text', '')[:200]
                }
                for chunk in legal_chunks
            ]

            print(f"✅ Analysis complete!")
            print(f"   Refund Eligible: {analysis_result.get('refund_eligible')}")
            print(f"   Refund Basis: {analysis_result.get('refund_basis')}")
            print(f"   Confidence: {analysis_result.get('confidence')}%")
            print(f"{'='*80}\n")

            return analysis_result

        except Exception as e:
            print(f"❌ Error in analysis: {e}")
            return {
                "error": str(e),
                "refund_eligible": False,
                "confidence": 0
            }

    def _build_legal_context(self, chunks: List[Dict]) -> str:
        """Build formatted legal context from chunks"""
        if not chunks:
            return "No relevant legal documents found."

        context = ""
        for i, chunk in enumerate(chunks):
            citation = chunk.get('citation', 'N/A')
            text = chunk.get('chunk_text', '')
            relevance = chunk.get('relevance_score', 'N/A')

            context += f"\n[Source {i+1}] {citation}"
            if relevance != 'N/A':
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
        tax: float
    ) -> Dict:
        """
        Compare all RAG methods side-by-side for the same query
        Useful for testing which method works best
        """

        query = f"""
Vendor: {vendor}
Product: {product_desc}
Product Type: {product_type}
Amount: ${amount:,.2f}
Tax Paid: ${tax:,.2f}

Determine if Washington State use tax refund is eligible.
"""

        print(f"\n{'='*80}")
        print(f"📊 COMPARING ALL RAG METHODS")
        print(f"Vendor: {vendor}")
        print(f"Product: {product_desc[:100]}")
        print(f"{'='*80}\n")

        # Use the RAG comparison method
        rag_results = self.rag.compare_methods(query, top_k=5)

        # Summarize comparison
        summary = {
            'query': query,
            'methods_compared': len(rag_results),
            'results': {}
        }

        for method, chunks in rag_results.items():
            summary['results'][method] = {
                'chunks_found': len(chunks),
                'citations': [c.get('citation', 'N/A') for c in chunks[:3]],
                'avg_relevance': sum(c.get('relevance_score', 0) for c in chunks) / len(chunks) if chunks else 0
            }

        return summary


def main():
    """Main entry point for enhanced refund analysis"""

    parser = argparse.ArgumentParser(description='Enhanced Refund Analysis with Improved RAG')

    parser.add_argument('--vendor', required=True, help='Vendor name')
    parser.add_argument('--product', required=True, help='Product description')
    parser.add_argument('--product-type', default='Unknown', help='Product type')
    parser.add_argument('--amount', type=float, required=True, help='Invoice amount')
    parser.add_argument('--tax', type=float, required=True, help='Tax paid')
    parser.add_argument('--method',
                       choices=['basic', 'corrective', 'reranking', 'expansion', 'hybrid', 'enhanced'],
                       default='enhanced',
                       help='RAG method to use (default: enhanced)')
    parser.add_argument('--compare', action='store_true', help='Compare all RAG methods')

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = EnhancedRefundAnalyzer()

    if args.compare:
        # Compare all methods
        comparison = analyzer.compare_rag_methods(
            args.vendor,
            args.product,
            args.product_type,
            args.amount,
            args.tax
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
            rag_method=args.method
        )

        print("\n📄 ANALYSIS RESULT:")
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
