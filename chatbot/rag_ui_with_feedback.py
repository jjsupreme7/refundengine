#!/usr/bin/env python3
"""
Enhanced RAG Chatbot UI with User Feedback & Continuous Learning

Features:
- All existing Enhanced RAG features
- User feedback collection (thumbs up/down, ratings, suggestions)
- Suggested answer input
- Preferred citation selection
- Answer structure feedback
- Real-time learning integration
- Analytics dashboard

Usage:
    streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503
"""

import os
import sys
import uuid
from pathlib import Path
import streamlit as st
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Import Enhanced RAG, Feedback System, and Law Version Handler
from core.enhanced_rag import EnhancedRAG
from core.feedback_system import FeedbackSystem
from core.law_version_handler import LawVersionHandler

# OpenAI for answer generation
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# Page configuration
st.set_page_config(
    page_title="WA Tax Law - Enhanced RAG with Learning",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AUTHENTICATION - Require login
from core.auth import require_authentication
if not require_authentication():
    st.stop()

# Custom CSS
st.markdown("""
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
    .feedback-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ffc107;
    }
    .learning-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #17a2b8;
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
""", unsafe_allow_html=True)


# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'rag' not in st.session_state:
    st.session_state.rag = EnhancedRAG()

if 'feedback_system' not in st.session_state:
    st.session_state.feedback_system = FeedbackSystem()

if 'law_version_handler' not in st.session_state:
    from core.database import get_supabase_client
    st.session_state.law_version_handler = LawVersionHandler(get_supabase_client())

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'current_response_id' not in st.session_state:
    st.session_state.current_response_id = None


def generate_answer(question: str, search_result: Dict, use_learning: bool = True) -> str:
    """Generate AI answer using RAG results with learned improvements"""

    # Build context from results
    context = ""
    results = search_result.get('results', [])

    if search_result['action'] == 'USE_CACHED':
        context = f"Using cached data:\n{results[0].get('data', {}) if results else 'No data'}"
    elif search_result['action'] == 'USE_RULES':
        rule_data = results[0].get('data', {}) if results else {}
        context = f"""Structured Tax Rule:
Product Type: {rule_data.get('product_type', 'N/A')}
Taxable: {rule_data.get('taxable', 'N/A')}
Classification: {rule_data.get('tax_classification', 'N/A')}
Legal Basis: {', '.join(rule_data.get('legal_basis', []))}
Description: {rule_data.get('description', 'N/A')}
"""
    else:
        # Regular search results
        for i, doc in enumerate(results, 1):
            if 'citation' in doc:
                context += f"\n[Source {i}: {doc.get('citation', 'N/A')}"
                if doc.get('section_title'):
                    context += f", {doc['section_title']}"
                context += f" (Relevance: {doc.get('similarity', 0):.0%})]\n"
                context += f"{doc.get('chunk_text', '')}\n"

    if not context:
        return "I couldn't find relevant information to answer your question. Please try rephrasing or adjusting your query."

    # Get learned improvements if enabled
    answer_template = None
    golden_examples = []

    if use_learning:
        # Get answer template
        answer_template = st.session_state.feedback_system.get_answer_template(question)

        # Get golden examples for few-shot learning
        golden_examples = st.session_state.feedback_system.get_golden_examples(question, limit=2)

    # System prompt
    system_prompt = """You are a senior tax consultant at KOM Consulting, a premier Washington State and local tax accounting firm specializing in sales and use tax refund recovery.

ABOUT KOM CONSULTING:
- Experts in Washington State and local tax law
- Focus on sales & use tax refund identification and recovery
- Work with attorneys and CPAs to provide comprehensive tax solutions
- Known for detailed, thorough analysis and deep technical expertise
- Specialize in navigating complex tax scenarios across multiple jurisdictions

YOUR EXPERTISE:
- Washington State RCW and WAC (both current and historical)
- ESSB 5814 (effective Oct 1, 2025) and its impact on service taxation
- Sales & use tax refund opportunities and strategies
- Vendor classification and industry-specific tax treatment
- Multi-state nexus and apportionment issues
- Detailed knowledge of exemptions, deductions, and credits

INSTRUCTIONS:
1. Answer questions using ONLY the provided context
2. ALWAYS cite specific WAC/RCW references with section numbers
3. Use direct quotes when appropriate (in quotation marks)
4. Be precise, legally accurate, and detail-oriented
5. If context lacks info, say so clearly and suggest what additional info would help
6. When discussing ESSB 5814, clearly distinguish old law vs new law
7. Focus on refund opportunities and tax-saving strategies
8. Format responses clearly with markdown

RESPONSE FORMAT:
- Start with a direct, actionable answer
- Support with specific citations, quotes, and legal reasoning
- Highlight refund opportunities or tax implications
- Be thorough but organized - our clients expect detailed technical analysis"""

    # Add template guidance if available
    if answer_template:
        system_prompt += f"\n\nPREFERRED ANSWER STRUCTURE:\n{answer_template}"

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add golden examples for few-shot learning
    if golden_examples:
        for example in golden_examples:
            messages.append({
                "role": "user",
                "content": f"Example question: {example['question']}"
            })
            messages.append({
                "role": "assistant",
                "content": example['golden_answer']
            })

    # Add current query
    messages.append({
        "role": "user",
        "content": f"""Context from Washington tax law:
{context}

Question: {question}

Please answer based on the context above."""
    })

    # Add recent conversation history
    for msg in st.session_state.messages[-4:]:
        if msg['role'] in ['user', 'assistant']:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=800
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating answer: {e}"


def render_feedback_widget(message_index: int):
    """Render feedback collection widget for a response"""
    msg = st.session_state.messages[message_index]

    if msg['role'] != 'assistant':
        return

    feedback_key = f"feedback_{message_index}"

    st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
    st.markdown("**📝 How was this answer?**")

    # Quick feedback row
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("👍 Helpful", key=f"thumbs_up_{message_index}", use_container_width=True):
            save_feedback(message_index, "thumbs_up", rating=5)
            st.success("Thanks!")
            st.rerun()

    with col2:
        if st.button("👎 Not Helpful", key=f"thumbs_down_{message_index}", use_container_width=True):
            save_feedback(message_index, "thumbs_down", rating=2)
            st.info("We'll improve!")
            st.rerun()

    with col3:
        if st.button("💡 Suggest Improvement", key=f"suggest_{message_index}", use_container_width=True):
            st.session_state[f"show_detailed_feedback_{message_index}"] = True
            st.rerun()

    # Star rating row
    st.markdown("**⭐ Rate this answer (optional):**")

    rating_col1, rating_col2 = st.columns([3, 1])

    with rating_col1:
        rating = st.select_slider(
            "Stars",
            options=[1, 2, 3, 4, 5],
            value=3,
            key=f"rating_{message_index}",
            format_func=lambda x: "⭐" * x,
            label_visibility="collapsed"
        )

    with rating_col2:
        if st.button("Submit Rating", key=f"submit_rating_{message_index}"):
            save_feedback(message_index, "rating", rating=rating)
            st.success(f"{rating} stars!")
            st.rerun()

    # Detailed feedback form
    if st.session_state.get(f"show_detailed_feedback_{message_index}", False):
        with st.expander("✍️ Provide Detailed Feedback", expanded=True):
            feedback_type = st.selectbox(
                "What would you like to improve?",
                [
                    "Better answer content",
                    "Better answer structure/format",
                    "Better citations/sources",
                    "Missing information",
                    "Incorrect information"
                ],
                key=f"feedback_type_{message_index}"
            )

            suggested_answer = st.text_area(
                "What should the answer have been? (Optional)",
                key=f"suggested_answer_{message_index}",
                height=100
            )

            suggested_structure = st.text_area(
                "How would you like the answer structured? (Optional)",
                key=f"suggested_structure_{message_index}",
                placeholder="Example: Start with yes/no, then explain reasoning, then cite sources",
                height=80
            )

            # Citation selection
            retrieved_chunks = msg.get('rag_metadata', {}).get('results', [])
            available_citations = [c.get('citation') for c in retrieved_chunks if c.get('citation')]

            if available_citations:
                suggested_citations = st.multiselect(
                    "Which citations would you prefer to see?",
                    options=available_citations,
                    key=f"suggested_citations_{message_index}"
                )
            else:
                suggested_citations = []

            feedback_comment = st.text_area(
                "Additional comments (Optional)",
                key=f"feedback_comment_{message_index}",
                height=60
            )

            if st.button("Submit Detailed Feedback", key=f"submit_feedback_{message_index}"):
                feedback_data = {
                    "feedback_type": {
                        "Better answer content": "better_answer",
                        "Better answer structure/format": "better_structure",
                        "Better citations/sources": "better_citations",
                        "Missing information": "missing_info",
                        "Incorrect information": "incorrect_info"
                    }[feedback_type],
                    "rating": rating,
                    "suggested_answer": suggested_answer if suggested_answer else None,
                    "suggested_structure": suggested_structure if suggested_structure else None,
                    "suggested_citations": suggested_citations if suggested_citations else None,
                    "feedback_comment": feedback_comment if feedback_comment else None
                }

                save_feedback(message_index, feedback_data["feedback_type"], **feedback_data)
                st.success("✅ Detailed feedback saved! The system will learn from this.")
                st.session_state[f"show_detailed_feedback_{message_index}"] = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def save_feedback(message_index: int, feedback_type: str, **kwargs):
    """Save feedback to database"""
    msg = st.session_state.messages[message_index]

    # Get the original query (look backwards for user message)
    query = None
    for i in range(message_index - 1, -1, -1):
        if st.session_state.messages[i]['role'] == 'user':
            query = st.session_state.messages[i]['content']
            break

    if not query:
        return

    feedback_data = {
        "feedback_type": feedback_type,
        **kwargs
    }

    # Get RAG metadata
    rag_metadata = msg.get('rag_metadata')

    st.session_state.feedback_system.save_feedback(
        query=query,
        response_text=msg['content'],
        feedback_data=feedback_data,
        session_id=st.session_state.session_id,
        rag_metadata=rag_metadata
    )


def render_learning_insights():
    """Show what the system has learned"""
    st.markdown('<div class="learning-box">', unsafe_allow_html=True)
    st.markdown("**🧠 System Learning Insights**")

    # Get recent improvements
    try:
        improvements = st.session_state.feedback_system.supabase.table("learned_improvements")\
            .select("*")\
            .eq("is_active", True)\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
    except Exception as e:
        # Table doesn't exist yet
        st.info("Learning insights will appear here as the system learns from feedback.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if improvements.data:
        st.markdown(f"**{len(improvements.data)} active improvement rules**")
        for imp in improvements.data[:3]:
            validation_rate = imp.get("validation_rate", 0) or 0
            st.markdown(f"- {imp['improvement_type']}: {validation_rate:.0%} success rate")
    else:
        st.markdown("_No improvements learned yet. Provide feedback to help the system learn!_")

    # Get golden dataset count
    golden = st.session_state.feedback_system.supabase.table("golden_qa_pairs")\
        .select("id", count="exact")\
        .execute()

    if golden.count:
        st.markdown(f"**{golden.count} high-quality examples** in golden dataset")

    st.markdown('</div>', unsafe_allow_html=True)


def render_decision_info(search_result: Dict):
    """Render the decision-making information"""
    action = search_result['action']
    reasoning = search_result['reasoning']
    confidence = search_result['confidence']
    cost_saved = search_result['cost_saved']

    action_icons = {
        'USE_CACHED': '💾',
        'USE_RULES': '📋',
        'RETRIEVE_SIMPLE': '🔍',
        'RETRIEVE_ENHANCED': '🚀'
    }

    if confidence >= 0.85:
        conf_class = "confidence-high"
        conf_emoji = "🟢"
    elif confidence >= 0.65:
        conf_class = "confidence-medium"
        conf_emoji = "🟡"
    else:
        conf_class = "confidence-low"
        conf_emoji = "🔴"

    decision_html = f"""
    <div class="decision-box">
        <strong>{action_icons.get(action, '🤖')} Decision: {action.replace('_', ' ').title()}</strong><br/>
        <strong>💭 Reasoning:</strong> {reasoning}<br/>
        <strong>{conf_emoji} Confidence:</strong> <span class="{conf_class}">{confidence:.0%}</span><br/>
        <strong>💰 Cost Saved:</strong> <span class="cost-saved">${cost_saved:.4f}</span>
    </div>
    """

    st.markdown(decision_html, unsafe_allow_html=True)


def get_file_url_for_document(document_id: str) -> tuple:
    """Fetch file_url and source_file from knowledge_documents table"""
    try:
        from core.database import get_supabase_client
        supabase = get_supabase_client()

        result = supabase.table('knowledge_documents').select('file_url, source_file').eq('id', document_id).execute()
        if result.data and len(result.data) > 0:
            return (result.data[0].get('file_url', ''), result.data[0].get('source_file', ''))
    except Exception as e:
        print(f"Error fetching file_url: {e}")
    return ('', '')


def render_source(doc: Dict, index: int):
    """Render a source document with clickable citation link and page numbers"""
    citation = doc.get('citation', 'N/A')
    section = doc.get('section_title', '')
    similarity = doc.get('similarity', 0)
    category = doc.get('law_category', '')
    text = doc.get('chunk_text', '')[:200]

    # Get file_url and source_file
    file_url = doc.get('file_url') or ''
    source_file = doc.get('source_file') or ''

    # If BOTH are missing, fetch from database
    if (not file_url and not source_file) and doc.get('document_id'):
        db_url, db_source = get_file_url_for_document(doc.get('document_id'))
        file_url = db_url or ''
        source_file = db_source or ''

    # Prioritize file_url (online URL), fall back to source_file (local path)
    if file_url:
        citation_display = f'<a href="{file_url}" target="_blank" style="color: #1f77b4; text-decoration: none; font-weight: bold;">{citation}</a> 🔗'
    elif source_file:
        # For local files, just show the citation and path (file:// URLs don't work reliably)
        import os
        filename = os.path.basename(source_file)
        citation_display = f'<span style="color: #1f77b4; font-weight: bold;">{citation}</span> 📄 <span style="color: #666; font-size: 0.85rem;">({filename})</span>'
    else:
        citation_display = f'<span style="color: #000; font-weight: bold;">{citation}</span>'

    page_info = ''
    if section and ('Page' in section or 'Pages' in section):
        page_info = f'<span style="color: #1f77b4; font-weight: bold;"> | 📄 {section}</span>'
    elif section:
        page_info = f'<span style="color: #666;"> - {section}</span>'

    source_html = f"""
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
    st.markdown('<div class="main-header">🧠 Enhanced RAG with Continuous Learning</div>', unsafe_allow_html=True)
    st.caption("Washington Tax Law - Powered by Agentic RAG + User Feedback Learning")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Learning toggle
        use_learning = st.checkbox(
            "🧠 Use Learned Improvements",
            value=True,
            help="Apply learned preferences from user feedback (templates, citation preferences, etc.)"
        )

        # Force retrieval option
        force_retrieval = st.checkbox(
            "Force Enhanced Retrieval",
            value=False,
            help="Skip AI decision-making and always use full enhanced search"
        )

        # Top-k setting
        top_k = st.slider(
            "Number of Results",
            min_value=1,
            max_value=15,
            value=5,
            help="How many source documents to retrieve (recommended: 5+ for compare mode)"
        )

        st.divider()

        # Law Version Selection (NEW!)
        st.subheader("📅 Law Version")

        law_version = st.radio(
            "Which law version?",
            options=["new_law", "old_law", "compare"],
            format_func=lambda x: {
                "new_law": "📘 New Law (ESSB 5814, Oct 2025+)",
                "old_law": "📕 Old Law (Pre-Oct 2025)",
                "compare": "🔄 Compare Old vs New"
            }[x],
            index=0,  # Default to new law
            help="ESSB 5814 effective October 1, 2025 changed several service taxation rules"
        )

        # Show context based on selection
        if law_version == "new_law":
            st.info("Showing current law (ESSB 5814 effective Oct 1, 2025)")
        elif law_version == "old_law":
            st.warning("Showing pre-ESSB 5814 law (before Oct 1, 2025)")
        elif law_version == "compare":
            st.success("Will compare old law vs new law side-by-side")

        st.divider()

        # Filters
        st.subheader("🔍 Filters")

        # Law Category
        law_category = st.selectbox(
            "Law Category",
            options=[None, "software", "digital_goods", "exemption", "general", "rate", "definition", "compliance"],
            format_func=lambda x: "All categories" if x is None else x.replace("_", " ").title(),
            help="Filter by type of tax law"
        )

        # Tax Types
        tax_types_options = ["sales tax", "use tax", "B&O tax", "retail sales tax"]
        tax_types = st.multiselect(
            "Tax Types",
            options=tax_types_options,
            help="Filter by specific tax types"
        )

        # Industries
        industries_options = ["general", "retail", "technology", "software development", "manufacturing"]
        industries = st.multiselect(
            "Industries",
            options=industries_options,
            help="Filter by industry applicability"
        )

        # Citation search
        citation_filter = st.text_input(
            "Citation Filter",
            placeholder="e.g., WAC 458-20-15503",
            help="Filter by specific citation (e.g., WAC or RCW number)"
        )

        # Clear filters button
        if st.button("🗑️ Clear Filters"):
            st.rerun()

        # Show active filters
        active_filters = sum([
            1 if law_category else 0,
            1 if tax_types else 0,
            1 if industries else 0,
            1 if citation_filter else 0
        ])
        if active_filters > 0:
            st.success(f"✅ {active_filters} filter(s) active")

        st.divider()

        # Learning insights
        render_learning_insights()

        st.divider()

        # Stats
        st.subheader("📊 Session Stats")
        total_messages = len([m for m in st.session_state.messages if m['role'] == 'user'])
        st.metric("Questions Asked", total_messages)

        total_saved = sum([
            m.get('decision', {}).get('cost_saved', 0)
            for m in st.session_state.messages
            if m['role'] == 'decision'
        ])
        st.metric("Total Cost Saved", f"${total_saved:.4f}")

        st.divider()

        # Help
        with st.expander("❓ Help"):
            st.markdown("""
            **How it works:**
            1. Ask your question
            2. Get AI-powered answer with sources
            3. Provide feedback to improve the system
            4. System learns and gets better over time!

            **Feedback helps with:**
            - Better answer quality
            - Preferred citation sources
            - Answer structure/format
            - Query understanding
            """)

        # Clear chat
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

    # Main chat interface
    st.divider()

    # Display conversation
    for i, message in enumerate(st.session_state.messages):
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])

        elif message['role'] == 'decision':
            with st.expander("🤖 Decision Analysis", expanded=False):
                render_decision_info(message['decision'])

        elif message['role'] == 'assistant':
            with st.chat_message("assistant"):
                st.markdown(message['content'])

            # Add feedback widget
            render_feedback_widget(i)

        elif message['role'] == 'sources':
            # Check if this is comparison mode
            if message.get('comparison_mode'):
                with st.expander("📚 View Sources - Comparison Mode", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### 📕 Old Law (Pre-Oct 2025)")
                        old_law_sources = message.get('old_law_results', [])
                        if old_law_sources:
                            st.caption(f"Found {len(old_law_sources)} sources")
                            for i, doc in enumerate(old_law_sources, 1):
                                if 'citation' in doc:
                                    st.markdown(f"<div style='border-left: 4px solid #dc3545; padding-left: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                                    render_source(doc, i)
                                    st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.info("No old law sources found")

                    with col2:
                        st.markdown("### 📘 New Law (ESSB 5814, Oct 2025+)")
                        new_law_sources = message.get('new_law_results', [])
                        if new_law_sources:
                            st.caption(f"Found {len(new_law_sources)} sources")
                            for i, doc in enumerate(new_law_sources, 1):
                                if 'citation' in doc:
                                    st.markdown(f"<div style='border-left: 4px solid #28a745; padding-left: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                                    render_source(doc, i)
                                    st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.info("No new law sources found")
            else:
                # Normal mode: show all sources together
                with st.expander("📚 View Sources", expanded=True):
                    for j, doc in enumerate(message['sources'], 1):
                        if 'citation' in doc:
                            render_source(doc, j)

    # Chat input
    if prompt := st.chat_input("Ask a question about Washington tax law..."):
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Making intelligent decision..."):
                # Build context with filters
                context = {}
                if law_category or tax_types or industries:
                    context['filters'] = {
                        'law_category': law_category,
                        'tax_types': tax_types if tax_types else None,
                        'industries': industries if industries else None
                    }

                # For compare mode, retrieve MORE results to ensure we get both old and new law
                search_top_k = top_k * 3 if law_version == "compare" else top_k

                # Use enhanced RAG with decision-making and filters
                search_result = st.session_state.rag.search_with_decision(
                    prompt,
                    context=context,
                    top_k=search_top_k,
                    force_retrieval=force_retrieval
                )

                # Apply citation filter client-side if specified
                if citation_filter and search_result.get('results'):
                    filtered_results = [
                        r for r in search_result['results']
                        if citation_filter.upper() in r.get('citation', '').upper()
                    ]
                    search_result['results'] = filtered_results

                # Apply law version filter
                if law_version in ["old_law", "new_law"] and search_result.get('results'):
                    search_result['results'] = st.session_state.law_version_handler.filter_by_law_version(
                        search_result['results'],
                        law_version
                    )
                elif law_version == "compare" and search_result.get('results'):
                    # For compare mode, separate into old and new
                    old_law_results = st.session_state.law_version_handler.filter_by_law_version(
                        search_result['results'],
                        "old_law"
                    )
                    new_law_results = st.session_state.law_version_handler.filter_by_law_version(
                        search_result['results'],
                        "new_law"
                    )

                    # Limit each to top_k results
                    old_law_results = old_law_results[:top_k]
                    new_law_results = new_law_results[:top_k]

                    # Store both for comparison display
                    search_result['old_law_results'] = old_law_results
                    search_result['new_law_results'] = new_law_results
                    search_result['comparison_mode'] = True

                    # Combine for answer generation (prioritize new law, then old law)
                    search_result['results'] = new_law_results + old_law_results

                # Store decision
                st.session_state.messages.append({
                    'role': 'decision',
                    'decision': search_result
                })

                # Check if we got results
                if not search_result.get('results'):
                    response = "❌ No relevant information found. Try rephrasing your question."
                    st.warning(response)
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response,
                        'rag_metadata': search_result
                    })
                else:
                    # Generate answer
                    with st.spinner("✍️ Generating answer..."):
                        answer = generate_answer(prompt, search_result, use_learning=use_learning)

                    # Display answer
                    st.markdown(answer)

                    # Store answer with metadata
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': answer,
                        'rag_metadata': search_result
                    })

                    # Store sources
                    sources_msg = {
                        'role': 'sources',
                        'sources': search_result['results']
                    }
                    # If comparison mode, include old/new law results
                    if search_result.get('comparison_mode'):
                        sources_msg['comparison_mode'] = True
                        sources_msg['old_law_results'] = search_result.get('old_law_results', [])
                        sources_msg['new_law_results'] = search_result.get('new_law_results', [])

                    st.session_state.messages.append(sources_msg)

        # Show decision analysis
        with st.expander("🤖 Decision Analysis", expanded=True):
            render_decision_info(search_result)

        # Show sources
        if search_result.get('comparison_mode'):
            # Comparison mode: show old vs new side by side
            with st.expander("📚 View Sources - Comparison Mode", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📕 Old Law (Pre-Oct 2025)")
                    old_law_sources = search_result.get('old_law_results', [])
                    if old_law_sources:
                        st.caption(f"Found {len(old_law_sources[:top_k])} sources")
                        for i, doc in enumerate(old_law_sources[:top_k], 1):
                            if 'citation' in doc:
                                # Add visual indicator that this is old law
                                st.markdown(f"<div style='border-left: 4px solid #dc3545; padding-left: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                                render_source(doc, i)
                                st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("No old law sources found")

                with col2:
                    st.markdown("### 📘 New Law (ESSB 5814, Oct 2025+)")
                    new_law_sources = search_result.get('new_law_results', [])
                    if new_law_sources:
                        st.caption(f"Found {len(new_law_sources[:top_k])} sources")
                        for i, doc in enumerate(new_law_sources[:top_k], 1):
                            if 'citation' in doc:
                                # Add visual indicator that this is new law
                                st.markdown(f"<div style='border-left: 4px solid #28a745; padding-left: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                                render_source(doc, i)
                                st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("No new law sources found")

                # Show key changes if available
                if old_law_sources and new_law_sources:
                    st.markdown("### 🔄 Key Changes")
                    comparison = st.session_state.law_version_handler.compare_old_vs_new(
                        prompt,
                        old_law_sources,
                        new_law_sources
                    )
                    for change in comparison['key_changes']:
                        st.markdown(f"- {change}")

                    if comparison['refund_implications']:
                        st.warning(f"**Refund Implications:** {comparison['refund_implications']}")

        elif search_result.get('results'):
            with st.expander("📚 View Sources", expanded=True):
                for i, doc in enumerate(search_result['results'][:top_k], 1):
                    if 'citation' in doc:
                        # Show law version label if present
                        if doc.get('law_version_label'):
                            st.markdown(f"**{doc['law_version_label']}**")
                        render_source(doc, i)

        st.rerun()

    # Footer
    st.divider()
    st.caption("🧠 Powered by Enhanced RAG + Continuous Learning | 📚 Washington State Tax Law")


if __name__ == "__main__":
    main()
