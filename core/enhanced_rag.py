#!/usr/bin/env python3
"""
Enhanced RAG Implementation with Corrective RAG, Reranking, and Query Expansion

Improvements over basic RAG:
1. Corrective RAG - Validates legal citations are actually relevant
2. Reranking - Improves retrieval accuracy using AI
3. Query Expansion - Better terminology matching
4. Hybrid Search - Combines vector + keyword search
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from supabase import Client

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EnhancedRAG:
    """Enhanced Retrieval Augmented Generation with validation and correction"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.embedding_model = "text-embedding-3-small"
        self.analysis_model = "gpt-4o"
        self.fast_model = "gpt-4o-mini"

        # Cache for embeddings
        self._embedding_cache = {}

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

    def basic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Basic vector search (original implementation)"""
        query_embedding = self.get_embedding(query)

        response = self.supabase.rpc(
            "match_legal_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": top_k,
            },
        ).execute()

        return response.data if response.data else []

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
            print(f"   Validating chunk {i+1}/{len(candidates)}...", end=" ")

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
                    f"⚠️  Medium relevance ({relevance['score']:.2f}), attempting correction..."
                )
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
                f"\n⚠️  Only found {len(validated)} relevant chunks, expanding search..."
            )
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

        prompt = f"""Assess the relevance of this legal text to the query.

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

        prompt = f"""Original query: {original_query}

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

        prompt = f"""Rank these legal text chunks by relevance to the query.

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
            print(f"   Searching with variation {i+1}: {q[:80]}...")
            chunks = self.basic_search(q, top_k=3)

            for chunk in chunks:
                chunk_id = chunk.get("id")
                if chunk_id not in seen_ids:
                    chunk["matched_query"] = q
                    chunk["query_variation_index"] = i
                    all_chunks.append(chunk)
                    seen_ids.add(chunk_id)

            print(
                f"      Found {len(chunks)} chunks ({len([c for c in chunks if c.get('id') not in seen_ids])} unique)"
            )

        # Step 3: Rerank combined results
        print(f"   Reranking {len(all_chunks)} total chunks...")
        reranked = self._rerank_chunks(query, all_chunks)

        final_results = reranked[:top_k]
        print(f"✅ Query expansion complete: {len(final_results)} chunks")
        return final_results

    def _expand_query(self, original_query: str) -> List[str]:
        """Generate multiple variations of query for better retrieval"""

        prompt = f"""Original Query: {original_query}

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
            # Use PostgreSQL text search
            response = (
                self.supabase.table("legal_chunks")
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

    # ==================== BEST METHOD: COMBINES ALL IMPROVEMENTS ====================

    def search_enhanced(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        **RECOMMENDED METHOD**
        Combines all improvements: Corrective RAG + Reranking + Query Expansion + Hybrid Search

        This is the most accurate but also most expensive method.
        Use for critical queries where accuracy is paramount.
        """
        print(f"\n{'='*80}")
        print(f"🚀 ENHANCED RAG SEARCH (All Improvements)")
        print(f"Query: {query}")
        print(f"{'='*80}\n")

        # Step 1: Query expansion to get multiple variations
        expanded_queries = self._expand_query(query)
        print(f"📈 Query Expansion: Generated {len(expanded_queries)} variations\n")

        # Step 2: Hybrid search (vector + keyword) for each variation
        all_candidates = []
        seen_ids = set()

        for i, exp_query in enumerate(expanded_queries):
            print(f"🔀 Hybrid Search for variation {i+1}:")

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

            print(
                f"   Found {len(vector_results)} vector + {len(keyword_results)} keyword chunks\n"
            )

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
        print(f"🔄 Final Reranking...")
        reranked = self._rerank_chunks(query, validated)

        # Step 5: Return top-k
        final_results = reranked[:top_k]

        print(f"\n{'='*80}")
        print(f"✅ ENHANCED RAG COMPLETE")
        print(f"   Final results: {len(final_results)} chunks")
        print(
            f"   Average relevance: {sum(r.get('relevance_score', 0) for r in final_results) / len(final_results):.2f}"
        )
        print(f"{'='*80}\n")

        return final_results

    # ==================== UTILITY METHODS ====================

    def compare_methods(self, query: str, top_k: int = 5) -> Dict:
        """
        Compare all RAG methods side-by-side
        Useful for testing and benchmarking
        """
        print(f"\n{'='*80}")
        print(f"📊 COMPARING ALL RAG METHODS")
        print(f"Query: {query}")
        print(f"{'='*80}\n")

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

        print(f"{'='*80}\n")

        return results
