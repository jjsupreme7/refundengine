#!/usr/bin/env python3
"""
Import Historical Patterns from JSON

Reads JSON pattern files and imports them into Supabase.
Run this on your personal laptop where you have .env credentials.

Usage:
    python scripts/import_patterns_from_json.py --dir extracted_patterns

Imports:
    - vendor_patterns.json → vendor_products table
    - keyword_patterns.json → keyword_patterns table
    - citation_patterns.json → refund_citations table
"""

import json
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client

def import_vendor_patterns(supabase, vendor_data):
    """Import vendor patterns to vendor_products table."""
    print(f"\nImporting {len(vendor_data)} vendor patterns...")

    imported = 0
    updated = 0

    for vendor in vendor_data:
        try:
            # Check if vendor already exists
            existing = supabase.table('vendor_products')\
                .select('*')\
                .eq('vendor_name', vendor['vendor_name'])\
                .execute()

            if existing.data and len(existing.data) > 0:
                # Update existing
                supabase.table('vendor_products')\
                    .update({
                        'historical_sample_count': vendor['historical_sample_count'],
                        'historical_success_rate': vendor['historical_success_rate'],
                        'typical_refund_basis': vendor.get('typical_refund_basis'),
                        'vendor_keywords': vendor.get('vendor_keywords'),
                        'description_keywords': vendor.get('description_keywords'),
                    })\
                    .eq('vendor_name', vendor['vendor_name'])\
                    .execute()
                updated += 1
            else:
                # Insert new
                supabase.table('vendor_products').insert({
                    'vendor_name': vendor['vendor_name'],
                    'product_type': vendor.get('product_type', 'Unknown'),
                    'historical_sample_count': vendor['historical_sample_count'],
                    'historical_success_rate': vendor['historical_success_rate'],
                    'typical_refund_basis': vendor.get('typical_refund_basis'),
                    'vendor_keywords': vendor.get('vendor_keywords'),
                    'description_keywords': vendor.get('description_keywords'),
                }).execute()
                imported += 1

        except Exception as e:
            print(f"  Error importing vendor {vendor['vendor_name']}: {e}")

    print(f"  Imported: {imported} new vendors")
    print(f"  Updated: {updated} existing vendors")
    return imported, updated

def import_keyword_patterns(supabase, keyword_data):
    """Import keyword patterns to keyword_patterns table."""
    print(f"\nImporting {len(keyword_data)} keyword patterns...")

    imported = 0
    updated = 0

    for pattern in keyword_data:
        try:
            # Check if pattern already exists
            existing = supabase.table('keyword_patterns')\
                .select('*')\
                .eq('keyword_signature', pattern['keyword_signature'])\
                .execute()

            if existing.data and len(existing.data) > 0:
                # Update existing
                supabase.table('keyword_patterns')\
                    .update({
                        'keywords': pattern['keywords'],
                        'success_rate': pattern['success_rate'],
                        'sample_count': pattern['sample_count'],
                        'typical_basis': pattern.get('typical_basis'),
                    })\
                    .eq('keyword_signature', pattern['keyword_signature'])\
                    .execute()
                updated += 1
            else:
                # Insert new
                supabase.table('keyword_patterns').insert({
                    'keyword_signature': pattern['keyword_signature'],
                    'keywords': pattern['keywords'],
                    'success_rate': pattern['success_rate'],
                    'sample_count': pattern['sample_count'],
                    'typical_basis': pattern.get('typical_basis'),
                }).execute()
                imported += 1

        except Exception as e:
            print(f"  Error importing keyword pattern: {e}")

    print(f"  Imported: {imported} new patterns")
    print(f"  Updated: {updated} existing patterns")
    return imported, updated

def import_citation_patterns(supabase, citation_data):
    """Import citation patterns to refund_citations table."""
    print(f"\nImporting {len(citation_data)} citation patterns...")

    imported = 0
    updated = 0

    for citation in citation_data:
        try:
            # Check if citation already exists
            existing = supabase.table('refund_citations')\
                .select('*')\
                .eq('refund_basis', citation['refund_basis'])\
                .execute()

            example_cases = ', '.join(citation.get('example_cases', [])[:3])

            if existing.data and len(existing.data) > 0:
                # Update existing
                supabase.table('refund_citations')\
                    .update({
                        'usage_count': citation['usage_count'],
                        'example_cases': example_cases,
                    })\
                    .eq('refund_basis', citation['refund_basis'])\
                    .execute()
                updated += 1
            else:
                # Insert new
                supabase.table('refund_citations').insert({
                    'refund_basis': citation['refund_basis'],
                    'usage_count': citation['usage_count'],
                    'example_cases': example_cases,
                }).execute()
                imported += 1

        except Exception as e:
            print(f"  Error importing citation {citation['refund_basis']}: {e}")

    print(f"  Imported: {imported} new citations")
    print(f"  Updated: {updated} existing citations")
    return imported, updated

def main():
    parser = argparse.ArgumentParser(description='Import historical patterns from JSON')
    parser.add_argument('--dir', required=True, help='Directory with JSON pattern files')

    args = parser.parse_args()

    if not os.path.exists(args.dir):
        print(f"Error: Directory not found: {args.dir}")
        sys.exit(1)

    vendor_file = os.path.join(args.dir, 'vendor_patterns.json')
    keyword_file = os.path.join(args.dir, 'keyword_patterns.json')
    citation_file = os.path.join(args.dir, 'citation_patterns.json')

    # Check files exist
    for file in [vendor_file, keyword_file, citation_file]:
        if not os.path.exists(file):
            print(f"Warning: File not found: {file}")

    # Connect to Supabase
    print("Connecting to Supabase...")
    try:
        supabase = get_supabase_client()
        print("✓ Connected successfully")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        print("\nMake sure you have:")
        print("  1. Created .env file with credentials")
        print("  2. Deployed schema: bash scripts/deploy_historical_knowledge_schema.sh")
        sys.exit(1)

    # Load and import patterns
    print(f"\n{'='*70}")
    print("IMPORTING HISTORICAL PATTERNS")
    print(f"{'='*70}")

    total_imported = 0
    total_updated = 0

    # Import vendors
    if os.path.exists(vendor_file):
        with open(vendor_file, 'r', encoding='utf-8') as f:
            vendor_data = json.load(f)
        imported, updated = import_vendor_patterns(supabase, vendor_data)
        total_imported += imported
        total_updated += updated

    # Import keywords
    if os.path.exists(keyword_file):
        with open(keyword_file, 'r', encoding='utf-8') as f:
            keyword_data = json.load(f)
        if keyword_data:  # Only import if there's data
            imported, updated = import_keyword_patterns(supabase, keyword_data)
            total_imported += imported
            total_updated += updated

    # Import citations
    if os.path.exists(citation_file):
        with open(citation_file, 'r', encoding='utf-8') as f:
            citation_data = json.load(f)
        imported, updated = import_citation_patterns(supabase, citation_data)
        total_imported += imported
        total_updated += updated

    print(f"\n{'='*70}")
    print("IMPORT COMPLETE")
    print(f"{'='*70}")
    print(f"Total records imported: {total_imported}")
    print(f"Total records updated: {total_updated}")
    print(f"\nHistorical pattern learning is now active!")
    print(f"Test it with: python analysis/analyze_refunds.py --input test.xlsx --output results.xlsx")

if __name__ == '__main__':
    main()
