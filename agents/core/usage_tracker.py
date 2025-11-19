"""
Claude Max Usage Tracker

Monitors Claude API usage to ensure we hit 80-85% of weekly limit.
Provides alerts if usage falls below target pace.
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .communication import post_to_discord


@dataclass
class UsageRecord:
    """Single usage record"""

    timestamp: str
    messages: int
    team: str
    agent: str
    tokens_input: int = 0
    tokens_output: int = 0


class UsageTracker:
    """
    Tracks Claude Max API usage to ensure we hit weekly targets.

    Weekly Limit: ~5,000 messages (Claude Max as of 2025)
    Target: 80-85% usage = 4,000-4,250 messages/week
    Daily Target: ~1,800 messages/day (7-hour schedule)
    """

    # Claude Max limits (approximate - actual limits may vary)
    WEEKLY_MESSAGE_LIMIT = 5000
    WEEKLY_RESET_DAY = 1  # Tuesday = 1 (Monday = 0)

    def __init__(self, workspace_path: str = "agents/workspace"):
        self.workspace = Path(workspace_path)
        self.usage_dir = self.workspace / "usage"
        self.usage_dir.mkdir(parents=True, exist_ok=True)

        # Load config targets
        self.weekly_target_percent = int(os.getenv("WEEKLY_TARGET_PERCENT", "85"))
        self.daily_target_messages = int(os.getenv("DAILY_TARGET_MESSAGES", "1800"))

    def record_usage(
        self,
        team: str,
        agent: str,
        messages: int = 1,
        tokens_input: int = 0,
        tokens_output: int = 0,
    ) -> None:
        """
        Record API usage.

        Args:
            team: Team name
            agent: Agent name
            messages: Number of messages (default 1)
            tokens_input: Input tokens used
            tokens_output: Output tokens used
        """
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            messages=messages,
            team=team,
            agent=agent,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        )

        # Append to daily log
        today = datetime.now().date().isoformat()
        log_file = self.usage_dir / f"{today}.jsonl"

        with open(log_file, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def get_daily_usage(self, date: Optional[str] = None) -> Dict:
        """
        Get usage statistics for a specific day.

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Dict with usage statistics
        """
        if date is None:
            date = datetime.now().date().isoformat()

        log_file = self.usage_dir / f"{date}.jsonl"

        if not log_file.exists():
            return {
                "date": date,
                "messages": 0,
                "tokens_input": 0,
                "tokens_output": 0,
                "by_team": {},
            }

        # Parse log file
        messages = 0
        tokens_input = 0
        tokens_output = 0
        by_team = {}

        with open(log_file, "r") as f:
            for line in f:
                record = json.loads(line)
                messages += record.get("messages", 1)
                tokens_input += record.get("tokens_input", 0)
                tokens_output += record.get("tokens_output", 0)

                team = record.get("team", "unknown")
                if team not in by_team:
                    by_team[team] = {
                        "messages": 0,
                        "tokens_input": 0,
                        "tokens_output": 0,
                    }

                by_team[team]["messages"] += record.get("messages", 1)
                by_team[team]["tokens_input"] += record.get("tokens_input", 0)
                by_team[team]["tokens_output"] += record.get("tokens_output", 0)

        return {
            "date": date,
            "messages": messages,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "by_team": by_team,
        }

    def get_weekly_usage(self) -> Dict:
        """
        Get current week's usage statistics.

        Week starts on Tuesday (when Claude Max resets).

        Returns:
            Dict with weekly usage statistics
        """
        # Find start of current week (last Tuesday)
        today = datetime.now().date()
        days_since_reset = (today.weekday() - self.WEEKLY_RESET_DAY) % 7
        week_start = today - timedelta(days=days_since_reset)

        # Aggregate usage from week_start to today
        total_messages = 0
        total_tokens_input = 0
        total_tokens_output = 0
        daily_breakdown = []

        current_date = week_start
        while current_date <= today:
            date_str = current_date.isoformat()
            daily = self.get_daily_usage(date_str)

            total_messages += daily["messages"]
            total_tokens_input += daily["tokens_input"]
            total_tokens_output += daily["tokens_output"]
            daily_breakdown.append(daily)

            current_date += timedelta(days=1)

        # Calculate percentages
        usage_percent = (total_messages / self.WEEKLY_MESSAGE_LIMIT) * 100
        target_messages = (self.weekly_target_percent / 100) * self.WEEKLY_MESSAGE_LIMIT

        # Days remaining in week
        days_until_reset = (self.WEEKLY_RESET_DAY - today.weekday()) % 7
        if days_until_reset == 0:
            days_until_reset = 7

        return {
            "week_start": week_start.isoformat(),
            "week_end": (week_start + timedelta(days=6)).isoformat(),
            "days_remaining": days_until_reset,
            "total_messages": total_messages,
            "weekly_limit": self.WEEKLY_MESSAGE_LIMIT,
            "usage_percent": round(usage_percent, 2),
            "target_percent": self.weekly_target_percent,
            "target_messages": int(target_messages),
            "messages_remaining": int(target_messages - total_messages),
            "daily_breakdown": daily_breakdown,
            "on_pace": usage_percent
            >= (self.weekly_target_percent * 0.9),  # Within 90% of target
        }

    def check_daily_pace(self) -> Dict:
        """
        Check if today's usage is on pace to meet weekly target.

        Returns:
            Dict with pace analysis
        """
        today_usage = self.get_daily_usage()
        weekly_usage = self.get_weekly_usage()

        messages_today = today_usage["messages"]
        target_today = self.daily_target_messages

        pace_percent = (messages_today / target_today) * 100 if target_today > 0 else 0

        return {
            "date": today_usage["date"],
            "messages_today": messages_today,
            "target_today": target_today,
            "pace_percent": round(pace_percent, 2),
            "messages_needed": max(0, target_today - messages_today),
            "on_pace": pace_percent >= 90,  # Within 90% of daily target
            "weekly_summary": {
                "usage_percent": weekly_usage["usage_percent"],
                "target_percent": weekly_usage["target_percent"],
                "on_pace": weekly_usage["on_pace"],
            },
        }

    def send_pace_alert(self, force: bool = False) -> bool:
        """
        Send Discord alert if usage is below pace.

        Args:
            force: Send alert even if on pace (for testing)

        Returns:
            True if alert was sent
        """
        pace = self.check_daily_pace()
        weekly = self.get_weekly_usage()

        if not force and pace["on_pace"] and weekly["on_pace"]:
            return False

        # Determine alert severity
        if pace["pace_percent"] < 50:
            emoji = "🔴"
            severity = "CRITICAL"
        elif pace["pace_percent"] < 75:
            emoji = "🟡"
            severity = "WARNING"
        else:
            emoji = "🟢"
            severity = "INFO"

        message = f"""{emoji} **Usage Pace Alert** - {severity}

**Today's Progress**:
- Messages: {pace['messages_today']:,} / {pace['target_today']:,} ({pace['pace_percent']:.1f}%)
- Needed: {pace['messages_needed']:,} more messages

**Weekly Progress**:
- Messages: {weekly['total_messages']:,} / {weekly['target_messages']:,} ({weekly['usage_percent']:.1f}%)
- Target: {weekly['target_percent']}% of weekly limit
- Days Remaining: {weekly['days_remaining']}

{"✅ On pace!" if weekly['on_pace'] else "⚠️ Below target - increase agent activity"}
"""

        return post_to_discord("digest", message, username="Usage Monitor")

    def get_usage_summary(self) -> str:
        """
        Get formatted usage summary for daily digest.

        Returns:
            Formatted string with usage statistics
        """
        weekly = self.get_weekly_usage()
        today = self.get_daily_usage()

        summary = f"""**Claude Max Usage Report**

**This Week** (Resets Tuesday):
- {weekly['total_messages']:,} / {weekly['weekly_limit']:,} messages ({weekly['usage_percent']:.1f}%)
- Target: {weekly['target_percent']}% = {weekly['target_messages']:,} messages
- Days Remaining: {weekly['days_remaining']}
- Status: {"✅ On Pace" if weekly['on_pace'] else "⚠️ Below Target"}

**Today**:
- {today['messages']:,} messages
- Target: {self.daily_target_messages:,} messages/day

**Team Breakdown** (Today):
"""

        for team, stats in today.get("by_team", {}).items():
            summary += f"\n- {team}: {stats['messages']:,} messages"

        return summary
