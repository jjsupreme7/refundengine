#!/usr/bin/env python3
"""
Enhanced RAG Implementation with Corrective RAG, Reranking, and Query Expansion

Improvements over basic RAG:
1. Corrective RAG - Validates legal citations are actually relevant
2. Reranking - Improves retrieval accuracy using AI
3. Query Expansion - Better terminology matching
4. Hybrid Search - Combines vector + keyword search

MIGRATION NOTE: Now uses NEW schema (search_tax_law, tax_law_chunks)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from openai import OpenAI
from supabase import Client

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import centralized database client
from core.database import get_supabase_client  # noqa: E402

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EnhancedRAG:
    """Enhanced Retrieval Augmented Generation with validation and correction"""

    def __init__(
        self,
        supabase_client: Client = None,
        tax_rules_path: str = None,
        enable_dynamic_models: bool = False,
    ):
        """
        Initialize Enhanced RAG

        Args:
            supabase_client: Optional Supabase client. If None, uses centralized client.
            tax_rules_path: Path to tax_rules.json file. If None, uses default location.
            enable_dynamic_models: If True, dynamically select models based on stakes
        """
        self.supabase = supabase_client or get_supabase_client()
        self.embedding_model = "text-embedding-3-small"
        self.analysis_model = "gpt-4o"
        self.fast_model = "gpt-4o-mini"

        # Dynamic model selection
        self.enable_dynamic_models = enable_dynamic_models

        # Cache for embeddings
        self._embedding_cache = {}

        # Load structured tax rules for fast lookup
        self.tax_rules = self._load_tax_rules(tax_rules_path)

        # Decision thresholds (configurable)
        self.confidence_threshold_high = 0.85  # Skip retrieval if confidence > this
        self.confidence_threshold_medium = 0.65  # Use fast retrieval

        # Stakes-based model thresholds (configurable)
        self.stakes_threshold_high = 25000  # Use best model above this
        self.stakes_threshold_medium = 5000  # Use mid-tier model above this

    def _load_tax_rules(self, tax_rules_path: str = None) -> Dict:
        """Load structured tax rules from JSON file"""
        if tax_rules_path is None:
            # Default path
            project_root = Path(__file__).parent.parent
            tax_rules_path = (
                project_root / "knowledge_base/states/washington/tax_rules.json"
            )

        try:
            if Path(tax_rules_path).exists():
                with open(tax_rules_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tax rules: {e}")

        return {}

    # ==================== DYNAMIC MODEL SELECTION ====================

    def calculate_stakes(self, context: Dict) -> int:
        """
        Calculate stakes for model selection decisions

        Priority for base stakes:
        1. If we know potential refund → use that (most accurate)
        2. Else use tax paid (maximum possible refund)
        3. Else use transaction amount * avg tax rate (estimate)
        4. Apply multipliers for complexity and client tier

        Args:
            context: Dictionary with keys:
                - potential_refund: Known refund amount
                - tax_paid: Tax amount paid
                - amount: Transaction amount
                - complexity: simple|medium|complex
                - client_tier: standard|premium|enterprise

        Returns:
            Final stakes value (int)
        """
        # Get base financial amount
        potential_refund = context.get("potential_refund", 0)
        tax_paid = context.get("tax_paid", 0)
        amount = context.get("amount", 0)

        if potential_refund > 0:
            base_stakes = potential_refund
            source = "known refund"
        elif tax_paid > 0:
            base_stakes = tax_paid
            source = "tax paid (max refund)"
        elif amount > 0:
            # Estimate: WA tax rate ~10%
            base_stakes = amount * 0.10
            source = "estimated tax"
        else:
            base_stakes = 0
            source = "unknown"

        # Apply complexity multiplier
        complexity = context.get("complexity", "medium")
        complexity_multipliers = {
            "simple": 1.0,  # No adjustment
            "medium": 1.5,  # 50% more important
            "complex": 2.0,  # 2x more important
        }

        # Apply client tier multiplier
        client_tier = context.get("client_tier", "standard")
        tier_multipliers = {
            "standard": 1.0,
            "premium": 1.5,
            "enterprise": 2.0,
        }

        final_stakes = (
            base_stakes
            * complexity_multipliers.get(complexity, 1.0)
            * tier_multipliers.get(client_tier, 1.0)
        )

        if base_stakes > 0:
            print("\n💰 Stakes Calculation:")
            print(f"   Base: ${base_stakes:,.0f} ({source})")
            print(
                f"   Complexity: {complexity} ({
                    complexity_multipliers.get(
                        complexity, 1.0)}x)")
            print(
                f"   Client tier: {client_tier} ({
                    tier_multipliers.get(
                        client_tier,
                        1.0)}x)")
            print(f"   Final stakes: ${final_stakes:,.0f}")

        return int(final_stakes)

    def select_model(self, task: str, context: Dict) -> Dict:
        """
        Dynamically select which LLM to use based on stakes and task

        Args:
            task: Type of operation (final_answer|reranking|validation|query_expansion)
            context: Context dictionary (same as calculate_stakes)

        Returns:
            Dictionary with:
                - model: Model identifier (e.g., "gpt-4o", "claude-sonnet-4.5")
                - reason: Why this model was selected
                - stakes: Calculated stakes value
                - cost_estimate: Estimated cost per 1k tokens
        """
        # If dynamic models disabled, use defaults
        if not self.enable_dynamic_models:
            if task in ["validation", "query_expansion"]:
                return {
                    "model": self.fast_model,
                    "reason": "Default fast model",
                    "stakes": 0,
                    "cost_estimate": 0.001,
                }
            else:
                return {
                    "model": self.analysis_model,
                    "reason": "Default analysis model",
                    "stakes": 0,
                    "cost_estimate": 0.004,
                }

        # Calculate stakes
        stakes = self.calculate_stakes(context)
        complexity = context.get("complexity", "medium")

        # High stakes thresholds
        if stakes > self.stakes_threshold_high:  # $25k+ at risk
            return {
                "model": "claude-sonnet-4.5",
                "reason": f"${stakes:,.0f} at stake - maximum accuracy required",
                "stakes": stakes,
                "cost_estimate": 0.0075,
            }

        # Medium stakes
        elif stakes > self.stakes_threshold_medium:  # $5k-$25k at risk
            return {
                "model": "gpt-4o",
                "reason": f"${stakes:,.0f} at stake - balanced approach",
                "stakes": stakes,
                "cost_estimate": 0.0042,
            }

        # Low stakes but complex reasoning
        elif complexity == "complex" and task in ["final_answer", "reranking"]:
            return {
                "model": "gpt-4o",
                "reason": "Complex analysis requires capable model",
                "stakes": stakes,
                "cost_estimate": 0.0042,
            }

        # Fast operations - always use cheap model
        elif task in ["validation", "query_expansion"]:
            return {
                "model": "gpt-4o-mini",
                "reason": "Simple task - cost-optimized",
                "stakes": stakes,
                "cost_estimate": 0.001,
            }

        # Low stakes default
        else:
            return {
                "model": "gpt-4o-mini",
                "reason": f"${stakes:,.0f} at stake - cost-optimized",
                "stakes": stakes,
                "cost_estimate": 0.001,
            }

    # ==================== AGENTIC RAG: DECISION LAYER ====================

    def search_with_decision(
        self,
        query: str,
        context: Dict = None,
        top_k: int = 5,
        force_retrieval: bool = False,
    ) -> Dict:
        """
        🤖 AGENTIC RAG: Decide whether/how to retrieve information

        This method implements intelligent decision-making:
        1. Check if we already have high-confidence cached knowledge
        2. Check if structured rules (tax_rules.json) are sufficient
        3. Decide which retrieval strategy to use based on complexity
        4. Only perform expensive retrieval when necessary

        Args:
            query: The search query
            context: Optional context dictionary with keys:
                - vendor: Vendor name (e.g., "Microsoft")
                - product: Product description
                - product_type: Product category (e.g., "saas_subscription")
                - amount: Transaction amount
                - tax_paid: Tax amount paid
                - prior_analysis: Previous analysis results with confidence
            top_k: Number of results to return
            force_retrieval: If True, skip decision logic and always retrieve

        Returns:
            Dictionary with:
                - action: Decision taken (USE_CACHED | USE_RULES | RETRIEVE_SIMPLE | RETRIEVE_ENHANCED)  # noqa: E501
                - reasoning: Why this decision was made
                - results: The actual search results/cached data
                - confidence: Confidence score (0-1)
                - cost_saved: Estimated API cost saved by decision

        Example:
            >>> context = {
            ...     "vendor": "Microsoft",
            ...     "product": "Azure",
            ...     "product_type": "iaas_paas",
            ...     "prior_analysis": {"confidence_score": 0.92, "refund_eligible": True}  # noqa: E501
            ... }
            >>> result = rag.search_with_decision("Is Azure taxable?", context)
            >>> print(result['action'])  # "USE_CACHED" (confidence 0.92 > 0.85)
        """
        context = context or {}

        print(f"\n{'=' * 80}")
        print("🤖 AGENTIC RAG: Making Retrieval Decision")
        print(f"Query: {query}")
        if context:
            print(f"Context: {', '.join(
                [f'{k}={v}' for k, v in list(context.items())[:3]])}")
        print(f"{'=' * 80}\n")

        # Skip decision if forced retrieval
        if force_retrieval:
            print("⚠️  Force retrieval enabled - using enhanced search\n")
            results = self.search_enhanced(query, top_k)
            return {
                "action": "RETRIEVE_ENHANCED",
                "reasoning": "Forced retrieval requested",
                "results": results,
                "confidence": 0.8,
                "cost_saved": 0.0,
            }

        # Step 1: Make decision
        decision = self._make_retrieval_decision(query, context)

        print(f"📊 Decision: {decision['action']}")
        print(f"   Reasoning: {decision['reasoning']}")
        print(f"   Estimated cost saved: ${decision['cost_saved']:.4f}\n")

        # Step 2: Execute based on decision
        if decision["action"] == "USE_CACHED":
            return decision

        elif decision["action"] == "USE_RULES":
            return decision

        elif decision["action"] == "RETRIEVE_SIMPLE":
            print("🔍 Using fast retrieval (basic search)...")
            # Extract filters from context if provided
            filters = context.get("filters") if context else None
            results = self.basic_search(query, top_k, filters=filters)
            decision["results"] = results
            decision["confidence"] = 0.7  # Medium confidence for simple retrieval
            return decision

        elif decision["action"] == "RETRIEVE_ENHANCED":
            print("🚀 Using enhanced retrieval (all improvements)...")
            # Note: search_enhanced doesn't support filters yet, but basic search is
            # called within it
            results = self.search_enhanced(query, top_k)
            decision["results"] = results
            decision["confidence"] = 0.9  # High confidence for enhanced retrieval
            return decision

        else:
            # Fallback
            print("⚠️  Unknown decision, defaulting to enhanced search...")
            results = self.search_enhanced(query, top_k)
            return {
                "action": "RETRIEVE_ENHANCED",
                "reasoning": "Fallback to enhanced search",
                "results": results,
                "confidence": 0.8,
                "cost_saved": 0.0,
            }

    def _make_retrieval_decision(self, query: str, context: Dict) -> Dict:
        """
        Core decision logic: Determine if/how to retrieve

        Decision tree:
        1. High-confidence prior analysis (>0.85)? → USE_CACHED
        2. Product type has structured rules? → USE_RULES
        3. Simple query (single fact)? → RETRIEVE_SIMPLE
        4. Complex query (multi-step reasoning)? → RETRIEVE_ENHANCED
        """

        # Check for high-confidence cached results
        prior_analysis = context.get("prior_analysis", {})
        if prior_analysis and isinstance(prior_analysis, dict):
            confidence = prior_analysis.get("confidence_score", 0)

            if confidence >= self.confidence_threshold_high:
                print(
                    f"✅ High-confidence cached result found (confidence: {confidence:.2f})"  # noqa: E501
                )
                return {
                    "action": "USE_CACHED",
                    "reasoning": f"Prior analysis has high confidence ({confidence:.2f} ≥ {self.confidence_threshold_high})",  # noqa: E501
                    "results": [{"source": "cached", "data": prior_analysis}],
                    "confidence": confidence,
                    "cost_saved": 0.015,  # Saved: ~5 embeddings + 1 LLM call
                }

        # Check if structured rules are sufficient
        product_type = context.get("product_type", "")
        if product_type and self._has_structured_rule(product_type):
            rule = self._get_structured_rule(product_type, query)
            if rule:
                print(f"✅ Structured rule found for product type: {product_type}")
                return {
                    "action": "USE_RULES",
                    "reasoning": f"Structured tax rules available for {product_type}",
                    "results": [{"source": "structured_rules", "data": rule}],
                    "confidence": 0.8,
                    "cost_saved": 0.012,  # Saved: embeddings + retrieval + validation
                }

        # Check query complexity to decide retrieval strategy
        complexity = self._assess_query_complexity(query, context)

        if complexity == "simple":
            print("📌 Simple query detected - using fast retrieval")
            return {
                "action": "RETRIEVE_SIMPLE",
                "reasoning": "Query is straightforward, basic search sufficient",
                "results": [],  # Will be filled by search_with_decision
                "confidence": 0.7,
                "cost_saved": 0.008,  # Saved: validation + reranking steps
            }
        else:
            print("🔬 Complex query detected - using enhanced retrieval")
            return {
                "action": "RETRIEVE_ENHANCED",
                "reasoning": "Query requires comprehensive analysis",
                "results": [],  # Will be filled by search_with_decision
                "confidence": 0.9,
                "cost_saved": 0.0,  # No savings, but highest accuracy
            }

    def _has_structured_rule(self, product_type: str) -> bool:
        """Check if we have structured rules for this product type"""
        if not self.tax_rules or "product_type_rules" not in self.tax_rules:
            return False
        return product_type in self.tax_rules["product_type_rules"]

    def _get_structured_rule(self, product_type: str, query: str) -> Optional[Dict]:
        """Get structured rule for product type, filtered by query relevance"""
        if not self._has_structured_rule(product_type):
            return None

        rule = self.tax_rules["product_type_rules"][product_type]

        # Build a comprehensive response from structured rules
        return {
            "product_type": product_type,
            "taxable": rule.get("taxable", True),
            "tax_classification": rule.get("tax_classification", ""),
            "legal_basis": rule.get("legal_basis", []),
            "description": rule.get("description", ""),
            "exemptions": rule.get("exemptions", []),
            "refund_scenarios": rule.get("refund_scenarios", []),
            "rule_text": json.dumps(rule, indent=2),
        }

    def _assess_query_complexity(self, query: str, context: Dict) -> str:
        """
        Determine if query is simple or complex

        Simple queries: Single-fact lookups (e.g., "Is X taxable?")
        Complex queries: Multi-step reasoning, edge cases, calculation needed
        """
        # Keywords indicating complexity
        complex_indicators = [
            "calculate",
            "compute",
            "allocate",
            "apportion",
            "multi-state",
            "multi-point",
            "distributed",
            "primarily human",
            "edge case",
            "exception",
            "how much",
            "refund amount",
            "methodology",
            "bundled",
            "combined",
            "mixed",
        ]

        query_lower = query.lower()

        # Check for complex indicators
        if any(indicator in query_lower for indicator in complex_indicators):
            return "complex"

        # Check context complexity
        if context.get("amount", 0) > 0 and "calculate" in query_lower:
            return "complex"

        # Check if asking about multiple things
        if " and " in query_lower or "," in query:
            and_count = query_lower.count(" and ")
            comma_count = query.count(",")
            if and_count + comma_count > 2:
                return "complex"

        # Default to simple
        return "simple"

    # ==================== CORE METHODS ====================

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with caching"""
        # Simple cache key
        cache_key = text[:100]  # Use first 100 chars as key

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        response = client.embeddings.create(input=text, model=self.embedding_model)

        embedding = response.data[0].embedding
        self._embedding_cache[cache_key] = embedding
        return embedding

    def basic_search(
        self, query: str, top_k: int = 5, filters: Dict = None
    ) -> List[Dict]:
        """Basic vector search using new schema with optional filters"""
        query_embedding = self.get_embedding(query)

        # Build RPC parameters - only include non-None values to avoid function
        # overloading issues
        rpc_params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.3,  # Lowered from 0.5 to catch more relevant results
            "match_count": top_k,
        }

        # Apply filters if provided (only add non-None filters)
        if filters:
            if filters.get("law_category"):
                rpc_params["law_category_filter"] = filters["law_category"]
            if filters.get("tax_types"):
                rpc_params["tax_types_filter"] = filters["tax_types"]
            if filters.get("industries"):
                rpc_params["industries_filter"] = filters["industries"]

        try:
            response = self.supabase.rpc("search_tax_law", rpc_params).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"⚠️  Error in basic_search: {e}")
            # Fallback: try with minimal params only
            try:
                minimal_params = {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.3,
                    "match_count": top_k,
                }
                response = self.supabase.rpc("search_tax_law", minimal_params).execute()
                return response.data if response.data else []
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")
                return []

    # ==================== IMPROVEMENT 1: CORRECTIVE RAG ====================

    def search_with_correction(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Corrective RAG: Validates and corrects retrieved chunks
        Ensures legal citations are actually relevant
        """
        print(f"🔍 Corrective RAG Search: {query[:100]}...")

        # Step 1: Initial retrieval (get more candidates)
        candidates = self.basic_search(query, top_k=top_k * 2)

        if not candidates:
            print("⚠️  No candidates found in initial search")
            return []

        # Step 2: Validate each chunk
        validated = []
        for i, chunk in enumerate(candidates):
            print(f"   Validating chunk {i + 1}/{len(candidates)}...", end=" ")

            relevance = self._assess_chunk_relevance(query, chunk)

            if relevance["score"] > 0.7:
                # High relevance - use as-is
                chunk["relevance_score"] = relevance["score"]
                chunk["relevance_reason"] = relevance["reason"]
                chunk["validated"] = True
                validated.append(chunk)
                print(f"✅ High relevance ({relevance['score']:.2f})")

            elif relevance["score"] > 0.4:
                # Medium relevance - try to improve
                print(
                    f"⚠️  Medium relevance ({
                        relevance['score']:.2f}), attempting correction...")
                corrected = self._attempt_correction(query, chunk, relevance["reason"])
                if corrected:
                    validated.append(corrected)
                    print("   ✅ Corrected")
                else:
                    print("   ❌ Could not correct")
            else:
                print(f"❌ Low relevance ({relevance['score']:.2f}), discarding")

        # Step 3: If not enough validated chunks, refine query and search again
        if len(validated) < 3:
            print(
                f"\n⚠️  Only found {
                    len(validated)} relevant chunks, expanding search...")
            refined_query = self._refine_query_with_ai(query)
            print(f"   Refined query: {refined_query[:100]}...")

            additional = self.basic_search(refined_query, top_k=3)

            for chunk in additional:
                if chunk.get("id") not in [v.get("id") for v in validated]:
                    chunk["relevance_score"] = 0.6  # Medium score for refined search
                    chunk["validated"] = True
                    chunk["from_refined_query"] = True
                    validated.append(chunk)

            print(f"   ✅ Added {len(additional)} chunks from refined search")

        # Step 4: Sort by relevance and return top-k
        validated.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        final_results = validated[:top_k]

        print(f"\n✅ Corrective RAG complete: {len(final_results)} validated chunks")
        return final_results

    def _assess_chunk_relevance(self, query: str, chunk: Dict) -> Dict:
        """Use AI to assess if chunk is truly relevant"""

        prompt = """Assess the relevance of this legal text to the query.

Query: {query}

Legal Text:
Citation: {chunk.get('citation', 'Unknown')}
{chunk.get('chunk_text', '')[:800]}

Rate relevance on 0.0-1.0 scale. Consider:
1. Does this legal text apply to the query's scenario?
2. Is the citation current and applicable to Washington State?
3. Does it provide actionable guidance for the specific question?

Return JSON:
{{
    "score": 0.85,  # 0.0-1.0
    "reason": "This RCW directly addresses software licensing taxation"
}}
"""

        try:
            response = client.chat.completions.create(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=150,
            )

            result = json.loads(response.choices[0].message.content)
            return {
                "score": float(result.get("score", 0.5)),
                "reason": result.get("reason", "No reason provided"),
            }
        except Exception as e:
            print(f"Error assessing relevance: {e}")
            return {"score": 0.5, "reason": "Error in assessment"}

    def _attempt_correction(
        self, query: str, chunk: Dict, issue: str
    ) -> Optional[Dict]:
        """Try to correct/improve a medium-relevance chunk"""

        # Search for related chunks with more specific query
        related_query = f"{query} {chunk.get('citation', '')}"
        related = self.basic_search(related_query, top_k=2)

        if related:
            # Return the most relevant related chunk
            best = max(related, key=lambda x: x.get("similarity", 0))
            best["relevance_score"] = 0.6
            best["corrected"] = True
            best["correction_reason"] = issue
            return best

        return None

    def _refine_query_with_ai(self, original_query: str) -> str:
        """Generate a refined query using AI with tax law terminology"""

        prompt = """Original query: {original_query}

The search didn't find enough relevant results.
Rewrite this query using Washington State tax law terminology.

Common conversions:
- "cloud software" → "digital automated services under RCW 82.04.192"
- "SaaS" → "software as a service"
- "consulting" → "professional services under WAC 458-20-15503"
- "custom software" → "custom software development services"
- "maintenance" → "maintenance and repair services"
- "multi-state" → "multi-point use under WAC 458-20-19402"

Return only the refined query, no explanation.
"""

        try:
            response = client.chat.completions.create(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
            )
            refined = response.choices[0].message.content.strip()
            return refined
        except Exception as e:
            print(f"Error refining query: {e}")
            return original_query

    # ==================== IMPROVEMENT 2: RERANKING ====================

    def search_with_reranking(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search with AI-powered reranking
        Better legal relevance than pure vector similarity
        """
        print(f"🔄 Reranking Search: {query[:100]}...")

        # Step 1: Get initial candidates (retrieve more than needed)
        candidates = self.basic_search(query, top_k=top_k * 3)

        if not candidates:
            return []

        # Step 2: Rerank using AI
        reranked = self._rerank_chunks(query, candidates)

        # Step 3: Return top-k after reranking
        final_results = reranked[:top_k]
        print(f"✅ Reranking complete: {len(final_results)} chunks")
        return final_results

    def _rerank_chunks(self, query: str, chunks: List[Dict]) -> List[Dict]:
        """Rerank chunks using AI understanding of legal context"""

        if not chunks:
            return []

        # Build prompt with all chunks
        chunks_text = ""
        for i, chunk in enumerate(chunks):
            chunks_text += f"\n[{i}] Citation: {chunk.get('citation', 'N/A')}\n"
            chunks_text += f"Preview: {chunk.get('chunk_text', '')[:300]}...\n"

        prompt = """Rank these legal text chunks by relevance to the query.

Query: {query}

Retrieved Legal Chunks:
{chunks_text}

Rank these chunks by relevance. Consider:
1. Legal applicability to the query
2. Specificity to the scenario
3. Clarity and actionability

Return JSON array of indices in order of MOST to LEAST relevant:
{{
    "ranked_indices": [2, 0, 5, 1, 3, ...]
}}
"""

        try:
            response = client.chat.completions.create(
                model=self.analysis_model,  # Use better model for reranking
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=200,
            )

            result = json.loads(response.choices[0].message.content)
            ranked_indices = result.get("ranked_indices", list(range(len(chunks))))

            # Reorder chunks based on ranking
            reranked = []
            for i in ranked_indices:
                if i < len(chunks):
                    chunk = chunks[i]
                    chunk["reranked_position"] = len(reranked) + 1
                    chunk["original_position"] = i + 1
                    reranked.append(chunk)

            return reranked
        except Exception as e:
            print(f"Error reranking chunks: {e}")
            # Fallback to original order
            return chunks

    # ==================== IMPROVEMENT 3: QUERY EXPANSION ====================

    def search_with_expansion(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search using multiple query variations
        Better terminology matching
        """
        print(f"📈 Query Expansion Search: {query[:100]}...")

        # Step 1: Expand query into multiple variations
        queries = self._expand_query(query)
        print(f"   Generated {len(queries)} query variations")

        # Step 2: Search with each query variation
        all_chunks = []
        seen_ids = set()

        for i, q in enumerate(queries):
            print(f"   Searching with variation {i + 1}: {q[:80]}...")
            chunks = self.basic_search(q, top_k=3)

            for chunk in chunks:
                chunk_id = chunk.get("id")
                if chunk_id not in seen_ids:
                    chunk["matched_query"] = q
                    chunk["query_variation_index"] = i
                    all_chunks.append(chunk)
                    seen_ids.add(chunk_id)

            print(f"      Found {len(chunks)} chunks ({
                len([c for c in chunks if c.get('id') not in seen_ids])} unique)")

        # Step 3: Rerank combined results
        print(f"   Reranking {len(all_chunks)} total chunks...")
        reranked = self._rerank_chunks(query, all_chunks)

        final_results = reranked[:top_k]
        print(f"✅ Query expansion complete: {len(final_results)} chunks")
        return final_results

    def _expand_query(self, original_query: str) -> List[str]:
        """Generate multiple variations of query for better retrieval"""

        prompt = """Original Query: {original_query}

Generate 3 alternative phrasings using Washington State tax terminology:
1. Using legal/technical terms (RCW/WAC citations, legal definitions)
2. Using common business terms (how businesses describe it)
3. Using tax authority phrasing (how DOR would describe it)

Return JSON:
{{
    "queries": [
        "digital automated services taxation under RCW 82.04.192",
        "cloud software licensing",
        "remote access software tax treatment"
    ]
}}
"""

        try:
            response = client.chat.completions.create(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=200,
            )

            result = json.loads(response.choices[0].message.content)
            expanded_queries = result.get("queries", [])

            # Always include original query first
            return [original_query] + expanded_queries
        except Exception as e:
            print(f"Error expanding query: {e}")
            return [original_query]

    # ==================== IMPROVEMENT 4: HYBRID SEARCH ====================

    def search_hybrid(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Hybrid search: Combines vector search + keyword search
        Better for exact matches (like finding specific RCW numbers)
        """
        print(f"🔀 Hybrid Search: {query[:100]}...")

        # Step 1: Vector search (semantic similarity)
        vector_results = self.basic_search(query, top_k=top_k)
        print(f"   Vector search: {len(vector_results)} chunks")

        # Step 2: Keyword search (exact matches)
        keyword_results = self._keyword_search(query, top_k=top_k)
        print(f"   Keyword search: {len(keyword_results)} chunks")

        # Step 3: Combine and deduplicate
        all_results = vector_results + keyword_results
        unique_results = self._deduplicate_by_id(all_results)
        print(f"   Combined: {len(unique_results)} unique chunks")

        # Step 4: Rerank combined results
        reranked = self._rerank_chunks(query, unique_results)

        final_results = reranked[:top_k]
        print(f"✅ Hybrid search complete: {len(final_results)} chunks")
        return final_results

    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Keyword-based search using PostgreSQL full-text search"""
        try:
            # Use PostgreSQL text search (updated to new schema)
            response = (
                self.supabase.table("tax_law_chunks")  # Updated to new schema table
                .select("*")
                .textSearch("chunk_text", query)
                .limit(top_k)
                .execute()
            )

            results = response.data if response.data else []

            # Mark as keyword search results
            for r in results:
                r["search_type"] = "keyword"

            return results
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []

    def _deduplicate_by_id(self, chunks: List[Dict]) -> List[Dict]:
        """Remove duplicate chunks based on ID"""
        seen_ids = set()
        unique = []

        for chunk in chunks:
            chunk_id = chunk.get("id")
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique.append(chunk)

        return unique

    # ==================== VENDOR BACKGROUND RETRIEVAL ====================

    def get_vendor_background(self, vendor_name: str) -> Optional[Dict]:
        """
        Retrieve vendor background information from knowledge_documents.

        This provides crucial context for analysis:
        - Industry and business model
        - Primary products/services
        - Known tax patterns
        - Confidence score from previous research

        Args:
            vendor_name: Vendor name to search for

        Returns:
            Dictionary with vendor background or None if not found
        """
        if not vendor_name:
            return None

        try:
            # Search for vendor background in knowledge_documents
            result = (
                self.supabase.table("knowledge_documents")
                .select("*")
                .eq("document_type", "vendor_background")
                .ilike("vendor_name", f"%{vendor_name.split()[0]}%")
                .limit(1)
                .execute()
            )

            if result.data and len(result.data) > 0:
                vendor_data = result.data[0]
                print(f"\n✅ Found vendor background for {vendor_name}")
                print(f"   Industry: {vendor_data.get('industry')}")
                print(f"   Business Model: {vendor_data.get('business_model')}")
                print(f"   Products: {vendor_data.get('primary_products', [])[:2]}")

                return {
                    "vendor_name": vendor_data.get("vendor_name"),
                    "industry": vendor_data.get("industry"),
                    "business_model": vendor_data.get("business_model"),
                    "primary_products": vendor_data.get("primary_products", []),
                    "confidence_score": vendor_data.get("confidence_score", 0),
                    "title": vendor_data.get("title"),
                }
            else:
                print(f"\n⚠️  No vendor background found for {vendor_name}")
                return None

        except Exception as e:
            print(f"Error retrieving vendor background: {e}")
            return None

    # ==================== BEST METHOD: COMBINES ALL IMPROVEMENTS ====================

    def search_enhanced(
        self, query: str, top_k: int = 5, vendor_name: str = None
    ) -> List[Dict]:
        """
        **RECOMMENDED METHOD**
        Combines all improvements: Corrective RAG + Reranking + Query Expansion + Hybrid Search  # noqa: E501

        This is the most accurate but also most expensive method.
        Use for critical queries where accuracy is paramount.
        """
        print(f"\n{'=' * 80}")
        print("🚀 ENHANCED RAG SEARCH (All Improvements)")
        print(f"Query: {query}")
        if vendor_name:
            print(f"Vendor: {vendor_name}")
        print(f"{'=' * 80}\n")

        # Step 0: Retrieve vendor background if provided
        vendor_context = None
        if vendor_name:
            vendor_context = self.get_vendor_background(vendor_name)

        # Step 1: Query expansion to get multiple variations
        expanded_queries = self._expand_query(query)
        print(f"📈 Query Expansion: Generated {len(expanded_queries)} variations\n")

        # Step 2: Hybrid search (vector + keyword) for each variation
        all_candidates = []
        seen_ids = set()

        for i, exp_query in enumerate(expanded_queries):
            print(f"🔀 Hybrid Search for variation {i + 1}:")

            # Vector search
            vector_results = self.basic_search(exp_query, top_k=3)

            # Keyword search
            keyword_results = self._keyword_search(exp_query, top_k=3)

            # Combine
            for chunk in vector_results + keyword_results:
                chunk_id = chunk.get("id")
                if chunk_id not in seen_ids:
                    chunk["matched_query_variation"] = i
                    all_candidates.append(chunk)
                    seen_ids.add(chunk_id)

            print(f"   Found {len(vector_results)
                              } vector + {len(keyword_results)} keyword chunks\n")

        print(f"📊 Total candidates: {len(all_candidates)}\n")

        # Step 3: Corrective validation
        print(f"🔍 Corrective RAG: Validating {len(all_candidates)} candidates...")
        validated = []

        for i, chunk in enumerate(all_candidates[:15]):  # Validate top 15 to save cost
            relevance = self._assess_chunk_relevance(query, chunk)

            if relevance["score"] > 0.4:  # Keep medium+ relevance
                chunk["relevance_score"] = relevance["score"]
                chunk["relevance_reason"] = relevance["reason"]
                validated.append(chunk)

        print(f"   ✅ Validated: {len(validated)} chunks passed threshold\n")

        # Step 4: Final reranking
        print("🔄 Final Reranking...")
        reranked = self._rerank_chunks(query, validated)

        # Step 5: Return top-k with vendor context
        final_results = reranked[:top_k]

        # Add vendor background to results
        if vendor_context:
            for result in final_results:
                result["vendor_background"] = vendor_context

        print(f"\n{'=' * 80}")
        print("✅ ENHANCED RAG COMPLETE")
        print(f"   Final results: {len(final_results)} chunks")
        if final_results:
            print(f"   Average relevance: {
                sum(r.get('relevance_score', 0) for r in final_results) / len(final_results):.2f}")  # noqa: E501
        if vendor_context:
            print("   ✅ Vendor background included")
        print(f"{'=' * 80}\n")

        return final_results

    # ==================== UTILITY METHODS ====================

    def compare_methods(self, query: str, top_k: int = 5) -> Dict:
        """
        Compare all RAG methods side-by-side
        Useful for testing and benchmarking
        """
        print(f"\n{'=' * 80}")
        print("📊 COMPARING ALL RAG METHODS")
        print(f"Query: {query}")
        print(f"{'=' * 80}\n")

        results = {}

        # Method 1: Basic
        print("1️⃣  Basic Vector Search")
        results["basic"] = self.basic_search(query, top_k)
        print(f"   Results: {len(results['basic'])}\n")

        # Method 2: Corrective
        print("2️⃣  Corrective RAG")
        results["corrective"] = self.search_with_correction(query, top_k)
        print(f"   Results: {len(results['corrective'])}\n")

        # Method 3: Reranking
        print("3️⃣  With Reranking")
        results["reranking"] = self.search_with_reranking(query, top_k)
        print(f"   Results: {len(results['reranking'])}\n")

        # Method 4: Query Expansion
        print("4️⃣  Query Expansion")
        results["expansion"] = self.search_with_expansion(query, top_k)
        print(f"   Results: {len(results['expansion'])}\n")

        # Method 5: Hybrid
        print("5️⃣  Hybrid Search")
        results["hybrid"] = self.search_hybrid(query, top_k)
        print(f"   Results: {len(results['hybrid'])}\n")

        # Method 6: Enhanced (All)
        print("6️⃣  Enhanced (All Improvements)")
        results["enhanced"] = self.search_enhanced(query, top_k)
        print(f"   Results: {len(results['enhanced'])}\n")

        print(f"{'=' * 80}\n")

        return results
