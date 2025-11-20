#!/usr/bin/env python3
"""
RAG Chatbot Interface with Enhanced RAG
Ask questions in natural language and get answers from the knowledge base

Now using Enhanced RAG for better accuracy:
- Corrective RAG (validates legal citations)
- Reranking (improves retrieval accuracy)
- Query Expansion (better terminology matching)
- Hybrid Search (vector + keyword)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(Path(__file__).parent.parent / ".env")
except Exception:
    pass

# OpenAI
from openai import OpenAI  # noqa: E402

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supabase - centralized client
from core.database import get_supabase_client  # noqa: E402
from core.enhanced_rag import EnhancedRAG  # noqa: E402

supabase = get_supabase_client()


class RAGChatbot:
    """Natural language chatbot powered by Enhanced RAG"""

    def __init__(self, use_enhanced_rag: bool = True):
        """
        Initialize RAG Chatbot

        Args:
            use_enhanced_rag: If True, uses Enhanced RAG (recommended).
                            If False, falls back to basic search.
        """
        self.chat_model = "gpt-4o-mini"
        self.conversation_history = []
        self.use_enhanced_rag = use_enhanced_rag

        # Initialize Enhanced RAG engine
        if use_enhanced_rag:
            self.enhanced_rag = EnhancedRAG(
                supabase_client=supabase,
                enable_dynamic_models=False,  # Keep models simple for chatbot
            )
            print(
                "✅ Using Enhanced RAG (Corrective + Reranking + Query Expansion + Hybrid Search)"  # noqa: E501
            )
        else:
            self.enhanced_rag = None
            self.embedding_model = "text-embedding-3-small"

        # Metadata filters (can be set by user)
        self.filters = {
            "law_category": None,  # e.g., 'software', 'digital_goods', 'manufacturing'
            "vendor_name": None,  # Filter vendor background by name
            "citation": None,  # Filter by specific citation (e.g., 'WAC 458-20-15502')
        }

    def get_embedding(self, text: str) -> List[float]:
        """Generate query embedding"""
        response = client.embeddings.create(input=text, model=self.embedding_model)
        return response.data[0].embedding

    def search_knowledge_base(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search tax law and vendor background knowledge base

        Uses Enhanced RAG if enabled, otherwise falls back to basic search
        """
        # Use Enhanced RAG if enabled
        if self.use_enhanced_rag:
            vendor_name = self.filters.get("vendor_name")
            enhanced_results = self.enhanced_rag.search_enhanced(
                query=query, top_k=top_k, vendor_name=vendor_name
            )

            # Convert Enhanced RAG format to chatbot format
            results = []
            for chunk in enhanced_results:
                # Apply citation filter if set
                if self.filters.get("citation") and self.filters[
                    "citation"
                ] not in chunk.get("citation", ""):
                    continue

                # Apply category filter if set
                if (
                    self.filters.get("law_category")
                    and chunk.get("law_category") != self.filters["law_category"]
                ):
                    continue

                results.append(
                    {
                        "source": "tax_law",
                        "text": chunk.get("chunk_text", ""),
                        "citation": chunk.get("citation", ""),
                        "category": chunk.get("law_category", ""),
                        "similarity": chunk.get(
                            "relevance_score", chunk.get("similarity", 0)
                        ),
                        "chunk_number": chunk.get("chunk_number"),
                        "page_number": chunk.get("section_title"),
                        "document_id": chunk.get("document_id"),
                        "enhanced_rag_score": chunk.get(
                            "relevance_score"
                        ),  # Track that this used Enhanced RAG
                    }
                )

            return results[:top_k]

        # Fallback to basic search (original implementation)
        else:
            query_embedding = self.get_embedding(query)
            results = []

            # Search tax law with optional category filter
            try:
                rpc_params = {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.3,
                    "match_count": top_k,
                }

                # Add category filter if set
                if self.filters.get("law_category"):
                    rpc_params["law_category_filter"] = self.filters["law_category"]

                tax_results = supabase.rpc("search_tax_law", rpc_params).execute()

                if tax_results.data:
                    for r in tax_results.data:
                        # Get document info for page numbers and section
                        doc_id = r.get("document_id")
                        chunk_number = None
                        section_title = None

                        # Fetch full chunk info including section_title (which stores
                        # page number)
                        chunk_info = (
                            supabase.table("tax_law_chunks")
                            .select("chunk_number, section_title")
                            .eq("id", r.get("id"))
                            .execute()
                        )
                        if chunk_info.data:
                            chunk_number = chunk_info.data[0].get("chunk_number")
                            section_title = chunk_info.data[0].get("section_title")

                        # Apply citation filter if set
                        if self.filters.get("citation") and self.filters[
                            "citation"
                        ] not in r.get("citation", ""):
                            continue

                        results.append(
                            {
                                "source": "tax_law",
                                "text": r.get("chunk_text", ""),
                                "citation": r.get("citation", ""),
                                "category": r.get("law_category", ""),
                                "similarity": r.get("similarity", 0),
                                "chunk_number": chunk_number,
                                "page_number": section_title,
                                "document_id": doc_id,
                            }
                        )
            except Exception as e:
                print(f"Error searching tax law: {e}")

            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

    def answer_question(self, question: str) -> str:
        """Answer a question using RAG"""

        print("\n💭 Searching knowledge base...", end="", flush=True)

        # Search knowledge base
        relevant_docs = self.search_knowledge_base(question, top_k=3)

        if not relevant_docs:
            return "❌ I couldn't find any relevant information in the knowledge base for that question. Try asking about software taxation, digital products, or computer software."  # noqa: E501

        print(f" Found {len(relevant_docs)} relevant documents!\n")

        # Build context from retrieved documents with full text and page numbers
        context = ""
        for i, doc in enumerate(relevant_docs, 1):
            if doc["source"] == "tax_law":
                page_ref = doc.get("page_number", "")  # "Page X"
                context += f"\n[Source {i}: {doc['citation']
                                             }, {page_ref} - {doc['category']}]\n"
            else:
                context += f"\n[Source {i}: {doc['vendor']} - {doc['category']}]\n"
            # Include full text for better citation
            context += doc["text"] + "\n"

        # Generate answer using GPT
        system_prompt = """You are a helpful assistant that answers questions about Washington State tax law.  # noqa: E501

IMPORTANT INSTRUCTIONS:
1. Use ONLY the information provided in the context below to answer questions
2. ALWAYS cite specific RCW/WAC references when making legal statements
3. Include DIRECT QUOTES from the source documents using quotation marks
4. Reference the specific section number when citing (e.g., "According to WAC 458-20-15502, Section 1...")  # noqa: E501
5. If quoting, use this format: "According to [CITATION]: '[EXACT QUOTE]'"
6. If the context doesn't contain enough information, say so
7. Be precise and thorough, maintaining legal accuracy"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": """Context from knowledge base:
{context}

Question: {question}

Please answer the question based on the context above.""",
            },
        ]

        # Add conversation history for context
        for msg in self.conversation_history[-4:]:  # Last 2 exchanges
            messages.append(msg)

        try:
            response = client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.3,
                max_tokens=500,
            )

            answer = response.choices[0].message.content

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})

            # Show sources with page number references
            sources_text = "\n\n📚 Sources Referenced:"
            for i, doc in enumerate(relevant_docs, 1):
                sim = doc["similarity"]
                if doc["source"] == "tax_law":
                    page_info = (
                        f", {doc.get('page_number', 'Page ?')}"
                        if doc.get("page_number")
                        else ""
                    )
                    # Show Enhanced RAG score if available
                    if doc.get("enhanced_rag_score"):
                        score_info = (
                            f" (Enhanced RAG score: {doc['enhanced_rag_score']:.2f})"
                        )
                    else:
                        score_info = f" (relevance: {sim:.2f})"
                    sources_text += f"\n  [{i}] {doc['citation']
                                                 }{page_info} - {doc['category']}{score_info}"  # noqa: E501
                else:
                    sources_text += f"\n  [{i}] {doc['vendor']
                                                 } - {doc['category']} (relevance: {sim:.2f})"  # noqa: E501

            # Add note about Enhanced RAG if used
            if self.use_enhanced_rag:
                sources_text += "\n\n🚀 Using Enhanced RAG (Corrective + Reranking + Query Expansion + Hybrid Search)"  # noqa: E501
            sources_text += "\n💡 Tip: Page numbers help you locate the exact section in the original documents."  # noqa: E501

            return answer + sources_text

        except Exception as e:
            return f"❌ Error generating answer: {e}"

    def set_filter(self, filter_name: str, value: str = None):
        """Set a metadata filter"""
        if filter_name in self.filters:
            self.filters[filter_name] = value
            if value:
                print(f"✅ Filter set: {filter_name} = '{value}'")
            else:
                print(f"✅ Filter cleared: {filter_name}")
        else:
            print(f"❌ Unknown filter: {filter_name}")
            print(f"   Available filters: {', '.join(self.filters.keys())}")

    def show_filters(self):
        """Show current metadata filters"""
        active_filters = {k: v for k, v in self.filters.items() if v is not None}

        if not active_filters:
            print("\n🔍 No filters active (searching all documents)")
        else:
            print("\n🔍 Active Filters:")
            for key, value in active_filters.items():
                print(f"  • {key}: {value}")

        print("\nAvailable filters: law_category, vendor_name, citation")
        print("Set filter: filter <name> <value>")
        print("Clear filter: filter <name> clear\n")

    def chat(self):
        """Start interactive chat"""
        print("\n" + "=" * 80)
        print("💬 RAG CHATBOT - Washington State Tax Law")
        if self.use_enhanced_rag:
            print("🚀 Enhanced RAG Mode (Better Accuracy + Validation)")
        print("=" * 80)
        print("\nI can answer questions like:")
        print("  • How is computer software taxed in Washington?")
        print("  • Are SaaS services subject to sales tax?")
        print("  • What are digital products under WA tax law?")
        print("  • Is cloud software taxable?")
        print("\n🔍 Metadata Filtering:")
        print("  • filter law_category software    - Only search software-related docs")
        print("  • filter citation WAC-458-20-15502 - Search specific citation")
        print("  • filters                          - Show active filters")
        print(
            "\nType 'quit' to exit, 'stats' to see knowledge base info, 'help' for all commands"  # noqa: E501
        )
        print("=" * 80 + "\n")

        while True:
            try:
                question = input("❓ You: ").strip()

                if not question:
                    continue

                if question.lower() in ["quit", "exit", "q"]:
                    print("\n👋 Goodbye!\n")
                    break

                if question.lower() == "stats":
                    self.show_stats()
                    continue

                if question.lower() in ["filters", "filter"]:
                    self.show_filters()
                    continue

                # Handle filter command: "filter <name> <value>"
                if question.lower().startswith("filter "):
                    parts = question.split(maxsplit=2)
                    if len(parts) >= 3:
                        filter_name = parts[1]
                        filter_value = parts[2] if parts[2].lower() != "clear" else None
                        self.set_filter(filter_name, filter_value)
                    else:
                        print("Usage: filter <name> <value>  OR  filter <name> clear")
                    continue

                if question.lower() in ["help", "h", "?"]:
                    self.show_help()
                    continue

                # Answer the question
                print()
                answer = self.answer_question(question)
                print(f"🤖 Assistant: {answer}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

    def show_stats(self):
        """Show knowledge base statistics"""
        try:
            docs = supabase.table("knowledge_documents").select("*").execute()
            tax_docs = [d for d in docs.data if d["document_type"] == "tax_law"]
            vendor_docs = [
                d for d in docs.data if d["document_type"] == "vendor_background"
            ]

            tax_chunks = (
                supabase.table("tax_law_chunks").select("id", count="exact").execute()
            )
            tax_chunk_count = tax_chunks.count if hasattr(tax_chunks, "count") else 0

            print("\n📊 Knowledge Base Stats:")
            print(f"  Documents: {len(docs.data)} ({
                len(tax_docs)} tax law, {len(vendor_docs)} vendor)")
            print(f"  Chunks: {tax_chunk_count}")

            if tax_docs:
                print("\n  Tax Law Documents:")
                for doc in tax_docs:
                    print(f"    • {doc.get('citation', 'N/A')}")
            print()

        except Exception as e:
            print(f"❌ Error fetching stats: {e}\n")

    def show_help(self):
        """Show help"""
        print(
            """
💡 Tips:
  - Ask natural questions about WA tax law
  - Be specific (e.g., "How is SaaS taxed?" vs "Tell me about tax")
  - The chatbot uses RAG to find relevant documents first
  - It will cite sources (RCW/WAC references)

🔧 Commands:
  stats                           - Show knowledge base statistics
  filters                         - Show active metadata filters
  filter <name> <value>           - Set a metadata filter
  filter <name> clear             - Clear a metadata filter
  help                            - Show this help message
  quit                            - Exit

🔍 Metadata Filters:
  filter law_category software    - Only search software-related documents
  filter law_category digital_goods - Only search digital goods documents
  filter citation WAC-458-20-15502 - Search specific citation
  filter vendor_name AT&T          - Search specific vendor (for vendor docs)

  Example workflow:
    > filters                      (see current filters)
    > filter law_category software (set filter to only software docs)
    > How is SaaS taxed?           (ask question - only searches software docs)
    > filter law_category clear    (remove filter)
"""
        )


def main():
    chatbot = RAGChatbot()
    chatbot.chat()


if __name__ == "__main__":
    main()
