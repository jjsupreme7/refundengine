"""
Approval Queue Management

Manages the human approval workflow for agent proposals.
Proposals are stored in the workspace and require explicit human approval.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Proposal:
    """Represents an agent proposal"""
    id: str
    title: str
    description: str
    impact: str
    priority: str  # "high", "medium", "low"
    team: str
    agent: str
    created_at: str
    status: str  # "pending", "approved", "rejected", "deferred"
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ApprovalQueue:
    """
    Manages proposal approval workflow.

    Proposals flow through states:
    1. PENDING - Waiting for human review
    2. APPROVED - Human approved, applied to codebase
    3. REJECTED - Human rejected with feedback
    4. DEFERRED - Postponed for later review
    """

    def __init__(self, workspace_path: str = "agents/workspace"):
        self.workspace = Path(workspace_path)
        self.proposals_dir = self.workspace / "proposals"

        # Ensure directories exist
        for status_dir in ["PENDING", "APPROVED", "REJECTED", "DEFERRED"]:
            (self.proposals_dir / status_dir).mkdir(parents=True, exist_ok=True)

    def get_proposals(self, status: str = "pending",
                     priority: Optional[List[str]] = None,
                     team: Optional[List[str]] = None) -> List[Proposal]:
        """
        Get proposals matching criteria.

        Args:
            status: Proposal status ("pending", "approved", "rejected", "deferred", "all")
            priority: Optional list of priorities to filter by
            team: Optional list of teams to filter by

        Returns:
            List of matching proposals
        """
        proposals = []

        # Determine which directories to scan
        if status == "all":
            status_dirs = ["PENDING", "APPROVED", "REJECTED", "DEFERRED"]
        else:
            status_dirs = [status.upper()]

        # Scan directories
        for status_dir in status_dirs:
            dir_path = self.proposals_dir / status_dir

            if not dir_path.exists():
                continue

            for proposal_dir in dir_path.iterdir():
                if not proposal_dir.is_dir():
                    continue

                # Load proposal.json
                proposal_file = proposal_dir / "proposal.json"
                if not proposal_file.exists():
                    continue

                with open(proposal_file, "r") as f:
                    data = json.load(f)

                proposal = Proposal(**data)

                # Apply filters
                if priority and proposal.priority not in priority:
                    continue
                if team and proposal.team not in team:
                    continue

                proposals.append(proposal)

        # Sort by priority (high first) then by created_at (newest first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        proposals.sort(key=lambda p: (priority_order.get(p.priority, 3), p.created_at), reverse=True)

        return proposals

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """
        Get a specific proposal by ID.

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal object or None if not found
        """
        # Search all status directories
        for status_dir in ["PENDING", "APPROVED", "REJECTED", "DEFERRED"]:
            proposal_dir = self.proposals_dir / status_dir / proposal_id

            if proposal_dir.exists():
                proposal_file = proposal_dir / "proposal.json"
                if proposal_file.exists():
                    with open(proposal_file, "r") as f:
                        data = json.load(f)
                    return Proposal(**data)

        return None

    def approve(self, proposal_id: str, notes: Optional[str] = None) -> bool:
        """
        Approve a proposal.

        Args:
            proposal_id: Proposal ID to approve
            notes: Optional approval notes

        Returns:
            True if successful
        """
        return self._move_proposal(proposal_id, "PENDING", "APPROVED", notes=notes)

    def reject(self, proposal_id: str, reason: str) -> bool:
        """
        Reject a proposal with feedback.

        Args:
            proposal_id: Proposal ID to reject
            reason: Rejection reason (sent to agents for learning)

        Returns:
            True if successful
        """
        return self._move_proposal(proposal_id, "PENDING", "REJECTED", notes=reason)

    def defer(self, proposal_id: str, notes: Optional[str] = None) -> bool:
        """
        Defer a proposal for later review.

        Args:
            proposal_id: Proposal ID to defer
            notes: Optional notes

        Returns:
            True if successful
        """
        return self._move_proposal(proposal_id, "PENDING", "DEFERRED", notes=notes)

    def request_revision(self, proposal_id: str, feedback: str) -> bool:
        """
        Request changes to a proposal.

        Args:
            proposal_id: Proposal ID
            feedback: Feedback for agents

        Returns:
            True if successful
        """
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return False

        # Add revision request to metadata
        if "revisions" not in proposal.metadata:
            proposal.metadata["revisions"] = []

        proposal.metadata["revisions"].append({
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback
        })

        # Update proposal
        self._update_proposal_metadata(proposal_id, proposal.metadata)

        return True

    def _move_proposal(self, proposal_id: str, from_status: str,
                      to_status: str, notes: Optional[str] = None) -> bool:
        """
        Move a proposal from one status to another.

        Args:
            proposal_id: Proposal ID
            from_status: Source status directory
            to_status: Destination status directory
            notes: Optional notes

        Returns:
            True if successful
        """
        src_dir = self.proposals_dir / from_status / proposal_id
        dest_dir = self.proposals_dir / to_status / proposal_id

        if not src_dir.exists():
            print(f"Proposal {proposal_id} not found in {from_status}")
            return False

        # Load proposal
        with open(src_dir / "proposal.json", "r") as f:
            data = json.load(f)

        # Update status
        data["status"] = to_status.lower()
        data[f"{to_status.lower()}_at"] = datetime.now().isoformat()

        if notes:
            data[f"{to_status.lower()}_notes"] = notes

        # Save updated proposal
        with open(src_dir / "proposal.json", "w") as f:
            json.dump(data, f, indent=2)

        # Move directory
        shutil.move(str(src_dir), str(dest_dir))

        return True

    def _update_proposal_metadata(self, proposal_id: str, metadata: Dict) -> bool:
        """Update proposal metadata"""
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return False

        # Find proposal file
        for status_dir in ["PENDING", "APPROVED", "REJECTED", "DEFERRED"]:
            proposal_file = self.proposals_dir / status_dir / proposal_id / "proposal.json"
            if proposal_file.exists():
                with open(proposal_file, "r") as f:
                    data = json.load(f)

                data["metadata"] = metadata

                with open(proposal_file, "w") as f:
                    json.dump(data, f, indent=2)

                return True

        return False

    def count_approved_today(self) -> int:
        """Count proposals approved today"""
        today = datetime.now().date().isoformat()
        count = 0

        approved_dir = self.proposals_dir / "APPROVED"
        if approved_dir.exists():
            for proposal_dir in approved_dir.iterdir():
                if not proposal_dir.is_dir():
                    continue

                proposal_file = proposal_dir / "proposal.json"
                if proposal_file.exists():
                    with open(proposal_file, "r") as f:
                        data = json.load(f)

                    if data.get("approved_at", "").startswith(today):
                        count += 1

        return count

    def get_weekly_usage_percent(self) -> int:
        """
        Get current week's Claude Max usage percentage.

        This is a placeholder - actual implementation would track
        API usage via Anthropic SDK or database.

        Returns:
            Percentage of weekly limit used (0-100)
        """
        # TODO: Implement actual usage tracking
        # For now, return placeholder
        return 0
