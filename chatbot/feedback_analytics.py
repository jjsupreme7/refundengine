#!/usr/bin/env python3
"""
Feedback Analytics Dashboard

Visualize and analyze user feedback to understand:
- What users are asking
- Quality of responses
- Learning progress
- System improvements over time

Usage:
    streamlit run chatbot/feedback_analytics.py --server.port 8504
"""

from core.database import get_supabase_client
from dotenv import load_dotenv
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment

load_dotenv(Path(__file__).parent.parent / ".env")


# Page config
st.set_page_config(page_title="Feedback Analytics", page_icon="📊", layout="wide")

# Initialize
supabase = get_supabase_client()


def get_feedback_data(days: int = 30):
    """Get all feedback from the last N days"""
    cutoff = datetime.now() - timedelta(days=days)

    result = (
        supabase.table("user_feedback")
        .select("*")
        .gte("created_at", cutoff.isoformat())
        .order("created_at", desc=True)
        .execute()
    )

    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def get_improvements_data():
    """Get all learned improvements"""
    result = (
        supabase.table("learned_improvements")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def get_golden_data():
    """Get golden Q&A pairs"""
    result = (
        supabase.table("golden_qa_pairs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def get_citation_preferences():
    """Get citation preferences"""
    result = (
        supabase.table("citation_preferences")
        .select("*")
        .order("preference_score", desc=True)
        .limit(20)
        .execute()
    )

    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def main():
    st.title("📊 Feedback & Learning Analytics")
    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        days = st.slider("Days of data", 7, 90, 30)
        st.markdown("---")

        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Get data
    feedback_df = get_feedback_data(days)
    improvements_df = get_improvements_data()
    golden_df = get_golden_data()
    citation_prefs_df = get_citation_preferences()

    # Summary metrics
    st.header("📈 Summary Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_feedback = len(feedback_df)
        st.metric("Total Feedback", total_feedback)

    with col2:
        if not feedback_df.empty and "rating" in feedback_df.columns:
            avg_rating = feedback_df["rating"].mean()
            st.metric("Avg Rating", f"{avg_rating:.2f} ⭐")
        else:
            st.metric("Avg Rating", "N/A")

    with col3:
        total_improvements = len(improvements_df)
        active_improvements = (
            len(improvements_df[improvements_df["is_active"] == True])
            if not improvements_df.empty
            else 0
        )
        st.metric("Active Improvements", f"{active_improvements}/{total_improvements}")

    with col4:
        total_golden = len(golden_df)
        verified_golden = (
            len(golden_df[golden_df["is_verified"] == True])
            if not golden_df.empty
            else 0
        )
        st.metric("Golden Q&A Pairs", f"{verified_golden}/{total_golden}")

    st.markdown("---")

    # Feedback over time
    st.header("📅 Feedback Over Time")

    if not feedback_df.empty and "created_at" in feedback_df.columns:
        feedback_df["created_at"] = pd.to_datetime(feedback_df["created_at"])
        feedback_df["date"] = feedback_df["created_at"].dt.date

        feedback_by_date = (
            feedback_df.groupby(["date", "feedback_type"])
            .size()
            .reset_index(name="count")
        )

        fig = px.bar(
            feedback_by_date,
            x="date",
            y="count",
            color="feedback_type",
            title="Feedback Volume by Type",
            labels={"count": "Number of Feedback", "date": "Date"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No feedback data available yet")

    st.markdown("---")

    # Feedback distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Feedback Type Distribution")
        if not feedback_df.empty and "feedback_type" in feedback_df.columns:
            feedback_type_counts = feedback_df["feedback_type"].value_counts()

            fig = px.pie(
                values=feedback_type_counts.values,
                names=feedback_type_counts.index,
                title="Feedback Types",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No feedback data")

    with col2:
        st.subheader("Rating Distribution")
        if not feedback_df.empty and "rating" in feedback_df.columns:
            rating_counts = feedback_df["rating"].value_counts().sort_index()

            fig = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                labels={"x": "Rating", "y": "Count"},
                title="Ratings Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rating data")

    st.markdown("---")

    # Learned Improvements
    st.header("🧠 Learned Improvements")

    if not improvements_df.empty:
        st.subheader(f"{len(improvements_df)} Total Improvements")

        # Filter active
        active_improvements_df = improvements_df[improvements_df["is_active"] == True]

        if not active_improvements_df.empty:
            # Show improvement types
            improvement_type_counts = active_improvements_df[
                "improvement_type"
            ].value_counts()

            fig = px.bar(
                x=improvement_type_counts.index,
                y=improvement_type_counts.values,
                labels={"x": "Improvement Type", "y": "Count"},
                title="Active Improvements by Type",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Top performing improvements
            st.subheader("🏆 Top Performing Improvements")

            top_improvements = active_improvements_df.nlargest(10, "validation_rate")[
                [
                    "improvement_type",
                    "confidence",
                    "times_applied",
                    "times_validated",
                    "validation_rate",
                ]
            ]

            st.dataframe(
                top_improvements.style.format(
                    {"confidence": "{:.1%}", "validation_rate": "{:.1%}"}
                ),
                use_container_width=True,
            )
        else:
            st.info("No active improvements yet")
    else:
        st.info("No improvements learned yet. Collect more feedback!")

    st.markdown("---")

    # Citation Preferences
    st.header("📚 Citation Preferences")

    if not citation_prefs_df.empty:
        st.subheader("Top 20 Preferred Citations")

        # Show top citations
        top_citations = citation_prefs_df.nlargest(20, "preference_score")[
            [
                "citation",
                "preference_score",
                "times_suggested_by_user",
                "times_retrieved_and_liked",
                "times_retrieved_and_disliked",
            ]
        ]

        st.dataframe(
            top_citations.style.format({"preference_score": "{:.2f}"}),
            use_container_width=True,
        )

        # Visualization
        fig = px.bar(
            top_citations.head(10),
            x="citation",
            y="preference_score",
            title="Top 10 Citations by Preference Score",
            labels={"preference_score": "Preference Score", "citation": "Citation"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No citation preferences learned yet")

    st.markdown("---")

    # Golden Q&A Dataset
    st.header("⭐ Golden Q&A Dataset")

    if not golden_df.empty:
        st.subheader(f"{len(golden_df)} Golden Q&A Pairs")

        # Show by category
        if "query_category" in golden_df.columns:
            category_counts = golden_df["query_category"].value_counts()

            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Golden Pairs by Category",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Show verified vs unverified
        verified_count = len(golden_df[golden_df["is_verified"] == True])
        unverified_count = len(golden_df[golden_df["is_verified"] == False])

        fig = go.Figure(
            data=[
                go.Bar(name="Verified", x=["Golden Q&A"], y=[verified_count]),
                go.Bar(name="Unverified", x=["Golden Q&A"], y=[unverified_count]),
            ]
        )
        fig.update_layout(title="Verification Status", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

        # Show recent golden pairs
        st.subheader("Recent Golden Q&A Pairs")
        if "created_at" in golden_df.columns:
            recent_golden = golden_df.nlargest(10, "created_at")[
                [
                    "question",
                    "query_category",
                    "difficulty",
                    "is_verified",
                    "created_at",
                ]
            ]
            st.dataframe(recent_golden, use_container_width=True)
    else:
        st.info(
            "No golden Q&A pairs yet. High-rated responses will be added automatically!"
        )

    st.markdown("---")

    # Recent Feedback Details
    st.header("💬 Recent Feedback Details")

    if not feedback_df.empty:
        # Show detailed feedback
        detailed_feedback = feedback_df[
            feedback_df["feedback_comment"].notna()
            | feedback_df["suggested_answer"].notna()
        ].nlargest(10, "created_at")

        if not detailed_feedback.empty:
            for idx, row in detailed_feedback.iterrows():
                with st.expander(
                    f"{row['feedback_type']} - {row['created_at']
                                                } - Rating: {row.get('rating', 'N/A')}"
                ):
                    st.write(f"**Query:** {row['query']}")

                    if pd.notna(row.get("suggested_answer")):
                        st.write("**Suggested Answer:**")
                        st.write(row["suggested_answer"])

                    if pd.notna(row.get("suggested_structure")):
                        st.write("**Suggested Structure:**")
                        st.write(row["suggested_structure"])

                    if pd.notna(row.get("feedback_comment")):
                        st.write("**Comment:**")
                        st.write(row["feedback_comment"])
        else:
            st.info("No detailed feedback available")
    else:
        st.info("No feedback data available")


if __name__ == "__main__":
    main()
