#!/usr/bin/env python3
"""
Streamlit Web UI for Washington Tax Law RAG Chatbot

Features:
- Clean chat interface with conversation history
- Clickable source document links
- Advanced filtering (law_category, tax_types, industries, citation)
- Real-time responses with streaming support

Usage:
    streamlit run chatbot/web_chat.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

# OpenAI
from openai import OpenAI  # noqa: E402

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supabase - centralized client
from core.database import get_supabase_client  # noqa: E402
from core.enhanced_rag import EnhancedRAG  # noqa: E402

supabase = get_supabase_client()

# Initialize Enhanced RAG
enhanced_rag = EnhancedRAG(supabase_client=supabase, enable_dynamic_models=False)


# Page configuration
st.set_page_config(
    page_title="WA Tax Law Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .citation-link {
        font-weight: bold;
        color: #1f77b4;
        text-decoration: none;
    }
    .citation-link:hover {
        text-decoration: underline;
    }
    .tag {
        display: inline-block;
        background-color: #e1e4e8;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "filters" not in st.session_state:
    st.session_state.filters = {
        "law_category": None,
        "tax_types": None,
        "industries": None,
        "citation": None,
    }


def get_embedding(text: str) -> List[float]:
    """Generate query embedding using OpenAI"""
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding


def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict]:
    """
    Search tax law knowledge base using Enhanced RAG

    Uses: Corrective RAG + Reranking + Query Expansion + Hybrid Search
    """
    try:
        # Get filters from session state
        filters = st.session_state.filters

        # Use Enhanced RAG for search
        with st.spinner(
            "🔍 Searching with Enhanced RAG (Corrective + Reranking + Query Expansion)..."  # noqa: E501
        ):
            enhanced_results = enhanced_rag.search_enhanced(query=query, top_k=top_k)

        # Convert Enhanced RAG results to web chat format
        chunks = []
        for r in enhanced_results:
            # Apply filters
            if filters.get("citation") and filters["citation"] not in r.get(
                "citation", ""
            ):
                continue
            if (
                filters.get("law_category")
                and r.get("law_category") != filters["law_category"]
            ):
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
                    "file_url": r.get("file_url", ""),
                    "similarity": r.get("relevance_score", r.get("similarity", 0)),
                    "enhanced_rag_score": r.get(
                        "relevance_score"
                    ),  # Track Enhanced RAG was used
                }
            )

        return chunks[:top_k]

    except Exception as e:
        st.error(f"Search error: {e}")
        return []


def generate_answer(question: str, relevant_docs: List[Dict]) -> str:
    """Generate AI answer using RAG"""

    # Build context
    context = ""
    for i, doc in enumerate(relevant_docs, 1):
        context += f"\n[Source {i}: {doc['citation']}"
        if doc["section"]:
            context += f", {doc['section']}"
        context += f"]\n{doc['text']}\n"

    # System prompt
    system_prompt = """You are a helpful assistant specializing in Washington State tax law.  # noqa: E501

INSTRUCTIONS:
1. Answer questions using ONLY the provided context
2. ALWAYS cite specific WAC/RCW references in your answer
3. Use direct quotes when possible (in quotation marks)
4. Be precise and legally accurate
5. If the context lacks information, say so clearly
6. Format your response in a clear, structured way

RESPONSE FORMAT:
- Start with a direct answer
- Support with citations and quotes
- Keep it concise but thorough
- Use markdown formatting for readability"""

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

    # Add conversation history (last 4 messages)
    for msg in st.session_state.messages[-4:]:
        if msg["role"] in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=messages, temperature=0.2, max_tokens=800
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating answer: {e}"


def render_source_with_link(doc: Dict, index: int):
    """Render a source with clickable link"""

    citation = doc["citation"]
    section = doc["section"]
    file_url = doc.get("file_url", "")
    similarity = doc["similarity"]
    tax_types = doc.get("tax_types", [])
    industries = doc.get("industries", [])

    # Create citation display with link if URL exists
    if file_url:
        citation_display = (
            f'<a href="{file_url}" target="_blank" '
            f'class="citation-link">{citation}</a>'
        )
    else:
        citation_display = f'<span class="citation-link">{citation}</span>'

    # Build tags
    tags_html = ""
    if tax_types:
        for tax in tax_types:
            tags_html += f'<span class="tag">Tax: {tax}</span>'
    if industries:
        for industry in industries:
            tags_html += f'<span class="tag">Industry: {industry}</span>'

    # Build source HTML with section if available
    section_part = f" - {section}" if section else ""
    source_html = f"""
    <div class="source-box">
        <strong>[{index}]</strong> {citation_display}{section_part}
        <br/>
        {tags_html}
        <span class="tag">Relevance: {similarity:.2%}</span>
    </div>
    """

    st.markdown(source_html, unsafe_allow_html=True)


def main():
    # Header
    st.markdown(
        '<div class="main-header">💬 Washington Tax Law Chatbot</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '🚀 <span style="color: #1f77b4; font-weight: bold;">Enhanced RAG Mode</span> - Corrective + Reranking + Query Expansion + Hybrid Search',  # noqa: E501
        unsafe_allow_html=True,
    )

    # Sidebar - Filters
    with st.sidebar:
        st.header("🔍 Filters")

        # Show active filters count
        active_filters = sum(1 for v in st.session_state.filters.values() if v)
        if active_filters > 0:
            st.success(f"✅ {active_filters} filter(s) active")

        # Law Category
        st.session_state.filters["law_category"] = st.selectbox(
            "Law Category",
            options=[
                None,
                "software",
                "digital_goods",
                "exemption",
                "general",
                "rate",
                "definition",
                "compliance",
            ],
            format_func=lambda x: "All categories" if x is None else x,
            key="law_category_filter",
        )

        # Tax Types (multiselect)
        tax_types_options = ["sales tax", "use tax", "B&O tax", "retail sales tax"]
        selected_tax_types = st.multiselect(
            "Tax Types",
            options=tax_types_options,
            default=st.session_state.filters.get("tax_types") or [],
            key="tax_types_filter",
        )
        st.session_state.filters["tax_types"] = (
            selected_tax_types if selected_tax_types else None
        )

        # Industries (multiselect)
        industries_options = [
            "general",
            "retail",
            "technology",
            "software development",
            "manufacturing",
        ]
        selected_industries = st.multiselect(
            "Industries",
            options=industries_options,
            default=st.session_state.filters.get("industries") or [],
            key="industries_filter",
        )
        st.session_state.filters["industries"] = (
            selected_industries if selected_industries else None
        )

        # Citation
        citation_input = st.text_input(
            "Citation (e.g., WAC 458-20-15503)",
            value=st.session_state.filters.get("citation") or "",
            key="citation_filter",
        )
        st.session_state.filters["citation"] = (
            citation_input if citation_input else None
        )

        # Clear filters button
        if st.button("🗑️ Clear All Filters"):
            st.session_state.filters = {
                k: None for k in st.session_state.filters.keys()
            }
            st.rerun()

        # Divider
        st.divider()

        # Knowledge base stats
        if st.button("📊 View Stats"):
            with st.spinner("Loading stats..."):
                try:
                    docs = supabase.table("knowledge_documents").select("*").execute()
                    st.info(f"**Documents:** {len(docs.data)}")

                    with st.expander("View all documents"):
                        for doc in docs.data:
                            st.write(f"• **{doc.get('citation', 'N/A')
                                            }**: {doc.get('title', 'N/A')[:60]}...")
                except Exception as e:
                    st.error(f"Error: {e}")

        # Help section
        with st.expander("❓ Help"):
            st.markdown(
                """
            **How to use:**
            1. Type your question in the chat
            2. Use filters to narrow results
            3. Click citation links to view source documents

            **Example questions:**
            - What are the rules for software taxation?
            - When is use tax applied?
            - What exemptions exist for digital goods?
            """
            )

    # Main chat interface
    st.divider()

    # Display conversation history
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])

        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])

        elif message["role"] == "sources":
            with st.expander("📚 View Sources", expanded=True):
                for i, doc in enumerate(message["sources"], 1):
                    render_source_with_link(doc, i)

    # Chat input
    if prompt := st.chat_input("Ask a question about Washington tax law..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching knowledge base..."):
                # Search
                relevant_docs = search_knowledge_base(prompt, top_k=3)

                if not relevant_docs:
                    response = "❌ No relevant information found. Try adjusting your filters or rephrasing your question."  # noqa: E501
                    st.warning(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                else:
                    # Generate answer
                    with st.spinner("🧠 Generating answer..."):
                        answer = generate_answer(prompt, relevant_docs)

                    # Display answer
                    st.markdown(answer)

                    # Add to history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

                    # Display sources
                    st.session_state.messages.append(
                        {"role": "sources", "sources": relevant_docs}
                    )

        # Display sources below the answer
        with st.expander("📚 View Sources", expanded=True):
            for i, doc in enumerate(relevant_docs, 1):
                render_source_with_link(doc, i)

    # Footer
    st.divider()
    st.caption(
        "💬 Powered by OpenAI GPT-4 | 🚀 Enhanced RAG (Corrective + Reranking + Query Expansion) | 📚 Washington State Tax Law Database"  # noqa: E501
    )


if __name__ == "__main__":
    main()
