#!/usr/bin/env python3
"""
User Feedback & Continuous Learning System

This module handles:
1. Collecting user feedback on RAG responses
2. Learning from feedback patterns
3. Automatically improving the system
4. Managing golden Q&A pairs and preferences
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from supabase import Client

from core.database import get_supabase_client

client = OpenAI()


class FeedbackSystem:
    """Manages user feedback collection and learning"""

    def __init__(self, supabase_client: Client = None):
        self.supabase = supabase_client or get_supabase_client()

    # ==================== FEEDBACK COLLECTION ====================

    def save_feedback(
        self,
        query: str,
        response_text: str,
        feedback_data: Dict,
        session_id: str = None,
        user_id: str = None,
        rag_metadata: Dict = None,
    ) -> str:
        """
        Save user feedback to database

        Args:
            query: Original user query
            response_text: AI-generated response
            feedback_data: Dictionary containing:
                - feedback_type: Type of feedback
                - rating: 1-5 star rating
                - suggested_answer: What user thinks answer should be
                - suggested_structure: How user wants answer formatted
                - suggested_citations: Citations user would prefer
                - feedback_comment: Free-form comment
            session_id: Conversation session ID
            user_id: User identifier (optional)
            rag_metadata: Metadata about RAG process (decision, chunks, confidence)

        Returns:
            Feedback ID (UUID string)
        """
        feedback_record = {
            "query": query,
            "response_text": response_text,
            "session_id": session_id or str(uuid.uuid4()),
            "user_id": user_id,
            **feedback_data,
        }

        # Add RAG metadata if provided
        if rag_metadata:
            feedback_record.update(
                {
                    "decision_action": rag_metadata.get("action"),
                    "retrieved_chunks": rag_metadata.get("results"),
                    "confidence_score": rag_metadata.get("confidence"),
                }
            )

        result = self.supabase.table("user_feedback").insert(feedback_record).execute()

        if result.data:
            feedback_id = result.data[0]["id"]
            print(f"✅ Feedback saved: {feedback_id}")

            # Trigger async learning process
            self._trigger_learning_from_feedback(feedback_id, feedback_record)

            return feedback_id

        return None

    def get_feedback_stats(self, days: int = 7) -> Dict:
        """Get feedback statistics for the last N days"""
        result = self.supabase.rpc("get_feedback_stats", {"days_back": days}).execute()

        if result.data:
            return result.data
        return {}

    # ==================== LEARNING FROM FEEDBACK ====================

    def _trigger_learning_from_feedback(self, feedback_id: str, feedback_data: Dict):
        """
        Analyze feedback and extract learnings
        This runs after each feedback submission
        """
        feedback_type = feedback_data.get("feedback_type")

        # Different learning strategies based on feedback type
        if feedback_type == "better_answer":
            self._learn_better_answer(feedback_id, feedback_data)

        elif feedback_type == "better_citations":
            self._learn_citation_preferences(feedback_id, feedback_data)

        elif feedback_type == "better_structure":
            self._learn_answer_structure(feedback_id, feedback_data)

        elif feedback_type == "thumbs_up" and feedback_data.get("rating", 0) >= 4:
            # High-quality response - add to golden dataset
            self._add_to_golden_dataset(feedback_id, feedback_data)

        # Check if we have enough feedback to create new improvement rules
        self._check_for_patterns()

    def _learn_better_answer(self, feedback_id: str, feedback_data: Dict):
        """
        Learn from user's suggested better answer
        Extract what makes the suggested answer better
        """
        query = feedback_data["query"]
        ai_answer = feedback_data["response_text"]
        suggested_answer = feedback_data.get("suggested_answer")

        if not suggested_answer:
            return

        # Use AI to analyze what's different/better
        analysis = self._analyze_answer_difference(query, ai_answer, suggested_answer)

        if analysis.get("improvement_type"):
            # Store the learning
            improvement = {
                "improvement_type": analysis["improvement_type"],
                "pattern_match": {
                    "query_contains": self._extract_key_terms(query),
                    "query_category": analysis.get("category"),
                },
                "action": {
                    "preferred_approach": analysis.get("preferred_approach"),
                    "example_answer": suggested_answer,
                },
                "source_feedback_ids": [feedback_id],
                "confidence": 0.6,  # Start with medium confidence
            }

            self.supabase.table("learned_improvements").insert(improvement).execute()
            print(f"📚 Learned new improvement: {analysis['improvement_type']}")

    def _learn_citation_preferences(self, feedback_id: str, feedback_data: Dict):
        """Learn which citations users prefer"""
        suggested_citations = feedback_data.get("suggested_citations", [])
        retrieved_chunks = feedback_data.get("retrieved_chunks", [])
        query = feedback_data["query"]

        # Extract topics from query
        topics = self._extract_topics(query)

        # Update citation preferences
        for citation in suggested_citations:
            # Check if citation preference exists
            existing = (
                self.supabase.table("citation_preferences")
                .select("*")
                .eq("citation", citation)
                .execute()
            )

            if existing.data:
                # Update existing
                citation_id = existing.data[0]["id"]
                self.supabase.table("citation_preferences").update(
                    {
                        "times_suggested_by_user": existing.data[0][
                            "times_suggested_by_user"
                        ]
                        + 1,
                        "preferred_for_topics": list(
                            set(
                                existing.data[0].get("preferred_for_topics", [])
                                + topics
                            )
                        ),
                    }
                ).eq("id", citation_id).execute()
            else:
                # Create new
                self.supabase.table("citation_preferences").insert(
                    {
                        "citation": citation,
                        "times_suggested_by_user": 1,
                        "preferred_for_topics": topics,
                    }
                ).execute()

        # Also track citations that were retrieved
        for chunk in retrieved_chunks:
            citation = chunk.get("citation")
            if not citation:
                continue

            existing = (
                self.supabase.table("citation_preferences")
                .select("*")
                .eq("citation", citation)
                .execute()
            )

            # Determine if user liked or disliked this citation
            liked = (
                feedback_data.get("feedback_type") == "thumbs_up"
                or feedback_data.get("rating", 0) >= 4
            )
            disliked = (
                feedback_data.get("feedback_type") == "thumbs_down"
                or feedback_data.get("rating", 0) <= 2
            )

            if existing.data:
                citation_id = existing.data[0]["id"]
                update_data = {}

                if liked:
                    update_data["times_retrieved_and_liked"] = (
                        existing.data[0].get("times_retrieved_and_liked", 0) + 1
                    )
                elif disliked:
                    update_data["times_retrieved_and_disliked"] = (
                        existing.data[0].get("times_retrieved_and_disliked", 0) + 1
                    )

                if update_data:
                    self.supabase.table("citation_preferences").update(update_data).eq(
                        "id", citation_id
                    ).execute()

        print(
            f"📊 Updated citation preferences for {len(suggested_citations)} citations"
        )

    def _learn_answer_structure(self, feedback_id: str, feedback_data: Dict):
        """Learn preferred answer structure/format"""
        suggested_structure = feedback_data.get("suggested_structure")
        query = feedback_data["query"]

        if not suggested_structure:
            return

        # Extract query type (e.g., "Is X taxable?", "How to calculate...?")
        query_type = self._classify_query_type(query)
        category = self._extract_topics(query)

        # Check if we have a template for this query type
        existing = (
            self.supabase.table("answer_templates")
            .select("*")
            .contains("applies_to_query_types", [query_type])
            .execute()
        )

        if existing.data:
            # Update existing template
            template_id = existing.data[0]["id"]
            self.supabase.table("answer_templates").update(
                {
                    "source_feedback_ids": existing.data[0].get(
                        "source_feedback_ids", []
                    )
                    + [feedback_id],
                    "times_used": existing.data[0].get("times_used", 0) + 1,
                }
            ).eq("id", template_id).execute()
        else:
            # Create new template
            self.supabase.table("answer_templates").insert(
                {
                    "template_name": f"Template for {query_type}",
                    "template_structure": suggested_structure,
                    "applies_to_query_types": [query_type],
                    "applies_to_categories": category,
                    "source_feedback_ids": [feedback_id],
                }
            ).execute()

        print(f"📝 Learned answer structure for query type: {query_type}")

    def _add_to_golden_dataset(self, feedback_id: str, feedback_data: Dict):
        """Add high-quality Q&A pair to golden dataset"""
        query = feedback_data["query"]
        answer = feedback_data["response_text"]
        retrieved_chunks = feedback_data.get("retrieved_chunks", [])

        # Extract citations
        citations = [
            chunk.get("citation") for chunk in retrieved_chunks if chunk.get("citation")
        ]

        # Classify query
        category = (
            self._extract_topics(query)[0] if self._extract_topics(query) else None
        )
        difficulty = self._assess_query_complexity(query)

        golden_pair = {
            "question": query,
            "golden_answer": answer,
            "golden_citations": citations,
            "created_from_feedback_id": feedback_id,
            "query_category": category,
            "difficulty": difficulty,
            "is_verified": False,  # Requires manual verification
        }

        self.supabase.table("golden_qa_pairs").insert(golden_pair).execute()
        print(f"⭐ Added to golden dataset: {query[:50]}...")

    def _check_for_patterns(self):
        """
        Check if we have enough feedback to identify patterns
        and create new improvement rules
        """
        # Get recent unresolved feedback
        recent_feedback = (
            self.supabase.table("user_feedback")
            .select("*")
            .eq("is_resolved", False)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        if not recent_feedback.data or len(recent_feedback.data) < 5:
            return

        # Group by query similarity and feedback type
        # (This is a simplified version - you could use embeddings for better clustering)
        patterns = self._identify_feedback_patterns(recent_feedback.data)

        for pattern in patterns:
            if pattern["count"] >= 3:  # At least 3 similar feedback instances
                self._create_improvement_rule(pattern)

    def _identify_feedback_patterns(self, feedback_list: List[Dict]) -> List[Dict]:
        """
        Identify common patterns in feedback
        Returns list of patterns with count and examples
        """
        # Group by feedback type and query similarity
        patterns = {}

        for feedback in feedback_list:
            feedback_type = feedback.get("feedback_type")
            query = feedback.get("query", "")

            # Extract key terms
            key_terms = tuple(sorted(self._extract_key_terms(query)))

            pattern_key = (feedback_type, key_terms)

            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    "feedback_type": feedback_type,
                    "key_terms": key_terms,
                    "examples": [],
                    "count": 0,
                }

            patterns[pattern_key]["examples"].append(feedback)
            patterns[pattern_key]["count"] += 1

        return list(patterns.values())

    def _create_improvement_rule(self, pattern: Dict):
        """Create a new improvement rule from a pattern"""
        # Use AI to synthesize the pattern into an actionable rule
        examples = pattern["examples"][:3]  # Use first 3 examples

        prompt = f"""Based on these user feedback examples, create an improvement rule.

Feedback Type: {pattern['feedback_type']}
Common Terms: {', '.join(pattern['key_terms'])}

Examples:
"""
        for i, ex in enumerate(examples, 1):
            prompt += f"\n{i}. Query: {ex.get('query')}"
            if ex.get("suggested_answer"):
                prompt += f"\n   Suggested: {ex.get('suggested_answer')[:100]}..."

        prompt += """

Create a rule in this format:
{
    "improvement_type": "query_rewrite_rule | citation_preference | answer_template | retrieval_strategy",
    "pattern_match": {"query_contains": ["term1", "term2"], "context": "..."},
    "action": {"description": "what to do", "specific_action": "..."}
}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            rule = json.loads(response.choices[0].message.content)

            # Save to learned_improvements
            improvement = {
                **rule,
                "source_feedback_ids": [ex["id"] for ex in examples],
                "confidence": min(0.5 + (pattern["count"] * 0.1), 0.9),
                "times_applied": 0,
            }

            self.supabase.table("learned_improvements").insert(improvement).execute()
            print(
                f"🎯 Created new improvement rule from pattern with {pattern['count']} instances"
            )

        except Exception as e:
            print(f"Error creating improvement rule: {e}")

    # ==================== APPLYING LEARNINGS ====================

    def get_active_improvements(self, query: str, context: Dict = None) -> List[Dict]:
        """
        Get all active improvement rules that apply to this query

        Args:
            query: User query
            context: Additional context

        Returns:
            List of applicable improvement rules
        """
        # Get all active improvements
        improvements = (
            self.supabase.table("learned_improvements")
            .select("*")
            .eq("is_active", True)
            .order("confidence", desc=True)
            .execute()
        )

        if not improvements.data:
            return []

        # Filter to those that match the query
        applicable = []
        query_lower = query.lower()

        for imp in improvements.data:
            pattern = imp.get("pattern_match", {})

            # Check if pattern matches
            if self._pattern_matches(query_lower, pattern, context):
                applicable.append(imp)

        return applicable

    def get_preferred_citations(self, query: str, top_k: int = 5) -> List[str]:
        """
        Get preferred citations for this query based on learning

        Args:
            query: User query
            top_k: How many citations to return

        Returns:
            List of citation strings ordered by preference
        """
        topics = self._extract_topics(query)

        # Get citations that match these topics
        preferred = (
            self.supabase.table("citation_preferences")
            .select("citation, preference_score")
            .gt("preference_score", 0)
            .order("preference_score", desc=True)
            .execute()
        )

        if not preferred.data:
            return []

        # Filter to relevant topics
        relevant = []
        for cit in preferred.data:
            pref_topics = cit.get("preferred_for_topics", [])
            if any(topic in pref_topics for topic in topics):
                relevant.append(cit["citation"])

        return relevant[:top_k]

    def get_answer_template(self, query: str) -> Optional[str]:
        """Get preferred answer template for this query type"""
        query_type = self._classify_query_type(query)

        template = (
            self.supabase.table("answer_templates")
            .select("*")
            .contains("applies_to_query_types", [query_type])
            .eq("is_active", True)
            .order("times_used", desc=True)
            .limit(1)
            .execute()
        )

        if template.data:
            return template.data[0].get("template_structure")

        return None

    def get_golden_examples(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Get similar golden Q&A pairs for few-shot learning

        Args:
            query: User query
            limit: How many examples to return

        Returns:
            List of golden Q&A pairs
        """
        # Get verified golden pairs
        golden = (
            self.supabase.table("golden_qa_pairs")
            .select("*")
            .eq("is_verified", True)
            .execute()
        )

        if not golden.data:
            return []

        # Simple similarity: match by topics/categories
        query_topics = set(self._extract_topics(query))

        scored = []
        for qa in golden.data:
            qa_topics = set(
                [qa.get("query_category")] if qa.get("query_category") else []
            )
            overlap = len(query_topics & qa_topics)

            if overlap > 0:
                scored.append((overlap, qa))

        # Sort by overlap and return top-k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [qa for _, qa in scored[:limit]]

    # ==================== HELPER METHODS ====================

    def _analyze_answer_difference(
        self, query: str, ai_answer: str, suggested_answer: str
    ) -> Dict:
        """Use AI to analyze what makes the suggested answer better"""
        prompt = f"""Analyze the difference between these two answers.

Query: {query}

AI Answer:
{ai_answer}

User's Suggested Better Answer:
{suggested_answer}

What makes the suggested answer better? Identify the improvement type and approach.

Return JSON:
{{
    "improvement_type": "answer_template | citation_preference | query_rewrite_rule",
    "category": "software_taxation | use_tax | etc",
    "preferred_approach": "description of what makes it better",
    "key_differences": ["difference 1", "difference 2"]
}}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300,
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error analyzing answer difference: {e}")
            return {}

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Simple extraction - could be improved with NLP
        stopwords = {
            "is",
            "are",
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "and",
            "or",
        }
        words = text.lower().split()
        return [w for w in words if w not in stopwords and len(w) > 3]

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics/categories from text"""
        topics = []

        topic_keywords = {
            "software": ["software", "saas", "digital", "cloud", "application"],
            "use_tax": ["use tax", "out-of-state", "remote"],
            "sales_tax": ["sales tax", "retail", "purchase"],
            "exemption": ["exempt", "exemption", "non-taxable"],
            "services": ["service", "consulting", "professional"],
        }

        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)

        return topics if topics else ["general"]

    def _classify_query_type(self, query: str) -> str:
        """Classify query into a type pattern"""
        query_lower = query.lower()

        if query_lower.startswith("is ") or query_lower.startswith("are "):
            return "is_x_taxable"
        elif "how to" in query_lower or "how do" in query_lower:
            return "how_to_question"
        elif "what is" in query_lower or "what are" in query_lower:
            return "definition_question"
        elif "calculate" in query_lower or "computation" in query_lower:
            return "calculation_question"
        elif "when" in query_lower:
            return "when_question"
        else:
            return "general_question"

    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity"""
        words = len(query.split())

        if words < 8:
            return "simple"
        elif words < 20:
            return "medium"
        else:
            return "complex"

    def _pattern_matches(self, query: str, pattern: Dict, context: Dict = None) -> bool:
        """Check if a pattern matches the query"""
        # Check query_contains
        if "query_contains" in pattern:
            required_terms = pattern["query_contains"]
            if not all(term.lower() in query for term in required_terms):
                return False

        # Check context if provided
        if context and "context" in pattern:
            # Add context matching logic here
            pass

        return True
