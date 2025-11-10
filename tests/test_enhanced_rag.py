"""
Tests for Enhanced RAG Implementation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enhanced_rag import EnhancedRAG


class TestCorrectiveRAG:
    """Test Corrective RAG functionality"""

    @patch("core.enhanced_rag.client")
    def test_assess_chunk_relevance_high_score(self, mock_client, mock_supabase_client):
        """Should return high relevance for relevant chunks"""
        rag = EnhancedRAG(mock_supabase_client)

        # Mock AI response
        mock_client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content='{"score": 0.95, "reason": "Directly addresses MPU for software"}'
                    )
                )
            ]
        )

        chunk = {
            "citation": "WAC 458-20-19402",
            "chunk_text": "Multi-point use software allocation...",
        }

        result = rag._assess_chunk_relevance("software MPU allocation", chunk)

        assert result["score"] == 0.95
        assert "MPU" in result["reason"]

    @patch("core.enhanced_rag.client")
    def test_assess_chunk_relevance_low_score(self, mock_client, mock_supabase_client):
        """Should return low relevance for irrelevant chunks"""
        rag = EnhancedRAG(mock_supabase_client)

        mock_client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content='{"score": 0.2, "reason": "About agriculture, not software"}'
                    )
                )
            ]
        )

        chunk = {
            "citation": "RCW 82.08.02565",
            "chunk_text": "Agricultural equipment exemption...",
        }

        result = rag._assess_chunk_relevance("software MPU allocation", chunk)

        assert result["score"] == 0.2
        assert result["score"] < 0.4

    @patch("core.enhanced_rag.client")
    def test_refine_query_with_ai(self, mock_client, mock_supabase_client):
        """Should convert business terms to tax law terminology"""
        rag = EnhancedRAG(mock_supabase_client)

        mock_client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="digital automated services under RCW 82.04.192"
                    )
                )
            ]
        )

        original_query = "cloud software taxation"
        refined = rag._refine_query_with_ai(original_query)

        assert "digital automated services" in refined.lower()
        assert "rcw" in refined.lower()


class TestReranking:
    """Test AI-powered reranking"""

    @patch("core.enhanced_rag.client")
    def test_rerank_chunks(self, mock_client, mock_supabase_client):
        """Should reorder chunks by legal relevance"""
        rag = EnhancedRAG(mock_supabase_client)

        chunks = [
            {"id": 1, "citation": "WAC 1", "chunk_text": "Irrelevant text"},
            {"id": 2, "citation": "RCW 2", "chunk_text": "Highly relevant text"},
            {"id": 3, "citation": "WAC 3", "chunk_text": "Somewhat relevant"},
        ]

        # Mock reranking to put most relevant first
        mock_client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content='{"ranked_indices": [1, 2, 0]}'  # Reorder: 2, 3, 1
                    )
                )
            ]
        )

        result = rag._rerank_chunks("test query", chunks)

        # Should be reordered
        assert result[0]["id"] == 2  # Most relevant first
        assert result[1]["id"] == 3
        assert result[2]["id"] == 1

    def test_rerank_empty_chunks(self, mock_supabase_client):
        """Should handle empty chunk list"""
        rag = EnhancedRAG(mock_supabase_client)

        result = rag._rerank_chunks("test query", [])

        assert result == []


class TestQueryExpansion:
    """Test query expansion functionality"""

    @patch("core.enhanced_rag.client")
    def test_expand_query(self, mock_client, mock_supabase_client):
        """Should generate multiple query variations"""
        rag = EnhancedRAG(mock_supabase_client)

        mock_client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content='{"queries": ["digital automated services", "cloud software licensing", "remote access software"]}'
                    )
                )
            ]
        )

        original = "cloud software taxation"
        expanded = rag._expand_query(original)

        # Should include original + expansions
        assert len(expanded) >= 2
        assert original in expanded
        assert any("digital" in q.lower() for q in expanded)

    @patch("core.enhanced_rag.client")
    def test_expand_query_handles_errors(self, mock_client, mock_supabase_client):
        """Should fallback to original query on error"""
        rag = EnhancedRAG(mock_supabase_client)

        mock_client.chat.completions.create.side_effect = Exception("API error")

        original = "cloud software taxation"
        expanded = rag._expand_query(original)

        # Should return original query
        assert expanded == [original]


class TestHybridSearch:
    """Test hybrid search (vector + keyword)"""

    def test_deduplicate_by_id(self, mock_supabase_client):
        """Should remove duplicate chunks"""
        rag = EnhancedRAG(mock_supabase_client)

        chunks = [
            {"id": 1, "text": "chunk 1"},
            {"id": 2, "text": "chunk 2"},
            {"id": 1, "text": "chunk 1 duplicate"},
            {"id": 3, "text": "chunk 3"},
        ]

        result = rag._deduplicate_by_id(chunks)

        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 3

    def test_keyword_search_handles_errors(self, mock_supabase_client):
        """Should handle keyword search errors gracefully"""
        rag = EnhancedRAG(mock_supabase_client)

        # Mock error
        mock_supabase_client.table.side_effect = Exception("DB error")

        result = rag._keyword_search("test query", top_k=5)

        assert result == []


class TestCaching:
    """Test embedding caching"""

    @patch("core.enhanced_rag.client")
    def test_embedding_cache(self, mock_client, mock_supabase_client):
        """Should cache embeddings to reduce API calls"""
        rag = EnhancedRAG(mock_supabase_client)

        mock_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )

        text = "test query for caching"

        # First call - should hit API
        embedding1 = rag.get_embedding(text)

        # Second call - should use cache
        embedding2 = rag.get_embedding(text)

        # Should only call API once
        assert mock_client.embeddings.create.call_count == 1

        # Should return same embedding
        assert embedding1 == embedding2


class TestIntegration:
    """Integration tests for enhanced RAG"""

    @patch("core.enhanced_rag.client")
    def test_search_with_correction_workflow(self, mock_client, mock_supabase_client):
        """Should complete full corrective RAG workflow"""
        rag = EnhancedRAG(mock_supabase_client)

        # Mock basic search
        mock_supabase_client.rpc.return_value.execute.return_value = Mock(
            data=[
                {
                    "id": 1,
                    "citation": "WAC 1",
                    "chunk_text": "relevant text",
                    "similarity": 0.8,
                },
                {
                    "id": 2,
                    "citation": "RCW 2",
                    "chunk_text": "less relevant",
                    "similarity": 0.6,
                },
            ]
        )

        # Mock relevance assessment
        mock_client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(content='{"score": 0.9, "reason": "Highly relevant"}')
                )
            ]
        )

        # Mock embedding
        mock_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )

        result = rag.search_with_correction("test query", top_k=2)

        assert len(result) > 0
        assert all("relevance_score" in chunk for chunk in result)
        assert all("validated" in chunk for chunk in result)


# Fixtures
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock = MagicMock()

    # Mock RPC for vector search
    mock.rpc.return_value.execute.return_value = Mock(data=[])

    # Mock table for keyword search
    mock.table.return_value.select.return_value.textSearch.return_value.limit.return_value.execute.return_value = Mock(
        data=[]
    )

    return mock
