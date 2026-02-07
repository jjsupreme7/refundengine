from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from refund_engine.constants import PROJECT_ROOT, REQUIRED_REASONING_HEADERS


_VALID_RCWS: set[str] = set()
_TARGET_RCWS_PATH = PROJECT_ROOT / "knowledge_base" / "target_rcws.txt"
_VALID_DECISIONS = {"REFUND", "NO REFUND", "REVIEW", "PASS"}
_WAC_PATTERN = re.compile(
    r"^WAC\s+458-20-\d+[A-Z]?(?:\([^)]+\))*$",
    re.IGNORECASE,
)


def generate_process_token() -> str:
    return f"ENFORCED_PROCESS|{datetime.now().isoformat()}|v2"


def ensure_process_token(reasoning: str, token: str | None = None) -> str:
    text = (reasoning or "").strip()
    if "ENFORCED_PROCESS|" in text:
        return text
    token_value = token or generate_process_token()
    return f"{text}\n\n[{token_value}]".strip()


def normalize_final_decision(value: Any) -> str:
    text = str(value or "").strip().upper().replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    if text in {"NOREFUND", "NO REFUNDS"}:
        return "NO REFUND"
    return text


def load_valid_rcws() -> set[str]:
    if _VALID_RCWS:
        return _VALID_RCWS
    if not _TARGET_RCWS_PATH.exists():
        return _VALID_RCWS
    with open(_TARGET_RCWS_PATH, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                _VALID_RCWS.add(stripped)
    return _VALID_RCWS


def is_valid_citation(citation: str) -> bool:
    if not citation:
        return True

    valid_rcws = load_valid_rcws()

    for part in re.split(r"[/,]", citation):
        part = part.strip()
        if not part:
            continue
        if part.upper().startswith("WAC"):
            if not _WAC_PATTERN.match(part):
                return False
            continue

        rcw_num = re.sub(r"^RCW\s*", "", part, flags=re.IGNORECASE).strip()
        if rcw_num in valid_rcws:
            continue
        base_rcw = re.sub(r"\([^)]+\)$", "", rcw_num)
        if base_rcw in valid_rcws:
            continue
        return False

    return True


def validate_output_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    reasoning = str(row.get("AI_Reasoning") or "").strip()
    if not reasoning:
        errors.append("AI_Reasoning is empty")
    else:
        for header in REQUIRED_REASONING_HEADERS:
            if header not in reasoning:
                errors.append(f"AI_Reasoning missing required header: {header}")

    decision = normalize_final_decision(row.get("Final_Decision"))
    if decision not in _VALID_DECISIONS:
        errors.append(
            f"Invalid Final_Decision '{decision}'. Expected one of: "
            f"{', '.join(sorted(_VALID_DECISIONS))}"
        )

    citation = str(row.get("Citation") or "").strip()
    if decision == "REFUND" and not citation:
        errors.append("Citation is required for REFUND decisions")
    if citation and not is_valid_citation(citation):
        errors.append(f"Invalid citation format/content: {citation}")

    confidence_raw = row.get("Confidence")
    if confidence_raw not in (None, ""):
        try:
            confidence = float(confidence_raw)
            if not (0.0 <= confidence <= 1.0):
                errors.append(f"Confidence out of range: {confidence}")
        except (TypeError, ValueError):
            errors.append(f"Invalid confidence value: {confidence_raw!r}")

    estimated_refund_raw = row.get("Estimated_Refund")
    if estimated_refund_raw not in (None, ""):
        try:
            estimated_refund = float(estimated_refund_raw)
            if estimated_refund < 0:
                errors.append(f"Estimated_Refund cannot be negative: {estimated_refund}")
        except (TypeError, ValueError):
            errors.append(f"Invalid Estimated_Refund value: {estimated_refund_raw!r}")

    product_desc = str(row.get("Product_Desc") or "").strip()
    if decision in {"REFUND", "NO REFUND"} and not product_desc:
        errors.append("Product_Desc is required for REFUND/NO REFUND decisions")

    return errors
