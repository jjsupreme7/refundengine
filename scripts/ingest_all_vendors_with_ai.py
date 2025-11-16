#!/usr/bin/env python3
"""
Ingest All 465 Vendors with AI Research

Reads Vendor_List_From_Client_Data.xlsx and researches each vendor using AI
to populate metadata (industry, business model, products, tax notes).

This will take ~30-60 minutes to complete due to rate limiting.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
from tqdm import tqdm
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI
from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = get_supabase_client()


class VendorAIResearcher:
    """Research vendors using AI and ingest to Supabase"""

    def __init__(self):
        self.openai_client = openai_client
        self.supabase = supabase
        self.processed_count = 0
        self.error_count = 0
        self.skipped_count = 0

    def research_vendor_with_ai(self, vendor_name: str) -> Dict:
        """
        Use AI to research vendor and extract metadata
        """
        prompt = f"""Analyze this vendor and provide structured metadata for tax refund analysis.

Vendor Name: {vendor_name}

CRITICAL CONTEXT: This vendor has PREVIOUSLY QUALIFIED FOR SALES TAX REFUNDS.

Provide your best analysis of this vendor based on the name alone (no web search needed).

Return JSON with these fields:
{{
  "vendor_name": "{vendor_name}",
  "industry": "Primary industry (Technology, Professional Services, Telecommunications, Manufacturing, Retail, etc.)",
  "business_model": "Business model (B2B SaaS, B2C Retail, Manufacturing, Consulting, Telecom Services, Distribution, etc.)",
  "vendor_category": "manufacturer | distributor | service_provider | retailer",
  "primary_products": ["List 2-4 likely products/services"],
  "typical_delivery": "Cloud-based | On-premise | Hybrid | In-person | Physical goods | Digital services | Mixed",
  "tax_notes": "REFUND-FOCUSED analysis. Common refund bases for this vendor type:
    - SaaS/Cloud: MPU exemption (multi-state usage <10% WA), Out-of-state server, Improper sourcing
    - Hardware: Out-of-state delivery, Manufacturing exemption, Resale, Interstate commerce
    - Professional Services: Separately stated consulting (exempt), Wrong rate, Out-of-state services
    - Telecom: Equipment for production use, Interstate/international use, Out-of-state installation
    - Software: Custom software development (not prewritten), License vs. SaaS distinction",
  "confidence_score": 0-100,
  "data_source": "ai_inference",
  "notes": "Any additional relevant information for tax analysis"
}}

Guidelines:
- Higher confidence (70-100) if vendor name is well-known or descriptive
- Medium confidence (50-69) if you can infer from name
- Lower confidence (20-49) if name is generic or unclear
- FOCUS ON REFUND OPPORTUNITIES not just taxability
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst specializing in vendor classification and Washington State sales tax refund analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
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
                "notes": f"Error: {str(e)}"
            }

    def check_if_vendor_exists(self, vendor_name: str) -> bool:
        """Check if vendor already in database"""
        try:
            result = self.supabase.table("knowledge_documents") \
                .select("id") \
                .eq("vendor_name", vendor_name) \
                .eq("document_type", "vendor_background") \
                .limit(1) \
                .execute()

            return len(result.data) > 0
        except:
            return False

    def ingest_vendor(self, vendor_name: str, transaction_count: int = None):
        """
        Complete workflow: Research and ingest vendor
        """
        # Check if already exists
        if self.check_if_vendor_exists(vendor_name):
            print(f"  ⏭️  Already in database: {vendor_name}")
            self.skipped_count += 1
            return

        # Research with AI
        print(f"  🤖 Researching: {vendor_name}")
        metadata = self.research_vendor_with_ai(vendor_name)

        # Prepare data for insertion
        primary_products = metadata.get('primary_products', [])
        if isinstance(primary_products, str):
            primary_products = [p.strip() for p in primary_products.split(',')]

        confidence_score = metadata.get('confidence_score', 50.0)
        if isinstance(confidence_score, str):
            confidence_score = float(confidence_score)

        data = {
            "document_type": "vendor_background",
            "title": f"Vendor: {vendor_name}",
            "vendor_name": vendor_name,
            "vendor_category": metadata.get('vendor_category', 'service_provider'),
            "industry": metadata.get('industry'),
            "business_model": metadata.get('business_model'),
            "primary_products": primary_products,
            "typical_delivery": metadata.get('typical_delivery'),
            "tax_notes": metadata.get('tax_notes'),
            "confidence_score": confidence_score,
            "data_source": metadata.get('data_source', 'ai_inference'),
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        try:
            result = self.supabase.table("knowledge_documents") \
                .insert(data) \
                .execute()

            self.processed_count += 1
            conf_emoji = "🟢" if confidence_score >= 70 else "🟡" if confidence_score >= 50 else "🔴"
            print(f"  ✅ Ingested {conf_emoji} ({int(confidence_score)}% confidence)")
            if transaction_count:
                print(f"     Transactions in data: {int(transaction_count)}")

        except Exception as e:
            print(f"  ❌ Error ingesting: {e}")
            self.error_count += 1

    def ingest_from_excel(self, excel_path: str, limit: int = None, batch_size: int = 10):
        """
        Ingest all vendors from Excel file with batching and rate limiting
        """
        print("="*80)
        print("VENDOR AI RESEARCH & INGESTION")
        print("="*80)
        print()

        # Read vendor list
        df = pd.read_excel(excel_path)
        print(f"📊 Total vendors in file: {len(df)}")

        if limit:
            df = df.head(limit)
            print(f"⚠️  Limiting to first {limit} vendors for testing")

        print()

        # Process in batches with progress bar
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing vendors"):
            vendor_name = row['Row Labels']
            transaction_count = row.get('Count of Vendor Name')

            # Skip if blank
            if pd.isna(vendor_name) or not vendor_name or vendor_name == "(blank)":
                continue

            self.ingest_vendor(vendor_name, transaction_count)

            # Rate limiting: pause every batch_size vendors
            if (idx + 1) % batch_size == 0:
                print(f"\n  ⏸️  Processed {idx + 1} vendors, pausing 5 seconds for rate limiting...")
                time.sleep(5)
            else:
                # Small delay between requests
                time.sleep(0.5)

        # Final summary
        print()
        print("="*80)
        print("FINAL SUMMARY")
        print("="*80)
        print(f"✅ Successfully processed: {self.processed_count}")
        print(f"⏭️  Skipped (already exists): {self.skipped_count}")
        print(f"❌ Errors: {self.error_count}")
        print(f"📊 Total: {self.processed_count + self.skipped_count + self.error_count}")
        print()

        # Calculate cost estimate
        total_requests = self.processed_count + self.error_count
        estimated_cost = total_requests * 0.00015  # ~$0.00015 per request with GPT-4o-mini
        print(f"💰 Estimated API cost: ${estimated_cost:.2f}")
        print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest vendors with AI research")
    parser.add_argument("--limit", type=int, help="Limit number of vendors (for testing)")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for rate limiting")

    args = parser.parse_args()

    researcher = VendorAIResearcher()

    # Path to vendor file
    vendor_file = Path(__file__).parent.parent / "knowledge_base" / "vendors" / "Common_Vendor.xlsx"

    if not vendor_file.exists():
        print(f"❌ Vendor file not found: {vendor_file}")
        print("   Looking for: knowledge_base/vendors/Common_Vendor.xlsx")
        sys.exit(1)

    researcher.ingest_from_excel(
        str(vendor_file),
        limit=args.limit,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
