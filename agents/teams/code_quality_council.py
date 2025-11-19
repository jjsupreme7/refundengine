"""
Code Quality Council

Team of agents that continuously review code architecture, security, and performance.
Runs every 1.5 hours (1am-8am).

Team Members:
- Architect: Reviews architecture and design patterns
- Security: Scans for vulnerabilities and PII exposure
- Performance: Identifies optimization opportunities
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from agents.core.agent_base import Agent
from agents.core.approval_queue import ApprovalQueue
from agents.core.communication import create_discussion_thread, post_to_discord
from agents.core.usage_tracker import UsageTracker


def extract_json(response: str) -> dict:
    """Extract JSON from Claude response, handling markdown code blocks."""
    result_clean = response.strip()
    if result_clean.startswith("```"):
        # Extract from markdown code block
        result_clean = result_clean.split("```")[1]
        if result_clean.startswith("json"):
            result_clean = result_clean[4:]
        result_clean = result_clean.strip()
    return json.loads(result_clean)


class CodeQualityCouncil:
    """
    Manages the Code Quality Council team.

    This team reviews the codebase for:
    1. Architecture issues and design pattern improvements
    2. Security vulnerabilities and PII exposure
    3. Performance bottlenecks and optimization opportunities
    """

    def __init__(self, workspace_path: str = "agents/workspace"):
        self.workspace = Path(workspace_path)
        self.team_name = "code_quality_council"

        # Initialize agents
        self.architect = Agent(name="architect", team=self.team_name)

        self.security = Agent(name="security", team=self.team_name)

        self.performance = Agent(name="performance", team=self.team_name)

        self.approval_queue = ApprovalQueue(workspace_path)
        self.usage_tracker = UsageTracker(workspace_path)

    def run(self) -> Dict:
        """
        Execute Code Quality Council review cycle.

        Returns:
            Dict with execution summary
        """
        start_time = datetime.now()

        post_to_discord(
            "code_quality",
            f"🏛️ **Code Quality Council** - Starting review cycle at {start_time.strftime('%I:%M %p')}",
            username="Code Quality Council",
        )

        # Phase 1: Individual Reviews
        architect_findings = self._architect_review()
        security_findings = self._security_review()
        performance_findings = self._performance_review()

        # Phase 2: Team Discussion
        proposals = self._team_discussion(
            architect_findings, security_findings, performance_findings
        )

        # Phase 3: Generate Proposals
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
            "architect_findings": len(architect_findings),
            "security_findings": len(security_findings),
            "performance_findings": len(performance_findings),
        }

        post_to_discord(
            "code_quality",
            f"✅ **Review Complete** - Generated {len(proposals)} proposals in {duration:.1f}s",
            username="Code Quality Council",
        )

        return summary

    def _architect_review(self) -> List[Dict]:
        """
        Architect reviews code architecture and design patterns.

        Returns:
            List of findings
        """
        post_to_discord(
            "code_quality",
            "**[Architect]** Starting architecture review...",
            username="Architect Agent",
        )

        # Define review areas
        areas = [
            {
                "name": "Core Architecture",
                "paths": ["core/*.py", "api/*.py"],
                "focus": "Separation of concerns, SOLID principles, dependency injection",
            },
            {
                "name": "Agent System",
                "paths": ["agents/core/*.py", "agents/teams/*.py"],
                "focus": "Agent communication patterns, proposal workflow, error handling",
            },
            {
                "name": "Database Layer",
                "paths": ["scripts/*supabase*.py", "scripts/db*.py"],
                "focus": "Connection pooling, query optimization, transaction management",
            },
        ]

        findings = []

        for area in areas:
            prompt = f"""Review {area['name']} for architectural improvements.

Focus on: {area['focus']}

Analyze files matching: {', '.join(area['paths'])}

Look for:
1. Design pattern opportunities (Factory, Strategy, Observer, etc.)
2. Code duplication that could be abstracted
3. Tight coupling that could be loosened
4. Missing abstraction layers
5. Inconsistent patterns across similar components

Return findings in JSON format:
{{
    "area": "{area['name']}",
    "findings": [
        {{
            "title": "Finding title",
            "description": "Detailed description",
            "severity": "high|medium|low",
            "affected_files": ["file1.py", "file2.py"],
            "suggested_fix": "How to fix it"
        }}
    ]
}}
"""

            try:
                result = self.architect.claude_analyze(
                    prompt, context="architecture_review"
                )
                self.usage_tracker.record_usage(self.team_name, "architect")

                # Parse findings
                area_findings = extract_json(result)
                findings.extend(area_findings.get("findings", []))

            except Exception as e:
                post_to_discord(
                    "code_quality",
                    f"⚠️ **[Architect]** Error reviewing {area['name']}: {str(e)}",
                    username="Architect Agent",
                )

        post_to_discord(
            "code_quality",
            f"**[Architect]** Found {len(findings)} architectural improvements",
            username="Architect Agent",
        )

        return findings

    def _security_review(self) -> List[Dict]:
        """
        Security agent scans for vulnerabilities and PII exposure.

        Returns:
            List of security findings
        """
        post_to_discord(
            "code_quality",
            "**[Security]** Starting security scan...",
            username="Security Agent",
        )

        # Security review checklist
        checks = [
            {
                "name": "SQL Injection",
                "pattern": r"execute\(|executemany\(|cursor\.",
                "focus": "Ensure parameterized queries, no string concatenation",
            },
            {
                "name": "PII Exposure",
                "pattern": r"email|ssn|social_security|phone|address",
                "focus": "Verify encryption and proper handling of sensitive data",
            },
            {
                "name": "API Key Security",
                "pattern": r"OPENAI_API_KEY|ANTHROPIC_API_KEY|SUPABASE",
                "focus": "Ensure keys are in .env, never hardcoded or logged",
            },
            {
                "name": "Input Validation",
                "pattern": r"request\.|input\(|raw_input\(",
                "focus": "Validate and sanitize all user inputs",
            },
            {
                "name": "Unsafe Deserialization",
                "pattern": r"pickle\.load|yaml\.load|eval\(",
                "focus": "Avoid unsafe deserialization, use safe alternatives",
            },
        ]

        findings = []

        for check in checks:
            prompt = f"""Security Check: {check['name']}

Search codebase for pattern: {check['pattern']}
Focus: {check['focus']}

Analyze each occurrence and determine if it's a security risk.

Return findings in JSON format:
{{
    "check": "{check['name']}",
    "findings": [
        {{
            "title": "Finding title",
            "description": "Security concern description",
            "severity": "critical|high|medium|low",
            "file": "path/to/file.py",
            "line": 42,
            "code_snippet": "vulnerable code",
            "fix": "How to remediate"
        }}
    ]
}}
"""

            try:
                result = self.security.claude_analyze(prompt, context="security_scan")
                self.usage_tracker.record_usage(self.team_name, "security")

                check_findings = extract_json(result)
                findings.extend(check_findings.get("findings", []))

            except Exception as e:
                post_to_discord(
                    "code_quality",
                    f"⚠️ **[Security]** Error in {check['name']} check: {str(e)}",
                    username="Security Agent",
                )

        # Auto-reject critical security issues
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        if critical_count > 0:
            post_to_discord(
                "code_quality",
                f"🔴 **CRITICAL**: Found {critical_count} critical security issues!",
                username="Security Agent",
            )

        post_to_discord(
            "code_quality",
            f"**[Security]** Completed scan - {len(findings)} issues found",
            username="Security Agent",
        )

        return findings

    def _performance_review(self) -> List[Dict]:
        """
        Performance agent identifies optimization opportunities.

        Returns:
            List of performance findings
        """
        post_to_discord(
            "code_quality",
            "**[Performance]** Starting performance analysis...",
            username="Performance Agent",
        )

        # Performance review areas
        areas = [
            {
                "name": "Database Queries",
                "pattern": r"execute\(|query\(|search\(",
                "focus": "N+1 queries, missing indexes, inefficient joins",
            },
            {
                "name": "Vector Search",
                "pattern": r"match_documents|similarity_search",
                "focus": "Chunk size optimization, embedding caching, batch processing",
            },
            {
                "name": "API Calls",
                "pattern": r"requests\.|http\.|openai\.|anthropic\.",
                "focus": "Rate limiting, retry logic, connection pooling, caching",
            },
            {
                "name": "File I/O",
                "pattern": r"open\(|read\(|write\(",
                "focus": "Buffering, batch operations, async I/O opportunities",
            },
        ]

        findings = []

        for area in areas:
            prompt = f"""Performance Review: {area['name']}

Search for pattern: {area['pattern']}
Focus: {area['focus']}

Analyze code for:
1. Inefficient algorithms (O(n²) that could be O(n))
2. Unnecessary loops or redundant operations
3. Missing caching opportunities
4. Synchronous operations that could be async
5. Resource leaks (unclosed connections, files)

Return findings in JSON format:
{{
    "area": "{area['name']}",
    "findings": [
        {{
            "title": "Finding title",
            "description": "Performance issue description",
            "impact": "high|medium|low",
            "file": "path/to/file.py",
            "current_complexity": "O(n²)",
            "optimized_complexity": "O(n)",
            "suggested_fix": "How to optimize"
        }}
    ]
}}
"""

            try:
                result = self.performance.claude_analyze(
                    prompt, context="performance_review"
                )
                self.usage_tracker.record_usage(self.team_name, "performance")

                area_findings = extract_json(result)
                findings.extend(area_findings.get("findings", []))

            except Exception as e:
                post_to_discord(
                    "code_quality",
                    f"⚠️ **[Performance]** Error analyzing {area['name']}: {str(e)}",
                    username="Performance Agent",
                )

        post_to_discord(
            "code_quality",
            f"**[Performance]** Analysis complete - {len(findings)} optimizations identified",
            username="Performance Agent",
        )

        return findings

    def _team_discussion(
        self,
        architect_findings: List[Dict],
        security_findings: List[Dict],
        performance_findings: List[Dict],
    ) -> List[Dict]:
        """
        Agents discuss findings and prioritize proposals.

        Returns:
            List of prioritized proposals
        """
        post_to_discord(
            "code_quality",
            "💬 **Team Discussion** - Reviewing findings...",
            username="Code Quality Council",
        )

        # Combine all findings
        all_findings = {
            "architect": architect_findings,
            "security": security_findings,
            "performance": performance_findings,
        }

        discussion_prompt = f"""You are participating in a Code Quality Council discussion.

Findings from team members:

**Architect**: {len(architect_findings)} findings
**Security**: {len(security_findings)} findings
**Performance**: {len(performance_findings)} findings

All findings:
{json.dumps(all_findings, indent=2)}

As a team, discuss and prioritize these findings:

1. Which findings are most critical?
2. Are there any findings that overlap or conflict?
3. What should be the top 5 proposals to submit for human review?
4. For each proposal, what's the impact and implementation effort?

IMPORTANT: Return ONLY valid JSON, no explanation or markdown. Use this exact format:
{{
    "proposals": [
        {{
            "title": "Proposal title",
            "description": "What needs to be done",
            "priority": "high|medium|low",
            "impact": "Impact description",
            "effort": "low|medium|high",
            "affected_files": ["file1.py"],
            "related_findings": ["finding1", "finding2"]
        }}
    ],
    "discussion_summary": "Brief summary of team discussion"
}}

Limit to top 5 proposals. If no critical issues, return: {{"proposals": [], "discussion_summary": "No critical issues requiring immediate action"}}
"""

        try:
            # Use architect to analyze and create proposals
            result_text = self.architect.claude_analyze(
                discussion_prompt, context="team_discussion"
            )

            self.usage_tracker.record_usage(self.team_name, "team_discussion")

            # Parse proposals
            result = extract_json(result_text)

            # Post discussion summary to Discord
            if result.get("discussion_summary"):
                post_to_discord(
                    "code_quality",
                    f"💬 **Discussion Summary**: {result['discussion_summary']}",
                    username="Code Quality Council",
                )

            return result.get("proposals", [])

        except Exception as e:
            post_to_discord(
                "code_quality",
                f"⚠️ Error in team discussion: {str(e)}",
                username="Code Quality Council",
            )
            return []

    def _create_proposal(self, proposal_data: Dict) -> None:
        """
        Create a proposal for human review.

        Args:
            proposal_data: Proposal details from team discussion
        """
        try:
            proposal_id = self.architect.create_proposal(
                title=proposal_data["title"],
                description=proposal_data["description"],
                impact=proposal_data["impact"],
                priority=proposal_data["priority"],
                metadata={
                    "effort": proposal_data.get("effort", "unknown"),
                    "affected_files": proposal_data.get("affected_files", []),
                    "related_findings": proposal_data.get("related_findings", []),
                },
            )

            post_to_discord(
                "approvals",
                f"""🔔 **New Proposal from Code Quality Council**

**Title**: {proposal_data['title']}
**Priority**: {proposal_data['priority'].upper()}
**Impact**: {proposal_data['impact']}

Review in dashboard: http://localhost:8501
""",
                username="Code Quality Council",
            )

        except Exception as e:
            post_to_discord(
                "code_quality",
                f"⚠️ Error creating proposal: {str(e)}",
                username="Code Quality Council",
            )


def run_code_quality_council():
    """Entry point for scheduled task"""
    council = CodeQualityCouncil()
    return council.run()
