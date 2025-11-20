"""
Agent Proposal Dashboard

Streamlit dashboard for reviewing and approving agent proposals.

Run with: streamlit run agents/streamlit_dashboard.py
Access at: http://localhost:8501
"""

from agents.core.usage_tracker import UsageTracker
from agents.core.approval_queue import ApprovalQueue, Proposal
import streamlit as st
from datetime import datetime
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Page configuration
st.set_page_config(
    page_title="Refund Engine - Agent Proposals", page_icon="🤖", layout="wide"
)


def main():
    """Main dashboard"""

    # Initialize
    queue = ApprovalQueue()
    tracker = UsageTracker()

    # Header
    st.title("🤖 Refund Engine Agent Dashboard")
    st.markdown("Review and approve proposals from autonomous agent teams")

    # Sidebar - Usage Stats
    with st.sidebar:
        st.header("📊 Usage Statistics")

        weekly = tracker.get_weekly_usage()
        daily = tracker.check_daily_pace()

        st.metric(
            "Weekly Usage",
            f"{weekly['usage_percent']:.1f}%",
            delta=f"Target: {weekly['target_percent']}%",
        )

        st.metric(
            "Messages This Week",
            f"{weekly['total_messages']:,}",
            delta=f"{weekly['messages_remaining']:,} to target",
        )

        st.metric(
            "Messages Today",
            f"{daily['messages_today']:,}",
            delta=f"{daily['messages_needed']:,} needed",
        )

        # Status indicator
        if weekly["on_pace"]:
            st.success("✅ On pace to meet weekly target")
        else:
            st.warning("⚠️ Below weekly target")

        st.markdown("---")
        st.caption("Week resets Tuesday")
        st.caption(f"Days remaining: {weekly['days_remaining']}")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Pending Proposals", "✅ Approved", "❌ Rejected", "📊 Analytics"]
    )

    # Tab 1: Pending Proposals
    with tab1:
        show_pending_proposals(queue)

    # Tab 2: Approved Proposals
    with tab2:
        show_approved_proposals(queue)

    # Tab 3: Rejected Proposals
    with tab3:
        show_rejected_proposals(queue)

    # Tab 4: Analytics
    with tab4:
        show_analytics(queue, tracker)


def show_pending_proposals(queue: ApprovalQueue):
    """Show pending proposals for review"""

    st.header("📋 Pending Proposals")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        priority_filter = st.multiselect(
            "Priority", ["high", "medium", "low"], default=["high", "medium", "low"]
        )

    with col2:
        team_filter = st.multiselect(
            "Team",
            ["code_quality_council", "knowledge_curation", "pattern_learning"],
            default=["code_quality_council", "knowledge_curation", "pattern_learning"],
        )

    with col3:
        sort_by = st.selectbox(
            "Sort By",
            ["Priority (High→Low)", "Date (Newest→Oldest)", "Date (Oldest→Newest)"],
        )

    # Get pending proposals
    proposals = queue.get_proposals(
        status="pending",
        priority=priority_filter if priority_filter else None,
        team=team_filter if team_filter else None,
    )

    if not proposals:
        st.info("🎉 No pending proposals! Your agents are waiting for more data.")
        return

    st.markdown(f"**{len(proposals)} pending proposals**")

    # Display each proposal
    for proposal in proposals:
        show_proposal_card(proposal, queue)


def show_proposal_card(proposal: Proposal, queue: ApprovalQueue):
    """Display a single proposal card with action buttons"""

    # Priority emoji
    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
        proposal.priority, "⚪"
    )

    # Team emoji
    team_emoji = {
        "code_quality_council": "🏛️",
        "knowledge_curation": "📚",
        "pattern_learning": "🧠",
    }.get(proposal.team, "🤖")

    with st.expander(
        f"{priority_emoji} {team_emoji} **{proposal.title}**",
        expanded=(proposal.priority == "high"),
    ):
        # Metadata row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.caption("**Team**")
            st.write(proposal.team.replace("_", " ").title())

        with col2:
            st.caption("**Agent**")
            st.write(proposal.agent.title())

        with col3:
            st.caption("**Priority**")
            st.write(proposal.priority.upper())

        with col4:
            st.caption("**Created**")
            created = datetime.fromisoformat(proposal.created_at)
            st.write(created.strftime("%b %d, %I:%M %p"))

        st.markdown("---")

        # Description
        st.markdown("**Description**")
        st.write(proposal.description)

        # Impact
        st.markdown("**Impact**")
        st.info(proposal.impact)

        # Metadata
        if proposal.metadata:
            st.markdown("**Additional Details**")
            st.json(proposal.metadata)

        st.markdown("---")

        # Action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button("✅ Approve", key=f"approve_{proposal.id}"):
                notes = st.text_input(
                    "Approval notes (optional)", key=f"notes_{proposal.id}"
                )
                if queue.approve(proposal.id, notes):
                    st.success("Proposal approved!")
                    st.rerun()

        with col2:
            if st.button("❌ Reject", key=f"reject_{proposal.id}"):
                reason = st.text_area(
                    "Rejection reason (required)",
                    key=f"reason_{proposal.id}",
                    placeholder="Explain why this proposal is rejected...",
                )
                if reason and queue.reject(proposal.id, reason):
                    st.success("Proposal rejected with feedback")
                    st.rerun()
                elif not reason:
                    st.warning("Please provide a rejection reason")

        with col3:
            if st.button("⏸️ Defer", key=f"defer_{proposal.id}"):
                defer_notes = st.text_input(
                    "Defer notes (optional)", key=f"defer_{proposal.id}"
                )
                if queue.defer(proposal.id, defer_notes):
                    st.success("Proposal deferred")
                    st.rerun()


def show_approved_proposals(queue: ApprovalQueue):
    """Show approved proposals"""

    st.header("✅ Approved Proposals")

    proposals = queue.get_proposals(status="approved")

    if not proposals:
        st.info("No approved proposals yet")
        return

    st.markdown(f"**{len(proposals)} approved proposals**")

    for proposal in proposals:
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            proposal.priority, "⚪"
        )

        team_emoji = {
            "code_quality_council": "🏛️",
            "knowledge_curation": "📚",
            "pattern_learning": "🧠",
        }.get(proposal.team, "🤖")

        with st.expander(f"{priority_emoji} {team_emoji} **{proposal.title}**"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.caption("**Team**")
                st.write(proposal.team.replace("_", " ").title())

            with col2:
                st.caption("**Approved**")
                approved = proposal.metadata.get("approved_at", "Unknown")
                if approved != "Unknown":
                    approved_dt = datetime.fromisoformat(approved)
                    st.write(approved_dt.strftime("%b %d, %I:%M %p"))
                else:
                    st.write("Unknown")

            with col3:
                st.caption("**Priority**")
                st.write(proposal.priority.upper())

            st.markdown("**Description**")
            st.write(proposal.description)

            st.markdown("**Impact**")
            st.success(proposal.impact)


def show_rejected_proposals(queue: ApprovalQueue):
    """Show rejected proposals"""

    st.header("❌ Rejected Proposals")

    proposals = queue.get_proposals(status="rejected")

    if not proposals:
        st.info("No rejected proposals")
        return

    st.markdown(f"**{len(proposals)} rejected proposals**")

    for proposal in proposals:
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            proposal.priority, "⚪"
        )

        team_emoji = {
            "code_quality_council": "🏛️",
            "knowledge_curation": "📚",
            "pattern_learning": "🧠",
        }.get(proposal.team, "🤖")

        with st.expander(f"{priority_emoji} {team_emoji} **{proposal.title}**"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.caption("**Team**")
                st.write(proposal.team.replace("_", " ").title())

            with col2:
                st.caption("**Rejected**")
                rejected = proposal.metadata.get("rejected_at", "Unknown")
                if rejected != "Unknown":
                    rejected_dt = datetime.fromisoformat(rejected)
                    st.write(rejected_dt.strftime("%b %d, %I:%M %p"))
                else:
                    st.write("Unknown")

            with col3:
                st.caption("**Priority**")
                st.write(proposal.priority.upper())

            st.markdown("**Description**")
            st.write(proposal.description)

            # Rejection reason
            rejection_reason = proposal.metadata.get(
                "rejected_notes", "No reason provided"
            )
            st.markdown("**Rejection Reason**")
            st.error(rejection_reason)


def show_analytics(queue: ApprovalQueue, tracker: UsageTracker):
    """Show analytics and insights"""

    st.header("📊 Analytics & Insights")

    # Proposal statistics
    st.subheader("Proposal Statistics")

    col1, col2, col3, col4 = st.columns(4)

    pending = len(queue.get_proposals(status="pending"))
    approved = len(queue.get_proposals(status="approved"))
    rejected = len(queue.get_proposals(status="rejected"))
    deferred = len(queue.get_proposals(status="deferred"))

    with col1:
        st.metric("Pending", pending)

    with col2:
        st.metric("Approved", approved)

    with col3:
        st.metric("Rejected", rejected)

    with col4:
        st.metric("Deferred", deferred)

    # Approval rate
    total = approved + rejected
    if total > 0:
        approval_rate = (approved / total) * 100
        st.metric("Approval Rate", f"{approval_rate:.1f}%")

    st.markdown("---")

    # Usage breakdown
    st.subheader("Usage Breakdown")

    weekly = tracker.get_weekly_usage()

    if weekly["daily_breakdown"]:
        st.markdown("**Messages per Day (This Week)**")

        for day_data in weekly["daily_breakdown"]:
            date = day_data["date"]
            messages = day_data["messages"]

            if messages > 0:
                st.text(f"{date}: {messages:,} messages")

                # Team breakdown
                if day_data.get("by_team"):
                    for team, stats in day_data["by_team"].items():
                        st.caption(f"  - {team}: {stats['messages']} messages")

    st.markdown("---")

    # Recommendations
    st.subheader("💡 Recommendations")

    pace = tracker.check_daily_pace()

    if not pace["on_pace"]:
        st.warning(
            """
**Usage Below Target**

You're at {pace['pace_percent']:.1f}% of today's target. Consider:
- Increasing agent frequency
- Enabling more agent teams
- Reviewing agent schedules
        """
        )

    if weekly["usage_percent"] > 90:
        st.success(
            """
**Excellent Usage!**

You're on track to maximize your Claude Max subscription. Keep it up!
        """
        )


if __name__ == "__main__":
    main()
