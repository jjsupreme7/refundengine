#!/usr/bin/env python3
"""
Upload Pattern Data to Supabase

Uploads cleaned pattern files to Supabase tables:
- vendor_patterns (sales + use tax)
- refund_basis_patterns (sales + use tax)
- keyword_patterns (sales + use tax)

Usage:
    python scripts/upload_patterns_to_supabase.py

    # Dry run (preview without uploading)
    python scripts/upload_patterns_to_supabase.py --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client  # noqa: E402


def load_json_file(file_path: Path) -> Any:
    """Load JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def upload_vendor_patterns(supabase, tax_type: str, data: List[Dict], dry_run: bool = False):
    """Upload vendor patterns to vendor_products table"""

    print(f"\n{'='*70}")
    print(f"Uploading Vendor Patterns - {tax_type.upper()}")
    print(f"{'='*70}")

    if not isinstance(data, list):
        print("❌ Error: Expected list of vendor objects")
        return

    records = []
    for vendor_data in data:
        if not isinstance(vendor_data, dict):
            continue

        record = {
            "vendor_name": vendor_data.get("vendor_name", "Unknown"),
            "tax_type": tax_type,
            "historical_sample_count": vendor_data.get("historical_sample_count", 0),
            "historical_success_rate": vendor_data.get("historical_success_rate"),
            "typical_refund_basis": vendor_data.get("typical_refund_basis"),
            "typical_final_decision": vendor_data.get("typical_final_decision"),
            "common_tax_categories": vendor_data.get("common_tax_categories"),
            "common_refund_bases": vendor_data.get("common_refund_bases"),
            "description_keywords": vendor_data.get("description_keywords"),
            "common_allocation_methods": vendor_data.get("common_allocation_methods"),
            "product_type": vendor_data.get("product_type"),
            "learning_source": "historical_patterns",  # Mark as pattern data
        }

        records.append(record)

    print(f"  📊 Total vendors: {len(records)}")
    print(f"  📋 Sample vendors:")
    for rec in records[:3]:
        print(f"    - {rec['vendor_name']}: {rec['historical_sample_count']} samples")

    if dry_run:
        print(f"  🔍 DRY RUN: Would upload {len(records)} vendor records to vendor_products table")
        return

    # Upload in batches (Supabase has limits)
    batch_size = 500
    total_uploaded = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        try:
            # Use vendor_products table (existing)
            result = supabase.table("vendor_products").upsert(
                batch,
                on_conflict="vendor_name,tax_type"
            ).execute()

            total_uploaded += len(batch)
            print(f"  ✅ Uploaded batch {i // batch_size + 1}: {len(batch)} records ({total_uploaded}/{len(records)})")

        except Exception as e:
            print(f"  ❌ Error uploading batch: {e}")
            raise

    print(f"\n✅ Total uploaded: {total_uploaded} vendor patterns to vendor_products")


def upload_refund_basis_patterns(supabase, tax_type: str, data: Any, dry_run: bool = False):
    """Upload refund basis patterns to refund_citations table"""

    print(f"\n{'='*70}")
    print(f"Uploading Refund Basis Patterns - {tax_type.upper()}")
    print(f"{'='*70}")

    # Handle both list and dict formats
    if isinstance(data, dict):
        patterns = data
    elif isinstance(data, list):
        patterns = {p.get("refund_basis", f"pattern_{i}"): p for i, p in enumerate(data)}
    else:
        print("❌ Error: Unexpected data format")
        return

    records = []
    for refund_basis, pattern_data in patterns.items():
        if isinstance(pattern_data, dict):
            record = {
                "refund_basis": pattern_data.get("refund_basis", refund_basis),
                "tax_type": tax_type,
                "usage_count": pattern_data.get("usage_count", 0),
                "percentage": pattern_data.get("percentage"),
                "vendor_count": pattern_data.get("vendor_count", 0),
                "all_vendors": pattern_data.get("all_vendors"),
                "typical_final_decision": pattern_data.get("typical_final_decision"),
                "legal_citation": None,  # Existing column, set to NULL for pattern data
                "example_cases": None,   # Existing column, set to NULL for pattern data
            }
            records.append(record)

    print(f"  📊 Total patterns: {len(records)}")
    print(f"  📋 Top patterns:")
    sorted_records = sorted(records, key=lambda x: x["usage_count"], reverse=True)
    for rec in sorted_records[:5]:
        print(f"    - {rec['refund_basis']}: {rec['usage_count']} uses ({rec.get('percentage', 0):.1f}%)")

    if dry_run:
        print(f"  🔍 DRY RUN: Would upload {len(records)} refund basis records to refund_citations table")
        return

    try:
        # Use refund_citations table (existing)
        result = supabase.table("refund_citations").upsert(
            records,
            on_conflict="refund_basis,tax_type"
        ).execute()

        print(f"\n✅ Uploaded {len(records)} refund basis patterns to refund_citations")

    except Exception as e:
        print(f"  ❌ Error uploading: {e}")
        raise


def upload_keyword_patterns(supabase, tax_type: str, data: List[Dict], dry_run: bool = False):
    """Upload keyword patterns for a tax type"""

    print(f"\n{'='*70}")
    print(f"Uploading Keyword Patterns - {tax_type.upper()}")
    print(f"{'='*70}")

    if not isinstance(data, list):
        print("❌ Error: Expected list of category objects")
        return

    records = []
    for category_obj in data:
        if not isinstance(category_obj, dict):
            continue

        category = category_obj.get("category", "unknown")
        keywords_data = category_obj.get("keywords", [])

        # Extract just the keyword/term strings
        keywords = []
        for kw in keywords_data:
            if isinstance(kw, dict):
                keyword = kw.get("keyword") or kw.get("term", "")
            else:
                keyword = str(kw)

            if keyword:
                keywords.append(keyword)

        record = {
            "category": category,
            "tax_type": tax_type,
            "keywords": keywords,
            "keyword_count": len(keywords),
        }

        records.append(record)

    print(f"  📊 Total categories: {len(records)}")
    for rec in records:
        print(f"    - {rec['category']}: {rec['keyword_count']} keywords")

    if dry_run:
        print(f"  🔍 DRY RUN: Would upload {len(records)} keyword category records")
        return

    try:
        result = supabase.table("keyword_patterns").upsert(
            records,
            on_conflict="category,tax_type"
        ).execute()

        print(f"\n✅ Uploaded {len(records)} keyword pattern categories")

    except Exception as e:
        print(f"  ❌ Error uploading: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Upload patterns to Supabase")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be uploaded without actually uploading"
    )

    args = parser.parse_args()

    print("🚀 PATTERN UPLOAD TO SUPABASE")
    print("="*70)

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No data will be uploaded")
        print("="*70)

    # Initialize Supabase
    print("\n🔌 Connecting to Supabase...")
    try:
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return 1

    # Define paths
    project_root = Path(__file__).parent.parent
    patterns_dir = project_root / "extracted_patterns"

    # ==========================================
    # SALES TAX PATTERNS
    # ==========================================
    print("\n\n📊 SALES TAX PATTERNS")
    print("="*70)

    sales_tax_dir = patterns_dir / "sales_tax"

    # Vendor patterns
    vendor_file = sales_tax_dir / "vendor_patterns.json"
    if vendor_file.exists():
        print(f"\n📁 Loading: {vendor_file}")
        vendor_data = load_json_file(vendor_file)
        upload_vendor_patterns(supabase, "sales_tax", vendor_data, dry_run=args.dry_run)
    else:
        print(f"⚠️  File not found: {vendor_file}")

    # Refund basis patterns
    refund_file = sales_tax_dir / "refund_basis_patterns.json"
    if refund_file.exists():
        print(f"\n📁 Loading: {refund_file}")
        refund_data = load_json_file(refund_file)
        upload_refund_basis_patterns(supabase, "sales_tax", refund_data, dry_run=args.dry_run)
    else:
        print(f"⚠️  File not found: {refund_file}")

    # Keyword patterns
    keyword_file = sales_tax_dir / "keyword_patterns.json"
    if keyword_file.exists():
        print(f"\n📁 Loading: {keyword_file}")
        keyword_data = load_json_file(keyword_file)
        upload_keyword_patterns(supabase, "sales_tax", keyword_data, dry_run=args.dry_run)
    else:
        print(f"⚠️  File not found: {keyword_file}")

    # ==========================================
    # USE TAX PATTERNS
    # ==========================================
    print("\n\n📊 USE TAX PATTERNS")
    print("="*70)

    use_tax_dir = patterns_dir / "use_tax"

    # Vendor patterns
    vendor_file = use_tax_dir / "vendor_patterns.json"
    if vendor_file.exists():
        print(f"\n📁 Loading: {vendor_file}")
        vendor_data = load_json_file(vendor_file)
        upload_vendor_patterns(supabase, "use_tax", vendor_data, dry_run=args.dry_run)
    else:
        print(f"⚠️  File not found: {vendor_file}")

    # Refund basis patterns
    refund_file = use_tax_dir / "refund_basis_patterns.json"
    if refund_file.exists():
        print(f"\n📁 Loading: {refund_file}")
        refund_data = load_json_file(refund_file)
        upload_refund_basis_patterns(supabase, "use_tax", refund_data, dry_run=args.dry_run)
    else:
        print(f"⚠️  File not found: {refund_file}")

    # Keyword patterns
    keyword_file = use_tax_dir / "keyword_patterns.json"
    if keyword_file.exists():
        print(f"\n📁 Loading: {keyword_file}")
        keyword_data = load_json_file(keyword_file)
        upload_keyword_patterns(supabase, "use_tax", keyword_data, dry_run=args.dry_run)
    else:
        print(f"⚠️  File not found: {keyword_file}")

    # ==========================================
    # DONE
    # ==========================================
    print("\n" + "="*70)
    if args.dry_run:
        print("✅ DRY RUN COMPLETE - No data was uploaded")
        print("\n💡 Run without --dry-run to actually upload the data")
    else:
        print("✅ UPLOAD COMPLETE!")
        print("\n📊 Summary:")
        print("  - Sales tax: vendors, refund basis, keywords")
        print("  - Use tax: vendors, refund basis, keywords")
        print("\n💡 You can now use these patterns in fast_batch_analyzer.py")

    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
