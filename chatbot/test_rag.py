#!/usr/bin/env python3
"""
RAG Testing Interface
Interactive tool to test vector search with metadata filters
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import argparse

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except:
    pass

# OpenAI
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Supabase
from supabase import create_client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)


class RAGTester:
    """Test RAG system with various queries and filters"""

    def __init__(self):
        self.embedding_model = "text-embedding-3-small"

    def get_embedding(self, text: str) -> List[float]:
        """Generate query embedding"""
        response = client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return response.data[0].embedding

    def search_tax_law(
        self,
        query: str,
        match_count: int = 5,
        threshold: float = 0.5,
        citation_filter: str = None,
        category_filter: str = None
    ) -> List[Dict]:
        """
        Search tax law knowledge base

        Args:
            query: Search query
            match_count: Number of results
            threshold: Similarity threshold (0-1)
            citation_filter: Filter by citation (e.g., "WAC 458-20-15502")
            category_filter: Filter by category (exemption, rate, etc.)
        """
        print(f"\n{'='*80}")
        print(f"SEARCHING TAX LAW")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Filters: citation={citation_filter}, category={category_filter}")
        print(f"{'='*80}\n")

        # Get embedding
        query_embedding = self.get_embedding(query)

        # Search using RPC function
        result = supabase.rpc('search_tax_law', {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': match_count
        }).execute()

        results = result.data if result.data else []

        # Apply additional filters if needed
        if citation_filter:
            results = [r for r in results if citation_filter.upper() in (r.get('citation') or '').upper()]

        if category_filter:
            results = [r for r in results if r.get('law_category') == category_filter]

        # Display results
        if not results:
            print("❌ No results found")
            return []

        print(f"✓ Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            similarity = result.get('similarity', 0)
            citation = result.get('citation', 'N/A')
            category = result.get('law_category', 'N/A')
            text = result.get('chunk_text', '')

            print(f"[{i}] Similarity: {similarity:.3f} | Citation: {citation} | Category: {category}")
            print(f"    {text[:200]}...")
            print()

        return results

    def search_vendor_background(
        self,
        query: str,
        match_count: int = 3,
        threshold: float = 0.5,
        vendor_filter: str = None
    ) -> List[Dict]:
        """
        Search vendor background knowledge base

        Args:
            query: Search query
            match_count: Number of results
            threshold: Similarity threshold (0-1)
            vendor_filter: Filter by vendor name
        """
        print(f"\n{'='*80}")
        print(f"SEARCHING VENDOR BACKGROUND")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Filters: vendor={vendor_filter}")
        print(f"{'='*80}\n")

        # Get embedding
        query_embedding = self.get_embedding(query)

        # Search using RPC function
        result = supabase.rpc('search_vendor_background', {
            'query_embedding': query_embedding,
            'vendor_filter': vendor_filter,
            'match_threshold': threshold,
            'match_count': match_count
        }).execute()

        results = result.data if result.data else []

        # Display results
        if not results:
            print("❌ No results found")
            return []

        print(f"✓ Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            similarity = result.get('similarity', 0)
            vendor = result.get('vendor_name', 'N/A')
            doc_category = result.get('document_category', 'N/A')
            text = result.get('chunk_text', '')

            print(f"[{i}] Similarity: {similarity:.3f} | Vendor: {vendor} | Category: {doc_category}")
            print(f"    {text[:200]}...")
            print()

        return results

    def show_stats(self):
        """Show knowledge base statistics"""
        print(f"\n{'='*80}")
        print(f"KNOWLEDGE BASE STATISTICS")
        print(f"{'='*80}\n")

        # Count documents
        docs = supabase.table('knowledge_documents').select('*').execute()
        tax_docs = [d for d in docs.data if d['document_type'] == 'tax_law']
        vendor_docs = [d for d in docs.data if d['document_type'] == 'vendor_background']

        print(f"Documents:")
        print(f"  Tax Law:            {len(tax_docs)}")
        print(f"  Vendor Background:  {len(vendor_docs)}")
        print(f"  Total:              {len(docs.data)}")
        print()

        # Count chunks
        tax_chunks = supabase.table('tax_law_chunks').select('id', count='exact').execute()
        vendor_chunks = supabase.table('vendor_background_chunks').select('id', count='exact').execute()

        tax_chunk_count = tax_chunks.count if hasattr(tax_chunks, 'count') else 0
        vendor_chunk_count = vendor_chunks.count if hasattr(vendor_chunks, 'count') else 0

        print(f"Chunks:")
        print(f"  Tax Law:            {tax_chunk_count}")
        print(f"  Vendor Background:  {vendor_chunk_count}")
        print(f"  Total:              {tax_chunk_count + vendor_chunk_count}")
        print()

        # List tax law documents
        if tax_docs:
            print("Tax Law Documents:")
            for doc in tax_docs:
                citation = doc.get('citation', 'N/A')
                category = doc.get('law_category', 'N/A')
                chunks = doc.get('total_chunks', 0)
                print(f"  • {citation:30} | {category:15} | {chunks} chunks")
            print()

        # List vendor documents
        if vendor_docs:
            print("Vendor Documents:")
            for doc in vendor_docs:
                vendor = doc.get('vendor_name', 'N/A')
                category = doc.get('vendor_category', 'N/A')
                chunks = doc.get('total_chunks', 0)
                print(f"  • {vendor:30} | {category:15} | {chunks} chunks")
            print()

        print(f"{'='*80}\n")

    def interactive_mode(self):
        """Interactive search mode"""
        print("\n" + "="*80)
        print("RAG TESTING INTERFACE - Interactive Mode")
        print("="*80)
        print("\nCommands:")
        print("  tax <query>              - Search tax law")
        print("  vendor <query>           - Search vendor background")
        print("  stats                    - Show knowledge base stats")
        print("  quit                     - Exit")
        print("\nFilters (append to tax/vendor commands):")
        print("  --citation WAC-XXX       - Filter by citation")
        print("  --category exemption     - Filter by category")
        print("  --vendor Nokia           - Filter by vendor name")
        print("  --threshold 0.7          - Set similarity threshold")
        print("  --count 10               - Number of results")
        print("\n" + "="*80 + "\n")

        while True:
            try:
                user_input = input("🔍 > ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break

                if user_input.lower() == 'stats':
                    self.show_stats()
                    continue

                # Parse command
                parts = user_input.split()
                cmd = parts[0].lower()

                if cmd not in ['tax', 'vendor']:
                    print("❌ Unknown command. Use: tax, vendor, stats, quit")
                    continue

                # Extract query and filters
                query_parts = []
                filters = {
                    'citation': None,
                    'category': None,
                    'vendor': None,
                    'threshold': 0.5,
                    'count': 5
                }

                i = 1
                while i < len(parts):
                    if parts[i].startswith('--'):
                        filter_name = parts[i][2:]
                        if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                            filter_value = parts[i + 1]
                            if filter_name in ['threshold', 'count']:
                                filters[filter_name] = float(filter_value) if filter_name == 'threshold' else int(filter_value)
                            else:
                                filters[filter_name] = filter_value
                            i += 2
                        else:
                            i += 1
                    else:
                        query_parts.append(parts[i])
                        i += 1

                query = ' '.join(query_parts)

                if not query:
                    print("❌ Please provide a search query")
                    continue

                # Execute search
                if cmd == 'tax':
                    self.search_tax_law(
                        query,
                        match_count=filters['count'],
                        threshold=filters['threshold'],
                        citation_filter=filters['citation'],
                        category_filter=filters['category']
                    )
                else:  # vendor
                    self.search_vendor_background(
                        query,
                        match_count=filters['count'],
                        threshold=filters['threshold'],
                        vendor_filter=filters['vendor']
                    )

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(description='Test RAG system')
    parser.add_argument('--mode', choices=['interactive', 'tax', 'vendor', 'stats'], default='interactive',
                       help='Mode: interactive, tax, vendor, or stats')
    parser.add_argument('--query', help='Search query (for tax/vendor modes)')
    parser.add_argument('--citation', help='Filter by citation')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--vendor', help='Filter by vendor')
    parser.add_argument('--threshold', type=float, default=0.5, help='Similarity threshold')
    parser.add_argument('--count', type=int, default=5, help='Number of results')

    args = parser.parse_args()

    tester = RAGTester()

    if args.mode == 'interactive':
        tester.interactive_mode()
    elif args.mode == 'stats':
        tester.show_stats()
    elif args.mode == 'tax':
        if not args.query:
            print("Error: --query required for tax search")
            sys.exit(1)
        tester.search_tax_law(
            args.query,
            match_count=args.count,
            threshold=args.threshold,
            citation_filter=args.citation,
            category_filter=args.category
        )
    elif args.mode == 'vendor':
        if not args.query:
            print("Error: --query required for vendor search")
            sys.exit(1)
        tester.search_vendor_background(
            args.query,
            match_count=args.count,
            threshold=args.threshold,
            vendor_filter=args.vendor
        )


if __name__ == '__main__':
    main()
