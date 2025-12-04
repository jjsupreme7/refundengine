#!/usr/bin/env python3
"""
TaxDesk - NexusTax Dashboard (Dark Theme)
=========================================

Main entry point for the redesigned Streamlit multi-page application.
Features:
- Dark theme with glass morphism effects
- Clean stat card overview
- Liability trend visualization
- Urgent actions panel
- AI assistant integration

Usage:
    DEV_MODE=1 PYTHONPATH=. streamlit run dashboard/Dashboard.py --server.port 8501
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="NexusTax - Tax Refund Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "NexusTax - AI-Powered Tax Refund Analysis Platform"},
)

# AUTHENTICATION
from core.auth import require_authentication

if not require_authentication():
    st.stop()

# Import styles and components
from dashboard.styles import inject_css, ACCENT_PURPLE, WA_EMERALD
from dashboard.components import render_stat_grid

# Inject CSS theme
inject_css()

# Import data functions
from dashboard.utils.data_loader import load_analyzed_transactions, get_dashboard_stats

# Get real data
df = load_analyzed_transactions()
stats = get_dashboard_stats(df)


# =============================================================================
# SIDEBAR - Dark Theme
# =============================================================================
with st.sidebar:
    # Brand
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 1rem 0;
        margin-bottom: 1rem;
    ">
        <div style="
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, {ACCENT_PURPLE}, #6366f1);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"></rect>
                <rect x="14" y="3" width="7" height="7"></rect>
                <rect x="14" y="14" width="7" height="7"></rect>
                <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
        </div>
        <span style="font-weight: 700; font-size: 1.25rem; color: #ffffff;">
            Nexus<span style="color: {ACCENT_PURPLE};">Tax</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick stats in sidebar
    st.markdown("### Quick Stats")

    total_transactions = stats.get("total_transactions", 0)
    flagged_count = stats.get("flagged_count", 0)
    total_refund = stats.get("total_refund", 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", total_transactions)
    with col2:
        st.metric("Flagged", flagged_count)

    st.metric("Est. Refund", f"${total_refund:,.0f}")

    st.markdown("---")

    # AI Assistant toggle
    if "show_ai_panel" not in st.session_state:
        st.session_state.show_ai_panel = False

    if st.button("Ask AI Assistant", use_container_width=True, type="primary"):
        st.session_state.show_ai_panel = not st.session_state.show_ai_panel


# =============================================================================
# MAIN CONTENT
# =============================================================================
def main():
    """Main dashboard landing page"""

    # Header - Dark theme
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="
            font-size: 1.875rem;
            font-weight: 700;
            color: #ffffff;
            margin: 0;
            letter-spacing: -0.025em;
        ">Tax Overview</h1>
        <p style="
            color: #9ca3af;
            margin-top: 0.25rem;
            font-size: 0.875rem;
        ">Washington State Department of Revenue compliance status.</p>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # STAT CARDS
    # ==========================================================================
    total_refund = stats.get("total_refund", 0)
    pending_reviews = stats.get("flagged_count", 0)
    refund_rows = stats.get("refund_rows", 0)
    use_tax_due = stats.get("use_tax_due", 840)  # Placeholder

    render_stat_grid([
        {
            "label": "Est. B&O Liability",
            "value": f"${total_refund:,.0f}",
            "subtitle": "Q4 2024 Projections",
            "change": "+2.4%",
            "icon": "trending_up",
            "variant": "success",
        },
        {
            "label": "Pending Invoices",
            "value": str(pending_reviews),
            "subtitle": "Requires classification",
            "icon": "file_text",
            "variant": "warning",
        },
        {
            "label": "Audit Risk Score",
            "value": "Low",
            "subtitle": "Based on recent patterns",
            "icon": "alert_circle",
            "variant": "info",
        },
        {
            "label": "Use Tax Due",
            "value": f"${use_tax_due:,.0f}",
            "subtitle": "Unpaid consumer use tax",
            "icon": "arrow_up_right",
            "variant": "purple",
        },
    ])

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # ==========================================================================
    # MAIN CONTENT GRID
    # ==========================================================================
    col_chart, col_actions = st.columns([2, 1])

    # --------------------------------------------------------------------------
    # LIABILITY TREND CHART
    # --------------------------------------------------------------------------
    with col_chart:
        st.markdown("""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #ffffff; margin: 0;">Liability Trend</h2>
            </div>
        """, unsafe_allow_html=True)

        # Time range selector
        time_range = st.selectbox(
            "Time Range",
            ["Last 6 Months", "YTD", "Last Year"],
            label_visibility="collapsed",
            key="trend_time_range"
        )

        # Sample chart data
        import pandas as pd

        chart_data = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
            "Liability": [4000, 3000, 2000, 2780, 1890, 2390, 3490]
        })

        st.area_chart(
            chart_data.set_index("Month"),
            color="#8b5cf6",
            height=300,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # URGENT ACTIONS PANEL
    # --------------------------------------------------------------------------
    with col_actions:
        st.markdown("""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 1.5rem;
        ">
            <h2 style="font-size: 1.125rem; font-weight: 600; color: #ffffff; margin-bottom: 1rem;">Urgent Actions</h2>
        """, unsafe_allow_html=True)

        # Get flagged items from data
        if df is not None and not df.empty:
            # Look for flagged/low confidence items
            flagged_items = []

            # Check for AI_Confidence column
            conf_col = None
            for col in ["AI_Confidence", "Confidence_Score", "confidence"]:
                if col in df.columns:
                    conf_col = col
                    break

            if conf_col:
                low_conf = df[df[conf_col] < 0.9].head(3)
                for _, row in low_conf.iterrows():
                    vendor = row.get("Vendor_Name", row.get("vendor", "Unknown Vendor"))
                    amount = row.get("Tax_Paid", row.get("Amount", row.get("amount", 0)))
                    flagged_items.append({"vendor": vendor, "amount": amount})

            if flagged_items:
                for item in flagged_items:
                    st.markdown(f"""
                    <div style="
                        display: flex;
                        align-items: flex-start;
                        gap: 0.75rem;
                        padding: 0.75rem;
                        border-radius: 0.75rem;
                        background: rgba(239, 68, 68, 0.15);
                        border: 1px solid rgba(239, 68, 68, 0.3);
                        margin-bottom: 0.5rem;
                    ">
                        <div style="min-width: 16px; margin-top: 2px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fca5a5" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                        </div>
                        <div>
                            <p style="font-size: 0.875rem; font-weight: 500; color: #ffffff; margin: 0;">Review: {item['vendor']}</p>
                            <p style="font-size: 0.75rem; color: #9ca3af; margin: 0.25rem 0 0 0;">Potential miss-classification on ${item['amount']:,.2f}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    background: rgba(34, 197, 94, 0.15);
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 0.75rem;
                    padding: 0.75rem;
                    color: #86efac;
                    font-size: 0.875rem;
                ">No urgent items requiring review</div>
                """, unsafe_allow_html=True)

        # Legislative update
        st.markdown("""
        <div style="
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            padding: 0.75rem;
            border-radius: 0.75rem;
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            margin-top: 0.5rem;
        ">
            <div style="min-width: 16px; margin-top: 2px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#93c5fd" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
            </div>
            <div>
                <p style="font-size: 0.875rem; font-weight: 500; color: #ffffff; margin: 0;">ESSB 5814 Update</p>
                <p style="font-size: 0.75rem; color: #9ca3af; margin: 0.25rem 0 0 0;">New workforce education surcharge rates apply effective Jan 1.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        if st.button("View All Notifications", use_container_width=True):
            st.info("Navigate to Settings for notification preferences")

        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================================================
    # AI ASSISTANT PANEL (Slide-in from sidebar toggle)
    # ==========================================================================
    if st.session_state.get("show_ai_panel", False):
        st.markdown("---")
        st.markdown("### AI Tax Assistant")

        from dashboard.components import render_ai_chat
        render_ai_chat()

    # ==========================================================================
    # FOOTER
    # ==========================================================================
    st.markdown("---")
    st.markdown("""
    <div style="
        text-align: center;
        font-size: 0.75rem;
        color: #6b7280;
        padding: 1rem 0;
    ">
        Powered by Enhanced RAG + Multi-Model AI | Washington State Tax Law Database
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
