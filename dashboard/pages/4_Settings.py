#!/usr/bin/env python3
"""
Settings Page
=============

Configure AI models, API keys, and notification preferences.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import os

# Page configuration
st.set_page_config(
    page_title="Settings | NexusTax",
    page_icon="",
    layout="wide"
)

# Auth
from core.auth import require_authentication
if not require_authentication():
    st.stop()

# Import styles
from dashboard.styles import inject_css
inject_css()

# =============================================================================
# PAGE HEADER
# =============================================================================
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <h1 style="
        font-size: 1.875rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    ">Settings</h1>
    <p style="color: #9ca3af; margin-top: 0.25rem;">
        Configure AI models, API keys, and preferences.
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SETTINGS TABS
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["AI Models", "API Keys", "Notifications", "Account"])

# =============================================================================
# AI MODELS TAB
# =============================================================================
with tab1:
    st.markdown("### AI Model Configuration")
    st.markdown("Configure which models to use for different tasks.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Extraction Tasks")
        st.markdown("*PDF scanning, OCR, data extraction*")

        extraction_model = st.selectbox(
            "Extraction Model",
            ["GPT-4o (Recommended)", "GPT-4o-mini (Budget)", "Claude Sonnet 4.5"],
            key="extraction_model"
        )

        st.markdown("#### Analysis Tasks")
        st.markdown("*Tax categorization, exemption analysis*")

        analysis_model = st.selectbox(
            "Analysis Model",
            ["Claude Sonnet 4.5 (Recommended)", "Claude Opus 4.5 (Premium)", "GPT-4o"],
            key="analysis_model"
        )

    with col2:
        st.markdown("#### Legal Citation Tasks")
        st.markdown("*RCW/WAC matching, legal research*")

        legal_model = st.selectbox(
            "Legal Model",
            ["Claude Sonnet 4.5 (Recommended)", "Claude Opus 4.5 (Premium)", "GPT-4o"],
            key="legal_model"
        )

        st.markdown("#### Validation Tasks")
        st.markdown("*Format checking, confidence scoring*")

        validation_model = st.selectbox(
            "Validation Model",
            ["GPT-4o-mini (Budget, Recommended)", "Claude Haiku", "GPT-4o"],
            key="validation_model"
        )

    st.markdown("---")

    st.markdown("#### Stakes-Based Model Routing")
    st.info("When enabled, higher-value transactions automatically use premium models for extra accuracy.")

    stakes_routing = st.checkbox("Enable stakes-based routing", value=True)

    if stakes_routing:
        col1, col2 = st.columns(2)
        with col1:
            high_stakes = st.number_input("High stakes threshold ($)", value=25000, step=5000)
        with col2:
            medium_stakes = st.number_input("Medium stakes threshold ($)", value=5000, step=1000)

        st.markdown(f"""
        - **< ${medium_stakes:,}**: Budget models (GPT-4o-mini, Claude Haiku)
        - **${medium_stakes:,} - ${high_stakes:,}**: Standard models (Claude Sonnet, GPT-4o)
        - **> ${high_stakes:,}**: Premium models (Claude Opus 4.5)
        """)

    if st.button("Save Model Settings", type="primary"):
        st.success("Model settings saved!")

# =============================================================================
# API KEYS TAB
# =============================================================================
with tab2:
    st.markdown("### API Key Configuration")
    st.warning("API keys are stored in your local `.env` file. Never share these keys.")

    # Check current status
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    anthropic_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
    supabase_configured = bool(os.getenv("SUPABASE_URL"))

    st.markdown("#### Current Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        status_color = "#86efac" if openai_configured else "#fca5a5"
        status_bg = "rgba(34, 197, 94, 0.2)" if openai_configured else "rgba(239, 68, 68, 0.2)"
        status_text = "Configured" if openai_configured else "Not Configured"
        st.markdown(f"""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 1rem;
            text-align: center;
        ">
            <div style="font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">OpenAI</div>
            <div style="
                display: inline-block;
                background: {status_bg};
                color: {status_color};
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
            ">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_color = "#86efac" if anthropic_configured else "#fca5a5"
        status_bg = "rgba(34, 197, 94, 0.2)" if anthropic_configured else "rgba(239, 68, 68, 0.2)"
        status_text = "Configured" if anthropic_configured else "Not Configured"
        st.markdown(f"""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 1rem;
            text-align: center;
        ">
            <div style="font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">Anthropic</div>
            <div style="
                display: inline-block;
                background: {status_bg};
                color: {status_color};
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
            ">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        status_color = "#86efac" if supabase_configured else "#fca5a5"
        status_bg = "rgba(34, 197, 94, 0.2)" if supabase_configured else "rgba(239, 68, 68, 0.2)"
        status_text = "Configured" if supabase_configured else "Not Configured"
        st.markdown(f"""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 1rem;
            text-align: center;
        ">
            <div style="font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">Supabase</div>
            <div style="
                display: inline-block;
                background: {status_bg};
                color: {status_color};
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
            ">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("#### Update API Keys")
    st.caption("To update API keys, edit your `.env` file in the project root directory.")

    with st.expander("View .env template"):
        st.code("""
# OpenAI API Key (for GPT-4o, embeddings)
OPENAI_API_KEY=sk-...

# Anthropic API Key (for Claude models)
ANTHROPIC_API_KEY=sk-ant-...

# Supabase Configuration
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# Google AI (optional, for Gemini)
GOOGLE_API_KEY=...
        """, language="bash")

# =============================================================================
# NOTIFICATIONS TAB
# =============================================================================
with tab3:
    st.markdown("### Notification Preferences")

    st.markdown("#### Email Notifications")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox("New document processed", value=True)
        st.checkbox("Analysis complete", value=True)
        st.checkbox("Low confidence alerts", value=True)

    with col2:
        st.checkbox("Claim status updates", value=True)
        st.checkbox("Legislative updates", value=False)
        st.checkbox("Weekly summary", value=True)

    st.markdown("---")

    st.markdown("#### Alert Thresholds")

    confidence_threshold = st.slider(
        "Low confidence alert threshold",
        min_value=0.5,
        max_value=0.95,
        value=0.9,
        step=0.05,
        format="%.0f%%"
    )

    amount_threshold = st.number_input(
        "Large transaction alert threshold ($)",
        value=10000,
        step=1000
    )

    if st.button("Save Notification Settings", type="primary"):
        st.success("Notification settings saved!")

# =============================================================================
# ACCOUNT TAB
# =============================================================================
with tab4:
    st.markdown("### Account Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Profile")
        st.text_input("Display Name", value="Analyst")
        st.text_input("Email", value="analyst@company.com")
        st.selectbox("Default Jurisdiction", ["Washington State", "Oregon", "California"])

    with col2:
        st.markdown("#### Preferences")
        st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        st.selectbox("Currency", ["USD ($)", "CAD ($)", "EUR"])
        st.selectbox("Theme", ["Dark", "Light"], disabled=True, help="Dark theme is now the default")

    st.markdown("---")

    st.markdown("#### Data Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Export All Data", use_container_width=True):
            st.info("Data export coming soon")

    with col2:
        if st.button("Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")

    with col3:
        if st.button("Reset Settings", use_container_width=True, type="secondary"):
            st.warning("This will reset all settings to defaults")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="
    font-size: 0.75rem;
    color: #6b7280;
    text-align: center;
">Settings | NexusTax Platform v2.0</div>
""", unsafe_allow_html=True)
