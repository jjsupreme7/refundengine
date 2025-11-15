#!/usr/bin/env python3
"""
Quick test of Enhanced RAG system
Run this to test the RAG with some sample questions
"""

import os
import sys
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import enhanced RAG
from core.enhanced_rag import EnhancedRAG

def main():
    """Test enhanced RAG with sample questions"""

    print("=" * 80)
    print("🚀 Enhanced RAG Test")
    print("=" * 80)

    # Initialize enhanced RAG
    rag = EnhancedRAG()

    # Test questions
    questions = [
        "How are digitally automated services taxed?",
        "What is the definition of custom software?",
        "When is use tax applied instead of sales tax?",
        "Are SaaS subscriptions taxable in Washington?",
        "What exemptions exist for software development tools?"
    ]

    print("\nTesting Enhanced RAG with sample questions...\n")

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print(f"{'='*80}")

        try:
            # Use search_with_decision (agentic RAG)
            result = rag.search_with_decision(question, top_k=3)

            print(f"\n✅ Action: {result['action']}")
            print(f"📝 Reasoning: {result['reasoning']}")
            print(f"💯 Confidence: {result['confidence']:.2%}")
            print(f"💰 Cost Saved: ${result['cost_saved']:.4f}")

            # Display results
            if result.get('results'):
                print(f"\n📚 Found {len(result['results'])} results:")
                for j, chunk in enumerate(result['results'][:3], 1):
                    if 'citation' in chunk:
                        print(f"\n  [{j}] {chunk.get('citation', 'N/A')}")
                        print(f"      Category: {chunk.get('law_category', 'N/A')}")
                        print(f"      Similarity: {chunk.get('similarity', 0):.2%}")
                        print(f"      Text: {chunk.get('chunk_text', '')[:150]}...")
                    elif chunk.get('source') == 'cached':
                        print(f"\n  [{j}] Source: CACHED DATA")
                        print(f"      Data: {str(chunk.get('data', {}))[:150]}...")
                    elif chunk.get('source') == 'structured_rules':
                        print(f"\n  [{j}] Source: STRUCTURED RULES")
                        print(f"      Data: {str(chunk.get('data', {}))[:150]}...")
            else:
                print("\n⚠️ No results found")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
