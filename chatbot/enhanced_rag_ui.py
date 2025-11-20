#!/usr/bin/env python3
"""
Enhanced RAG Chatbot UI with Streamlit

Features:
- Agentic RAG with intelligent decision-making
- Shows decision reasoning and cost savings
- Displays source citations with relevance scores
- Clean, professional interface

Usage:
    streamlit run chatbot/enhanced_rag_ui.py
"""

from core.enhanced_rag import EnhancedRAG
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from typing import Dict, List

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment

load_dotenv(Path(__file__).parent.parent / ".env")

# OpenAI for answer generation

# Import Enhanced RAG

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Page configuration
st.set_page_config(
    page_title="WA Tax Law - Enhanced RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .decision-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .cost-saved {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rag" not in st.session_state:
    st.session_state.rag = EnhancedRAG()


def generate_answer(question: str, search_result: Dict) -> str:
    """Generate AI answer using RAG results"""

    # Build context from results
    context = ""
    results = search_result.get("results", [])

    if search_result["action"] == "USE_CACHED":
        context = f"Using cached data:\n{
            results[0].get('data', {}) if results else 'No data'}"
    elif search_result["action"] == "USE_RULES":
        rule_data = results[0].get("data", {}) if results else {}
        context = """Structured Tax Rule:
Product Type: {rule_data.get('product_type', 'N/A')}
Taxable: {rule_data.get('taxable', 'N/A')}
Classification: {rule_data.get('tax_classification', 'N/A')}
Legal Basis: {', '.join(rule_data.get('legal_basis', []))}
Description: {rule_data.get('description', 'N/A')}
"""
    else:
        # Regular search results - use all results, not just first 3
        for i, doc in enumerate(results, 1):
            if "citation" in doc:
                context += f"\n[Source {i}: {doc.get('citation', 'N/A')}"
                if doc.get("section_title"):
                    context += f", {doc['section_title']}"
                context += f" (Relevance: {doc.get('similarity', 0):.0%})]\n"
                context += f"{doc.get('chunk_text', '')}\n"

    if not context:
        return "I couldn't find relevant information to answer your question. Please try rephrasing or adjusting your query."

    # System prompt
    system_prompt = """You are a Washington State tax law expert assistant.

INSTRUCTIONS:
1. Answer questions using ONLY the provided context
2. ALWAYS cite specific WAC/RCW references
3. Use direct quotes when appropriate (in quotation marks)
4. Be precise and legally accurate
5. If context lacks info, say so clearly
6. Format responses clearly with markdown

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

    # Add recent conversation history
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


def render_decision_info(search_result: Dict):
    """Render the decision-making information"""

    action = search_result["action"]
    reasoning = search_result["reasoning"]
    confidence = search_result["confidence"]
    cost_saved = search_result["cost_saved"]

    # Decision icon mapping
    action_icons = {
        "USE_CACHED": "💾",
        "USE_RULES": "📋",
        "RETRIEVE_SIMPLE": "🔍",
        "RETRIEVE_ENHANCED": "🚀",
    }

    # Confidence color
    if confidence >= 0.85:
        conf_class = "confidence-high"
        conf_emoji = "🟢"
    elif confidence >= 0.65:
        conf_class = "confidence-medium"
        conf_emoji = "🟡"
    else:
        conf_class = "confidence-low"
        conf_emoji = "🔴"

    decision_html = """
    <div class="decision-box">
        <strong>{action_icons.get(action, '🤖')} Decision: {action.replace('_', ' ').title()}</strong><br/>
        <strong>💭 Reasoning:</strong> {reasoning}<br/>
        <strong>{conf_emoji} Confidence:</strong> <span class="{conf_class}">{confidence:.0%}</span><br/>
        <strong>💰 Cost Saved:</strong> <span class="cost-saved">${cost_saved:.4f}</span>
    </div>
    """

    st.markdown(decision_html, unsafe_allow_html=True)


def get_file_url_for_document(document_id: str) -> str:
    """Fetch file_url from knowledge_documents table"""
    try:
        from core.database import get_supabase_client  # noqa: E402

        supabase = get_supabase_client()

        result = (
            supabase.table("knowledge_documents")
            .select("file_url")
            .eq("id", document_id)
            .execute()
        )
        if result.data and len(result.data) > 0:
            return result.data[0].get("file_url", "")
    except Exception as e:
        print(f"Error fetching file_url: {e}")
    return ""


def render_source(doc: Dict, index: int):
    """Render a source document with clickable citation link and page numbers"""

    citation = doc.get("citation", "N/A")
    section = doc.get("section_title", "")
    similarity = doc.get("similarity", 0)
    category = doc.get("law_category", "")
    text = doc.get("chunk_text", "")[:200]

    # Try to get file_url from doc, or fetch it using document_id
    file_url = doc.get("file_url", "")
    if not file_url and doc.get("document_id"):
        file_url = get_file_url_for_document(doc.get("document_id"))

    # Make citation clickable if URL exists
    if file_url:
        citation_display = f'<a href="{
            # 1f77b4; text-decoration: none; font-weight: bold;">{citation}</a> 🔗'
            file_url}" target="_blank" style="color:
    else:
        citation_display = (
            f'<span style="color: #000; font-weight: bold;">{citation}</span>'
        )

    # Parse and highlight page numbers from section_title
    page_info = ""
    if section and ("Page" in section or "Pages" in section):
        # Extract page info and make it more prominent
        page_info = (
            f'<span style="color: #1f77b4; font-weight: bold;"> | 📄 {section}</span>'
        )
    elif section:
        page_info = f'<span style="color: #666;"> - {section}</span>'

    source_html = """
    <div class="source-box">
        [{index}] {citation_display}{page_info}
        <br/>
        <span style="font-size: 0.85rem; color: #666;">
            Category: {category} | Relevance: {similarity:.1%}
        </span>
        <br/>
        <span style="font-size: 0.9rem; color: #555;">
            {text}...
        </span>
    </div>
    """

    st.markdown(source_html, unsafe_allow_html=True)


def main():
    # Header
    st.markdown(
        '<div class="main-header">🧠 Enhanced RAG Chatbot</div>', unsafe_allow_html=True
    )
    st.caption(
        "Washington Tax Law - Powered by Agentic RAG with Intelligent Decision-Making"
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Force retrieval option
        force_retrieval = st.checkbox(
            "Force Enhanced Retrieval",
            value=False,
            help="Skip AI decision-making and always use full enhanced search (Corrective RAG + Reranking + Query Expansion). Slower but more thorough.",
        )

        # Top-k setting
        top_k = st.slider(
            "Number of Results",
            min_value=1,
            max_value=10,
            value=3,
            help="How many source documents to retrieve",
        )

        st.divider()

        # Filters
        st.subheader("🔍 Filters")

        # Law Category
        law_category = st.selectbox(
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
            format_func=lambda x: (
                "All categories" if x is None else x.replace("_", " ").title()
            ),
            help="Filter by type of tax law",
        )

        # Tax Types
        tax_types_options = ["sales tax", "use tax", "B&O tax", "retail sales tax"]
        tax_types = st.multiselect(
            "Tax Types", options=tax_types_options, help="Filter by specific tax types"
        )

        # Industries
        industries_options = [
            "general",
            "retail",
            "technology",
            "software development",
            "manufacturing",
        ]
        industries = st.multiselect(
            "Industries",
            options=industries_options,
            help="Filter by industry applicability",
        )

        # Citation search
        citation_filter = st.text_input(
            "Citation Filter",
            placeholder="e.g., WAC 458-20-15503",
            help="Filter by specific citation (e.g., WAC or RCW number)",
        )

        # Clear filters button
        if st.button("🗑️ Clear Filters"):
            st.rerun()

        # Show active filters
        active_filters = sum(
            [
                1 if law_category else 0,
                1 if tax_types else 0,
                1 if industries else 0,
                1 if citation_filter else 0,
            ]
        )
        if active_filters > 0:
            st.success(f"✅ {active_filters} filter(s) active")

        st.divider()

        # Stats
        st.subheader("📊 Session Stats")
        total_messages = len(
            [m for m in st.session_state.messages if m["role"] == "user"]
        )
        st.metric("Questions Asked", total_messages)

        total_saved = sum(
            [
                m.get("decision", {}).get("cost_saved", 0)
                for m in st.session_state.messages
                if m["role"] == "decision"
            ]
        )
        st.metric("Total Cost Saved", f"${total_saved:.4f}")

        st.divider()

        # Help
        with st.expander("❓ Help"):
            st.markdown(
                """
            **How it works:**
            1. Type your question
            2. AI decides optimal retrieval strategy
            3. Get accurate answers with sources

            **Example questions:**
            - How are SaaS products taxed?
            - What is custom software?
            - When is use tax applied?
            - Are digital goods taxable?
            """
            )

        # Clear chat
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    # Main chat interface
    st.divider()

    # Display conversation
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])

        elif message["role"] == "decision":
            with st.expander("🤖 Decision Analysis", expanded=False):
                render_decision_info(message["decision"])

        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])

        elif message["role"] == "sources":
            with st.expander("📚 View Sources", expanded=True):
                for i, doc in enumerate(message["sources"], 1):
                    if "citation" in doc:
                        render_source(doc, i)
                    elif doc.get("source") == "cached":
                        st.info(f"**[{i}] Source: Cached Data**")
                    elif doc.get("source") == "structured_rules":
                        st.info(f"**[{i}] Source: Structured Tax Rules**")

    # Chat input
    if prompt := st.chat_input("Ask a question about Washington tax law..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Making intelligent decision..."):
                # Build context with filters
                context = {}
                if law_category or tax_types or industries:
                    context["filters"] = {
                        "law_category": law_category,
                        "tax_types": tax_types if tax_types else None,
                        "industries": industries if industries else None,
                    }

                # Use enhanced RAG with decision-making and filters
                search_result = st.session_state.rag.search_with_decision(
                    prompt,
                    context=context,
                    top_k=top_k,
                    force_retrieval=force_retrieval,
                )

                # Apply citation filter client-side if specified
                if citation_filter and search_result.get("results"):
                    filtered_results = [
                        r
                        for r in search_result["results"]
                        if citation_filter.upper() in r.get("citation", "").upper()
                    ]
                    search_result["results"] = filtered_results

                # Store decision
                st.session_state.messages.append(
                    {"role": "decision", "decision": search_result}
                )

                # Check if we got results
                if not search_result.get("results"):
                    response = "❌ No relevant information found. Try rephrasing your question."
                    st.warning(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                else:
                    # Generate answer
                    with st.spinner("✍️ Generating answer..."):
                        answer = generate_answer(prompt, search_result)

                    # Display answer
                    st.markdown(answer)

                    # Store answer
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

                    # Store sources
                    st.session_state.messages.append(
                        {"role": "sources", "sources": search_result["results"]}
                    )

        # Show decision analysis
        with st.expander("🤖 Decision Analysis", expanded=True):
            render_decision_info(search_result)

        # Show sources
        if search_result.get("results"):
            with st.expander("📚 View Sources", expanded=True):
                for i, doc in enumerate(search_result["results"][:top_k], 1):
                    if "citation" in doc:
                        render_source(doc, i)
                    elif doc.get("source") == "cached":
                        st.info(f"**[{i}] Source: Cached Data**")
                    elif doc.get("source") == "structured_rules":
                        st.info(f"**[{i}] Source: Structured Tax Rules**")
                        st.json(doc.get("data", {}))

    # Footer
    st.divider()
    st.caption(
        "🧠 Powered by Enhanced RAG | 🤖 Intelligent Decision-Making | 📚 Washington State Tax Law"
    )


if __name__ == "__main__":
    main()
