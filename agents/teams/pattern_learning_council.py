"""
Pattern Learning Council

Team of agents that discovers patterns in refund decisions and corrections.
Runs every 3 hours (1am-8am).

Team Members:
- Pattern Discovery: Finds subtle patterns in corrections
- Validator: Tests patterns against historical data
- Edge Case: Identifies exceptions and boundary conditions
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


class PatternLearningCouncil:
    """
    Manages the Pattern Learning Council team.

    This team discovers patterns from refund corrections to improve
    the refund engine's accuracy over time.

    Focus areas:
    1. Embedded sales tax patterns (vendor-specific)
    2. Industry-specific exemptions
    3. Use tax vs. sales tax boundary conditions
    4. State-specific vendor behaviors
    """

    # Pattern requires 95% accuracy and 50+ examples before deployment
    MIN_ACCURACY = 0.95
    MIN_SAMPLE_SIZE = 50

    def __init__(self, workspace_path: str = "agents/workspace"):
        self.workspace = Path(workspace_path)
        self.team_name = "pattern_learning"

        # Initialize agents
        self.pattern_discovery = Agent(
            name="pattern_discovery",
            team=self.team_name
        )

        self.validator = Agent(
            name="validator",
            team=self.team_name
        )

        self.edge_case = Agent(
            name="edge_case",
            team=self.team_name
        )

        self.approval_queue = ApprovalQueue(workspace_path)
        self.usage_tracker = UsageTracker(workspace_path)

    def run(self) -> Dict:
        """
        Execute Pattern Learning cycle.

        Returns:
            Dict with execution summary
        """
        start_time = datetime.now()

        post_to_discord(
            "patterns",
            f"🧠 **Pattern Learning Council** - Starting pattern discovery at {start_time.strftime('%I:%M %p')}",
            username="Pattern Learning Council"
        )

        # Phase 1: Discover Patterns
        discovered_patterns = self._discover_patterns()

        # Phase 2: Validate Patterns
        validated_patterns = self._validate_patterns(discovered_patterns)

        # Phase 3: Find Edge Cases
        edge_cases = self._find_edge_cases(validated_patterns)

        # Phase 4: Team Discussion
        proposals = self._team_discussion(
            discovered_patterns,
            validated_patterns,
            edge_cases
        )

        # Phase 5: Generate Proposals
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
            "patterns_discovered": len(discovered_patterns),
            "patterns_validated": len(validated_patterns),
            "edge_cases_found": len(edge_cases)
        }

        post_to_discord(
            "patterns",
            f"✅ **Learning Complete** - Generated {len(proposals)} pattern proposals in {duration:.1f}s",
            username="Pattern Learning Council"
        )

        return summary

    def _discover_patterns(self) -> List[Dict]:
        """
        Discover patterns from refund corrections.

        Returns:
            List of discovered patterns
        """
        post_to_discord("patterns", "**[Pattern Discovery]** Analyzing refund corrections...", username="Pattern Discovery")

        prompt = """Analyze refund calculations and corrections to discover patterns.

Focus on these pattern types:

1. **Embedded Sales Tax Patterns**
   - Which vendors consistently have embedded sales tax?
   - Are there industry-specific patterns? (e.g., SaaS vs. cloud infrastructure)
   - State-specific vendor behaviors (WA tax collection patterns)

2. **Exemption Patterns**
   - Which exemptions are commonly missed?
   - Are there product/service combinations that trigger exemptions?
   - Industry-specific exemption patterns

3. **Calculation Patterns**
   - Common calculation errors
   - Rounding or precision issues
   - Multi-state allocation patterns

4. **Vendor Behavior Patterns**
   - Vendors that changed tax collection policies
   - Vendors with inconsistent tax treatment
   - New vendor patterns based on similar vendors

Look for patterns with:
- High frequency (occurring 10+ times)
- High consistency (>90% accuracy)
- Clear business logic
- Actionable rules

Return findings in JSON format:
{
    "patterns": [
        {
            "type": "embedded_tax|exemption|calculation|vendor_behavior",
            "title": "Pattern title",
            "description": "Pattern description",
            "rule": "If X, then Y",
            "confidence": 0.95,
            "sample_size": 50,
            "examples": ["example1", "example2", "example3"],
            "business_logic": "Why this pattern exists"
        }
    ]
}

Focus on discovering 3-5 high-value patterns.
"""

        try:
            result = self.pattern_discovery.claude_analyze(prompt, context="pattern_discovery")
            self.usage_tracker.record_usage(self.team_name, "pattern_discovery")

            patterns_data = extract_json(result)
            patterns = patterns_data.get("patterns", [])

            post_to_discord(
                "patterns",
                f"**[Pattern Discovery]** Discovered {len(patterns)} patterns",
                username="Pattern Discovery"
            )

            return patterns

        except Exception as e:
            post_to_discord(
                "patterns",
                f"⚠️ **[Pattern Discovery]** Error discovering patterns: {str(e)}",
                username="Pattern Discovery"
            )
            return []

    def _validate_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Validate discovered patterns against historical data.

        Args:
            patterns: Discovered patterns to validate

        Returns:
            List of validated patterns
        """
        post_to_discord("patterns", "**[Validator]** Validating patterns...", username="Validator Agent")

        if not patterns:
            post_to_discord("patterns", "**[Validator]** No patterns to validate", username="Validator Agent")
            return []

        validated = []

        for pattern in patterns:
            prompt = f"""Validate this pattern against historical refund data:

Pattern: {pattern['title']}
Rule: {pattern['rule']}
Type: {pattern['type']}
Claimed Confidence: {pattern['confidence']}
Claimed Sample Size: {pattern['sample_size']}

Validation tasks:
1. Find all cases where this pattern should apply
2. Count true positives (pattern applied, result correct)
3. Count false positives (pattern applied, result incorrect)
4. Count false negatives (pattern should apply, but didn't)
5. Calculate actual accuracy

Minimum thresholds:
- Accuracy: {self.MIN_ACCURACY * 100}%
- Sample Size: {self.MIN_SAMPLE_SIZE}+ cases

Return validation results in JSON format:
{{
    "pattern_title": "{pattern['title']}",
    "validation_passed": true/false,
    "actual_accuracy": 0.XX,
    "actual_sample_size": XX,
    "true_positives": XX,
    "false_positives": XX,
    "false_negatives": XX,
    "recommendation": "deploy|needs_more_data|reject",
    "reasoning": "Why this recommendation"
}}
"""

            try:
                result = self.validator.claude_analyze(prompt, context="pattern_validation")
                self.usage_tracker.record_usage(self.team_name, "validator")

                validation = extract_json(result)

                # Add validation results to pattern
                pattern["validation"] = validation

                if validation.get("validation_passed"):
                    validated.append(pattern)

            except Exception as e:
                post_to_discord(
                    "patterns",
                    f"⚠️ **[Validator]** Error validating pattern '{pattern['title']}': {str(e)}",
                    username="Validator Agent"
                )

        post_to_discord(
            "patterns",
            f"**[Validator]** Validated {len(validated)}/{len(patterns)} patterns",
            username="Validator Agent"
        )

        return validated

    def _find_edge_cases(self, patterns: List[Dict]) -> List[Dict]:
        """
        Identify edge cases and boundary conditions for patterns.

        Args:
            patterns: Validated patterns

        Returns:
            List of edge cases
        """
        post_to_discord("patterns", "**[Edge Case]** Identifying edge cases...", username="Edge Case Agent")

        if not patterns:
            post_to_discord("patterns", "**[Edge Case]** No patterns to analyze", username="Edge Case Agent")
            return []

        all_edge_cases = []

        for pattern in patterns:
            prompt = f"""Identify edge cases and boundary conditions for this pattern:

Pattern: {pattern['title']}
Rule: {pattern['rule']}
Type: {pattern['type']}
Accuracy: {pattern['validation']['actual_accuracy']}

Find edge cases where this pattern might fail:

1. **Boundary Conditions**
   - Threshold values (e.g., amount limits, date ranges)
   - State boundaries (multi-state scenarios)
   - Industry edge cases

2. **Exceptions**
   - Known vendor exceptions
   - Product/service combinations that break the rule
   - Regulatory exceptions

3. **Timing Issues**
   - Vendor policy changes over time
   - Tax law changes
   - Seasonal patterns

4. **Data Quality Issues**
   - Missing data that pattern assumes exists
   - Ambiguous classifications
   - Data entry errors

Return edge cases in JSON format:
{{
    "pattern_title": "{pattern['title']}",
    "edge_cases": [
        {{
            "title": "Edge case title",
            "description": "What makes this an edge case",
            "frequency": "common|rare|very_rare",
            "severity": "breaks_pattern|reduces_accuracy|minor_issue",
            "handling": "How to handle this edge case"
        }}
    ]
}}

Focus on edge cases that are common or high-severity.
"""

            try:
                result = self.edge_case.claude_analyze(prompt, context="edge_case_analysis")
                self.usage_tracker.record_usage(self.team_name, "edge_case")

                edge_data = extract_json(result)
                edge_cases = edge_data.get("edge_cases", [])

                for edge in edge_cases:
                    edge["pattern"] = pattern["title"]

                all_edge_cases.extend(edge_cases)

            except Exception as e:
                post_to_discord(
                    "patterns",
                    f"⚠️ **[Edge Case]** Error analyzing '{pattern['title']}': {str(e)}",
                    username="Edge Case Agent"
                )

        post_to_discord(
            "patterns",
            f"**[Edge Case]** Identified {len(all_edge_cases)} edge cases",
            username="Edge Case Agent"
        )

        return all_edge_cases

    def _team_discussion(self, discovered_patterns: List[Dict],
                        validated_patterns: List[Dict],
                        edge_cases: List[Dict]) -> List[Dict]:
        """
        Team discusses patterns and creates deployment proposals.

        Returns:
            List of proposals
        """
        post_to_discord("patterns", "💬 **Team Discussion** - Reviewing patterns...", username="Pattern Learning Council")

        all_findings = {
            "discovered_patterns": discovered_patterns,
            "validated_patterns": validated_patterns,
            "edge_cases": edge_cases
        }

        discussion_prompt = f"""You are participating in a Pattern Learning Council discussion.

Findings from team members:

**Pattern Discovery**: {len(discovered_patterns)} patterns discovered
**Validator**: {len(validated_patterns)} patterns validated
**Edge Case**: {len(edge_cases)} edge cases identified

All findings:
{json.dumps(all_findings, indent=2)}

As a team, decide which patterns to deploy:

1. Which patterns are ready for production?
2. Which patterns need more data?
3. How should edge cases be handled?
4. What's the risk/reward of each pattern?

For deployable patterns:
- Must have ≥{self.MIN_ACCURACY * 100}% accuracy
- Must have ≥{self.MIN_SAMPLE_SIZE} examples
- Must have clear edge case handling
- Must have measurable business impact

Return proposals in JSON format:
{{
    "proposals": [
        {{
            "title": "Deploy pattern: [pattern name]",
            "description": "What this pattern does",
            "priority": "high|medium|low",
            "impact": "Expected impact on refund accuracy",
            "pattern_data": {{
                "rule": "Pattern rule",
                "accuracy": 0.XX,
                "sample_size": XX,
                "edge_cases": ["edge1", "edge2"]
            }},
            "deployment_plan": "How to deploy this pattern",
            "rollback_plan": "How to rollback if issues occur"
        }}
    ],
    "discussion_summary": "Brief summary of team discussion"
}}

Only propose patterns that are truly ready. Quality over quantity.
"""

        try:
            discussion = self.pattern_discovery.claude_discuss(
                discussion_prompt,
                participants=[self.pattern_discovery, self.validator, self.edge_case]
            )

            self.usage_tracker.record_usage(self.team_name, "team_discussion", messages=3)

            # Save discussion
            self.pattern_discovery.save_discussion_log(
                f"pattern_discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                discussion
            )

            # Post to Discord
            messages = []
            for msg in discussion:
                messages.append({
                    "agent": msg.get("agent", "unknown"),
                    "content": msg.get("content", "")[:500]
                })

            create_discussion_thread("patterns", "Pattern Learning Discussion", messages)

            # Parse proposals
            final_result = discussion[-1].get("content", "{}")
            result = json.loads(final_result)

            return result.get("proposals", [])

        except Exception as e:
            post_to_discord(
                "patterns",
                f"⚠️ Error in team discussion: {str(e)}",
                username="Pattern Learning Council"
            )
            return []

    def _create_proposal(self, proposal_data: Dict) -> None:
        """
        Create a proposal for human review.

        Args:
            proposal_data: Proposal details
        """
        try:
            # Extract pattern accuracy for priority calculation
            pattern_data = proposal_data.get("pattern_data", {})
            accuracy = pattern_data.get("accuracy", 0)
            sample_size = pattern_data.get("sample_size", 0)

            # High accuracy + large sample = high priority
            if accuracy >= 0.98 and sample_size >= 100:
                priority = "high"
            elif accuracy >= 0.95 and sample_size >= 50:
                priority = "medium"
            else:
                priority = "low"

            proposal_id = self.pattern_discovery.create_proposal(
                title=proposal_data["title"],
                description=proposal_data["description"],
                impact=proposal_data["impact"],
                priority=proposal_data.get("priority", priority),
                metadata={
                    "pattern_data": pattern_data,
                    "deployment_plan": proposal_data.get("deployment_plan", ""),
                    "rollback_plan": proposal_data.get("rollback_plan", "")
                }
            )

            # Format pattern details for Discord
            pattern_summary = f"""
**Accuracy**: {accuracy * 100:.1f}%
**Sample Size**: {sample_size} cases
**Edge Cases**: {len(pattern_data.get('edge_cases', []))} identified
"""

            post_to_discord(
                "approvals",
                f"""🧠 **New Pattern Proposal**

**Title**: {proposal_data['title']}
**Priority**: {priority.upper()}

{pattern_summary}

**Impact**: {proposal_data['impact']}

Review in dashboard: http://localhost:8501
""",
                username="Pattern Learning Council"
            )

        except Exception as e:
            post_to_discord(
                "patterns",
                f"⚠️ Error creating proposal: {str(e)}",
                username="Pattern Learning Council"
            )


def run_pattern_learning():
    """Entry point for scheduled task"""
    council = PatternLearningCouncil()
    return council.run()
