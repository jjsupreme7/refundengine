from __future__ import annotations

import json
from typing import Any

from refund_engine.constants import PROJECT_ROOT
from refund_engine.validation_rules import normalize_methodology

_CONFIG_PATH = PROJECT_ROOT / "config" / "allocation_percentages.json"
_CACHE: dict[str, Any] | None = None


def _load_config() -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not _CONFIG_PATH.exists():
        _CACHE = {}
        return _CACHE
    with open(_CONFIG_PATH) as f:
        _CACHE = json.load(f)
    return _CACHE


def calculate_refund(
    tax_amount: float,
    methodology: str,
    llm_estimate: float,
) -> tuple[float, str]:
    """Return (refund_amount, source).

    source is "calculated" when a deterministic allocation_pct exists,
    or "estimated" when falling back to the LLM estimate.
    """
    config = _load_config()
    entry = config.get(normalize_methodology(methodology))
    if entry is None or not isinstance(entry, dict):
        return (max(0.0, llm_estimate), "estimated")

    allocation_pct = entry.get("allocation_pct")
    if allocation_pct is None:
        return (max(0.0, llm_estimate), "estimated")

    refund = tax_amount * float(allocation_pct)
    return (max(0.0, refund), "calculated")
