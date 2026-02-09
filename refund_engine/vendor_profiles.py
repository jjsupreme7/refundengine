from __future__ import annotations

import json
from typing import Any

from fuzzywuzzy import fuzz

from refund_engine.constants import PROJECT_ROOT

_PROFILES_PATH = PROJECT_ROOT / "config" / "vendor_profiles.json"
_CACHE: dict[str, Any] | None = None
_VENDOR_NAMES: list[str] = []


def _load() -> dict[str, Any]:
    global _CACHE, _VENDOR_NAMES
    if _CACHE is not None:
        return _CACHE
    if not _PROFILES_PATH.exists():
        _CACHE = {}
        return _CACHE
    with open(_PROFILES_PATH) as f:
        data = json.load(f)
    _CACHE = data.get("vendors", {})
    _VENDOR_NAMES = list(_CACHE.keys())
    return _CACHE


def _match_vendor(vendor_name: str, threshold: int = 80) -> str | None:
    vendors = _load()
    upper = vendor_name.strip().upper()
    if upper in vendors:
        return upper
    best_name, best_score = None, 0
    for name in _VENDOR_NAMES:
        score = fuzz.token_sort_ratio(upper, name)
        if score > best_score:
            best_name, best_score = name, score
    if best_score >= threshold:
        return best_name
    return None


def _fmt(label: str, value: str, count: int | None = None) -> str:
    if count is not None:
        return f"  {label}: {value} ({count} rows)"
    return f"  {label}: {value}"


def _confidence_label(total_rows: int) -> str:
    if total_rows >= 30:
        return "HIGH"
    if total_rows >= 10:
        return "MEDIUM"
    return "LOW"


def load_vendor_profile(vendor_name: str) -> str | None:
    """Return a formatted text block for the given vendor, or None."""
    vendors = _load()
    matched = _match_vendor(vendor_name)
    if matched is None:
        return None
    p = vendors[matched]
    confidence = _confidence_label(p["total_rows"])
    lines = [
        f"VENDOR PROFILE ({p['total_rows']} historical rows, {confidence} confidence):",
        f"  Vendor: {matched}",
        _fmt("Dominant Tax Category", p["dominant_tax_category"]["value"], p["dominant_tax_category"]["count"]),
        _fmt("Dominant Product Type", p["dominant_product_type"]["value"], p["dominant_product_type"]["count"]),
        _fmt("Dominant Refund Basis", p["dominant_refund_basis"]["value"], p["dominant_refund_basis"]["count"]),
        _fmt("Dominant Methodology", p["dominant_methodology"]["value"], p["dominant_methodology"]["count"]),
        f"  Claimed: {p['claimed_count']}, Pass: {p['pass_count']}",
    ]
    # Add methodology mix with allocation percentages if available
    mix = p.get("methodology_mix", {})
    if mix:
        mix_parts = []
        for meth_name, info in list(mix.items())[:4]:
            avg = info.get("avg_pct")
            if avg is not None:
                mix_parts.append(f"{meth_name} ({info['count']} rows, avg alloc {avg:.0%})")
            else:
                mix_parts.append(f"{meth_name} ({info['count']} rows)")
        if mix_parts:
            lines.append("  Methodology mix: " + "; ".join(mix_parts))
    descs = p.get("sample_descriptions", [])
    if descs:
        lines.append("  Typical descriptions:")
        for d in descs[:3]:
            lines.append(f"    - {d}")
    examples = p.get("few_shot_examples", [])
    if examples:
        lines.append("  Analyst decision examples for this vendor:")
        for i, ex in enumerate(examples[:3], 1):
            desc = ex.get("description", "N/A")
            tc = ex.get("tax_category", "")
            rb = ex.get("refund_basis", "")
            meth = ex.get("methodology", "")
            lines.append(
                f'    Ex{i}: "{desc}" -> tax_category={tc}, refund_basis={rb}, methodology={meth}'
            )
            notes = ex.get("notes", "")
            if len(notes) > 10:
                lines.append(f'         Analyst: "{notes}"')
    lines.append(
        "  NOTE: Use as prior context, not definitive. Verify against invoice evidence."
    )
    return "\n".join(lines)
