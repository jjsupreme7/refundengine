#!/usr/bin/env python3
"""
Simple RAG Chatbot with Clean UI
Ask questions about Washington State tax law and get AI-powered answers
"""

from core.database import get_supabase_client
from openai import OpenAI
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(Path(__file__).parent.parent / ".env")
except BaseException:
    pass

# OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supabase - using centralized client

supabase = get_supabase_client()


class SimpleTaxChatbot:
    """Simple chatbot with enhanced filtering"""

    def __init__(self):
        self.embedding_model = "text-embedding-3-small"
        self.chat_model = "gpt-4o"
        self.conversation_history = []

        # Active filters
        self.filters = {
            "law_category": None,
            "tax_types": None,  # Array filter
            "industries": None,  # Array filter
            "citation": None,
        }

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system("clear" if os.name != "nt" else "cls")

    def print_header(self):
        """Print chatbot header"""
        print("\n" + "=" * 80)
        print("  💬 WASHINGTON TAX LAW CHATBOT")
        print("=" * 80)

        # Show active filters if any
        active = {k: v for k, v in self.filters.items() if v}
        if active:
            print("\n  🔍 Active Filters:")
            for key, value in active.items():
                if isinstance(value, list):
                    print(f"     • {key}: {', '.join(value)}")
                else:
                    print(f"     • {key}: {value}")

        print("\n  Type your question or use commands:")
        print("    • /filter - Manage filters")
        print("    • /clear - Clear conversation")
        print("    • /stats - Knowledge base stats")
        print("    • /help - Show help")
        print("    • /quit - Exit")
        print("=" * 80 + "\n")

    def get_embedding(self, text: str) -> List[float]:
        """Generate query embedding"""
        response = client.embeddings.create(input=text, model=self.embedding_model)
        return response.data[0].embedding

    def search_knowledge_base(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search tax law with metadata filters"""
        query_embedding = self.get_embedding(query)

        # Build RPC params
        rpc_params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.3,
            "match_count": top_k,
        }

        # Add filters if set
        if self.filters.get("law_category"):
            rpc_params["law_category_filter"] = self.filters["law_category"]

        if self.filters.get("tax_types"):
            rpc_params["tax_types_filter"] = self.filters["tax_types"]

        if self.filters.get("industries"):
            rpc_params["industries_filter"] = self.filters["industries"]

        try:
            results = supabase.rpc("search_tax_law", rpc_params).execute()

            chunks = []
            for r in results.data:
                # Apply citation filter (client-side since not in RPC yet)
                if self.filters.get("citation") and self.filters[
                    "citation"
                ] not in r.get("citation", ""):
                    continue

                chunks.append(
                    {
                        "text": r.get("chunk_text", ""),
                        "citation": r.get("citation", ""),
                        "category": r.get("law_category", ""),
                        "section": r.get("section_title", ""),
                        "tax_types": r.get("tax_types", []),
                        "industries": r.get("industries", []),
                        "topic_tags": r.get("topic_tags", []),
                        "similarity": r.get("similarity", 0),
                    }
                )

            return chunks

        except Exception as e:
            print(f"\n⚠️  Search error: {e}")
            return []

    def answer_question(self, question: str) -> str:
        """Answer a question using RAG"""

        print("\n  🔍 Searching knowledge base...")

        # Search
        relevant_docs = self.search_knowledge_base(question, top_k=3)

        if not relevant_docs:
            return "\n  ❌ No relevant information found. Try adjusting your filters or question.\n"

        print(f"  ✅ Found {len(relevant_docs)} relevant sources\n")

        # Build context
        context = ""
        for i, doc in enumerate(relevant_docs, 1):
            context += f"\n[Source {i}: {doc['citation']}"
            if doc["section"]:
                context += f", {doc['section']}"
            context += f"]\n{doc['text']}\n"

        # System prompt
        system_prompt = """You are a helpful assistant specializing in Washington State tax law.

INSTRUCTIONS:
1. Answer questions using ONLY the provided context
2. ALWAYS cite specific WAC/RCW references
3. Use direct quotes when possible (in quotation marks)
4. Be precise and legally accurate
5. If the context lacks information, say so clearly
6. Format your response in a clear, structured way

RESPONSE FORMAT:
- Start with a direct answer
- Support with citations and quotes
- Keep it concise but thorough"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": """Context from Washington tax law:
{context}

Question: {question}

Please answer based on the context above.""",
            },
        ]

        # Add conversation history
        for msg in self.conversation_history[-4:]:
            messages.append(msg)

        try:
            response = client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.2,
                max_tokens=800,
            )

            answer = response.choices[0].message.content

            # Update history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})

            # Format response
            result = f"\n  💬 ANSWER:\n\n{self._indent(answer)}\n"
            result += "\n  📚 SOURCES:\n"

            for i, doc in enumerate(relevant_docs, 1):
                tags = []
                if doc["tax_types"]:
                    tags.append(f"Tax: {', '.join(doc['tax_types'])}")
                if doc["industries"]:
                    tags.append(f"Industry: {', '.join(doc['industries'])}")

                tags_str = f" ({'; '.join(tags)})" if tags else ""

                result += f"     [{i}] {doc['citation']}"
                if doc["section"]:
                    result += f" - {doc['section']}"
                result += f"{tags_str} (relevance: {doc['similarity']:.2f})\n"

            return result

        except Exception as e:
            return f"\n  ❌ Error generating answer: {e}\n"

    def _indent(self, text: str, spaces: int = 5) -> str:
        """Indent text for better formatting"""
        indent = " " * spaces
        return "\n".join(indent + line for line in text.split("\n"))

    def manage_filters(self):
        """Interactive filter management"""
        print("\n" + "=" * 80)
        print("  🔍 FILTER MANAGEMENT")
        print("=" * 80)

        # Show current filters
        print("\n  Current Filters:")
        for key, value in self.filters.items():
            status = f"✅ {value}" if value else "⬜ Not set"
            print(f"     {key}: {status}")

        print("\n  Available Options:")
        print("     1. Set law_category")
        print("     2. Set tax_types (can select multiple)")
        print("     3. Set industries (can select multiple)")
        print("     4. Set citation")
        print("     5. Clear all filters")
        print("     6. Back to chat")

        choice = input("\n  Enter choice (1-6): ").strip()

        if choice == "1":
            print("\n  Common categories: software, digital_goods, exemption, general")
            value = input("  Enter law_category (or blank to clear): ").strip()
            self.filters["law_category"] = value if value else None
            print(f"  ✅ law_category set to: {self.filters['law_category']}")

        elif choice == "2":
            print("\n  Common tax types: sales tax, use tax, B&O tax")
            value = input(
                "  Enter tax_types (comma-separated, or blank to clear): "
            ).strip()
            self.filters["tax_types"] = (
                [t.strip() for t in value.split(",")] if value else None
            )
            print(f"  ✅ tax_types set to: {self.filters['tax_types']}")

        elif choice == "3":
            print(
                "\n  Common industries: general, retail, technology, software development"
            )
            value = input(
                "  Enter industries (comma-separated, or blank to clear): "
            ).strip()
            self.filters["industries"] = (
                [i.strip() for i in value.split(",")] if value else None
            )
            print(f"  ✅ industries set to: {self.filters['industries']}")

        elif choice == "4":
            print("\n  Example: WAC 458-20-15503")
            value = input("  Enter citation (or blank to clear): ").strip()
            self.filters["citation"] = value if value else None
            print(f"  ✅ citation set to: {self.filters['citation']}")

        elif choice == "5":
            self.filters = {k: None for k in self.filters.keys()}
            print("  ✅ All filters cleared")

        input("\n  Press Enter to continue...")

    def show_stats(self):
        """Show knowledge base statistics"""
        try:
            docs = supabase.table("knowledge_documents").select("*").execute()
            chunks = (
                supabase.table("tax_law_chunks").select("id", count="exact").execute()
            )

            print("\n" + "=" * 80)
            print("  📊 KNOWLEDGE BASE STATISTICS")
            print("=" * 80)
            print(f"\n  Documents: {len(docs.data)}")
            print(
                f"  Total Chunks: {
                    chunks.count if hasattr(
                        chunks,
                        'count') else len(
                        chunks.data)}"
            )

            print("\n  Available Documents:")
            for doc in docs.data:
                print(f"     • {doc.get('citation', 'N/A')}: {doc.get('title', 'N/A')}")
                print(
                    f"       Category: {
                        doc.get('law_category', 'N/A')}, Chunks: {doc.get('total_chunks', 'N/A')}"
                )

            print("=" * 80)
        except Exception as e:
            print(f"\n  ❌ Error fetching stats: {e}")

        input("\n  Press Enter to continue...")

    def show_help(self):
        """Show help information"""
        print("\n" + "=" * 80)
        print("  ℹ️  HELP")
        print("=" * 80)
        print(
            """
  ASK QUESTIONS:
  Just type your question naturally, for example:
    • How are digital products taxed in Washington?
    • What is the tax treatment of SaaS?
    • Are cloud services subject to sales tax?

  COMMANDS:
    /filter  - Set filters to narrow search (by tax type, industry, etc.)
    /clear   - Clear conversation history
    /stats   - View knowledge base statistics
    /help    - Show this help message
    /quit    - Exit the chatbot

  TIPS:
    • Be specific in your questions
    • Use filters to focus on specific areas
    • The chatbot uses RAG to find relevant legal text
    • All answers are based on ingested Washington tax law documents
"""
        )
        print("=" * 80)
        input("\n  Press Enter to continue...")

    def run(self):
        """Main chat loop with simple UI"""
        self.clear_screen()

        while True:
            self.print_header()

            try:
                user_input = input("  💬 You: ").strip()

                if not user_input:
                    continue

                # Commands
                if user_input.lower() in ["/quit", "/exit", "/q"]:
                    print("\n  👋 Goodbye!\n")
                    break

                elif user_input.lower() == "/clear":
                    self.conversation_history = []
                    self.clear_screen()
                    print("\n  ✅ Conversation cleared\n")
                    input("  Press Enter to continue...")
                    self.clear_screen()
                    continue

                elif user_input.lower() == "/filter":
                    self.manage_filters()
                    self.clear_screen()
                    continue

                elif user_input.lower() == "/stats":
                    self.show_stats()
                    self.clear_screen()
                    continue

                elif user_input.lower() in ["/help", "/h", "/?"]:
                    self.show_help()
                    self.clear_screen()
                    continue

                # Answer question
                answer = self.answer_question(user_input)
                print(answer)

                input("\n  Press Enter to continue...")
                self.clear_screen()

            except KeyboardInterrupt:
                print("\n\n  👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n  ❌ Error: {e}\n")
                input("  Press Enter to continue...")
                self.clear_screen()


def main():
    chatbot = SimpleTaxChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
