#!/usr/bin/env python3
"""
Pattern Cleanup Script

Removes analyst decision categories and junk keywords from pattern files.

What gets removed:
- refund_basis_terms (analyst decisions → belongs in refund_basis_patterns table)
- final_decisions (workflow outcomes → not useful)
- gl_account_descriptions (accounting codes → not useful)
- material_groups (SAP codes → not useful)
- allocation_methods (methodology → not useful)
- location_keywords (messy data → not useful)
- Truncated/junk keywords from description_keywords

What gets kept:
- tax_categories (Services, Hardware, License, etc.)
- product_descriptors (meaningful product/service keywords)

Usage:
    python scripts/clean_patterns.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


# Categories to keep
KEEP_CATEGORIES = {
    "tax_categories",
    "product_types",  # Will rename to product_descriptors
}

# Categories to remove
REMOVE_CATEGORIES = {
    "refund_basis_terms",      # Analyst decisions
    "final_decisions",         # Workflow outcomes
    "gl_account_descriptions", # Accounting codes
    "material_groups",         # SAP codes
    "allocation_methods",      # Methodology
    "location_keywords",       # Messy location data
}

# Generic/junk words to filter out from description keywords
JUNK_KEYWORDS = {
    "One", "New", "Act", "Keep", "Phase", "Request", "Fee",
    "Site", "Orr", "Bolin", "AEHC", "EOL", "Non_POR",
    "SPECIAL", "PROJECT", "Active", "Anchor", "funding"
}

# Code patterns to filter (numbers, truncated words)
CODE_PATTERNS = [
    r'^[A-Z0-9]{2,6}$',  # L600, SE02, etc.
    r'^[A-Za-z]{2,4}i$', # Acti, Ente, Protec-ending
    r'^[A-Za-z]{2,4}a$', # Repla-ending
]


def is_junk_keyword(keyword: str) -> bool:
    """Check if keyword is junk that should be filtered"""

    # Too short (less than 4 chars, except valid short terms)
    VALID_SHORT = {"DAS", "Fee", "SIF", "EOL"}
    if len(keyword) < 4 and keyword not in VALID_SHORT:
        return True

    # In junk list
    if keyword in JUNK_KEYWORDS:
        return True

    # Matches code pattern
    for pattern in CODE_PATTERNS:
        if re.match(pattern, keyword):
            return True

    # Contains parentheses or special chars (except hyphen)
    if re.search(r'[(){}[\]<>]', keyword):
        return True

    return False


def clean_description_keywords(keywords: List[Dict]) -> List[Dict]:
    """Clean description_keywords by removing junk"""
    cleaned = []

    for item in keywords:
        keyword = item.get("keyword") or item.get("term", "")

        if not keyword:
            continue

        # Filter junk
        if is_junk_keyword(keyword):
            continue

        cleaned.append(item)

    return cleaned


def clean_keyword_patterns(input_file: Path, output_file: Path, tax_type: str):
    """Clean keyword patterns file"""

    print(f"\n{'='*70}")
    print(f"Cleaning: {input_file.name}")
    print(f"Tax Type: {tax_type}")
    print(f"{'='*70}")

    # Load input
    with open(input_file, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("❌ Error: Expected list of categories")
        return

    cleaned_categories = []
    removed_categories = []

    for category_obj in data:
        category = category_obj.get("category", "")

        # Remove unwanted categories
        if category in REMOVE_CATEGORIES:
            removed_categories.append(category)
            print(f"  ❌ Removing category: {category}")
            continue

        # Keep wanted categories
        if category in KEEP_CATEGORIES:
            # Special handling for description_keywords
            if category == "description_keywords":
                original_count = len(category_obj.get("keywords", []))
                category_obj["keywords"] = clean_description_keywords(
                    category_obj["keywords"]
                )
                new_count = len(category_obj["keywords"])
                print(f"  ✅ Cleaned {category}: {original_count} → {new_count} keywords "
                      f"({original_count - new_count} removed)")
            else:
                keyword_count = len(category_obj.get("keywords", []))
                print(f"  ✅ Keeping {category}: {keyword_count} keywords")

            cleaned_categories.append(category_obj)
        else:
            # Handle description_keywords (use tax only)
            if category == "description_keywords":
                original_count = len(category_obj.get("keywords", []))
                category_obj["keywords"] = clean_description_keywords(
                    category_obj["keywords"]
                )
                new_count = len(category_obj["keywords"])
                print(f"  ✅ Cleaned {category}: {original_count} → {new_count} keywords "
                      f"({original_count - new_count} removed)")
                cleaned_categories.append(category_obj)

    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"  Categories kept: {len(cleaned_categories)}")
    print(f"  Categories removed: {len(removed_categories)}")
    if removed_categories:
        print(f"  Removed: {', '.join(removed_categories)}")

    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cleaned_categories, f, indent=2)

    print(f"\n✅ Cleaned file saved: {output_file}")


def clean_vendor_patterns(input_file: Path, output_file: Path, tax_type: str):
    """Clean vendor patterns - remove junk from description_keywords"""

    print(f"\n{'='*70}")
    print(f"Cleaning: {input_file.name}")
    print(f"Tax Type: {tax_type}")
    print(f"{'='*70}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Handle both dict and list formats
    if isinstance(data, dict):
        vendors = data
    elif isinstance(data, list):
        vendors = {v.get("vendor_name", f"vendor_{i}"): v for i, v in enumerate(data)}
    else:
        print("❌ Error: Unexpected data format")
        return

    total_vendors = len(vendors)
    total_keywords_before = 0
    total_keywords_after = 0

    cleaned_vendors = []

    for vendor_name, vendor_data in vendors.items():
        if not isinstance(vendor_data, dict):
            continue

        # Get description_keywords
        desc_keywords = vendor_data.get("description_keywords", [])

        if desc_keywords:
            total_keywords_before += len(desc_keywords)

            # Clean keywords
            cleaned = []
            for keyword in desc_keywords:
                # Skip numeric codes (001, 002, etc.)
                if re.match(r'^\d{3,}$', keyword):
                    continue

                # Skip pure numbers
                if keyword.isdigit():
                    continue

                # Skip product codes (PO12345, AA-XCAP-*, etc.)
                if re.match(r'^[A-Z]{2}\d+', keyword) or '-' in keyword and len(keyword) > 10:
                    continue

                # Skip too short (< 4 chars) unless it's a known acronym
                VALID_SHORT = {"DAS", "AWS", "SaaS", "API", "VPN", "IoT", "ACS"}
                if len(keyword) < 4 and keyword not in VALID_SHORT:
                    continue

                # Skip generic single words
                SKIP_GENERIC = {
                    "from", "with", "and", "the", "for", "Active", "New", "One",
                    "emails", "shipped", "Brian", "Venue"
                }
                if keyword in SKIP_GENERIC:
                    continue

                # Skip if it contains punctuation (like "Eldredge,")
                if re.search(r'[,;!?]', keyword):
                    continue

                # Skip if it's the vendor name itself (case-insensitive)
                vendor_name_words = set(vendor_name.upper().split())
                if keyword.upper() in vendor_name_words:
                    continue

                # Keep it!
                cleaned.append(keyword)

            vendor_data["description_keywords"] = cleaned
            total_keywords_after += len(cleaned)

        cleaned_vendors.append(vendor_data)

    # Summary
    print(f"  ✅ Vendor count: {total_vendors}")
    print(f"  🧹 Description keywords: {total_keywords_before} → {total_keywords_after} "
          f"({total_keywords_before - total_keywords_after} removed)")

    # Sample
    print(f"  📋 Sample vendors:")
    for vendor_data in cleaned_vendors[:5]:
        vendor_name = vendor_data.get("vendor_name", "Unknown")
        sample_count = vendor_data.get("historical_sample_count", 0)
        typical_basis = vendor_data.get("typical_refund_basis", "N/A")
        keywords = vendor_data.get("description_keywords", [])
        print(f"    - {vendor_name}: {sample_count} samples, typical: {typical_basis}")
        if keywords:
            print(f"      Keywords: {', '.join(keywords[:5])}")

    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cleaned_vendors, f, indent=2)

    print(f"\n✅ Cleaned file saved: {output_file}")


def validate_refund_basis_patterns(input_file: Path, tax_type: str):
    """Validate refund basis patterns (no cleaning needed, just report)"""

    print(f"\n{'='*70}")
    print(f"Validating: {input_file.name}")
    print(f"Tax Type: {tax_type}")
    print(f"{'='*70}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    if isinstance(data, dict):
        patterns = list(data.keys())
    elif isinstance(data, list):
        patterns = data
    else:
        print("❌ Error: Unexpected data format")
        return

    print(f"  ✅ Refund basis pattern count: {len(patterns)}")
    print(f"  📋 Top patterns:")
    for i, pattern_data in enumerate(list(patterns)[:5], 1):
        if isinstance(data, dict):
            pattern_obj = data[pattern_data]
        else:
            pattern_obj = pattern_data if isinstance(pattern_data, dict) else {}

        if isinstance(pattern_obj, dict):
            refund_basis = pattern_obj.get("refund_basis", pattern_data)
            usage_count = pattern_obj.get("usage_count", "N/A")
            percentage = pattern_obj.get("percentage", "N/A")
            print(f"    {i}. {refund_basis}: {usage_count} uses ({percentage}%)")

    print(f"\n✅ Refund basis patterns look good (no cleaning needed)")


def main():
    project_root = Path(__file__).parent.parent
    patterns_dir = project_root / "extracted_patterns"
    cleaned_dir = project_root / "extracted_patterns_cleaned"

    print("🧹 PATTERN CLEANUP SCRIPT")
    print("="*70)

    # ==========================================
    # SALES TAX PATTERNS
    # ==========================================
    print("\n📊 SALES TAX PATTERNS")
    print("="*70)

    # Clean keyword patterns
    clean_keyword_patterns(
        input_file=patterns_dir / "keyword_patterns.json",
        output_file=cleaned_dir / "sales_tax" / "keyword_patterns.json",
        tax_type="sales_tax"
    )

    # Clean vendor patterns
    clean_vendor_patterns(
        input_file=patterns_dir / "vendor_patterns.json",
        output_file=cleaned_dir / "sales_tax" / "vendor_patterns.json",
        tax_type="sales_tax"
    )

    # Validate refund basis patterns (just copy)
    validate_refund_basis_patterns(
        input_file=patterns_dir / "refund_basis_patterns.json",
        tax_type="sales_tax"
    )

    # ==========================================
    # USE TAX PATTERNS
    # ==========================================
    print("\n📊 USE TAX PATTERNS")
    print("="*70)

    # Clean keyword patterns
    clean_keyword_patterns(
        input_file=patterns_dir / "use_tax" / "keyword_patterns.json",
        output_file=cleaned_dir / "use_tax" / "keyword_patterns.json",
        tax_type="use_tax"
    )

    # Clean vendor patterns
    clean_vendor_patterns(
        input_file=patterns_dir / "use_tax" / "vendor_patterns.json",
        output_file=cleaned_dir / "use_tax" / "vendor_patterns.json",
        tax_type="use_tax"
    )

    # Validate refund basis patterns (just copy)
    validate_refund_basis_patterns(
        input_file=patterns_dir / "use_tax" / "refund_basis_patterns.json",
        tax_type="use_tax"
    )

    # ==========================================
    # COPY REFUND BASIS PATTERNS (no cleaning needed)
    # ==========================================
    print(f"\n📁 COPYING REFUND BASIS PATTERNS")
    print("="*70)

    import shutil

    # Sales tax
    shutil.copy2(
        patterns_dir / "refund_basis_patterns.json",
        cleaned_dir / "sales_tax" / "refund_basis_patterns.json"
    )
    print(f"  ✅ Copied sales_tax/refund_basis_patterns.json")

    # Use tax
    shutil.copy2(
        patterns_dir / "use_tax" / "refund_basis_patterns.json",
        cleaned_dir / "use_tax" / "refund_basis_patterns.json"
    )
    print(f"  ✅ Copied use_tax/refund_basis_patterns.json")

    # ==========================================
    # DONE
    # ==========================================
    print(f"\n✅ CLEANUP COMPLETE!")
    print("="*70)
    print(f"Output directory: {cleaned_dir}")
    print(f"\n📂 Cleaned pattern files:")
    print(f"  Sales Tax:")
    print(f"    - {cleaned_dir / 'sales_tax' / 'keyword_patterns.json'}")
    print(f"    - {cleaned_dir / 'sales_tax' / 'vendor_patterns.json'}")
    print(f"    - {cleaned_dir / 'sales_tax' / 'refund_basis_patterns.json'}")
    print(f"  Use Tax:")
    print(f"    - {cleaned_dir / 'use_tax' / 'keyword_patterns.json'}")
    print(f"    - {cleaned_dir / 'use_tax' / 'vendor_patterns.json'}")
    print(f"    - {cleaned_dir / 'use_tax' / 'refund_basis_patterns.json'}")
    print(f"\n👀 Review the cleaned files and if you like them,")
    print(f"   we can delete the originals and use these instead!")


if __name__ == "__main__":
    main()
