from __future__ import annotations

from openai import OpenAI

from refund_engine.config import get_openai_settings, require_openai_api_key


def create_openai_client(*, settings=None) -> OpenAI:
    settings = settings or get_openai_settings()
    kwargs = {"api_key": require_openai_api_key(settings)}
    if settings.base_url:
        kwargs["base_url"] = settings.base_url
    return OpenAI(**kwargs)

