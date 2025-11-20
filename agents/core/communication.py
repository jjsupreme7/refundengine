"""
Discord Communication Module

Handles all Discord webhook communications for agent discussions.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


# Discord webhook URLs (configured in .env)
WEBHOOK_URLS = {
    "discussions": os.getenv("DISCORD_WEBHOOK_DISCUSSIONS"),
    "code_quality": os.getenv("DISCORD_WEBHOOK_CODE_QUALITY"),
    "knowledge": os.getenv("DISCORD_WEBHOOK_KNOWLEDGE"),
    "patterns": os.getenv("DISCORD_WEBHOOK_PATTERNS"),
    "approvals": os.getenv("DISCORD_WEBHOOK_APPROVALS"),
    "digest": os.getenv("DISCORD_WEBHOOK_DIGEST"),
}


def post_to_discord(channel: str, message: str, username: Optional[str] = None) -> bool:
    """
    Post a message to a Discord channel via webhook.

    Args:
        channel: Channel name ("discussions", "code_quality", "knowledge", "patterns", "approvals", "digest")
        message: Message to post (supports markdown)
        username: Optional username override

    Returns:
        True if successful, False otherwise
    """
    webhook_url = WEBHOOK_URLS.get(channel)

    if not webhook_url:
        print(f"Warning: No webhook configured for channel '{channel}'")
        return False

    # Prepare payload
    payload = {"content": message, "username": username or "Refund Engine Agent"}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Discord channel '{channel}': {e}")
        return False


def create_discussion_thread(channel: str, title: str, messages: list) -> bool:
    """
    Create a threaded discussion in Discord.

    Args:
        channel: Channel name
        title: Discussion title
        messages: List of message dicts with {"agent": "name", "content": "message"}

    Returns:
        True if successful
    """
    # Post thread starter
    header = f"## 🗨️ {title}\n**Started**: {datetime.now().strftime('%I:%M %p')}\n\n"
    post_to_discord(channel, header)

    # Post each message in sequence
    for msg in messages:
        agent_name = msg.get("agent", "Unknown")
        content = msg.get("content", "")
        formatted_msg = f"**[{agent_name}]**\n{content}"
        post_to_discord(channel, formatted_msg)

    # Post footer
    footer = f"\n{'─' * 40}\n✅ Discussion complete"
    post_to_discord(channel, footer)

    return True


def post_approval_needed(
    proposal_id: str, title: str, priority: str, impact: str
) -> bool:
    """
    Post an approval notification to the approvals channel.

    Args:
        proposal_id: Unique proposal ID
        title: Proposal title
        priority: Priority level ("high", "medium", "low")
        impact: Impact description

    Returns:
        True if successful
    """
    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

    message = """{priority_emoji} **New Proposal Needs Review**

**Title**: {title}
**ID**: `{proposal_id}`
**Priority**: {priority}
**Impact**: {impact}

👉 Review in dashboard: http://localhost:8501
"""

    return post_to_discord("approvals", message)


def post_daily_digest_summary(stats: dict) -> bool:
    """
    Post daily digest summary to Discord.

    Args:
        stats: Statistics dict with agent activity

    Returns:
        True if successful
    """
    message = """📊 **Daily Agent Summary** - {datetime.now().strftime('%b %d, %Y')}

🕒 **Agent Hours**: {stats.get('agent_hours', 0)} hours
💬 **Messages Exchanged**: {stats.get('messages_exchanged', 0)}
📋 **Proposals Generated**: {stats.get('proposals_generated', 0)}
📈 **Claude Usage**: {stats.get('claude_usage_percent', 0)}% of weekly limit

🔴 **High Priority**: {stats.get('high_priority_count', 0)} proposals
🟡 **Medium Priority**: {stats.get('medium_priority_count', 0)} proposals

👉 Full digest sent to email
👉 Review proposals: http://localhost:8501
"""

    return post_to_discord("digest", message)


def test_webhook(channel: str) -> bool:
    """
    Test a webhook connection.

    Args:
        channel: Channel name to test

    Returns:
        True if webhook works
    """
    test_message = f"✅ Webhook test successful for channel '{
        channel}' at {datetime.now().strftime('%I:%M %p')}"
    return post_to_discord(channel, test_message, username="Webhook Tester")
