#!/usr/bin/env python3
"""
Automated Vendor Research Script

Researches vendors using web search and AI analysis to populate metadata:
- Industry classification
- Business model
- Products/services
- Delivery method
- Tax treatment notes

Features:
- Web search for company information
- AI analysis to extract structured data
- Fuzzy matching for vendor name normalization
- Excel export/import workflow for review
- Batch processing with rate limiting

Usage:
    # Step 1: Research vendors from Excel list
    python scripts/research_vendors.py --file outputs/Vendors_To_Research.xlsx --output outputs/Vendor_Research_Results.xlsx --limit 10

    # Step 2: Review/edit the output Excel

    # Step 3: Import researched vendors to database
    python scripts/research_vendors.py --import outputs/Vendor_Research_Results.xlsx
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process
from openai import OpenAI

# Import centralized Supabase client
from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()


class VendorResearcher:
    """Automated vendor research using web search and AI"""

    def __init__(self):
        self.openai_client = openai_client
        self.supabase = supabase
        self.research_results = []

    def normalize_vendor_name(self, raw_name: str) -> str:
        """
        Normalize vendor name for better matching
        Removes common suffixes, standardizes format
        """
        if not raw_name:
            return ""

        # Convert to uppercase for consistency
        normalized = raw_name.upper().strip()

        # Remove trailing punctuation first (commas, periods)
        normalized = normalized.rstrip(".,")

        # Remove common legal entity suffixes
        suffixes_to_remove = [
            " LLC",
            " L.L.C.",
            " L.L.C",
            " LTD",
            " LIMITED",
            " LTD.",
            " INC",
            " INC.",
            " INCORPORATED",
            " CORP",
            " CORP.",
            " CORPORATION",
            " CO.",
            " CO",
            " LP",
            " L.P.",
            " LLP",
            " COMPANY",
            " & CO",
            " AND CO",
            " USA",
            " US",
            " AMERICA",
        ]

        # Keep removing suffixes until none are found (handles multiple suffixes)
        changed = True
        while changed:
            changed = False
            for suffix in suffixes_to_remove:
                if normalized.endswith(suffix):
                    normalized = normalized[: -len(suffix)].strip()
                    normalized = normalized.rstrip(
                        ".,"
                    )  # Remove trailing punctuation after each removal
                    changed = True
                    break  # Start over from the beginning of the list

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def fuzzy_match_vendor(
        self, vendor_name: str, known_vendors: List[str], threshold: int = 85
    ) -> Optional[str]:
        """
        Find best fuzzy match for vendor name from known vendors list
        Returns matched vendor if confidence > threshold, else None
        """
        if not vendor_name or not known_vendors:
            return None

        # Normalize input
        normalized_input = self.normalize_vendor_name(vendor_name)

        # Fuzzy match using fuzzywuzzy
        match, score = process.extractOne(
            normalized_input,
            [self.normalize_vendor_name(v) for v in known_vendors],
            scorer=fuzz.token_sort_ratio,
        )

        if score >= threshold:
            # Return original vendor name (not normalized)
            idx = [self.normalize_vendor_name(v) for v in known_vendors].index(match)
            return known_vendors[idx]

        return None

    def web_search_vendor(self, vendor_name: str) -> List[Dict[str, str]]:
        """
        Perform web search for vendor information
        Returns list of search results
        """
        try:
            # Note: WebSearch would be called here via Claude Code's WebSearch tool
            # For now, we'll use a placeholder that you can replace with actual web search
            print(f"    🔍 Searching web for: {vendor_name}")

            # TODO: Implement actual web search
            # This would use the WebSearch tool in Claude Code
            # For now, return empty to allow AI to work with vendor name only
            return []

        except Exception as e:
            print(f"    ⚠️  Web search failed: {e}")
            return []

    def research_vendor_with_ai(
        self, vendor_name: str, search_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze vendor and extract structured metadata
        """
        # Build prompt with search results if available
        search_context = ""
        if search_results:
            search_context = "\n\nWeb search results:\n"
            for i, result in enumerate(search_results[:5], 1):
                search_context += (
                    f"{i}. {result.get('title', '')}\n{result.get('snippet', '')}\n\n"
                )

        prompt = f"""Analyze this company and provide structured metadata for REFUND ANALYSIS purposes.

Company Name: {vendor_name}
{search_context}

CRITICAL CONTEXT: This vendor has PREVIOUSLY QUALIFIED FOR SALES TAX REFUNDS. Your analysis should focus on identifying WHY refunds occur, not just whether items are taxable.

Based on the company name{' and search results' if search_results else ''}, provide your best analysis of this vendor.

Return JSON with these fields:
{{
  "vendor_name": "{vendor_name}",
  "industry": "Primary industry (e.g., Technology, Professional Services, Manufacturing, Telecommunications, etc.)",
  "business_model": "Business model (e.g., B2B SaaS, B2C Retail, Manufacturing, Consulting, Telecom Services, etc.)",
  "vendor_category": "manufacturer | distributor | service_provider | retailer",
  "primary_products": ["Main products or services - be specific"],
  "typical_delivery": "Cloud-based | On-premise | Hybrid | In-person | Physical goods | Digital services",
  "tax_notes": "REFUND-FOCUSED analysis identifying common refund scenarios for this vendor type. Examples:
    - SaaS/Cloud: 'Common refund bases: MPU exemption (multi-state usage <10% WA), Out-of-state server location, Improper commercial activity sourcing'
    - Hardware: 'Common refund bases: Out-of-state delivery, Manufacturing equipment exemption, Resale certificate, Interstate/international commerce'
    - Professional Services: 'Common refund bases: Separately stated consulting (exempt), Wrong tax rate, Out-of-state services performed'
    - Telecom Equipment: 'Common refund bases: Equipment for production use (manufacturing exemption), Interstate/international use, Out-of-state installation'",
  "confidence_score": 0-100 (how confident you are in this analysis),
  "data_source": "web_research | name_inference",
  "notes": "Any additional relevant information"
}}

IMPORTANT - REFUND FOCUS:
- This vendor HAS qualified for refunds in the past
- Identify COMMON REFUND SCENARIOS for this type of vendor
- Don't just say "taxable" - explain REFUND OPPORTUNITIES
- Consider: Out-of-state delivery, MPU exemption, Manufacturing exemption, Resale, Interstate commerce, Wrong rate, Improper sourcing
- For SaaS: Focus on MPU multi-state usage and server location
- For hardware: Focus on out-of-state delivery and manufacturing exemptions
- For services: Focus on separately stated services and out-of-state performance
- Higher confidence if you found actual information, lower if inferring from name only
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst specializing in vendor classification and tax treatment analysis for Washington State.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            import json

            metadata = json.loads(response.choices[0].message.content)
            return metadata

        except Exception as e:
            print(f"    ❌ AI analysis failed: {e}")
            return {
                "vendor_name": vendor_name,
                "industry": "Unknown",
                "business_model": "Unknown",
                "vendor_category": "service_provider",
                "primary_products": [],
                "typical_delivery": "Unknown",
                "tax_notes": "Requires manual research",
                "confidence_score": 0,
                "data_source": "failed",
                "notes": f"Error: {str(e)}",
            }

    def research_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """
        Complete research workflow for a single vendor
        """
        print(f"\n{'='*70}")
        print(f"Researching: {vendor_name}")
        print(f"{'='*70}")

        # Step 1: Web search
        search_results = self.web_search_vendor(vendor_name)

        # Step 2: AI analysis
        print(f"    🤖 Analyzing with AI...")
        metadata = self.research_vendor_with_ai(vendor_name, search_results)

        # Add timestamp
        metadata["researched_at"] = datetime.now().isoformat()

        print(f"    ✅ Research complete")
        print(f"       Industry: {metadata.get('industry', 'Unknown')}")
        print(f"       Business Model: {metadata.get('business_model', 'Unknown')}")
        print(f"       Confidence: {metadata.get('confidence_score', 0)}%")

        return metadata

    def research_vendors_from_excel(
        self, excel_path: str, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Research multiple vendors from Excel file
        """
        print(f"\n📂 Loading vendor list from: {excel_path}")
        df = pd.read_excel(excel_path)

        if "Vendor_Name" not in df.columns:
            raise ValueError("Excel must have 'Vendor_Name' column")

        vendors = df["Vendor_Name"].dropna().unique()

        if limit:
            vendors = vendors[:limit]
            print(f"⚠️  Limiting to first {limit} vendors")

        print(f"📊 Total vendors to research: {len(vendors)}")
        print()

        results = []

        for vendor_name in tqdm(vendors, desc="Researching vendors"):
            # Skip blank vendors
            if not vendor_name or vendor_name.strip() == "" or vendor_name == "(blank)":
                continue

            try:
                metadata = self.research_vendor(vendor_name)
                results.append(metadata)

                # Rate limiting - avoid overwhelming APIs
                time.sleep(1)

            except Exception as e:
                print(f"    ❌ Error researching {vendor_name}: {e}")
                results.append(
                    {
                        "vendor_name": vendor_name,
                        "industry": "Error",
                        "business_model": "Error",
                        "vendor_category": "service_provider",
                        "primary_products": [],
                        "typical_delivery": "Unknown",
                        "tax_notes": "Research failed",
                        "confidence_score": 0,
                        "data_source": "error",
                        "notes": str(e),
                        "researched_at": datetime.now().isoformat(),
                    }
                )
                continue

        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        return results_df

    def export_to_excel(self, df: pd.DataFrame, output_path: str):
        """
        Export research results to Excel for review
        """
        print(f"\n💾 Exporting results to: {output_path}")

        # Convert array fields to comma-separated strings
        if "primary_products" in df.columns:
            df["primary_products"] = df["primary_products"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x)
            )

        # Add status column for review
        df.insert(1, "Status", "Review")

        # Reorder columns
        column_order = [
            "vendor_name",
            "Status",
            "industry",
            "business_model",
            "vendor_category",
            "primary_products",
            "typical_delivery",
            "tax_notes",
            "confidence_score",
            "data_source",
            "notes",
            "researched_at",
        ]

        df = df[[col for col in column_order if col in df.columns]]

        # Export
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Vendor Research", index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets["Vendor Research"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"✅ Exported {len(df)} vendors")
        print()
        print("📋 Next steps:")
        print(f"  1. Open {output_path}")
        print("  2. Review AI research results")
        print("  3. Edit any incorrect information")
        print("  4. Set Status='Approved' for vendors to import")
        print("  5. Run: python scripts/research_vendors.py --import {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Automated vendor research with web search and AI"
    )
    parser.add_argument("--file", help="Input Excel file with vendor names")
    parser.add_argument("--output", help="Output Excel file for research results")
    parser.add_argument(
        "--import", dest="import_file", help="Import researched vendors to database"
    )
    parser.add_argument("--limit", type=int, help="Limit number of vendors to research")

    args = parser.parse_args()

    researcher = VendorResearcher()

    if args.import_file:
        # TODO: Implement import to database
        print("❌ Import functionality not yet implemented")
        print("Use: python core/ingest_documents.py --import-metadata <file>")
        return

    if args.file and args.output:
        # Research vendors
        results_df = researcher.research_vendors_from_excel(args.file, limit=args.limit)
        researcher.export_to_excel(results_df, args.output)
        return

    # Show usage
    parser.print_help()


if __name__ == "__main__":
    main()
