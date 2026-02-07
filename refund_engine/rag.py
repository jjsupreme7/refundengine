from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from supabase import create_client

from refund_engine.config import (
    OpenAISettings,
    RAGSettings,
    SupabaseSettings,
    get_openai_settings,
    get_rag_settings,
    get_supabase_settings,
    require_openai_api_key,
    require_supabase_credentials,
)
from refund_engine.openai_client import create_openai_client


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _clip(text: str, max_chars: int) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3] + "..."


@dataclass(frozen=True)
class RAGChunk:
    text: str
    citation: str = ""
    source: str = ""
    similarity: float | None = None
    url: str = ""
    category: str = ""


@dataclass(frozen=True)
class RAGContext:
    legal_chunks: tuple[RAGChunk, ...] = ()
    vendor_chunks: tuple[RAGChunk, ...] = ()
    warnings: tuple[str, ...] = ()

    def is_empty(self) -> bool:
        return not self.legal_chunks and not self.vendor_chunks


def format_rag_context_for_prompt(
    context: RAGContext,
    *,
    max_chunk_chars: int,
) -> str:
    def render(label: str, chunks: tuple[RAGChunk, ...]) -> list[str]:
        if not chunks:
            return [f"{label}: none"]
        lines: list[str] = [f"{label}:"]
        for idx, chunk in enumerate(chunks, start=1):
            header_parts = [f"[{idx}]"]
            if chunk.citation:
                header_parts.append(f"citation={chunk.citation}")
            if chunk.source:
                header_parts.append(f"source={chunk.source}")
            if chunk.category:
                header_parts.append(f"category={chunk.category}")
            if chunk.similarity is not None:
                header_parts.append(f"similarity={chunk.similarity:.4f}")
            if chunk.url:
                header_parts.append(f"url={chunk.url}")
            header = " ".join(header_parts)
            lines.append(header)
            lines.append(f"text={_clip(chunk.text, max_chunk_chars)}")
        return lines

    output: list[str] = []
    output.extend(render("RAG legal context", context.legal_chunks))
    output.append("")
    output.extend(render("RAG vendor context", context.vendor_chunks))
    if context.warnings:
        output.append("")
        output.append(f"RAG warnings: {' | '.join(context.warnings)}")
    return "\n".join(output)


class SupabaseRAGRetriever:
    def __init__(
        self,
        *,
        openai_settings: OpenAISettings,
        supabase_settings: SupabaseSettings,
        rag_settings: RAGSettings,
        openai_client: Any | None = None,
        supabase_client: Any | None = None,
    ):
        self.openai_settings = openai_settings
        self.supabase_settings = require_supabase_credentials(supabase_settings)
        self.rag_settings = rag_settings
        require_openai_api_key(openai_settings)
        self.openai_client = openai_client or create_openai_client(settings=openai_settings)
        self.supabase = supabase_client or create_client(
            self.supabase_settings.url,
            self.supabase_settings.service_role_key,
        )

    @classmethod
    def from_env(cls) -> tuple[SupabaseRAGRetriever | None, str | None]:
        rag_settings = get_rag_settings()
        if not rag_settings.enabled:
            return None, None
        try:
            retriever = cls(
                openai_settings=get_openai_settings(),
                supabase_settings=get_supabase_settings(),
                rag_settings=rag_settings,
            )
            return retriever, None
        except Exception as exc:
            return None, f"RAG disabled due to setup error: {exc}"

    def _embed(self, text: str) -> list[float]:
        response = self.openai_client.embeddings.create(
            model=self.openai_settings.embedding_model,
            input=text,
        )
        if not getattr(response, "data", None):
            raise ValueError("OpenAI embeddings returned no vectors")
        vector = response.data[0].embedding
        if not vector:
            raise ValueError("OpenAI embeddings returned an empty vector")
        return vector

    def _rpc_search(self, rpc_name: str, embedding: list[float], top_k: int) -> tuple[list[dict[str, Any]], str | None]:
        if top_k <= 0:
            return [], None

        threshold = self.rag_settings.similarity_threshold
        payloads = [
            {
                "query_embedding": embedding,
                "match_threshold": threshold,
                "match_count": top_k,
            },
            {
                "query_embedding": embedding,
                "threshold": threshold,
                "count": top_k,
            },
            {
                "query_embedding": embedding,
                "match_threshold": threshold,
                "count": top_k,
            },
            {
                "query_embedding": embedding,
                "threshold": threshold,
                "match_count": top_k,
            },
        ]

        last_error: Exception | None = None
        for payload in payloads:
            try:
                response = self.supabase.rpc(rpc_name, payload).execute()
                data = getattr(response, "data", None)
                if data is None:
                    return [], None
                if isinstance(data, list):
                    return [row for row in data if isinstance(row, dict)], None
                if isinstance(data, dict):
                    return [data], None
                return [], f"Unexpected RPC result type from {rpc_name}: {type(data).__name__}"
            except Exception as exc:
                last_error = exc
        return [], f"{rpc_name} RPC failed: {last_error}"

    def _row_to_chunk(self, row: dict[str, Any]) -> RAGChunk:
        text = (
            _safe_text(row.get("chunk_text"))
            or _safe_text(row.get("content"))
            or _safe_text(row.get("text"))
            or _safe_text(row.get("summary"))
        )
        citation = (
            _safe_text(row.get("citation"))
            or _safe_text(row.get("source_citation"))
            or _safe_text(row.get("reference"))
        )
        source = (
            _safe_text(row.get("document_name"))
            or _safe_text(row.get("source_title"))
            or _safe_text(row.get("title"))
            or _safe_text(row.get("document_id"))
        )
        return RAGChunk(
            text=text,
            citation=citation,
            source=source,
            similarity=_safe_float(row.get("similarity") or row.get("score")),
            url=_safe_text(row.get("source_url") or row.get("url") or row.get("document_url")),
            category=_safe_text(row.get("law_category") or row.get("category")),
        )

    def retrieve(
        self,
        *,
        vendor: str,
        description: str,
        invoice_preview_1: str,
        invoice_preview_2: str,
    ) -> RAGContext:
        warnings: list[str] = []
        legal_chunks: list[RAGChunk] = []
        vendor_chunks: list[RAGChunk] = []

        legal_query_parts = [
            "Washington sales and use tax guidance for 2023-2024 transactions before October 1, 2025.",
            f"Vendor: {vendor}" if vendor else "",
            f"Description: {description}" if description else "",
            f"Invoice evidence: {_clip(invoice_preview_1, 700)}" if invoice_preview_1 else "",
            f"Secondary invoice evidence: {_clip(invoice_preview_2, 500)}" if invoice_preview_2 else "",
        ]
        legal_query = "\n".join(part for part in legal_query_parts if part)

        try:
            legal_embedding = self._embed(legal_query)
            legal_rows, error = self._rpc_search(
                self.rag_settings.legal_rpc,
                legal_embedding,
                self.rag_settings.legal_top_k,
            )
            if error:
                warnings.append(error)
            legal_chunks = [self._row_to_chunk(row) for row in legal_rows if row]
        except Exception as exc:
            warnings.append(f"Legal retrieval failed: {exc}")

        vendor_query = "\n".join(
            part
            for part in [
                f"Vendor profile and products for: {vendor}" if vendor else "",
                f"Transaction description: {description}" if description else "",
            ]
            if part
        )
        if vendor_query and self.rag_settings.vendor_top_k > 0:
            try:
                vendor_embedding = self._embed(vendor_query)
                vendor_rows, error = self._rpc_search(
                    self.rag_settings.vendor_rpc,
                    vendor_embedding,
                    self.rag_settings.vendor_top_k,
                )
                if error:
                    warnings.append(error)
                vendor_chunks = [self._row_to_chunk(row) for row in vendor_rows if row]
            except Exception as exc:
                warnings.append(f"Vendor retrieval failed: {exc}")

        return RAGContext(
            legal_chunks=tuple(legal_chunks),
            vendor_chunks=tuple(vendor_chunks),
            warnings=tuple(warnings),
        )
