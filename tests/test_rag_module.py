from __future__ import annotations

from refund_engine.rag import RAGChunk, RAGContext, SupabaseRAGRetriever, format_rag_context_for_prompt


def test_format_rag_context_for_prompt_renders_chunks_and_warnings():
    context = RAGContext(
        legal_chunks=(
            RAGChunk(
                text="Legal chunk text",
                citation="RCW 82.12.020",
                source="RCW",
                similarity=0.81,
                url="https://app.leg.wa.gov",
                category="rcw",
            ),
        ),
        vendor_chunks=(RAGChunk(text="Vendor chunk text", source="Vendor DB"),),
        warnings=("vendor rpc timeout",),
    )

    rendered = format_rag_context_for_prompt(context, max_chunk_chars=120)

    assert "RAG legal context:" in rendered
    assert "citation=RCW 82.12.020" in rendered
    assert "RAG vendor context:" in rendered
    assert "RAG warnings: vendor rpc timeout" in rendered


def test_from_env_returns_none_when_rag_disabled(monkeypatch):
    monkeypatch.setenv("RAG_ENABLED", "false")
    retriever, warning = SupabaseRAGRetriever.from_env()
    assert retriever is None
    assert warning is None
