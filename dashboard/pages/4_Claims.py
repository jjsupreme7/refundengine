"""
Claims Page - Draft and finalize refund claims

Create, review, and submit tax refund claims.
"""

from core.auth import require_authentication
from dashboard.utils.data_loader import get_projects_from_db, load_analyzed_transactions
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Page configuration
st.set_page_config(page_title="Claims - TaxDesk", page_icon="📋", layout="wide")

# AUTHENTICATION

if not require_authentication():
    st.stop()

# Header
st.markdown('<div class="main-header">📋 Claims</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Draft and finalize tax refund claims for submission</div>',
    unsafe_allow_html=True,
)

# Action buttons
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("➕ Create New Claim", type="primary", use_container_width=True):
        st.session_state.show_create_claim = True

with col2:
    if st.button("📥 Export All", use_container_width=True):
        st.info("Export functionality coming soon")

st.markdown("---")

# Create claim form
if st.session_state.get("show_create_claim", False):
    with st.expander("✨ Create New Claim", expanded=True):
        projects = get_projects_from_db()
        project_options = {p["id"]: p["name"] for p in projects}

        col1, col2 = st.columns(2)

        with col1:
            selected_project = st.selectbox(
                "Select Project*",
                options=list(project_options.keys()),
                format_func=lambda x: project_options[x],
            )

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
            if st.button("✅ Create Claim", type="primary", use_container_width=True):
                st.success("✅ Claim created successfully!")
                st.session_state.show_create_claim = False
                st.rerun()

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_create_claim = False
                st.rerun()

    st.markdown("---")

# Load approved transactions
df = load_analyzed_transactions()
if not df.empty and "Final_Decision" in df.columns:
    approved_df = df[df["Final_Decision"].str.contains("Add to Claim|Yes|Approved", na=False, case=False)]
else:
    approved_df = pd.DataFrame()

# Display draft claims
st.markdown("### 📋 Draft Claims")

# Mock claim data (in a real app, this would come from database)
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
    st.info("No draft claims yet. Create your first claim to get started!")
else:
    for claim in claims:
        status_class = {
            "Draft": "warning",
            "Ready to Submit": "success",
            "Submitted": "info",
            "Approved": "success",
            "Rejected": "danger",
        }.get(claim["status"], "neutral")

        st.markdown(
            """
        <div class="section-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="margin: 0; color: #1a202c;">📋 {claim['id']}</h3>
                    <p style="color: #718096; font-size: 0.875rem; margin-top: 0.25rem;">
                        {claim['project']} | {claim['jurisdiction']}
                    </p>
                    <p style="color: #4a5568; margin-top: 0.5rem; font-size: 0.875rem;">
                        <strong>Status:</strong> <span class="badge {status_class}">{claim['status']}</span> |
                        <strong>Created:</strong> {claim['created_date']} |
                        <strong>Transactions:</strong> {claim['transactions']}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2rem; font-weight: 700; color: #38a169;">
                        ${claim['total_refund']:,.2f}
                    </div>
                    <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase;">
                        Total Refund
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button(
                "👁️ View Details", key=f"view_{claim['id']}", use_container_width=True
            ):
                st.session_state.show_claim_detail = True
                st.session_state.current_claim = claim["id"]
                st.rerun()

        with col2:
            if st.button(
                "📊 Generate Report",
                key=f"report_{claim['id']}",
                use_container_width=True,
            ):
                st.info("Generating claim report...")

        with col3:
            if st.button(
                "📤 Submit",
                key=f"submit_{claim['id']}",
                use_container_width=True,
                disabled=claim["status"] != "Draft",
            ):
                st.success("Claim submitted successfully!")

        st.markdown("<br>", unsafe_allow_html=True)

# Claim detail view
if st.session_state.get("show_claim_detail", False):
    st.markdown("---")
    st.markdown("### 📋 Claim Details: CLAIM-WA-2024-001")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Summary", "📋 Transactions", "📄 Documentation", "📝 Notes"]
    )

    with tab1:
        st.markdown("#### Claim Summary")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(
                """
            <div class="section-card">
                <h4>WA Use Tax Review 2022-2024</h4>
                <p><strong>Claim ID:</strong> CLAIM-WA-2024-001</p>
                <p><strong>Jurisdiction:</strong> Washington State DOR</p>
                <p><strong>Period:</strong> 2022-01-01 to 2024-12-31</p>
                <p><strong>Status:</strong> <span class="badge warning">Draft</span></p>
                <p><strong>Filing Method:</strong> Electronic (Online Portal)</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.metric("Total Refund", "$184,230.00")
            st.metric("Transactions", "23")
            st.metric("Confidence", "96%")

    with tab2:
        st.markdown("#### Included Transactions")

        if not approved_df.empty:
            display_df = approved_df[
                [
                    "Vendor_Name",
                    "Invoice_Number",
                    "Line_Item_Description",
                    "Total_Amount",
                    "Tax_Amount",
                    "Estimated_Refund",
                    "AI_Confidence",
                ]
            ].copy()

            display_df["Total_Amount"] = display_df["Total_Amount"].apply(
                lambda x: f"${x:,.2f}"
            )
            display_df["Tax_Amount"] = display_df["Tax_Amount"].apply(
                lambda x: f"${x:,.2f}"
            )
            display_df["Estimated_Refund"] = display_df["Estimated_Refund"].apply(
                lambda x: f"${x:,.2f}"
            )
            display_df["AI_Confidence"] = display_df["AI_Confidence"].apply(
                lambda x: f"{x:.1f}%"
            )

            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No approved transactions to include in claim yet.")

    with tab3:
        st.markdown("#### Supporting Documentation")

        st.markdown(
            """
        <div class="section-card">
            <ul style="line-height: 2; color: #4a5568;">
                <li>📄 Invoice: INV-10021.pdf (Red Bison Tech Services)</li>
                <li>📄 Invoice: INV-10022.jpg (CloudOps Northwest)</li>
                <li>📄 Contract: SOW-DC-01.pdf</li>
                <li>📋 Analysis Summary Report</li>
                <li>📚 Legal Citations & References</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button("📎 Add Documentation", use_container_width=True):
            st.info("Documentation upload coming soon")

    with tab4:
        st.markdown("#### Claim Notes & History")

        notes = st.text_area(
            "Add Note", placeholder="Add notes about this claim...", height=100
        )

        if st.button("💾 Save Note", type="primary"):
            if notes:
                st.success("Note saved successfully!")

        st.markdown("#### Activity History")
        st.markdown(
            """
        <div class="section-card">
            <ul style="line-height: 2; color: #4a5568;">
                <li><strong>2024-11-14 10:30 AM:</strong> Claim created</li>
                <li><strong>2024-11-14 02:15 PM:</strong> Added 23 transactions</li>
                <li><strong>2024-11-14 04:45 PM:</strong> Generated analysis report</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Back button
    if st.button("🔙 Back to Claims List", use_container_width=False):
        st.session_state.show_claim_detail = False
        st.rerun()

# Footer
st.markdown("---")
st.caption("📋 Claims Management | TaxDesk Platform")
