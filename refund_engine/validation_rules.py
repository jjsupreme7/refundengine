from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from refund_engine.constants import (
    PROJECT_ROOT,
    REQUIRED_REASONING_HEADERS,
    VALID_METHODOLOGIES,
    VALID_PRODUCT_TYPES,
    VALID_REFUND_BASES,
    VALID_SALES_USE_TAX,
    VALID_TAX_CATEGORIES,
)


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


_METHODOLOGY_ALIASES: dict[str, str] = {
    "equipment location": "Equipment Location",
    "call center": "Call center",
    "call center, retail": "Call center Retail",
    "call center,retail": "Call center Retail",
    "wrong rate": "Wrong rate",
    "rf engineering": "RF Engineering",
    "ship-to location": "Ship-to location",
    "delivery out-of-state": "Delivery out-of-state",
    "care + retail": "Care+Retail",
    "care+retail": "Care+Retail",
    "project location": "Project location",
    "call center + marketing": "Call center + Marketing",
}


def normalize_methodology(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    return _METHODOLOGY_ALIASES.get(text.lower(), text)


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


def _extract_header_value(reasoning: str, header: str) -> str:
    idx = reasoning.find(header)
    if idx < 0:
        return ""
    start = idx + len(header)
    end = reasoning.find("\n", start)
    return reasoning[start:end].strip() if end > start else reasoning[start:].strip()


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

    product_type = str(row.get("Product_Type") or "").strip()
    if product_type and product_type not in VALID_PRODUCT_TYPES:
        errors.append(f"Product_Type '{product_type}' not in controlled vocabulary")

    refund_basis = str(row.get("Refund_Basis") or "").strip()
    if decision == "REFUND" and refund_basis and refund_basis not in VALID_REFUND_BASES:
        errors.append(f"Refund_Basis '{refund_basis}' not in controlled vocabulary")

    tax_category = str(row.get("Tax_Category") or "").strip()
    if tax_category and tax_category not in VALID_TAX_CATEGORIES:
        errors.append(f"Tax_Category '{tax_category}' not in controlled vocabulary")

    sales_use_tax = str(row.get("Sales_Use_Tax") or "").strip()
    if sales_use_tax and sales_use_tax not in VALID_SALES_USE_TAX:
        errors.append(
            f"Sales_Use_Tax '{sales_use_tax}' not in controlled vocabulary. "
            f"Expected one of: {', '.join(sorted(VALID_SALES_USE_TAX))}"
        )

    # 1. Methodology vocabulary check (normalize first)
    methodology = normalize_methodology(row.get("Methodology"))
    if methodology and methodology not in VALID_METHODOLOGIES:
        errors.append(f"Methodology '{methodology}' not in controlled vocabulary")

    # 2. REFUND requires Refund_Basis and Methodology
    if decision == "REFUND":
        if not refund_basis:
            errors.append("Refund_Basis is required for REFUND decisions")
        if not methodology:
            errors.append("Methodology is required for REFUND decisions")

    # 3. Matched line item content quality (REFUND/NO REFUND only)
    if decision in {"REFUND", "NO REFUND"} and reasoning:
        matched_item = _extract_header_value(reasoning, "MATCHED LINE ITEM:")
        if not matched_item or matched_item == "UNKNOWN":
            errors.append("MATCHED LINE ITEM must identify a specific line item, not UNKNOWN")
        elif "$" not in matched_item:
            errors.append("MATCHED LINE ITEM must include a dollar amount (e.g., '@ $1,000.00')")

    # 4. Ship-to address quality (REFUND/NO REFUND only)
    if decision in {"REFUND", "NO REFUND"} and reasoning:
        ship_to = _extract_header_value(reasoning, "SHIP-TO:")
        if len(ship_to) <= 5:
            errors.append("SHIP-TO must be a full address, not just a state abbreviation")

    # 5. Follow-up questions for REVIEW
    if decision == "REVIEW":
        follow_up = str(row.get("Follow_Up_Questions") or "").strip()
        if len(follow_up) < 20:
            errors.append("REVIEW decisions require specific follow-up questions (>20 chars)")

    # 6. Confidence vs REVIEW logic
    if decision == "REVIEW" and confidence_raw not in (None, ""):
        try:
            conf_val = float(confidence_raw)
            if conf_val >= 0.85:
                errors.append(
                    f"Confidence {conf_val} is too high for REVIEW — commit to REFUND or NO REFUND"
                )
        except (TypeError, ValueError):
            pass

    # 7. Explanation required for REFUND/NO REFUND
    explanation = str(row.get("Explanation") or "").strip()
    if decision in {"REFUND", "NO REFUND"} and not explanation:
        errors.append("Explanation is required for REFUND/NO REFUND decisions")

    return errors
