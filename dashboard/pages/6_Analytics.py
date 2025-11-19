#!/usr/bin/env python3
"""
Analytics Dashboard - Performance & Insights

Shows key metrics and visualizations for:
- Analysis performance and volume
- AI accuracy and learning progress
- Refund opportunities by category/vendor
- System learning and improvement over time
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize Supabase
supabase = get_supabase_client()

# Page config
st.set_page_config(page_title="Analytics - TaxDesk", page_icon="📊", layout="wide")

# AUTHENTICATION
from core.auth import require_authentication

if not require_authentication():
    st.stop()

st.markdown(
    '<div class="main-header">📊 Analytics & Insights</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="main-subtitle">Performance metrics, AI accuracy, and refund analysis</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_analysis_overview():
    """Get high-level analysis statistics"""
    try:
        # Total items analyzed
        total_result = (
            supabase.table("analysis_results").select("id", count="exact").execute()
        )
        total_analyzed = total_result.count if hasattr(total_result, "count") else 0

        # Total estimated refund
        refund_result = (
            supabase.table("analysis_results").select("ai_estimated_refund").execute()
        )
        total_refund = (
            sum([r.get("ai_estimated_refund", 0) or 0 for r in refund_result.data])
            if refund_result.data
            else 0
        )

        # Items pending review
        pending_result = (
            supabase.table("analysis_results")
            .select("id", count="exact")
            .eq("analysis_status", "pending_review")
            .execute()
        )
        pending_count = pending_result.count if hasattr(pending_result, "count") else 0

        return {
            "total_analyzed": total_analyzed,
            "total_refund": total_refund,
            "pending_review": pending_count,
        }
    except Exception as e:
        st.error(f"Error fetching overview: {e}")
        return {"total_analyzed": 0, "total_refund": 0, "pending_review": 0}


@st.cache_data(ttl=300)
def get_ai_performance():
    """Get AI performance metrics"""
    try:
        # Get all analysis results with confidence scores
        results = supabase.table("analysis_results").select("ai_confidence").execute()

        if not results.data:
            return None

        df = pd.DataFrame(results.data)
        df["ai_confidence"] = pd.to_numeric(df["ai_confidence"], errors="coerce")

        return df
    except Exception as e:
        st.error(f"Error fetching AI performance: {e}")
        return None


@st.cache_data(ttl=300)
def get_correction_stats():
    """Get correction statistics"""
    try:
        # Get all reviews with fields corrected
        reviews = (
            supabase.table("analysis_reviews")
            .select("fields_corrected, review_status")
            .execute()
        )

        if not reviews.data:
            return None

        # Flatten the fields_corrected arrays
        all_fields = []
        for review in reviews.data:
            if review.get("fields_corrected"):
                all_fields.extend(review["fields_corrected"])

        if not all_fields:
            return None

        # Count occurrences
        field_counts = pd.Series(all_fields).value_counts().head(10)

        return field_counts
    except Exception as e:
        st.error(f"Error fetching corrections: {e}")
        return None


@st.cache_data(ttl=300)
def get_refund_breakdown():
    """Get refund breakdown by exemption type"""
    try:
        results = (
            supabase.table("analysis_results")
            .select("ai_exemption_type, ai_estimated_refund")
            .execute()
        )

        if not results.data:
            return None

        df = pd.DataFrame(results.data)
        df["ai_estimated_refund"] = pd.to_numeric(
            df["ai_estimated_refund"], errors="coerce"
        ).fillna(0)

        # Group by exemption type
        breakdown = (
            df.groupby("ai_exemption_type")["ai_estimated_refund"]
            .sum()
            .sort_values(ascending=False)
        )

        return breakdown
    except Exception as e:
        st.error(f"Error fetching refund breakdown: {e}")
        return None


@st.cache_data(ttl=300)
def get_vendor_opportunities():
    """Get top vendors by refund opportunity"""
    try:
        results = (
            supabase.table("analysis_results")
            .select("vendor_name, ai_estimated_refund")
            .execute()
        )

        if not results.data:
            return None

        df = pd.DataFrame(results.data)
        df["ai_estimated_refund"] = pd.to_numeric(
            df["ai_estimated_refund"], errors="coerce"
        ).fillna(0)

        # Group by vendor and sum refunds
        vendor_totals = (
            df.groupby("vendor_name")["ai_estimated_refund"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        return vendor_totals
    except Exception as e:
        st.error(f"Error fetching vendor opportunities: {e}")
        return None


@st.cache_data(ttl=300)
def get_learning_progress():
    """Get learning system metrics"""
    try:
        # Vendor patterns learned
        patterns_result = (
            supabase.table("vendor_product_patterns")
            .select("id", count="exact")
            .execute()
        )
        patterns_count = (
            patterns_result.count if hasattr(patterns_result, "count") else 0
        )

        # Product types cataloged
        products_result = (
            supabase.table("vendor_products").select("id", count="exact").execute()
        )
        products_count = (
            products_result.count if hasattr(products_result, "count") else 0
        )

        return {"patterns": patterns_count, "products": products_count}
    except Exception as e:
        st.error(f"Error fetching learning progress: {e}")
        return {"patterns": 0, "products": 0}


# ============================================================================
# SECTION 1: ANALYSIS OVERVIEW
# ============================================================================

st.markdown("### 📈 Analysis Overview")

overview = get_analysis_overview()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Items Analyzed",
        value=f"{overview['total_analyzed']:,}",
        help="Total number of invoice line items processed by AI",
    )

with col2:
    st.metric(
        label="Total Estimated Refund",
        value=f"${overview['total_refund']:,.2f}",
        help="Sum of all identified refund opportunities",
    )

with col3:
    st.metric(
        label="Items Pending Review",
        value=f"{overview['pending_review']:,}",
        help="Items awaiting human review",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 2: AI PERFORMANCE
# ============================================================================

st.markdown("### 🤖 AI Performance")

ai_perf = get_ai_performance()

if ai_perf is not None and len(ai_perf) > 0:
    col1, col2 = st.columns([2, 1])

    with col1:
        # Confidence distribution histogram
        fig_conf = px.histogram(
            ai_perf,
            x="ai_confidence",
            nbins=20,
            title="AI Confidence Distribution",
            labels={
                "ai_confidence": "Confidence Score (%)",
                "count": "Number of Items",
            },
            color_discrete_sequence=["#3182ce"],
        )
        fig_conf.update_layout(height=300, showlegend=False, xaxis_range=[0, 100])
        st.plotly_chart(fig_conf, use_container_width=True)

    with col2:
        # Summary statistics
        avg_confidence = ai_perf["ai_confidence"].mean()
        median_confidence = ai_perf["ai_confidence"].median()
        low_conf_pct = (ai_perf["ai_confidence"] < 70).sum() / len(ai_perf) * 100

        st.markdown("#### Key Metrics")
        st.metric("Average Confidence", f"{avg_confidence:.1f}%")
        st.metric("Median Confidence", f"{median_confidence:.1f}%")
        st.metric(
            "Low Confidence Items",
            f"{low_conf_pct:.1f}%",
            help="Items below 70% confidence",
        )

    # Most corrected fields
    corrections = get_correction_stats()

    if corrections is not None and len(corrections) > 0:
        st.markdown("#### Most Corrected Fields")
        st.markdown(
            "*These fields are most often corrected by reviewers - areas where AI needs improvement*"
        )

        fig_corrections = px.bar(
            x=corrections.values,
            y=corrections.index,
            orientation="h",
            labels={"x": "Number of Corrections", "y": "Field Name"},
            color_discrete_sequence=["#e53e3e"],
        )
        fig_corrections.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_corrections, use_container_width=True)
else:
    st.info(
        "📊 No analysis data available yet. Run invoice analysis to see AI performance metrics."
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: REFUND BREAKDOWN
# ============================================================================

st.markdown("### 💰 Refund Opportunity Breakdown")

refund_breakdown = get_refund_breakdown()
vendor_opps = get_vendor_opportunities()

if refund_breakdown is not None and len(refund_breakdown) > 0:
    col1, col2 = st.columns(2)

    with col1:
        # Pie chart by exemption type
        fig_pie = px.pie(
            values=refund_breakdown.values,
            names=refund_breakdown.index,
            title="Refunds by Exemption Type",
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Table with dollar amounts
        st.markdown("#### Exemption Type Details")
        breakdown_df = pd.DataFrame(
            {
                "Exemption Type": refund_breakdown.index,
                "Total Refund": refund_breakdown.values,
            }
        )
        breakdown_df["Total Refund"] = breakdown_df["Total Refund"].apply(
            lambda x: f"${x:,.2f}"
        )
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
else:
    st.info("📊 No refund data available yet.")

if vendor_opps is not None and len(vendor_opps) > 0:
    st.markdown("#### Top 10 Vendors by Refund Opportunity")

    fig_vendors = px.bar(
        x=vendor_opps.values,
        y=vendor_opps.index,
        orientation="h",
        labels={"x": "Estimated Refund ($)", "y": "Vendor"},
        color=vendor_opps.values,
        color_continuous_scale="Blues",
    )
    fig_vendors.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_vendors, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 4: LEARNING PROGRESS
# ============================================================================

st.markdown("### 🧠 System Learning Progress")

learning = get_learning_progress()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Vendor Patterns Learned",
        value=f"{learning['patterns']:,}",
        help="Number of vendor product patterns learned from corrections",
    )

with col2:
    st.metric(
        label="Product Types Cataloged",
        value=f"{learning['products']:,}",
        help="Unique vendor products identified and categorized",
    )

st.info(
    """
**How Learning Works:**
When you review and correct AI analysis, the system automatically learns from your corrections.
These patterns are used to improve future analysis accuracy for similar products from the same vendors.
"""
)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    f"🔄 Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data cached for 5 minutes"
)
st.caption("📊 Analytics powered by Supabase + Streamlit")
