#!/usr/bin/env python3
"""
Refund Analysis Script with Human-in-the-Loop Review
Analyzes Excel rows, queries legal knowledge base, outputs Excel with AI analysis for review
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

# Import OpenAI for embeddings and analysis
try:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)

# Import centralized Supabase client
try:
    from core.database import get_supabase_client

    supabase = get_supabase_client()
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)

# PDF parsing
try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)


class RefundAnalyzer:
    """Analyzes invoice line items for tax refund eligibility"""

    def __init__(self, docs_folder: str = "client_docs"):
        self.docs_folder = Path(docs_folder).resolve()
        self.embedding_model = "text-embedding-3-small"
        self.analysis_model = "gpt-4o"  # Use GPT-4 for complex legal analysis

    def validate_path(self, filename: str) -> Optional[Path]:
        """
        Validate that a filename doesn't contain path traversal attacks.
        Returns the safe path if valid, None if invalid.
        """
        try:
            # Construct the full path and resolve it
            full_path = (self.docs_folder / filename.strip()).resolve()

            # Check if the resolved path is within docs_folder
            if not str(full_path).startswith(str(self.docs_folder)):
                print(f"  WARNING: Path traversal attempt detected: {filename}")
                return None

            return full_path
        except Exception as e:
            print(f"  WARNING: Invalid filename: {filename} - {e}")
            return None

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
        """
        Use AI to find the specific line item in invoice text that matches the amount
        Returns: {product_desc, product_details, line_item_text}
        """
        prompt = f"""You are analyzing an invoice to find a specific line item.

Invoice Text:
{invoice_text[:4000]}  # Truncate if too long

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
                model="gpt-4o-mini",  # Faster model for extraction
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

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = client.embeddings.create(input=text, model=self.embedding_model)
        return response.data[0].embedding

    def search_legal_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search legal knowledge base using vector similarity"""
        query_embedding = self.get_embedding(query)

        # Search tax_law_chunks table using new function
        response = supabase.rpc(
            "search_tax_law",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": top_k,
                "law_category_filter": None,
                "tax_types_filter": None,
                "industries_filter": None,
            },
        ).execute()

        return response.data if response.data else []

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
                # Find best matching pattern
                for pattern in response.data:
                    if pattern["product_keyword"].lower() in product_desc.lower():
                        return pattern

            return None
        except Exception as e:
            print(f"Error checking vendor learning: {e}")
            return None

    def analyze_refund_eligibility(
        self,
        vendor: str,
        product_desc: str,
        product_type: str,
        amount: float,
        tax: float,
        invoice_text: str,
        po_text: str,
    ) -> Dict:
        """
        Main analysis: Determine if tax refund is eligible
        Uses legal knowledge base and vendor learning
        """

        # Check if we've learned about this vendor/product
        learned_info = self.check_vendor_learning(vendor, product_desc)

        # Build query for legal knowledge base
        query = f"""
Vendor: {vendor}
Product: {product_desc}
Product Type: {product_type}
Amount: ${amount:,.2f}
Tax Paid: ${tax:,.2f}

Determine if Washington State use tax refund is eligible.
Consider: exemptions for manufacturing, resale, agricultural equipment, etc.
"""

        # Search legal knowledge
        legal_chunks = self.search_legal_knowledge(query, top_k=5)

        # Build context from legal knowledge
        legal_context = "\n\n".join(
            [
                f"[Citation: {chunk.get('citation', 'N/A')}]\n{chunk.get('chunk_text', '')}"
                for chunk in legal_chunks
            ]
        )

        # Build prompt for AI analysis
        prompt = f"""You are a Washington State tax law expert analyzing use tax refund eligibility.

TRANSACTION DETAILS:
- Vendor: {vendor}
- Product: {product_desc}
- Product Type: {product_type}
- Amount: ${amount:,.2f}
- Tax Paid: ${tax:,.2f}

RELEVANT TAX LAW:
{legal_context[:3000]}

PREVIOUSLY LEARNED (if applicable):
{json.dumps(learned_info, indent=2) if learned_info else 'No prior learning for this vendor/product'}

ANALYSIS REQUIRED:
1. Is this purchase eligible for a use tax refund under Washington State law?
2. What is the legal basis (exemption type)?
3. What RCW/WAC citation applies?
4. What percentage of tax can be refunded?
5. What is your confidence level (0-100)?

Return JSON:
{{
    "refund_eligible": true/false,
    "refund_basis": "brief explanation of legal basis",
    "exemption_type": "e.g., manufacturing, resale, agricultural, etc.",
    "citation": "RCW/WAC reference",
    "refund_percentage": 0-100,
    "estimated_refund": dollar amount,
    "confidence": 0-100,
    "explanation": "detailed reasoning",
    "key_factors": ["list", "of", "key", "decision", "factors"]
}}
"""

        try:
            response = client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,  # Lower temperature for consistent legal analysis
            )

            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            print(f"Error during AI analysis: {e}")
            return {
                "refund_eligible": False,
                "refund_basis": "Error during analysis",
                "citation": "",
                "refund_percentage": 0,
                "estimated_refund": 0,
                "confidence": 0,
                "explanation": f"Analysis failed: {str(e)}",
            }

    def analyze_row(self, row: pd.Series) -> Dict:
        """Analyze a single row from Excel"""
        print(f"\n{'='*80}")
        print(f"Analyzing Row {row['Row_ID']}: {row['Vendor']} - ${row['Amount']:,.2f}")
        print(f"{'='*80}")

        # Get invoice and PO files
        invoice_files = (
            str(row["Inv_1_File"]).split(",") if pd.notna(row.get("Inv_1_File")) else []
        )
        po_files = (
            str(row["PO_1_File"]).split(",") if pd.notna(row.get("PO_1_File")) else []
        )

        invoice_text = ""
        po_text = ""

        # Extract text from invoice
        for inv_file in invoice_files:
            inv_path = self.validate_path(inv_file)
            if inv_path and inv_path.exists() and inv_path.suffix.lower() == ".pdf":
                print(f"  Reading invoice: {inv_file}")
                invoice_text += self.extract_text_from_pdf(inv_path) + "\n"

        # Extract text from PO
        for po_file in po_files:
            po_path = self.validate_path(po_file)
            if po_path and po_path.exists() and po_path.suffix.lower() == ".pdf":
                print(f"  Reading PO: {po_file}")
                po_text += self.extract_text_from_pdf(po_path) + "\n"

        # Find specific line item in invoice
        print(f"  Searching for line item: ${row['Amount']:,.2f}")
        line_item = self.find_line_item_in_invoice(
            invoice_text, float(row["Amount"]), float(row["Tax"])
        )

        print(f"  Product found: {line_item.get('product_desc', 'Unknown')}")
        print(f"  Product type: {line_item.get('product_type', 'Unknown')}")

        # Analyze refund eligibility
        print(f"  Analyzing refund eligibility...")
        analysis = self.analyze_refund_eligibility(
            vendor=row["Vendor"],
            product_desc=line_item.get("product_desc", "Unknown"),
            product_type=line_item.get("product_type", "Unknown"),
            amount=float(row["Amount"]),
            tax=float(row["Tax"]),
            invoice_text=invoice_text[:2000],  # Truncate for context
            po_text=po_text[:2000],
        )

        print(
            f"  ✓ Analysis complete - Refund: ${analysis.get('estimated_refund', 0):,.2f}"
        )

        # Combine results
        result = {
            "AI_Product_Desc": line_item.get("product_desc", "Unknown"),
            "AI_Product_Type": line_item.get("product_type", "Unknown"),
            "AI_Product_Details": line_item.get("details", ""),
            "AI_Refund_Eligible": analysis.get("refund_eligible", False),
            "AI_Refund_Basis": analysis.get("refund_basis", ""),
            "AI_Exemption_Type": analysis.get("exemption_type", ""),
            "AI_Citation": analysis.get("citation", ""),
            "AI_Confidence": analysis.get("confidence", 0),
            "AI_Refund_Percentage": analysis.get("refund_percentage", 0),
            "AI_Estimated_Refund": analysis.get("estimated_refund", 0),
            "AI_Explanation": analysis.get("explanation", ""),
            "AI_Key_Factors": ", ".join(analysis.get("key_factors", [])),
        }

        return result

    def save_to_database(self, row: pd.Series, analysis: Dict) -> str:
        """Save analysis results to database"""
        try:
            data = {
                "row_id": int(row["Row_ID"]),
                "vendor_name": row["Vendor"],
                "invoice_number": row.get("Invoice_Number"),
                "po_number": str(row.get("PO Number")),
                "amount": float(row["Amount"]),
                "tax_amount": float(row["Tax"]),
                "ai_product_desc": analysis.get("AI_Product_Desc"),
                "ai_product_type": analysis.get("AI_Product_Type"),
                "ai_refund_basis": analysis.get("AI_Refund_Basis"),
                "ai_citation": analysis.get("AI_Citation"),
                "ai_confidence": float(analysis.get("AI_Confidence", 0)),
                "ai_estimated_refund": float(analysis.get("AI_Estimated_Refund", 0)),
                "ai_refund_percentage": float(analysis.get("AI_Refund_Percentage", 0)),
                "ai_explanation": analysis.get("AI_Explanation"),
                "invoice_files": (
                    [row.get("Inv_1_File")] if pd.notna(row.get("Inv_1_File")) else []
                ),
                "po_files": (
                    [row.get("PO_1_File")] if pd.notna(row.get("PO_1_File")) else []
                ),
                "analysis_status": "pending_review",
            }

            response = supabase.table("analysis_results").insert(data).execute()
            return response.data[0]["id"] if response.data else None

        except Exception as e:
            print(f"Error saving to database: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Analyze refunds from Excel")
    parser.add_argument("input_excel", help="Path to input Excel file")
    parser.add_argument(
        "--output", "-o", help="Output Excel path (default: adds _analyzed suffix)"
    )
    parser.add_argument(
        "--docs-folder", default="client_docs", help="Folder containing invoice/PO PDFs"
    )
    parser.add_argument(
        "--save-db", action="store_true", help="Save results to database"
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input_excel)
        output_path = (
            input_path.parent / f"{input_path.stem}_analyzed{input_path.suffix}"
        )

    print(f"\n{'='*80}")
    print(f"REFUND ANALYSIS PIPELINE")
    print(f"{'='*80}")
    print(f"Input:  {args.input_excel}")
    print(f"Output: {output_path}")
    print(f"Docs:   {args.docs_folder}")
    print(f"{'='*80}\n")

    # Load Excel
    df = pd.read_excel(args.input_excel)
    print(f"Loaded {len(df)} rows from Excel\n")

    # Initialize analyzer
    analyzer = RefundAnalyzer(docs_folder=args.docs_folder)

    # Add columns for AI analysis and review
    review_columns = [
        "AI_Product_Desc",
        "AI_Product_Type",
        "AI_Product_Details",
        "AI_Refund_Eligible",
        "AI_Refund_Basis",
        "AI_Exemption_Type",
        "AI_Citation",
        "AI_Confidence",
        "AI_Refund_Percentage",
        "AI_Estimated_Refund",
        "AI_Explanation",
        "AI_Key_Factors",
        # Human review columns
        "Review_Status",
        "Corrected_Product_Desc",
        "Corrected_Product_Type",
        "Corrected_Refund_Basis",
        "Corrected_Citation",
        "Corrected_Estimated_Refund",
        "Reviewer_Notes",
    ]

    for col in review_columns:
        if col not in df.columns:
            df[col] = None

    # Analyze each row
    for idx, row in df.iterrows():
        try:
            analysis = analyzer.analyze_row(row)

            # Update DataFrame
            for key, value in analysis.items():
                df.at[idx, key] = value

            # Save to database if requested
            if args.save_db:
                analysis_id = analyzer.save_to_database(row, analysis)
                print(f"  Saved to database: {analysis_id}")

        except Exception as e:
            print(f"Error analyzing row {row['Row_ID']}: {e}")
            continue

    # Save output Excel
    print(f"\n{'='*80}")
    print(f"Saving results to: {output_path}")
    df.to_excel(output_path, index=False)
    print(f"✓ Analysis complete!")
    print(f"{'='*80}\n")

    # Summary
    total_refund = df["AI_Estimated_Refund"].sum()
    eligible_count = df["AI_Refund_Eligible"].sum()
    print(f"SUMMARY:")
    print(f"  Total rows analyzed: {len(df)}")
    print(f"  Refund eligible: {eligible_count}")
    print(f"  Total estimated refund: ${total_refund:,.2f}")
    print(
        f"\nNext step: Review the Excel file and fill in correction columns if needed."
    )


if __name__ == "__main__":
    main()
