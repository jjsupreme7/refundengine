"""
Review Queue Page - Review flagged transactions

Review and approve/reject transactions flagged for manual review.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.utils.data_loader import load_analyzed_transactions, get_review_queue
from core.html_utils import escape_html

# Page configuration
st.set_page_config(
    page_title="Review Queue - TaxDesk",
    page_icon="🔍",
    layout="wide"
)

# AUTHENTICATION
from core.auth import require_authentication
if not require_authentication():
    st.stop()

# Header
st.markdown('<div class="main-header">🔍 Review Queue</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Review transactions flagged for manual analysis</div>', unsafe_allow_html=True)

# Load data
df = load_analyzed_transactions()
review_df = get_review_queue(df, confidence_threshold=90.0)

# Summary stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total in Queue", len(review_df))
with col2:
    if not review_df.empty:
        total_refund = review_df['Estimated_Refund'].sum()
        st.metric("Potential Refund", f"${total_refund:,.2f}")
    else:
        st.metric("Potential Refund", "$0.00")
with col3:
    if not review_df.empty:
        avg_conf = review_df['AI_Confidence'].mean()
        st.metric("Avg Confidence", f"{avg_conf:.1f}%")
    else:
        st.metric("Avg Confidence", "N/A")
with col4:
    unique_vendors = review_df['Vendor_Name'].nunique() if not review_df.empty else 0
    st.metric("Unique Vendors", unique_vendors)

st.markdown("---")

# Filters
st.markdown("### 🔍 Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    confidence_range = st.slider(
        "Confidence Range",
        0.0, 100.0, (0.0, 90.0),
        help="Filter by AI confidence score"
    )

with col2:
    if not review_df.empty:
        vendor_options = ["All"] + sorted(review_df['Vendor_Name'].unique().tolist())
    else:
        vendor_options = ["All"]
    filter_vendor = st.selectbox("Vendor", vendor_options)

with col3:
    if not review_df.empty:
        category_options = ["All"] + sorted(review_df['Tax_Category'].unique().tolist())
    else:
        category_options = ["All"]
    filter_category = st.selectbox("Category", category_options)

with col4:
    st.write("")  # Spacing
    if st.button("🗑️ Clear Filters", use_container_width=True):
        st.rerun()

# Apply filters
filtered_df = review_df.copy()
if not filtered_df.empty:
    filtered_df = filtered_df[
        (filtered_df['AI_Confidence'] >= confidence_range[0]) &
        (filtered_df['AI_Confidence'] <= confidence_range[1])
    ]

    if filter_vendor != "All":
        filtered_df = filtered_df[filtered_df['Vendor_Name'] == filter_vendor]

    if filter_category != "All":
        filtered_df = filtered_df[filtered_df['Tax_Category'] == filter_category]

st.markdown("---")

# Review queue display
st.markdown(f"### 📋 Flagged Transactions ({len(filtered_df)})")

if filtered_df.empty:
    st.success("🎉 No transactions in review queue! All items meet confidence threshold.")
else:
    # Bulk actions
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("✅ Approve All Visible", use_container_width=True):
            st.success(f"Approved {len(filtered_df)} transactions")

    with col2:
        if st.button("❌ Reject All Visible", use_container_width=True):
            st.warning(f"Rejected {len(filtered_df)} transactions")

    with col3:
        if st.button("📥 Export to Excel", use_container_width=True):
            st.info("Export functionality coming soon")

    st.markdown("<br>", unsafe_allow_html=True)

    # Display each transaction for review
    for idx, row in filtered_df.iterrows():
        # Determine confidence badge
        confidence = row['AI_Confidence']
        if confidence >= 85:
            conf_class = "warning"
        elif confidence >= 70:
            conf_class = "warning"
        else:
            conf_class = "danger"

        # Determine decision badge
        decision = row['Final_Decision']
        if 'Add to Claim' in decision:
            decision_class = "success"
        elif 'Review' in decision:
            decision_class = "warning"
        else:
            decision_class = "neutral"

        with st.expander(f"🔍 {row['Vendor_Name']} - ${row['Total_Amount']:,.2f} | {row['Line_Item_Description'][:80]}...", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### 📄 Transaction Details")
                st.markdown(f"**Vendor:** {row['Vendor_Name']}")
                st.markdown(f"**Invoice:** {row['Invoice_Number']}")
                if pd.notna(row.get('Purchase_Order_Number')):
                    st.markdown(f"**PO Number:** {row['Purchase_Order_Number']}")
                st.markdown(f"**Description:** {row['Line_Item_Description']}")
                st.markdown(f"**Amount:** ${row['Total_Amount']:,.2f}")
                st.markdown(f"**Tax Paid:** ${row['Tax_Amount']:,.2f}")
                st.markdown(f"**Tax Rate:** {row.get('Tax_Rate_Charged', 'N/A')}")
                st.markdown(f"**Category:** {row['Tax_Category']}")

                st.markdown("#### 🤖 AI Analysis")
                st.markdown(f"**Decision:** <span class='badge {decision_class}'>{escape_html(decision)}</span>", unsafe_allow_html=True)
                st.markdown(f"**Confidence:** <span class='badge {conf_class}'>{escape_html(str(confidence)):.1f}%</span>", unsafe_allow_html=True)
                st.markdown(f"**Est. Refund:** ${row['Estimated_Refund']:,.2f}")
                st.markdown(f"**Refund Basis:** {row.get('Refund_Basis', 'N/A')}")

                # Analysis Notes
                if pd.notna(row.get('Analysis_Notes')):
                    st.markdown("**📝 Analysis Notes:**")
                    st.info(row['Analysis_Notes'])

                # Legal Citation
                if pd.notna(row.get('Legal_Citation')):
                    st.markdown("**📚 Legal Citation:**")
                    st.success(f"**{row['Legal_Citation']}**")

                # Additional Info
                if pd.notna(row.get('Additional_Info')):
                    st.markdown("**ℹ️ Additional Context:**")
                    st.warning(row['Additional_Info'])

            with col2:
                st.markdown("#### ✅ Your Decision")

                analyst_decision = st.radio(
                    "Decision",
                    ["Pending Review", "Approve (Add to Claim)", "Reject (Not Refundable)", "Need More Info"],
                    key=f"decision_{idx}"
                )

                adjusted_refund = st.number_input(
                    "Adjusted Refund Amount",
                    min_value=0.0,
                    value=float(row['Estimated_Refund']),
                    step=0.01,
                    key=f"refund_{idx}"
                )

                analyst_notes = st.text_area(
                    "Analyst Notes",
                    placeholder="Add any notes about this transaction...",
                    key=f"notes_{idx}",
                    height=100
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Save", key=f"save_{idx}", use_container_width=True, type="primary"):
                        st.success(f"Saved decision for {row['Vendor_Name']}")

                with col_b:
                    if st.button("⏭️ Skip", key=f"skip_{idx}", use_container_width=True):
                        st.info("Skipped to next item")

            st.markdown("---")

            # Additional context (if available)
            st.markdown("#### 📚 Related Legal Context")

            if pd.notna(row.get('Legal_Citation')):
                st.markdown(f"""
                <div class="section-card">
                    <h4>Primary Citation: {row['Legal_Citation']}</h4>
                    <p style="color: #4a5568; margin-top: 0.5rem;">
                        This transaction's tax treatment is primarily governed by <strong>{row['Legal_Citation']}</strong>.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                col_legal1, col_legal2 = st.columns(2)
                with col_legal1:
                    if st.button("📖 View Full Text", key=f"view_law_{idx}", use_container_width=True):
                        st.info(f"View full text of {row['Legal_Citation']} (feature coming soon)")

                with col_legal2:
                    if st.button("🔍 Search Related Rules", key=f"search_law_{idx}", use_container_width=True):
                        st.info("Search RAG system for related rules (feature coming soon)")
            else:
                st.info("No specific legal citation provided. Consider researching applicable tax law for this transaction type.")

# Footer
st.markdown("---")
st.caption("🔍 Review Queue | TaxDesk Platform")
