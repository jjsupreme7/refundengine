"""
Knowledge Base Curation Team

Team of agents that continuously improve tax law knowledge and vendor understanding.
Runs every 15 minutes (1am-8am).

Team Members:
- Legal Researcher: Monitors WA legislature for tax law updates
- Taxonomy: Classifies vendors and products
- Summarizer: Creates plain-English summaries
- Cross-Reference: Links related WAC/RCW/WTD documents
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from agents.core.agent_base import Agent
from agents.core.approval_queue import ApprovalQueue
from agents.core.communication import post_to_discord, create_discussion_thread
from agents.core.usage_tracker import UsageTracker


def extract_json(response: str) -> dict:
    """Extract JSON from Claude response, handling markdown code blocks."""
    result_clean = response.strip()
    if result_clean.startswith('```'):
        # Extract from markdown code block
        result_clean = result_clean.split('```')[1]
        if result_clean.startswith('json'):
            result_clean = result_clean[4:]
        result_clean = result_clean.strip()
    return json.loads(result_clean)


class KnowledgeCurationTeam:
    """
    Manages the Knowledge Curation team.

    This team continuously improves the knowledge base by:
    1. Monitoring WA legislature for tax law updates
    2. Researching and classifying vendors
    3. Creating plain-English summaries of complex tax code
    4. Cross-referencing related legal documents
    """

    def __init__(self, workspace_path: str = "agents/workspace"):
        self.workspace = Path(workspace_path)
        self.team_name = "knowledge_curation"

        # Initialize agents
        self.legal_researcher = Agent(
            name="legal_researcher",
            team=self.team_name
        )

        self.taxonomy = Agent(
            name="taxonomy",
            team=self.team_name
        )

        self.summarizer = Agent(
            name="summarizer",
            team=self.team_name
        )

        self.cross_reference = Agent(
            name="cross_reference",
            team=self.team_name
        )

        self.approval_queue = ApprovalQueue(workspace_path)
        self.usage_tracker = UsageTracker(workspace_path)

    def run(self) -> Dict:
        """
        Execute Knowledge Curation cycle.

        Returns:
            Dict with execution summary
        """
        start_time = datetime.now()

        post_to_discord(
            "knowledge",
            f"📚 **Knowledge Curation Team** - Starting curation cycle at {start_time.strftime('%I:%M %p')}",
            username="Knowledge Curation Team"
        )

        # Phase 1: Research and Discovery
        law_updates = self._monitor_tax_law_updates()
        vendor_research = self._research_vendors()

        # Phase 2: Content Creation
        summaries = self._create_summaries()
        cross_refs = self._create_cross_references()

        # Phase 3: Team Discussion
        proposals = self._team_discussion(
            law_updates,
            vendor_research,
            summaries,
            cross_refs
        )

        # Phase 4: Generate Proposals
        for proposal in proposals:
            self._create_proposal(proposal)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "team": self.team_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "proposals_created": len(proposals),
            "law_updates_found": len(law_updates),
            "vendors_researched": len(vendor_research),
            "summaries_created": len(summaries),
            "cross_references_created": len(cross_refs)
        }

        post_to_discord(
            "knowledge",
            f"✅ **Curation Complete** - Generated {len(proposals)} proposals in {duration:.1f}s",
            username="Knowledge Curation Team"
        )

        return summary

    def _monitor_tax_law_updates(self) -> List[Dict]:
        """
        Legal researcher monitors WA legislature for tax law updates.

        Returns:
            List of potential law updates
        """
        post_to_discord("knowledge", "**[Legal Researcher]** Monitoring tax law updates...", username="Legal Researcher")

        # Check for recent updates in knowledge base
        prompt = """Monitor Washington State tax law for recent updates.

Review the knowledge base for:
1. WAC 458-20 sections (Use Tax)
2. Recent RCW updates
3. WTD (Washington Tax Decisions) rulings

Check:
- Are there any WAC sections referenced in code but not in knowledge base?
- Are there recent WTD rulings we should ingest?
- Do any existing documents need updates?

Also check these critical sections:
- WAC 458-20-178 (Use Tax)
- WAC 458-20-15502 (Extracted Sales Tax)
- WAC 458-20-15503 (Delivered Materials)

IMPORTANT: Return ONLY valid JSON, no explanation or markdown. Use this exact format:
{
    "updates": [
        {
            "type": "missing_document|outdated_document|new_ruling",
            "title": "Document title",
            "url": "https://app.leg.wa.gov/...",
            "priority": "high|medium|low",
            "reason": "Why this is important",
            "action": "What should be done"
        }
    ]
}

If no updates found, return: {"updates": []}
"""

        try:
            result = self.legal_researcher.claude_analyze(prompt, context="tax_law_monitoring")
            self.usage_tracker.record_usage(self.team_name, "legal_researcher")

            updates = extract_json(result)
            findings = updates.get("updates", [])

            if findings:
                post_to_discord(
                    "knowledge",
                    f"**[Legal Researcher]** Found {len(findings)} potential updates",
                    username="Legal Researcher"
                )
            else:
                post_to_discord(
                    "knowledge",
                    "**[Legal Researcher]** No updates found - knowledge base is current",
                    username="Legal Researcher"
                )

            return findings

        except Exception as e:
            post_to_discord(
                "knowledge",
                f"⚠️ **[Legal Researcher]** Error monitoring updates: {str(e)}",
                username="Legal Researcher"
            )
            return []

    def _research_vendors(self) -> List[Dict]:
        """
        Research vendors and classify their business models.

        Returns:
            List of vendor research findings
        """
        post_to_discord("knowledge", "**[Taxonomy]** Researching vendors...", username="Taxonomy Agent")

        # Get list of vendors from recent analyses
        prompt = """Review recent refund analyses to identify vendors that need better classification.

Look for:
1. Vendors without clear industry classification
2. Vendors with ambiguous business models
3. Vendors where we've made incorrect assumptions

For each vendor, determine:
- Industry (SaaS, Cloud Infrastructure, E-commerce, etc.)
- Business model (B2B, B2C, Marketplace, etc.)
- Tax implications (likely to have embedded sales tax?)
- Revenue model (subscription, usage-based, one-time)

Focus on these common vendors:
- AWS, Azure, GCP (cloud infrastructure)
- Stripe, Square (payment processors)
- Shopify, WooCommerce (e-commerce platforms)
- Salesforce, HubSpot (CRM/SaaS)

IMPORTANT: Return ONLY valid JSON, no explanation or markdown. Use this exact format:
{
    "vendors": [
        {
            "name": "Vendor name",
            "industry": "Industry classification",
            "business_model": "B2B|B2C|B2B2C|Marketplace",
            "embedded_tax_likelihood": "high|medium|low",
            "reasoning": "Why this classification",
            "recommended_action": "What to update in knowledge base"
        }
    ]
}

If no vendors to research, return: {"vendors": []}
"""

        try:
            result = self.taxonomy.claude_analyze(prompt, context="vendor_research")
            self.usage_tracker.record_usage(self.team_name, "taxonomy")

            research = extract_json(result)
            vendors = research.get("vendors", [])

            post_to_discord(
                "knowledge",
                f"**[Taxonomy]** Researched {len(vendors)} vendors",
                username="Taxonomy Agent"
            )

            return vendors

        except Exception as e:
            post_to_discord(
                "knowledge",
                f"⚠️ **[Taxonomy]** Error researching vendors: {str(e)}",
                username="Taxonomy Agent"
            )
            return []

    def _create_summaries(self) -> List[Dict]:
        """
        Create plain-English summaries of complex tax documents.

        Returns:
            List of summary proposals
        """
        post_to_discord("knowledge", "**[Summarizer]** Creating tax law summaries...", username="Summarizer Agent")

        prompt = """Review tax law documents in the knowledge base and identify which need plain-English summaries.

Priority documents:
- WAC 458-20-178 (Use Tax)
- WAC 458-20-15502 (Extracted Sales Tax)
- WAC 458-20-15503 (Delivered Materials)
- RCW 82.12 (Use Tax)

For each document without a good summary, create:
1. One-sentence summary
2. Key points (3-5 bullets)
3. Common scenarios where this applies
4. Related documents

Focus on making complex legal language accessible to business users.

Return findings in JSON format:
{
    "summaries": [
        {
            "document": "WAC 458-20-XXX",
            "title": "Document title",
            "one_line": "One sentence summary",
            "key_points": ["point 1", "point 2", "point 3"],
            "scenarios": ["scenario 1", "scenario 2"],
            "related_docs": ["WAC X", "RCW Y"]
        }
    ]
}

Limit to top 3 most important summaries.
"""

        try:
            result = self.summarizer.claude_analyze(prompt, context="summary_creation")
            self.usage_tracker.record_usage(self.team_name, "summarizer")

            summaries_data = extract_json(result)
            summaries = summaries_data.get("summaries", [])

            post_to_discord(
                "knowledge",
                f"**[Summarizer]** Created {len(summaries)} summaries",
                username="Summarizer Agent"
            )

            return summaries

        except Exception as e:
            post_to_discord(
                "knowledge",
                f"⚠️ **[Summarizer]** Error creating summaries: {str(e)}",
                username="Summarizer Agent"
            )
            return []

    def _create_cross_references(self) -> List[Dict]:
        """
        Create cross-references between related legal documents.

        Returns:
            List of cross-reference findings
        """
        post_to_discord("knowledge", "**[Cross-Reference]** Linking related documents...", username="Cross-Reference Agent")

        prompt = """Analyze tax law documents and create cross-references between related concepts.

Look for:
1. WAC sections that reference specific RCW sections
2. WTD rulings that clarify WAC/RCW interpretation
3. Related exemptions and exclusions
4. Conflicting or superseding regulations

Key relationships to map:
- Use Tax (RCW 82.12) ↔ WAC 458-20-178
- Extracted Sales Tax ↔ WAC 458-20-15502, 15503
- Vendor responsibility ↔ Buyer responsibility

Return findings in JSON format:
{
    "cross_references": [
        {
            "source_doc": "WAC 458-20-178",
            "target_doc": "RCW 82.12.020",
            "relationship": "defines|clarifies|exempts|supersedes",
            "description": "How these documents relate",
            "importance": "high|medium|low"
        }
    ]
}
"""

        try:
            result = self.cross_reference.claude_analyze(prompt, context="cross_referencing")
            self.usage_tracker.record_usage(self.team_name, "cross_reference")

            refs_data = extract_json(result)
            cross_refs = refs_data.get("cross_references", [])

            post_to_discord(
                "knowledge",
                f"**[Cross-Reference]** Created {len(cross_refs)} cross-references",
                username="Cross-Reference Agent"
            )

            return cross_refs

        except Exception as e:
            post_to_discord(
                "knowledge",
                f"⚠️ **[Cross-Reference]** Error creating cross-references: {str(e)}",
                username="Cross-Reference Agent"
            )
            return []

    def _team_discussion(self, law_updates: List[Dict], vendor_research: List[Dict],
                        summaries: List[Dict], cross_refs: List[Dict]) -> List[Dict]:
        """
        Team discusses findings and creates proposals.

        Returns:
            List of proposals
        """
        post_to_discord("knowledge", "💬 **Team Discussion** - Reviewing findings...", username="Knowledge Curation Team")

        all_findings = {
            "law_updates": law_updates,
            "vendor_research": vendor_research,
            "summaries": summaries,
            "cross_references": cross_refs
        }

        discussion_prompt = f"""You are participating in a Knowledge Curation Team discussion.

Findings from team members:

**Legal Researcher**: {len(law_updates)} updates
**Taxonomy**: {len(vendor_research)} vendor classifications
**Summarizer**: {len(summaries)} summaries
**Cross-Reference**: {len(cross_refs)} cross-references

All findings:
{json.dumps(all_findings, indent=2)}

As a team, create proposals for human review:

1. Which documents should be ingested into knowledge base?
2. Which vendor classifications should be updated?
3. Which summaries should be added to documentation?
4. Which cross-references are most valuable?

Return proposals in JSON format:
{{
    "proposals": [
        {{
            "title": "Proposal title",
            "description": "What needs to be done",
            "priority": "high|medium|low",
            "impact": "How this improves the knowledge base",
            "type": "ingest_document|update_vendor|add_summary|add_cross_reference",
            "metadata": {{
                // Type-specific metadata
            }}
        }}
    ],
    "discussion_summary": "Brief summary of team discussion"
}}

Focus on high-impact improvements. Limit to top 5 proposals.
"""

        try:
            discussion_result = self.legal_researcher.claude_analyze(
                discussion_prompt,
                context="team_discussion"
            )

            self.usage_tracker.record_usage(self.team_name, "team_discussion", messages=1)

            # Save discussion
            self.legal_researcher.save_discussion_log(
                f"knowledge_discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                discussion_result
            )

            # Post to Discord
            post_to_discord(
                "knowledge",
                f"💬 **Team Discussion** - Reviewing findings...",
                username="Knowledge Curation Team"
            )

            # Parse proposals
            result = extract_json(discussion_result)

            return result.get("proposals", [])

        except Exception as e:
            post_to_discord(
                "knowledge",
                f"⚠️ Error in team discussion: {str(e)}",
                username="Knowledge Curation Team"
            )
            return []

    def _create_proposal(self, proposal_data: Dict) -> None:
        """
        Create a proposal for human review.

        Args:
            proposal_data: Proposal details
        """
        try:
            proposal_id = self.legal_researcher.create_proposal(
                title=proposal_data["title"],
                description=proposal_data["description"],
                impact=proposal_data["impact"],
                priority=proposal_data["priority"],
                metadata={
                    "type": proposal_data.get("type", "unknown"),
                    **proposal_data.get("metadata", {})
                }
            )

            post_to_discord(
                "approvals",
                f"""📚 **New Proposal from Knowledge Curation Team**

**Title**: {proposal_data['title']}
**Type**: {proposal_data.get('type', 'unknown')}
**Priority**: {proposal_data['priority'].upper()}
**Impact**: {proposal_data['impact']}

Review in dashboard: http://localhost:8501
""",
                username="Knowledge Curation Team"
            )

        except Exception as e:
            post_to_discord(
                "knowledge",
                f"⚠️ Error creating proposal: {str(e)}",
                username="Knowledge Curation Team"
            )


def run_knowledge_curation():
    """Entry point for scheduled task"""
    team = KnowledgeCurationTeam()
    return team.run()
