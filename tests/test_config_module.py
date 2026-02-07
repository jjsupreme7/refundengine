from __future__ import annotations

from refund_engine.config import get_rag_settings


def test_get_rag_settings_reads_overrides(monkeypatch):
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_LEGAL_TOP_K", "7")
    monkeypatch.setenv("RAG_VENDOR_TOP_K", "2")
    monkeypatch.setenv("RAG_SIMILARITY_THRESHOLD", "0.45")
    monkeypatch.setenv("RAG_MAX_CHUNK_CHARS", "600")
    monkeypatch.setenv("RAG_LEGAL_RPC", "search_tax_law")
    monkeypatch.setenv("RAG_VENDOR_RPC", "search_vendor_background")

    settings = get_rag_settings()

    assert settings.enabled is True
    assert settings.legal_top_k == 7
    assert settings.vendor_top_k == 2
    assert settings.similarity_threshold == 0.45
    assert settings.max_chunk_chars == 600
