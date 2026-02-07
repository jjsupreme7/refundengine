from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

ReasoningEffort = Literal["low", "medium", "high"]
TextVerbosity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str | None
    base_url: str | None
    model_analysis: str
    model_fast: str
    model_pro: str
    embedding_model: str
    reasoning_effort: ReasoningEffort
    text_verbosity: TextVerbosity


@dataclass(frozen=True)
class SupabaseSettings:
    url: str | None
    service_role_key: str | None


@dataclass(frozen=True)
class RAGSettings:
    enabled: bool
    legal_rpc: str
    vendor_rpc: str
    similarity_threshold: float
    legal_top_k: int
    vendor_top_k: int
    max_chunk_chars: int


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _coerce_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Expected boolean-like env value, got {value!r}")


def _coerce_int(
    name: str,
    value: str | None,
    *,
    default: int,
    min_value: int,
    max_value: int,
) -> int:
    if value is None:
        return default
    try:
        parsed = int(value.strip())
    except Exception as exc:
        raise ValueError(f"{name} must be an integer (got {value!r})") from exc
    if parsed < min_value or parsed > max_value:
        raise ValueError(f"{name} must be between {min_value} and {max_value} (got {parsed})")
    return parsed


def _coerce_float(
    name: str,
    value: str | None,
    *,
    default: float,
    min_value: float,
    max_value: float,
) -> float:
    if value is None:
        return default
    try:
        parsed = float(value.strip())
    except Exception as exc:
        raise ValueError(f"{name} must be a float (got {value!r})") from exc
    if parsed < min_value or parsed > max_value:
        raise ValueError(f"{name} must be between {min_value} and {max_value} (got {parsed})")
    return parsed


def _coerce_reasoning_effort(value: str | None) -> ReasoningEffort:
    if value is None:
        return "medium"
    value = value.strip().lower()
    if value not in {"low", "medium", "high"}:
        raise ValueError(
            f"OPENAI_REASONING_EFFORT must be low|medium|high (got {value!r})"
        )
    return value  # type: ignore[return-value]


def _coerce_text_verbosity(value: str | None) -> TextVerbosity:
    if value is None:
        return "medium"
    value = value.strip().lower()
    if value not in {"low", "medium", "high"}:
        raise ValueError(f"OPENAI_TEXT_VERBOSITY must be low|medium|high (got {value!r})")
    return value  # type: ignore[return-value]


def get_openai_settings() -> OpenAISettings:
    """
    Load OpenAI settings from environment variables.

    Required for network calls:
      - OPENAI_API_KEY
    Optional:
      - OPENAI_BASE_URL
      - OPENAI_MODEL_ANALYSIS (default: gpt-5.2)
      - OPENAI_MODEL_FAST (default: gpt-5.2-mini)
      - OPENAI_MODEL_PRO (default: gpt-5.2-pro)
      - OPENAI_EMBEDDING_MODEL (default: text-embedding-3-small)
      - OPENAI_REASONING_EFFORT (default: medium)
      - OPENAI_TEXT_VERBOSITY (default: medium)
    """
    return OpenAISettings(
        api_key=_get_env("OPENAI_API_KEY"),
        base_url=_get_env("OPENAI_BASE_URL"),
        model_analysis=_get_env("OPENAI_MODEL_ANALYSIS", "gpt-5.2") or "gpt-5.2",
        model_fast=_get_env("OPENAI_MODEL_FAST", "gpt-5.2-mini") or "gpt-5.2-mini",
        model_pro=_get_env("OPENAI_MODEL_PRO", "gpt-5.2-pro") or "gpt-5.2-pro",
        embedding_model=_get_env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        or "text-embedding-3-small",
        reasoning_effort=_coerce_reasoning_effort(_get_env("OPENAI_REASONING_EFFORT")),
        text_verbosity=_coerce_text_verbosity(_get_env("OPENAI_TEXT_VERBOSITY")),
    )


def get_supabase_settings() -> SupabaseSettings:
    return SupabaseSettings(
        url=_get_env("SUPABASE_URL"),
        service_role_key=_get_env("SUPABASE_SERVICE_ROLE_KEY"),
    )


def get_rag_settings() -> RAGSettings:
    supabase = get_supabase_settings()
    default_enabled = bool(supabase.url and supabase.service_role_key)
    enabled = _coerce_bool(_get_env("RAG_ENABLED"), default=default_enabled)
    return RAGSettings(
        enabled=enabled,
        legal_rpc=_get_env("RAG_LEGAL_RPC", "search_tax_law") or "search_tax_law",
        vendor_rpc=_get_env("RAG_VENDOR_RPC", "search_vendor_background")
        or "search_vendor_background",
        similarity_threshold=_coerce_float(
            "RAG_SIMILARITY_THRESHOLD",
            _get_env("RAG_SIMILARITY_THRESHOLD"),
            default=0.3,
            min_value=0.0,
            max_value=1.0,
        ),
        legal_top_k=_coerce_int(
            "RAG_LEGAL_TOP_K",
            _get_env("RAG_LEGAL_TOP_K"),
            default=5,
            min_value=1,
            max_value=20,
        ),
        vendor_top_k=_coerce_int(
            "RAG_VENDOR_TOP_K",
            _get_env("RAG_VENDOR_TOP_K"),
            default=3,
            min_value=0,
            max_value=20,
        ),
        max_chunk_chars=_coerce_int(
            "RAG_MAX_CHUNK_CHARS",
            _get_env("RAG_MAX_CHUNK_CHARS"),
            default=420,
            min_value=120,
            max_value=4000,
        ),
    )


def require_openai_api_key(settings: OpenAISettings | None = None) -> str:
    settings = settings or get_openai_settings()
    if settings.api_key:
        return settings.api_key
    raise ValueError("OPENAI_API_KEY is not set. Copy .env.example to .env and set it.")


def require_supabase_credentials(settings: SupabaseSettings | None = None) -> SupabaseSettings:
    settings = settings or get_supabase_settings()
    if settings.url and settings.service_role_key:
        return settings
    raise ValueError(
        "Supabase credentials are missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
    )
