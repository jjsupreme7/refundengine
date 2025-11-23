#!/usr/bin/env python3
"""
Quick test to verify pattern integration in fast_batch_analyzer.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analysis.fast_batch_analyzer import (
    get_vendor_pattern,
    get_refund_basis_patterns,
    get_keyword_patterns,
)

def test_pattern_queries():
    print("🧪 TESTING PATTERN INTEGRATION")
    print("=" * 70)

    # Test 1: Query a known sales tax vendor
    print("\n1️⃣  Testing vendor pattern query (sales_tax)...")
    vendor_pattern = get_vendor_pattern("MOREDIRECT INC", "sales_tax")
    if vendor_pattern:
        print(f"   ✅ Found: {vendor_pattern['vendor_name']}")
        print(f"      Historical samples: {vendor_pattern.get('historical_sample_count', 0)}")
        print(f"      Typical refund: {vendor_pattern.get('typical_refund_basis', 'Unknown')}")
    else:
        print("   ❌ Vendor pattern not found")

    # Test 2: Query a known use tax vendor
    print("\n2️⃣  Testing vendor pattern query (use_tax)...")
    vendor_pattern = get_vendor_pattern("10UP INC", "use_tax")
    if vendor_pattern:
        print(f"   ✅ Found: {vendor_pattern['vendor_name']}")
        print(f"      Historical samples: {vendor_pattern.get('historical_sample_count', 0)}")
        print(f"      Typical refund: {vendor_pattern.get('typical_refund_basis', 'Unknown')}")
    else:
        print("   ❌ Vendor pattern not found")

    # Test 3: Query refund basis patterns
    print("\n3️⃣  Testing refund basis patterns (sales_tax)...")
    refund_patterns = get_refund_basis_patterns("sales_tax", limit=5)
    if refund_patterns:
        print(f"   ✅ Found {len(refund_patterns)} refund patterns")
        for pattern in refund_patterns[:3]:
            refund_basis = pattern.get('refund_basis', 'Unknown')
            usage_count = pattern.get('usage_count', 0)
            percentage = pattern.get('percentage', 0)
            print(f"      - {refund_basis}: {usage_count} uses ({percentage:.1f}%)")
    else:
        print("   ❌ Refund patterns not found")

    # Test 4: Query keyword patterns
    print("\n4️⃣  Testing keyword patterns (sales_tax)...")
    keyword_patterns = get_keyword_patterns("sales_tax")
    if keyword_patterns:
        print(f"   ✅ Found {len(keyword_patterns)} keyword categories")
        for category, keywords in keyword_patterns.items():
            print(f"      - {category}: {len(keywords)} keywords")
    else:
        print("   ❌ Keyword patterns not found")

    print("\n" + "=" * 70)
    print("✅ PATTERN INTEGRATION TEST COMPLETE")
    print("\n💡 Next step: Run analyzer with --tax-type flag:")
    print("   python analysis/fast_batch_analyzer.py --excel file.xlsx --tax-type sales_tax")


if __name__ == "__main__":
    test_pattern_queries()
