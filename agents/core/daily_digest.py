"""
Daily Digest Email

Sends daily summary email at 8am with overnight agent activity.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from .approval_queue import ApprovalQueue
from .communication import post_to_discord
from .usage_tracker import UsageTracker


class DailyDigest:
    """
    Generates and sends daily digest.

    Sent at 8:00 AM (when agents finish their 1am-8am shift).
    """

    def __init__(self, workspace_path: str = "agents/workspace"):
        self.workspace = Path(workspace_path)
        self.queue = ApprovalQueue(workspace_path)
        self.tracker = UsageTracker(workspace_path)

        # Email configuration
        self.recipient = os.getenv("USER_EMAIL", "jjgcallen11@gmail.com")

    def generate_digest(self) -> str:
        """
        Generate digest summary.

        Returns:
            Formatted digest string
        """
        # Get statistics
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()

        daily_usage = self.tracker.get_daily_usage(yesterday)
        weekly_usage = self.tracker.get_weekly_usage()

        # Get proposals
        high_priority = self.queue.get_proposals(status="pending", priority=["high"])
        medium_priority = self.queue.get_proposals(
            status="pending", priority=["medium"]
        )
        low_priority = self.queue.get_proposals(status="pending", priority=["low"])

        approved_today = self.queue.count_approved_today()

        # Build summary
        summary = """
📧 REFUND ENGINE DAILY DIGEST
{datetime.now().strftime('%A, %B %d, %Y')}

═══════════════════════════════════════

📊 USAGE STATISTICS

Weekly Usage: {weekly_usage['usage_percent']:.1f}% of {weekly_usage['weekly_limit']:,} messages
Target: {weekly_usage['target_percent']}%
Status: {"✅ ON PACE" if weekly_usage['on_pace'] else "⚠️ BELOW TARGET"}

This Week: {weekly_usage['total_messages']:,} messages
Yesterday: {daily_usage['messages']:,} messages
Days Until Reset: {weekly_usage['days_remaining']}

═══════════════════════════════════════

📋 PROPOSALS AWAITING REVIEW

🔴 High Priority: {len(high_priority)}
🟡 Medium Priority: {len(medium_priority)}
🟢 Low Priority: {len(low_priority)}

TOP HIGH PRIORITY PROPOSALS:
"""

        # Add top 5 high priority proposals
        for i, proposal in enumerate(high_priority[:5], 1):
            team_emoji = {
                "code_quality_council": "🏛️",
                "knowledge_curation": "📚",
                "pattern_learning": "🧠",
            }.get(proposal.team, "🤖")

            summary += """
{i}. {team_emoji} {proposal.title}
   Team: {proposal.team.replace('_', ' ').title()}
   Impact: {proposal.impact[:100]}{'...' if len(proposal.impact) > 100 else ''}
   Created: {datetime.fromisoformat(proposal.created_at).strftime('%b %d, %I:%M %p')}
"""

        if not high_priority:
            summary += "\n   No high priority proposals\n"

        summary += """
═══════════════════════════════════════

✅ APPROVED TODAY: {approved_today} proposals

🎯 TODAY'S RECOMMENDATIONS:

• Review {len(high_priority)} high-priority proposals
• Check Discord for detailed agent discussions
{"• ⚠️ Increase agent activity - below usage target" if not weekly_usage['on_pace'] else "• ✅ Usage on track!"}

👉 Open dashboard: http://localhost:8501

═══════════════════════════════════════

Overnight Summary (1am - 8am):
Your autonomous agents worked through the night analyzing
code quality, curating tax law knowledge, and discovering
patterns in refund calculations.

Agent System Configuration:
- Schedule: 1:00 AM - 8:00 AM Pacific
- Teams: Code Quality, Knowledge Curation, Pattern Learning
- Target: 80-85% of Claude Max weekly limit

"""

        return summary

    def send_digest(self) -> bool:
        """
        Send digest to Discord (email integration optional).

        Returns:
            True if successful
        """
        print("Generating daily digest...")

        # Generate digest
        summary = self.generate_digest()

        # Post to Discord (primary delivery method)
        success = post_to_discord("digest", summary, username="Daily Digest")

        if success:
            print("Daily digest sent to Discord")
        else:
            print("Failed to send daily digest")

        return success

    def run(self) -> bool:
        """
        Generate and send daily digest.

        Returns:
            True if successful
        """
        return self.send_digest()


def send_daily_digest():
    """Entry point for scheduled task"""
    digest = DailyDigest()
    return digest.run()


if __name__ == "__main__":
    # Test digest generation
    digest = DailyDigest()
    print("Generating test digest...")
    summary = digest.generate_digest()
    print("\n" + summary)
