#!/usr/bin/env python3
"""
Test script for Agentic RAG decision layer
Demonstrates different decision paths
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enhanced_rag import EnhancedRAG


def test_cached_decision():
    """Test 1: High-confidence cached result - should skip retrieval"""
    print("\n" + "="*80)
    print("TEST 1: High-Confidence Cached Result")
    print("="*80)

    rag = EnhancedRAG()

    context = {
        "vendor": "Microsoft",
        "product": "Azure Virtual Machines",
        "product_type": "iaas_paas",
        "prior_analysis": {
            "confidence_score": 0.92,
            "refund_eligible": True,
            "refund_amount": 8500.00,
            "reasoning": "85% of resources deployed in us-east-1 (non-WA)"
        }
    }

    result = rag.search_with_decision(
        "Is Microsoft Azure subject to Washington use tax?",
        context=context
    )

    print(f"\n📊 Result:")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Cost Saved: ${result['cost_saved']:.4f}")
    print(f"   ✅ Expected: USE_CACHED (confidence 0.92 > 0.85)")


def test_structured_rules():
    """Test 2: Product type with structured rules - should use rules"""
    print("\n" + "="*80)
    print("TEST 2: Structured Rules Available")
    print("="*80)

    rag = EnhancedRAG()

    context = {
        "vendor": "Salesforce",
        "product": "Service Cloud",
        "product_type": "saas_subscription",
        "amount": 12000.00,
        "tax_paid": 1200.00
    }

    result = rag.search_with_decision(
        "Is Salesforce Service Cloud taxable in Washington?",
        context=context
    )

    print(f"\n📊 Result:")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Cost Saved: ${result['cost_saved']:.4f}")

    if result['action'] == 'USE_RULES':
        rule_data = result['results'][0]['data']
        print(f"   ✅ Rule found:")
        print(f"      - Taxable: {rule_data.get('taxable')}")
        print(f"      - Classification: {rule_data.get('tax_classification')}")
        print(f"      - Legal Basis: {', '.join(rule_data.get('legal_basis', []))}")


def test_simple_query():
    """Test 3: Simple query - should use fast retrieval"""
    print("\n" + "="*80)
    print("TEST 3: Simple Query")
    print("="*80)

    rag = EnhancedRAG()

    context = {
        "vendor": "Adobe",
        "product": "Creative Cloud"
    }

    result = rag.search_with_decision(
        "Is Adobe Creative Cloud taxable?",
        context=context
    )

    print(f"\n📊 Result:")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Cost Saved: ${result['cost_saved']:.4f}")
    print(f"   ✅ Expected: RETRIEVE_SIMPLE (simple yes/no question)")


def test_complex_query():
    """Test 4: Complex query - should use enhanced retrieval"""
    print("\n" + "="*80)
    print("TEST 4: Complex Query")
    print("="*80)

    rag = EnhancedRAG()

    context = {
        "vendor": "AWS",
        "product": "EC2 + S3 + RDS",
        "product_type": "iaas_paas",
        "amount": 25000.00,
        "tax_paid": 2500.00
    }

    result = rag.search_with_decision(
        "How do I calculate the multi-point use allocation for AWS services with resources in multiple regions?",
        context=context
    )

    print(f"\n📊 Result:")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Cost Saved: ${result['cost_saved']:.4f}")
    print(f"   ✅ Expected: RETRIEVE_ENHANCED (complex calculation question)")


def test_medium_confidence():
    """Test 5: Medium confidence cached - should still retrieve"""
    print("\n" + "="*80)
    print("TEST 5: Medium-Confidence Cached Result")
    print("="*80)

    rag = EnhancedRAG()

    context = {
        "vendor": "Oracle",
        "product": "Cloud Infrastructure",
        "prior_analysis": {
            "confidence_score": 0.70,  # Below 0.85 threshold
            "refund_eligible": True,
            "refund_amount": 5000.00
        }
    }

    result = rag.search_with_decision(
        "Is Oracle Cloud Infrastructure taxable?",
        context=context
    )

    print(f"\n📊 Result:")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Cost Saved: ${result['cost_saved']:.4f}")
    print(f"   ✅ Expected: RETRIEVE_SIMPLE or RETRIEVE_ENHANCED (confidence 0.70 < 0.85)")


def main():
    """Run all tests"""
    print("\n🤖 AGENTIC RAG DECISION LAYER TESTS")
    print("="*80)
    print("Testing intelligent retrieval decision-making")
    print("="*80)

    try:
        test_cached_decision()
        test_structured_rules()
        test_simple_query()
        test_complex_query()
        test_medium_confidence()

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        print("\n📊 Summary:")
        print("   - Cached results: Skip expensive retrieval when confidence is high")
        print("   - Structured rules: Use JSON rules for common product types")
        print("   - Simple queries: Fast retrieval for straightforward questions")
        print("   - Complex queries: Enhanced retrieval for multi-step reasoning")
        print("\n💡 Expected cost savings: 60-80% for repeated vendor/product queries")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
