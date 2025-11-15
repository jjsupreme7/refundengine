"""Core agent infrastructure"""

from agents.core.agent_base import Agent
from agents.core.communication import post_to_discord, create_discussion_thread
from agents.core.approval_queue import ApprovalQueue, Proposal

__all__ = ['Agent', 'post_to_discord', 'create_discussion_thread', 'ApprovalQueue', 'Proposal']
