"""
Base Agent Class

Provides core functionality for all autonomous agents:
- Claude API integration
- Discord messaging
- Proposal generation
- Workspace management
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic

from agents.core.communication import create_discussion_thread, post_to_discord


class Agent:
    """
    Base class for all autonomous agents.

    Agents work in an isolated workspace and cannot directly modify the codebase.
    They create proposals that require human approval.
    """

    def __init__(self, name: str, team: str, config: Optional[Dict] = None):
        """
        Initialize agent.

        Args:
            name: Agent name (e.g., "Architect", "Security")
            team: Team name (e.g., "Code Quality Council")
            config: Optional configuration overrides
        """
        self.name = name
        self.team = team
        self.config = config or {}

        # Claude API client
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Workspace paths
        self.workspace_root = Path("agents/workspace")
        self.reviews_dir = self.workspace_root / "reviews"
        self.discussions_dir = self.workspace_root / "discussions"
        self.proposals_dir = self.workspace_root / "proposals"

        # Create directories if they don't exist
        for dir_path in [self.reviews_dir, self.discussions_dir, self.proposals_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Message tracking for usage statistics
        self.message_count = 0

    def claude_analyze(
        self,
        content: str,
        focus_areas: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """
        Analyze content using Claude.

        Args:
            content: Content to analyze
            focus_areas: Optional list of areas to focus on
            system_prompt: Optional system prompt override
            context: Optional context label (for logging/tracking)

        Returns:
            Analysis from Claude
        """
        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nFocus on these areas:\n" + "\n".join(
                f"- {area}" for area in focus_areas
            )

        default_system = f"You are {self.name}, an AI agent on the {self.team}. Provide thorough, technical analysis."

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system_prompt or default_system,
            messages=[{"role": "user", "content": content + focus_text}],
        )

        self.message_count += 1
        return message.content[0].text

    def claude_discuss(
        self, context: str, other_agent_input: str, question: Optional[str] = None
    ) -> str:
        """
        Respond to another agent's analysis (for multi-agent discussions).

        Args:
            context: Original context being discussed
            other_agent_input: What the other agent said
            question: Optional specific question to address

        Returns:
            Agent's response
        """
        prompt = f"""Context: {context}

Another agent said:
{other_agent_input}

{'Question: ' + question if question else 'Please respond to their analysis.'}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=f"You are {self.name} discussing with your team. Be concise but thorough.",
            messages=[{"role": "user", "content": prompt}],
        )

        self.message_count += 1
        return response.content[0].text

    def create_proposal(
        self,
        title: str,
        description: str,
        impact: str,
        priority: str = "medium",
        code_changes: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a proposal for human review.

        Args:
            title: Proposal title
            description: Detailed description
            impact: Impact assessment
            priority: "high", "medium", or "low"
            code_changes: Optional code diff/patch
            metadata: Optional additional metadata

        Returns:
            Proposal ID
        """
        # Generate proposal ID
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        proposal_id = f"{timestamp}-{hashlib.md5(title.encode()).hexdigest()[:8]}"

        # Create proposal directory
        proposal_dir = self.proposals_dir / "PENDING" / proposal_id
        proposal_dir.mkdir(parents=True, exist_ok=True)

        # Proposal metadata
        proposal_data = {
            "id": proposal_id,
            "title": title,
            "description": description,
            "impact": impact,
            "priority": priority,
            "team": self.team,
            "agent": self.name,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "metadata": metadata or {},
        }

        # Save proposal.json
        with open(proposal_dir / "proposal.json", "w") as f:
            json.dump(proposal_data, f, indent=2)

        # Save description as markdown
        with open(proposal_dir / "description.md", "w") as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Team**: {self.team}\n")
            f.write(f"**Agent**: {self.name}\n")
            f.write(f"**Priority**: {priority}\n")
            f.write(f"**Impact**: {impact}\n\n")
            f.write(f"## Description\n\n{description}\n")

        # Save code changes if provided
        if code_changes:
            with open(proposal_dir / "code_changes.patch", "w") as f:
                f.write(code_changes)

        return proposal_id

    def post_to_discord(self, message: str, channel: Optional[str] = None):
        """
        Post a message to Discord.

        Args:
            message: Message to post
            channel: Optional channel override (defaults to team channel)
        """
        # Determine channel
        if not channel:
            # Map team to channel
            channel_map = {
                "Code Quality Council": "code_quality",
                "Knowledge Base Curation": "knowledge",
                "Pattern Learning Council": "patterns",
            }
            channel = channel_map.get(self.team, "discussions")

        # Format message with agent attribution
        formatted_message = f"[{self.name}] {message}"

        post_to_discord(channel, formatted_message)

    def save_discussion_log(self, discussion_id: str, messages: List[Dict[str, str]]):
        """
        Save agent discussion log to workspace.

        Args:
            discussion_id: Unique discussion identifier
            messages: List of {"agent": "name", "message": "content"} dicts
        """
        log_path = self.discussions_dir / f"{discussion_id}.log"

        with open(log_path, "w") as f:
            f.write(f"Discussion: {discussion_id}\n")
            f.write(f"Team: {self.team}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

            for msg in messages:
                f.write(f"[{msg['agent']}]\n")
                f.write(f"{msg['message']}\n\n")
                f.write("-" * 80 + "\n\n")

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get agent usage statistics.

        Returns:
            Dict with message count and other stats
        """
        return {
            "agent": self.name,
            "team": self.team,
            "messages_sent": self.message_count,
            "timestamp": datetime.now().isoformat(),
        }
