#!/usr/bin/env python3
"""
Automated Vendor Research Script

Researches all vendors in vendor_products table via web search and enriches with:
- Industry classification
- Business model
- Primary products/services
- WA tax classification
- Product delivery methods

Features:
- Batched processing (configurable batch size)
- Resume capability (skip already researched vendors)
- Progress tracking
- WA tax law integration for classification
- JSON catalog generation

Usage:
    python scripts/research_all_vendors.py --batch-size 30 --start-from 0
    python scripts/research_all_vendors.py --resume  # Skip already researched
    python scripts/research_all_vendors.py --vendor "MICROSOFT CORPORATION"  # Single vendor  # noqa: E501
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client  # noqa: E402
from openai import OpenAI  # noqa: E402

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# WA Tax Classifications (from tax_rules.json)
WA_TAX_CLASSIFICATIONS = {
    "saas_subscription": "digital_automated_service",
    "iaas_paas": "digital_automated_service",
    "professional_services": "service_primarily_human_effort",
    "software_license": "prewritten_software",
    "tangible_personal_property": "tangible_personal_property",
    "data_processing": "digital_automated_service",
    "telecommunications": "telecommunications",
    "construction_services": "construction_services",
    "wholesale_distribution": "wholesale_distribution",
    "manufacturing": "manufacturing",
}

# Product type keywords for classification
PRODUCT_TYPE_KEYWORDS = {
    "saas_subscription": [
        "saas",
        "software as a service",
        "subscription",
        "cloud",
        "platform",
        "online",
        "web-based",
        "hosted",
    ],
    "iaas_paas": [
        "infrastructure",
        "iaas",
        "paas",
        "cloud computing",
        "virtual machine",
        "vm",
        "instance",
        "server",
        "compute",
    ],
    "professional_services": [
        "consulting",
        "advisory",
        "professional services",
        "expert",
        "consultant",
        "strategic",
        "management",
    ],
    "software_license": [
        "license",
        "perpetual",
        "term license",
        "software license",
        "desktop",
        "standalone",
    ],
    "tangible_personal_property": [
        "hardware",
        "equipment",
        "device",
        "physical",
        "machine",
        "computer",
        "laptop",
    ],
    "data_processing": [
        "data processing",
        "analytics",
        "database",
        "storage",
        "backup",
        "reporting",
        "intelligence",
    ],
    "telecommunications": [
        "phone",
        "telecom",
        "internet",
        "communication",
        "voip",
        "cellular",
        "mobile",
        "network",
    ],
    "construction_services": [
        "construction",
        "electrical",
        "installation",
        "contractor",
        "build",
        "engineering",
    ],
    "wholesale_distribution": [
        "wholesale",
        "distributor",
        "supplier",
        "reseller",
        "distribution",
    ],
    "manufacturing": [
        "manufacturer",
        "manufacturing",
        "fabrication",
        "assembly",
        "production",
    ],
}


class VendorResearcher:
    """Automated vendor research and enrichment"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.tax_rules = self._load_tax_rules()
        self.stats = {
            "total": 0,
            "researched": 0,
            "skipped": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

    def _load_tax_rules(self) -> Dict:
        """Load WA tax rules for classification"""
        tax_rules_path = (
            Path(__file__).parent.parent
            / "knowledge_base/states/washington/tax_rules.json"
        )
        if tax_rules_path.exists():
            with open(tax_rules_path, "r") as f:
                return json.load(f)
        return {}

    def get_vendors_to_research(
        self,
        resume: bool = False,
        vendor_name: Optional[str] = None,
        start_from: int = 0,
        batch_size: int = 30,
    ) -> List[Dict]:
        """Fetch vendors that need research"""

        if vendor_name:
            # Single vendor lookup
            result = (
                self.supabase.table("vendor_products")
                .select("*")
                .eq("vendor_name", vendor_name)
                .execute()
            )
            return result.data if result.data else []

        # Fetch all vendors
        result = (
            self.supabase.table("vendor_products")
            .select("*")
            .order("historical_sample_count", desc=True)
            .execute()
        )

        if not result.data:
            return []

        vendors = result.data
        self.stats["total"] = len(vendors)

        # Filter based on resume flag
        if resume:
            vendors = [v for v in vendors if not v.get("web_research_date")]
            print(
                f"Resume mode: {
                    len(vendors)} vendors need research (out of {
                    self.stats['total']} total)")

        # Apply pagination
        vendors = vendors[start_from: start_from + batch_size]

        return vendors

    def classify_product_type(self, description: str) -> str:
        """Classify product type based on description keywords"""
        description_lower = description.lower()

        # Score each product type
        scores = {}
        for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                scores[product_type] = score

        if not scores:
            return "unknown"

        # Return highest scoring type
        return max(scores.items(), key=lambda x: x[1])[0]

    def get_wa_tax_classification(self, product_type: str) -> str:
        """Get WA tax classification for product type"""
        return WA_TAX_CLASSIFICATIONS.get(product_type, "unknown")

    def infer_from_vendor_name(self, vendor_name: str) -> Dict:
        """
        Make educated guess about vendor based on name alone.
        This is a fallback when web search fails or for batch processing.
        """
        name_lower = vendor_name.lower()

        # Industry patterns
        if any(
            x in name_lower
            for x in ["software", "systems", "technology", "tech", "cloud", "data"]
        ):
            industry = "Technology"
            business_model = "B2B SaaS"
            product_type = "saas_subscription"
        elif any(
            x in name_lower for x in ["consulting", "advisory", "services", "solutions"]
        ):
            industry = "Professional Services"
            business_model = "B2B Consulting"
            product_type = "professional_services"
        elif any(
            x in name_lower
            for x in ["electric", "construction", "contractor", "builders"]
        ):
            industry = "Construction"
            business_model = "B2B Services"
            product_type = "construction_services"
        elif any(x in name_lower for x in ["wholesale", "supply", "distribution"]):
            industry = "Wholesale Distribution"
            business_model = "B2B Wholesale"
            product_type = "wholesale_distribution"
        elif any(
            x in name_lower for x in ["manufacturing", "industries", "industrial"]
        ):
            industry = "Manufacturing"
            business_model = "B2B Manufacturing"
            product_type = "manufacturing"
        elif any(x in name_lower for x in ["network", "telecom", "communications"]):
            industry = "Telecommunications"
            business_model = "B2B Services"
            product_type = "telecommunications"
        else:
            industry = "Unknown"
            business_model = "Unknown"
            product_type = "unknown"

        return {
            "industry": industry,
            "business_model": business_model,
            "product_type": product_type,
            "typical_delivery": self._infer_delivery(product_type),
            "wa_tax_classification": self.get_wa_tax_classification(product_type),
            "confidence": "low_inference",
        }

    def _infer_delivery(self, product_type: str) -> str:
        """Infer delivery method from product type"""
        delivery_map = {
            "saas_subscription": "Cloud-based",
            "iaas_paas": "Cloud infrastructure",
            "professional_services": "Human-delivered",
            "software_license": "Digital download or physical media",
            "tangible_personal_property": "Physical shipment",
            "data_processing": "Cloud-based",
            "telecommunications": "Network service",
            "construction_services": "On-site services",
            "wholesale_distribution": "Physical shipment",
            "manufacturing": "Physical production",
        }
        return delivery_map.get(product_type, "Unknown")

    def research_vendor_location(self, vendor_name: str) -> Dict:
        """
        Research vendor headquarters location using AI

        Returns dict with:
            - headquarters_city, headquarters_state, headquarters_country
            - confidence (0-100)
            - reasoning
        """
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a business research assistant. Given a company name, determine their headquarters location.

Provide your response in JSON format:
{
    "headquarters_city": "City name",
    "headquarters_state": "Two-letter state code (US only, otherwise null)",
    "headquarters_country": "Country code (US, CA, UK, etc.)",
    "confidence": 0-100,
    "reasoning": "Brief explanation of how confident you are and why"
}

Confidence levels:
- 90-100: Well-known company, certain of location
- 70-89: Strong evidence, likely correct
- 50-69: Some evidence, reasonable guess
- 30-49: Weak evidence, uncertain
- 0-29: Very uncertain, multiple possibilities or no information

For US companies, always provide state as 2-letter code (WA, CA, NY, etc.).
For non-US companies, state should be null.
If you cannot determine location at all, set all fields to null and confidence to 0."""
                    },
                    {
                        "role": "user",
                        "content": f"What is the headquarters location of the company: {vendor_name}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"  ⚠️  Location research error: {e}")
            return {
                "headquarters_city": None,
                "headquarters_state": None,
                "headquarters_country": None,
                "confidence": 0,
                "reasoning": f"Error: {str(e)}"
            }

    def update_vendor_in_supabase(self, vendor_id: str, enriched_data: Dict) -> bool:
        """Update vendor record in Supabase"""
        try:
            update_data = {
                "industry": enriched_data.get("industry"),
                "business_model": enriched_data.get("business_model"),
                "typical_delivery": enriched_data.get("typical_delivery"),
                "wa_tax_classification": enriched_data.get("wa_tax_classification"),
                "research_notes": enriched_data.get("research_notes", ""),
                "web_research_date": datetime.now().isoformat(),
                "product_description": enriched_data.get(
                    "product_description", "Automated inference from vendor name"
                ),
                # Location data
                "headquarters_city": enriched_data.get("headquarters_city"),
                "headquarters_state": enriched_data.get("headquarters_state"),
                "headquarters_country": enriched_data.get("headquarters_country"),
                "location_confidence": enriched_data.get("location_confidence"),
            }

            # Add primary_products if available
            if enriched_data.get("primary_products"):
                update_data["primary_products"] = json.dumps(
                    enriched_data["primary_products"]
                )

            self.supabase.table("vendor_products").update(update_data).eq(
                "id", vendor_id
            ).execute()
            return True
        except Exception as e:
            print(f"  Error updating vendor: {e}")
            return False

    def research_vendor_batch(
        self, vendors: List[Dict], use_inference_only: bool = False
    ) -> List[Dict]:
        """Research a batch of vendors"""
        enriched_vendors = []

        for i, vendor in enumerate(vendors, 1):
            vendor_name = vendor["vendor_name"]
            vendor_id = vendor["id"]

            print(f"\n[{i}/{len(vendors)}] Researching: {vendor_name}")

            try:
                if use_inference_only:
                    # Fast mode: Just infer from name
                    enriched_data = self.infer_from_vendor_name(vendor_name)
                    enriched_data["research_notes"] = (
                        "Automated inference from vendor name (no web search)"
                    )
                else:
                    # AI-based research with location lookup
                    print("  🔍 Researching vendor with AI...")

                    # Get industry/business info from name inference
                    enriched_data = self.infer_from_vendor_name(vendor_name)

                    # Add location research
                    location_data = self.research_vendor_location(vendor_name)
                    enriched_data["headquarters_city"] = location_data.get("headquarters_city")
                    enriched_data["headquarters_state"] = location_data.get("headquarters_state")
                    enriched_data["headquarters_country"] = location_data.get("headquarters_country")
                    enriched_data["location_confidence"] = location_data.get("confidence", 0)
                    enriched_data["location_reasoning"] = location_data.get("reasoning", "")

                    # Update research notes
                    conf = location_data.get("confidence", 0)
                    city = location_data.get("headquarters_city", "Unknown")
                    state = location_data.get("headquarters_state", "")
                    location_str = f"{city}, {state}" if state else city

                    enriched_data["research_notes"] = (
                        f"AI research: Location={location_str} (confidence: {conf}%)"
                    )

                    print(f"  📍 Location: {location_str} (confidence: {conf}%)")

                # Update Supabase
                if self.update_vendor_in_supabase(vendor_id, enriched_data):
                    print(f"  ✓ Updated: {
                        enriched_data['industry']} / {enriched_data['wa_tax_classification']}")  # noqa: E501
                    self.stats["researched"] += 1

                    # Add to enriched list
                    enriched_vendors.append({**vendor, **enriched_data})
                else:
                    self.stats["errors"] += 1

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"  Error: {e}")
                self.stats["errors"] += 1

        return enriched_vendors

    def print_stats(self):
        """Print research statistics"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()

        print(f"\n{'=' * 70}")
        print("VENDOR RESEARCH STATISTICS")
        print(f"{'=' * 70}")
        print(f"Total vendors: {self.stats['total']}")
        print(f"Researched: {self.stats['researched']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        if self.stats["researched"] > 0:
            print(
                f"Average time per vendor: {
                    elapsed /
                    self.stats['researched']:.1f} seconds")
        print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Research all vendors and enrich with product data"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=30,
        help="Number of vendors to process per batch",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start from vendor index (for pagination)",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Skip vendors already researched"
    )
    parser.add_argument("--vendor", type=str, help="Research specific vendor by name")
    parser.add_argument(
        "--inference-only",
        action="store_true",
        help="Use name-based inference only (fast, no web search)",
    )
    parser.add_argument("--export-json", type=str, help="Export results to JSON file")

    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print("AUTOMATED VENDOR RESEARCH")
    print(f"{'=' * 70}\n")

    # Connect to Supabase
    print("Connecting to Supabase...")
    try:
        supabase = get_supabase_client()
        print("✓ Connected successfully\n")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    # Initialize researcher
    researcher = VendorResearcher(supabase)

    # Get vendors to research
    vendors = researcher.get_vendors_to_research(
        resume=args.resume,
        vendor_name=args.vendor,
        start_from=args.start_from,
        batch_size=args.batch_size,
    )

    if not vendors:
        print("No vendors found to research.")
        return

    print(f"Researching {len(vendors)} vendors...")
    if args.inference_only:
        print("Mode: INFERENCE ONLY (fast, no web search)")
    else:
        print("Mode: WEB SEARCH + INFERENCE")

    # Research vendors
    enriched_vendors = researcher.research_vendor_batch(
        vendors, use_inference_only=args.inference_only
    )

    # Print statistics
    researcher.print_stats()

    # Export to JSON if requested
    if args.export_json:
        export_path = Path(args.export_json)
        with open(export_path, "w") as f:
            json.dump(enriched_vendors, f, indent=2, default=str)
        print(f"✓ Exported {len(enriched_vendors)} vendors to {export_path}")

    print("\nNext steps:")
    print(
        "  1. Review enriched data: SELECT * FROM v_vendor_intelligence WHERE research_status = 'complete';"  # noqa: E501
    )
    print(
        "  2. Run more batches: python scripts/research_all_vendors.py --start-from 30 --batch-size 30"  # noqa: E501
    )
    print(
        "  3. Update data quality scores: SELECT update_all_vendor_data_quality_scores();"  # noqa: E501
    )


if __name__ == "__main__":
    main()
