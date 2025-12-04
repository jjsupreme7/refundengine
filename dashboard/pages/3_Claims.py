#!/usr/bin/env python3
"""
Claims Page - Draft and finalize refund claims
==============================================

Create, review, and submit tax refund claims.
Updated with NexusTax styling.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Claims | NexusTax",
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

# Import data loader
from dashboard.utils.data_loader import load_analyzed_transactions

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
    ">Claims</h1>
    <p style="color: #9ca3af; margin-top: 0.25rem;">
        Draft and finalize tax refund claims for submission.
    </p>
</div>
""", unsafe_allow_html=True)

# Action buttons
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("Create New Claim", type="primary", use_container_width=True):
        st.session_state.show_create_claim = True

with col2:
    if st.button("Export All", use_container_width=True):
        st.info("Export functionality coming soon")

st.markdown("---")

# =============================================================================
# CREATE CLAIM FORM
# =============================================================================
if st.session_state.get("show_create_claim", False):
    with st.expander("Create New Claim", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            claim_type = st.selectbox(
                "Claim Type*",
                ["Use Tax Refund", "Sales Tax Refund", "B&O Tax Credit", "Other"],
            )

            jurisdiction = st.selectbox(
                "Jurisdiction*",
                ["Washington State DOR", "Oregon DOR", "California CDTFA", "Other"],
            )

        with col2:
            period_start = st.date_input("Period Start*")
            period_end = st.date_input("Period End*")

            filing_method = st.selectbox(
                "Filing Method*",
                ["Electronic (Online Portal)", "Paper Mail", "Email Submission"],
            )

        claim_summary = st.text_area(
            "Claim Summary",
            placeholder="Brief summary of the claim basis and supporting documentation...",
            height=100,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Create Claim", type="primary", use_container_width=True):
                st.success("Claim created successfully!")
                st.session_state.show_create_claim = False
                st.rerun()

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_create_claim = False
                st.rerun()

    st.markdown("---")

# =============================================================================
# LOAD DATA
# =============================================================================
df = load_analyzed_transactions()
approved_df = pd.DataFrame()

if df is not None and not df.empty and "Final_Decision" in df.columns:
    try:
        # Ensure column is string type before using str accessor
        df["Final_Decision"] = df["Final_Decision"].astype(str)
        approved_df = df[df["Final_Decision"].str.contains("Add to Claim|Yes|Approved", na=False, case=False)]
    except Exception:
        approved_df = pd.DataFrame()
elif df is not None and not df.empty:
    approved_df = pd.DataFrame()

# =============================================================================
# DRAFT CLAIMS LIST
# =============================================================================
st.markdown("### Draft Claims")

# Mock claim data
claims = [
    {
        "id": "CLAIM-WA-2024-001",
        "project": "WA Use Tax 2022-2024",
        "status": "Draft",
        "total_refund": 184230.00,
        "transactions": 23,
        "created_date": "2024-11-14",
        "jurisdiction": "Washington State DOR",
    }
]

if not claims:
    st.markdown("""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
        color: #9ca3af;
    ">
        No draft claims yet. Create your first claim to get started!
    </div>
    """, unsafe_allow_html=True)
else:
    for claim in claims:
        # Dark theme status colors
        status_colors = {
            "Draft": ("rgba(245, 158, 11, 0.2)", "#fcd34d"),
            "Ready to Submit": ("rgba(34, 197, 94, 0.2)", "#86efac"),
            "Submitted": ("rgba(59, 130, 246, 0.2)", "#93c5fd"),
            "Approved": ("rgba(34, 197, 94, 0.2)", "#86efac"),
            "Rejected": ("rgba(239, 68, 68, 0.2)", "#fca5a5"),
        }
        bg_color, text_color = status_colors.get(claim["status"], ("rgba(107, 114, 128, 0.2)", "#9ca3af"))

        st.markdown(f"""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        " onmouseover="this.style.borderColor='#8b5cf6'; this.style.boxShadow='0 0 20px rgba(139, 92, 246, 0.3)';"
           onmouseout="this.style.borderColor='rgba(49, 46, 129, 0.4)'; this.style.boxShadow='none';">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="margin: 0; color: #ffffff; font-size: 1.125rem; font-weight: 600;">{claim['id']}</h3>
                    <p style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.25rem;">
                        {claim['project']} | {claim['jurisdiction']}
                    </p>
                    <div style="margin-top: 0.75rem; display: flex; align-items: center; gap: 1rem; font-size: 0.875rem;">
                        <span style="
                            background: {bg_color};
                            color: {text_color};
                            padding: 0.25rem 0.75rem;
                            border-radius: 9999px;
                            font-size: 0.75rem;
                            font-weight: 600;
                        ">{claim['status']}</span>
                        <span style="color: #6b7280;">Created: {claim['created_date']}</span>
                        <span style="color: #6b7280;">Transactions: {claim['transactions']}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.875rem; font-weight: 700; color: #86efac;">
                        ${claim['total_refund']:,.2f}
                    </div>
                    <div style="font-size: 0.65rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em;">
                        Total Refund
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button("View Details", key=f"view_{claim['id']}", use_container_width=True):
                st.session_state.show_claim_detail = True
                st.session_state.current_claim = claim["id"]
                st.rerun()

        with col2:
            if st.button("Generate Report", key=f"report_{claim['id']}", use_container_width=True):
                st.info("Generating claim report...")

        with col3:
            if st.button("Submit", key=f"submit_{claim['id']}", use_container_width=True, disabled=claim["status"] != "Draft"):
                st.success("Claim submitted successfully!")

        st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# CLAIM DETAIL VIEW
# =============================================================================
if st.session_state.get("show_claim_detail", False):
    st.markdown("---")
    st.markdown("### Claim Details: CLAIM-WA-2024-001")

    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Transactions", "Documentation", "Notes"])

    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            <div style="
                background: rgba(30, 27, 75, 0.3);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(49, 46, 129, 0.4);
                border-radius: 0.75rem;
                padding: 1.5rem;
            ">
                <h4 style="color: #ffffff; margin-bottom: 1rem;">WA Use Tax Review 2022-2024</h4>
                <div style="display: grid; gap: 0.5rem; font-size: 0.875rem; color: #9ca3af;">
                    <p><strong style="color: #c4b5fd;">Claim ID:</strong> CLAIM-WA-2024-001</p>
                    <p><strong style="color: #c4b5fd;">Jurisdiction:</strong> Washington State DOR</p>
                    <p><strong style="color: #c4b5fd;">Period:</strong> 2022-01-01 to 2024-12-31</p>
                    <p><strong style="color: #c4b5fd;">Filing Method:</strong> Electronic (Online Portal)</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.metric("Total Refund", "$184,230.00")
            st.metric("Transactions", "23")
            st.metric("Confidence", "96%")

    with tab2:
        st.markdown("#### Included Transactions")

        if not approved_df.empty:
            cols_to_display = []
            for col in ["Vendor_Name", "Invoice_Number", "Line_Item_Description", "Total_Amount", "Tax_Amount", "Estimated_Refund", "AI_Confidence"]:
                if col in approved_df.columns:
                    cols_to_display.append(col)

            if cols_to_display:
                display_df = approved_df[cols_to_display].copy()
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No transaction data available.")
        else:
            st.info("No approved transactions to include in claim yet.")

    with tab3:
        st.markdown("#### Supporting Documentation")
        st.markdown("""
        - Invoice: INV-10021.pdf (Red Bison Tech Services)
        - Invoice: INV-10022.jpg (CloudOps Northwest)
        - Contract: SOW-DC-01.pdf
        - Analysis Summary Report
        - Legal Citations & References
        """)
        st.button("Add Documentation", use_container_width=True)

    with tab4:
        st.markdown("#### Claim Notes & History")
        notes = st.text_area("Add Note", placeholder="Add notes about this claim...", height=100)
        if st.button("Save Note", type="primary"):
            if notes:
                st.success("Note saved!")

        st.markdown("#### Activity History")
        st.markdown("""
        - **2024-11-14 10:30 AM:** Claim created
        - **2024-11-14 02:15 PM:** Added 23 transactions
        - **2024-11-14 04:45 PM:** Generated analysis report
        """)

    if st.button("Back to Claims List"):
        st.session_state.show_claim_detail = False
        st.rerun()

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="
    font-size: 0.75rem;
    color: #6b7280;
    text-align: center;
">Claims Management | NexusTax Platform</div>
""", unsafe_allow_html=True)
