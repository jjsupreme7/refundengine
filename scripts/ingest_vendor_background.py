#!/usr/bin/env python3
"""
Ingest Vendor Background Data to Supabase

Reads vendor metadata from:
- knowledge_base/vendors/vendor_database.json
- outputs/Vendor_Background.xlsx

And populates the knowledge_documents table with vendor metadata
(industry, business_model, primary_products, typical_delivery, tax_notes)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize Supabase client
supabase = get_supabase_client()


class VendorBackgroundIngester:
    """Ingest vendor background data to Supabase"""

    def __init__(self):
        self.supabase = supabase
        self.ingested_count = 0
        self.updated_count = 0
        self.error_count = 0

    def ingest_from_json(self, json_path: str):
        """
        Ingest vendors from JSON file
        """
        print(f"\n📂 Loading vendors from: {json_path}")

        with open(json_path, 'r') as f:
            vendor_data = json.load(f)

        print(f"📊 Found {len(vendor_data)} vendors in JSON")
        print()

        for vendor_name, metadata in vendor_data.items():
            try:
                self._upsert_vendor_metadata(vendor_name, metadata, source="json")
            except Exception as e:
                print(f"❌ Error ingesting {vendor_name}: {e}")
                self.error_count += 1

        print()
        print(f"✅ JSON ingestion complete")
        print(f"   New vendors: {self.ingested_count}")
        print(f"   Updated vendors: {self.updated_count}")
        print(f"   Errors: {self.error_count}")

    def ingest_from_excel(self, excel_path: str):
        """
        Ingest vendors from Excel file
        Expects columns: vendor_name, industry, business_model, primary_products, typical_delivery, tax_notes
        """
        print(f"\n📂 Loading vendors from: {excel_path}")

        try:
            # Try to read the Excel file
            df = pd.read_excel(excel_path)
            print(f"📊 Found {len(df)} rows in Excel")
            print(f"Columns: {', '.join(df.columns)}")
            print()

            # Check for required columns
            required_cols = ['vendor_name']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"⚠️  Warning: Missing columns: {missing_cols}")
                print("Available columns:", df.columns.tolist())
                return

            for idx, row in df.iterrows():
                vendor_name = row.get('vendor_name') or row.get('Vendor_Name') or row.get('Vendor Name')

                if pd.isna(vendor_name) or not vendor_name:
                    continue

                # Build metadata dict from row
                metadata = {}

                # Map Excel columns to metadata fields
                column_mappings = {
                    'industry': ['industry', 'Industry'],
                    'business_model': ['business_model', 'Business_Model', 'Business Model'],
                    'primary_products': ['primary_products', 'Primary_Products', 'Products', 'primary products'],
                    'typical_delivery': ['typical_delivery', 'Typical_Delivery', 'Delivery', 'delivery'],
                    'tax_notes': ['tax_notes', 'Tax_Notes', 'Tax Notes', 'Notes'],
                    'vendor_category': ['vendor_category', 'Vendor_Category', 'Category'],
                    'confidence_score': ['confidence_score', 'Confidence', 'confidence'],
                }

                for field, possible_cols in column_mappings.items():
                    for col in possible_cols:
                        if col in df.columns and not pd.isna(row.get(col)):
                            metadata[field] = row[col]
                            break

                try:
                    self._upsert_vendor_metadata(vendor_name, metadata, source="excel")
                except Exception as e:
                    print(f"❌ Error ingesting {vendor_name}: {e}")
                    self.error_count += 1

            print()
            print(f"✅ Excel ingestion complete")
            print(f"   New vendors: {self.ingested_count}")
            print(f"   Updated vendors: {self.updated_count}")
            print(f"   Errors: {self.error_count}")

        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")

    def _upsert_vendor_metadata(self, vendor_name: str, metadata: Dict, source: str = "manual"):
        """
        Insert or update vendor metadata in knowledge_documents table
        """
        print(f"Processing: {vendor_name}")

        # First, check if vendor already exists
        existing = self.supabase.table("knowledge_documents") \
            .select("id, vendor_name, industry, business_model") \
            .eq("vendor_name", vendor_name) \
            .limit(1) \
            .execute()

        # Extract primary_products as array
        primary_products = metadata.get('primary_products', [])
        if isinstance(primary_products, str):
            # If it's a string, split by comma or use as single item
            if ',' in primary_products:
                primary_products = [p.strip() for p in primary_products.split(',')]
            else:
                primary_products = [primary_products]
        elif isinstance(primary_products, dict):
            # If it's a dict (like in JSON), extract keys
            primary_products = list(primary_products.keys())

        # Parse confidence score (handle string values like "very_high")
        confidence_raw = metadata.get('confidence_score') or metadata.get('confidence')
        if isinstance(confidence_raw, str):
            # Map string confidence to numeric
            confidence_map = {
                "very_high": 95.0,
                "high": 85.0,
                "medium": 70.0,
                "low": 50.0,
                "very_low": 30.0
            }
            confidence_score = confidence_map.get(confidence_raw.lower(), 90.0)
        elif isinstance(confidence_raw, (int, float)):
            confidence_score = float(confidence_raw)
        else:
            confidence_score = 90.0

        # Build update/insert data
        data = {
            "vendor_name": vendor_name,
            "industry": metadata.get('industry'),
            "business_model": metadata.get('business_model'),
            "primary_products": primary_products,
            "typical_delivery": metadata.get('typical_delivery'),
            "tax_notes": metadata.get('tax_notes'),
            "confidence_score": confidence_score,
            "data_source": source,
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        if existing.data and len(existing.data) > 0:
            # Update existing vendor
            vendor_id = existing.data[0]['id']

            result = self.supabase.table("knowledge_documents") \
                .update(data) \
                .eq("id", vendor_id) \
                .execute()

            self.updated_count += 1
            print(f"  ✅ Updated vendor {vendor_name}")
        else:
            # Insert new vendor
            # We need to create a minimal document entry
            data.update({
                "document_type": "vendor_background",
                "title": f"Vendor: {vendor_name}",
            })

            result = self.supabase.table("knowledge_documents") \
                .insert(data) \
                .execute()

            self.ingested_count += 1
            print(f"  ✅ Inserted new vendor {vendor_name}")


def main():
    """Main ingestion workflow"""

    ingester = VendorBackgroundIngester()

    # Paths
    json_path = Path(__file__).parent.parent / "knowledge_base" / "vendors" / "vendor_database.json"
    excel_path = Path(__file__).parent.parent / "outputs" / "Vendor_Background.xlsx"

    print("="*70)
    print("VENDOR BACKGROUND DATA INGESTION")
    print("="*70)

    # Ingest from JSON if it exists
    if json_path.exists():
        ingester.ingest_from_json(str(json_path))
    else:
        print(f"⚠️  JSON file not found: {json_path}")

    # Ingest from Excel if it exists
    if excel_path.exists():
        ingester.ingest_from_excel(str(excel_path))
    else:
        print(f"⚠️  Excel file not found: {excel_path}")

    print()
    print("="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"✅ Total new vendors ingested: {ingester.ingested_count}")
    print(f"🔄 Total vendors updated: {ingester.updated_count}")
    print(f"❌ Total errors: {ingester.error_count}")
    print()


if __name__ == "__main__":
    main()
