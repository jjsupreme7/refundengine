#!/usr/bin/env python3
"""
Test that vendor background is properly integrated into RAG.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_supabase_client
from core.enhanced_rag import EnhancedRAG

def test_vendor_background_retrieval():
    """Test that vendor background can be retrieved."""

    print("=" * 80)
    print("TESTING VENDOR BACKGROUND RAG INTEGRATION")
    print("=" * 80)

    supabase = get_supabase_client()
    rag = EnhancedRAG(supabase)

    # Test 1: Direct vendor background retrieval
    print("\n1. Testing direct vendor background retrieval...")
    test_vendors = ["Microsoft", "Salesforce", "Oracle", "Deloitte"]

    for vendor in test_vendors:
        result = rag.get_vendor_background(vendor)
        if result:
            print(f"   ✅ {vendor}: Found - {result.get('industry')}")
        else:
            print(f"   ❌ {vendor}: Not found in database")

    # Test 2: RAG search with vendor name
    print("\n2. Testing RAG search with vendor context...")
    query = "Is custom software development taxable in Washington?"
    vendor_name = "Microsoft Corporation"

    results = rag.search_enhanced(query, top_k=3, vendor_name=vendor_name)

    if results and len(results) > 0:
        print(f"\n   ✅ Retrieved {len(results)} results")

        # Check if vendor background is attached
        if 'vendor_background' in results[0]:
            print(f"   ✅ Vendor background successfully attached to results!")
            vb = results[0]['vendor_background']
            print(f"      Industry: {vb.get('industry')}")
            print(f"      Business Model: {vb.get('business_model')}")
        else:
            print(f"   ❌ Vendor background NOT found in results")
    else:
        print(f"   ❌ No results returned")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    test_vendor_background_retrieval()
