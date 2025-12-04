"""
AI Chat Component
=================

Slide-in AI assistant chat panel with model routing.
Inspired by the React AIAssistant.tsx component.
"""

import streamlit as st
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # "user" or "assistant"
    content: str
    model: Optional[str] = None


# System prompt for the tax assistant
TAX_ASSISTANT_SYSTEM_PROMPT = """You are a Washington State Tax Assistant specializing in:
- RCW (Revised Code of Washington) citations
- WAC (Washington Administrative Code) rules
- ESSB 5814 interpretation
- B&O (Business & Occupation) tax classifications
- Sales and Use tax exemptions
- Invoice classification for tax purposes

When answering questions:
1. Cite specific RCW or WAC sections when applicable
2. Be precise about tax rates and classifications
3. Explain exemption criteria clearly
4. Note when professional tax advice should be sought

Keep responses concise but thorough. Use bullet points for clarity."""


def classify_query_complexity(query: str) -> tuple[str, float]:
    """
    Classify query complexity to determine which model to use.

    Returns:
        Tuple of (task_type, estimated_stakes)
    """
    query_lower = query.lower()

    # High complexity indicators (use premium models)
    high_complexity_keywords = [
        "analyze", "complex", "audit", "litigation", "appeal",
        "multiple", "combined", "nexus", "apportionment",
        "refund claim", "exemption certificate", "ruling"
    ]

    # Medium complexity (use standard models)
    medium_complexity_keywords = [
        "classify", "categorize", "determine", "which rate",
        "taxable or exempt", "b&o rate", "sales tax",
        "rcw", "wac", "essb"
    ]

    # Simple queries (use budget models)
    simple_keywords = [
        "what is", "define", "meaning", "rate for",
        "hello", "hi", "help", "thank"
    ]

    # Check keywords
    has_high = any(kw in query_lower for kw in high_complexity_keywords)
    has_medium = any(kw in query_lower for kw in medium_complexity_keywords)
    has_simple = any(kw in query_lower for kw in simple_keywords)

    # Determine task type and stakes
    if has_high:
        return "analysis", 30000  # Premium model
    elif has_medium:
        return "analysis", 10000  # Standard model
    else:
        return "validation", 1000  # Budget model


def get_ai_response(
    query: str,
    conversation_history: list[ChatMessage] = None,
    system_prompt: str = TAX_ASSISTANT_SYSTEM_PROMPT,
) -> tuple[str, str]:
    """
    Get AI response using the model router.

    Args:
        query: User's question
        conversation_history: Previous messages for context
        system_prompt: System prompt for the AI

    Returns:
        Tuple of (response_text, model_used)
    """
    try:
        from core.model_router import ModelRouter, get_router

        # Classify query complexity
        task_type, stakes = classify_query_complexity(query)

        # Get router
        router = get_router()

        # Build conversation context
        context = ""
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = "User" if msg.role == "user" else "Assistant"
                context += f"{role}: {msg.content}\n\n"

        full_prompt = f"{context}User: {query}" if context else query

        # Execute with model routing
        result = router.execute(
            task=task_type,
            prompt=full_prompt,
            stakes=stakes,
            system_prompt=system_prompt,
            max_tokens=1024,
        )

        return result["content"], result["model"]

    except ImportError:
        # Fallback if model_router not available
        return _fallback_response(query), "fallback"
    except Exception as e:
        return f"I encountered an error: {str(e)}", "error"


def _fallback_response(query: str) -> str:
    """Fallback response when model router is not available."""
    return """I'm currently unable to connect to the AI service.

Please check that:
1. API keys are configured in .env file
2. The model_router module is properly installed

For immediate help, consult:
- RCW 82.04 for B&O tax rates
- RCW 82.08 for retail sales tax
- RCW 82.12 for use tax
- WAC 458-20 for DOR rules"""


def render_ai_chat() -> None:
    """
    Render the AI chat interface in the sidebar or main area.
    """
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            ChatMessage(
                role="assistant",
                content="Hello! I'm your Washington State Tax Assistant. I can help with RCW citations, ESSB 5814 interpretation, and invoice classification. How can I assist you today?"
            )
        ]

    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    # Chat header
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 1rem;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 12px;
        margin-bottom: 1rem;
    ">
        <div style="
            width: 40px;
            height: 40px;
            background: white;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
                <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/>
                <path d="M5 19l1 3 3-1-1-3-3 1z"/>
                <path d="M19 19l-1 3-3-1 1-3 3 1z"/>
            </svg>
        </div>
        <div>
            <div style="font-weight: 600; color: white; font-size: 1rem;">Tax AI Assistant</div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="width: 8px; height: 8px; background: #86efac; border-radius: 50%;"></span>
                <span style="font-size: 0.75rem; color: rgba(255,255,255,0.9);">Online & Ready</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Messages container
    messages_container = st.container()

    with messages_container:
        for msg in st.session_state.chat_messages:
            if msg.role == "user":
                # User message
                st.markdown(f"""
                <div style="
                    display: flex;
                    justify-content: flex-end;
                    margin-bottom: 1rem;
                ">
                    <div style="
                        background: #1e293b;
                        color: white;
                        padding: 0.75rem 1rem;
                        border-radius: 1rem;
                        border-top-right-radius: 0;
                        max-width: 80%;
                        font-size: 0.875rem;
                        line-height: 1.5;
                    ">
                        {msg.content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message
                model_badge = f'<span style="font-size: 0.65rem; color: #94a3b8; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; margin-top: 4px; display: inline-block;">{msg.model}</span>' if msg.model else ''
                st.markdown(f"""
                <div style="
                    display: flex;
                    margin-bottom: 1rem;
                ">
                    <div style="
                        background: white;
                        border: 1px solid #e2e8f0;
                        padding: 0.75rem 1rem;
                        border-radius: 1rem;
                        border-top-left-radius: 0;
                        max-width: 80%;
                        font-size: 0.875rem;
                        line-height: 1.5;
                        color: #334155;
                    ">
                        {msg.content}
                        {model_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Input area
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])

    with col1:
        user_input = st.text_input(
            "Ask a question",
            placeholder="Ask about B&O rates, invoices, or RCW 82.04...",
            key="ai_chat_input",
            label_visibility="collapsed"
        )

    with col2:
        send_clicked = st.button("Send", type="primary", use_container_width=True)

    # Handle send
    if send_clicked and user_input:
        # Add user message
        st.session_state.chat_messages.append(
            ChatMessage(role="user", content=user_input)
        )

        # Get AI response
        with st.spinner("Thinking..."):
            response, model = get_ai_response(
                user_input,
                st.session_state.chat_messages[:-1]
            )

        # Add assistant message
        st.session_state.chat_messages.append(
            ChatMessage(role="assistant", content=response, model=model)
        )

        # Rerun to update UI
        st.rerun()

    # Disclaimer
    st.markdown("""
    <div style="
        text-align: center;
        font-size: 0.65rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    ">
        AI can make mistakes. Verify with official DOR guidance.
    </div>
    """, unsafe_allow_html=True)


def render_chat_button() -> bool:
    """
    Render a floating chat button that can toggle the AI panel.

    Returns:
        True if chat should be shown, False otherwise
    """
    if "show_ai_chat" not in st.session_state:
        st.session_state.show_ai_chat = False

    # Add floating button CSS
    st.markdown("""
    <style>
    .ai-toggle-btn {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 9999px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        z-index: 1000;
        font-weight: 500;
        border: none;
        transition: all 0.2s ease;
    }
    .ai-toggle-btn:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

    return st.session_state.show_ai_chat


# Export
__all__ = [
    "render_ai_chat",
    "render_chat_button",
    "get_ai_response",
    "ChatMessage",
    "TAX_ASSISTANT_SYSTEM_PROMPT",
]
