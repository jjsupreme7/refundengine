from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from refund_engine.config import get_openai_settings
from refund_engine.openai_client import create_openai_client
from refund_engine.rag import (
    RAGContext,
    SupabaseRAGRetriever,
    format_rag_context_for_prompt,
)
from refund_engine.rate_validator import validate_rate
from refund_engine.refund_calculator import calculate_refund
from refund_engine.validation_rules import (
    ensure_process_token,
    generate_process_token,
    normalize_final_decision,
    normalize_methodology,
)
from refund_engine.vendor_profiles import load_vendor_profile


@dataclass(frozen=True)
class InvoiceEvidence:
    filename: str | None
    path: str | None
    extraction_method: str
    text_preview: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RowEvidence:
    dataset_id: str
    row_index: int
    vendor: str
    description: str
    tax_amount: float | None
    tax_base: float | None
    invoice_number: str | None
    po_number: str | None
    invoice_1: InvoiceEvidence | None
    invoice_2: InvoiceEvidence | None
    rate: float | None = None
    jurisdiction: str | None = None


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("$", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _parse_json_object(text: str) -> dict[str, Any]:
    body = text.strip()
    if not body:
        raise ValueError("Model returned empty output")

    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", body, flags=re.DOTALL)
    if not match:
        raise ValueError("Model output did not contain a JSON object")

    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Model JSON output must be an object")
    return parsed


def _invoice_section(name: str, invoice: InvoiceEvidence | None) -> str:
    if not invoice:
        return f"{name}: none"
    warnings = "; ".join(invoice.warnings) if invoice.warnings else "none"
    return (
        f"{name}: file={invoice.filename or 'none'}, method={invoice.extraction_method}, "
        f"path={invoice.path or 'none'}, warnings={warnings}\n"
        f"{name} preview:\n{invoice.text_preview}"
    )


def _analysis_prompt(
    evidence: RowEvidence,
    *,
    rag_context: RAGContext | None = None,
    max_rag_chunk_chars: int = 420,
    guidance: str | None = None,
    vendor_profile: str | None = None,
) -> str:
    tax_amount_text = "N/A" if evidence.tax_amount is None else f"{evidence.tax_amount:,.2f}"
    tax_base_text = "N/A" if evidence.tax_base is None else f"{evidence.tax_base:,.2f}"
    rag_section = (
        format_rag_context_for_prompt(
            rag_context,
            max_chunk_chars=max_rag_chunk_chars,
        )
        if rag_context is not None
        else "RAG legal context: none\n\nRAG vendor context: none"
    )
    vendor_profile_section = f"\nHistorical vendor profile:\n{vendor_profile}\n" if vendor_profile else ""
    extra_guidance = f"\nValidation feedback to fix:\n{guidance}\n" if guidance else ""

    rate_validation = validate_rate(
        evidence.rate, evidence.jurisdiction, evidence.tax_base, evidence.tax_amount,
    )
    rate_section = ""
    if rate_validation.actual_rate is not None and rate_validation.is_wa:
        rate_section = f"\nRate validation context:\n{rate_validation.message}\n"

    line_match_section = ""
    if evidence.tax_base is not None:
        line_match_section = (
            f"\nLine item matching guidance:\n"
            f"When the invoice has multiple line items, match this row to the line item where:\n"
            f"1. The dollar amount matches tax_base (${evidence.tax_base:,.2f}) most closely\n"
            f"2. The description \"{evidence.description}\" aligns with the invoice line text\n"
            f"Report in matched_line_item as: \"[description] @ $[amount]\"\n"
        )

    return f"""
You are a Washington state sales/use tax analyst. Transactions are from 2023-2024 and must use pre-October 1, 2025 law.
Return only a single JSON object (no markdown, no prose outside JSON).
If uncertain, use final_decision = "REVIEW" with a specific explanation.
If retrieved legal context conflicts with invoice evidence, explain the conflict and choose "REVIEW".

Use these controlled vocabularies:
- product_type: License, Services, DAS, Maintenance, HW maintenance, HW\\SW maintenance, Hardware, HW Maintenance, Tangible goods, Digital good, Resale
- refund_basis: MPU, Non-taxable, Partial OOS services, Wrong rate, Partial OOS shipment, OOS services, OOS shipment, B&O tax, Resale, Discount
- tax_category: License, Services, Software maintenance, Hardware maintenance, Hardware, Tangible goods, Digital good, DAS, Maintenance
- methodology (how refund allocation is determined): User location, Non-taxable, Headcount, Equipment Location, Wrong rate, Call center, Call center Retail, Retail stores, Engineering, Resale, RF Engineering, Ship-to location, Delivery out-of-state, Subscribers, MPU, Care+Retail, Fraud team, Project location, Call center + Marketing
- sales_use_tax: Sales, Use, B&O

Row context:
- dataset_id: {evidence.dataset_id}
- row_index: {evidence.row_index}
- vendor: {evidence.vendor}
- description: {evidence.description}
- tax_amount: {tax_amount_text}
- tax_base: {tax_base_text}
- invoice_number_from_row: {evidence.invoice_number or ''}
- po_number_from_row: {evidence.po_number or ''}

Invoice evidence:
{_invoice_section("invoice_1", evidence.invoice_1)}

{_invoice_section("invoice_2", evidence.invoice_2)}
{line_match_section}
Internal RAG retrieval context:
{rag_section}
{vendor_profile_section}{rate_section}{extra_guidance}

Required JSON fields and types:
{{
  "invoice_number": "string",
  "invoice_date": "string",
  "ship_to_address": "string",
  "matched_line_item": "string",
  "vendor_research": "string",
  "product_description": "string",
  "service_classification": "string",
  "product_type": "string",
  "refund_basis": "string",
  "citation": "string",
  "citation_source": "string",
  "taxability_reasoning": "string",
  "final_decision": "REFUND|NO REFUND|REVIEW|PASS",
  "confidence": 0.0,
  "estimated_refund": 0.0,
  "explanation": "string",
  "follow_up_questions": "string",
  "tax_category": "string (from controlled list)",
  "methodology": "string (from controlled list)",
  "sales_use_tax": "Sales|Use|B&O"
}}
""".strip()


def _build_ai_reasoning(payload: dict[str, Any], evidence: RowEvidence, process_token: str) -> str:
    invoice_number = _safe_str(payload.get("invoice_number")) or _safe_str(evidence.invoice_number) or "UNKNOWN"
    invoice_date = _safe_str(payload.get("invoice_date")) or "UNKNOWN"
    ship_to_address = _safe_str(payload.get("ship_to_address")) or "UNKNOWN"
    matched_line_item = _safe_str(payload.get("matched_line_item")) or "UNKNOWN"
    amount_value = evidence.tax_base if evidence.tax_base is not None else evidence.tax_amount
    amount_text = f"${amount_value:,.2f}" if amount_value is not None else "N/A"

    vendor_research = _safe_str(payload.get("vendor_research"))
    product_description = _safe_str(payload.get("product_description"))
    taxability_reasoning = _safe_str(payload.get("taxability_reasoning"))
    product_type = _safe_str(payload.get("product_type"))
    refund_basis = _safe_str(payload.get("refund_basis")) or "N/A - taxable"
    citation = _safe_str(payload.get("citation"))
    final_decision = normalize_final_decision(payload.get("final_decision"))
    explanation = _safe_str(payload.get("explanation"))
    estimated_refund = _coerce_float(payload.get("estimated_refund"), default=0.0)

    lines = [
        f"INVOICE VERIFIED: Invoice #{invoice_number} dated {invoice_date}",
        f"SHIP-TO: {ship_to_address}",
        f"MATCHED LINE ITEM: {matched_line_item} @ {amount_text}",
        "---",
        "",
        "VENDOR RESEARCH (from web search):",
        vendor_research or "No additional vendor research provided.",
        "",
        "PRODUCT/SERVICE ANALYSIS:",
        product_description or evidence.description or "No product description provided.",
        "",
        "WHY THIS IS/ISN'T TAXABLE:",
        taxability_reasoning or "No taxability reasoning provided.",
        "",
        "TAX ANALYSIS:",
        f"- Product Type: {product_type or 'Unknown'}",
        f"- Tax Category: {_safe_str(payload.get('tax_category')) or 'Unknown'}",
        f"- Exemption Basis: {refund_basis}",
        f"- Methodology: {_safe_str(payload.get('methodology')) or 'Unknown'}",
        f"- Tax Type: {_safe_str(payload.get('sales_use_tax')) or 'Unknown'}",
        f"- Citation: {citation or 'N/A'}",
        "",
        f"DECISION: {final_decision or 'REVIEW'}",
        f"ESTIMATED REFUND: ${estimated_refund:,.2f}",
    ]

    if explanation:
        lines.append(f"EXPLANATION: {explanation}")

    return ensure_process_token("\n".join(lines), token=process_token)


def _to_output_row(payload: dict[str, Any], evidence: RowEvidence) -> dict[str, Any]:
    process_token = generate_process_token()
    final_decision = normalize_final_decision(payload.get("final_decision"))
    confidence = _coerce_float(payload.get("confidence"), default=0.0)
    estimated_refund = _coerce_float(payload.get("estimated_refund"), default=0.0)
    methodology = normalize_methodology(payload.get("methodology"))

    refund_amount = max(0.0, estimated_refund)
    refund_source = "estimated"
    if evidence.tax_amount is not None and methodology:
        refund_amount, refund_source = calculate_refund(
            evidence.tax_amount, methodology, estimated_refund,
        )

    output = {
        "Product_Desc": _safe_str(payload.get("product_description")),
        "Product_Type": _safe_str(payload.get("product_type")),
        "Service_Classification": _safe_str(payload.get("service_classification"))
        or _safe_str(payload.get("product_type")),
        "Refund_Basis": _safe_str(payload.get("refund_basis")),
        "Citation": _safe_str(payload.get("citation")),
        "Citation_Source": _safe_str(payload.get("citation_source")),
        "Confidence": confidence,
        "Estimated_Refund": refund_amount,
        "Refund_Source": refund_source,
        "Final_Decision": final_decision,
        "Explanation": _safe_str(payload.get("explanation")),
        "Needs_Review": "Yes" if final_decision == "REVIEW" else "No",
        "Follow_Up_Questions": _safe_str(payload.get("follow_up_questions")),
        "Tax_Category": _safe_str(payload.get("tax_category")),
        "Methodology": methodology,
        "Sales_Use_Tax": _safe_str(payload.get("sales_use_tax")),
    }
    output["AI_Reasoning"] = _build_ai_reasoning(payload, evidence, process_token)
    return output


class OpenAIAnalyzer:
    def __init__(
        self,
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        verbosity: str | None = None,
        rag_retriever: SupabaseRAGRetriever | None = None,
    ):
        settings = get_openai_settings()
        self.model = model or settings.model_analysis
        self.reasoning_effort = reasoning_effort or settings.reasoning_effort
        self.verbosity = verbosity or settings.text_verbosity
        self.client = create_openai_client(settings=settings)
        self.rag_retriever = rag_retriever
        self.rag_init_warning: str | None = None
        self.max_rag_chunk_chars = 420
        if self.rag_retriever is None:
            self.rag_retriever, self.rag_init_warning = SupabaseRAGRetriever.from_env()
        if self.rag_retriever is not None:
            self.max_rag_chunk_chars = self.rag_retriever.rag_settings.max_chunk_chars

    def analyze_row(
        self,
        evidence: RowEvidence,
        *,
        guidance: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        rag_context: RAGContext | None = None
        rag_warnings: list[str] = []
        if self.rag_init_warning:
            rag_warnings.append(self.rag_init_warning)
        if self.rag_retriever is not None:
            try:
                rag_context = self.rag_retriever.retrieve(
                    vendor=evidence.vendor,
                    description=evidence.description,
                    invoice_preview_1=evidence.invoice_1.text_preview if evidence.invoice_1 else "",
                    invoice_preview_2=evidence.invoice_2.text_preview if evidence.invoice_2 else "",
                )
                rag_warnings.extend(list(rag_context.warnings))
            except Exception as exc:
                rag_warnings.append(f"RAG retrieval failed: {exc}")
                rag_context = None

        vendor_profile = load_vendor_profile(evidence.vendor)

        prompt = _analysis_prompt(
            evidence,
            rag_context=rag_context,
            max_rag_chunk_chars=self.max_rag_chunk_chars,
            guidance=guidance,
            vendor_profile=vendor_profile,
        )
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.reasoning_effort},
            text={"verbosity": self.verbosity},
        )
        output_text = (response.output_text or "").strip()
        payload = _parse_json_object(output_text)
        result = _to_output_row(payload, evidence)

        usage = getattr(response, "usage", None)
        metadata = {
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "verbosity": self.verbosity,
            "response_id": getattr(response, "id", None),
            "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
            "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
            "rag_enabled": self.rag_retriever is not None,
            "rag_legal_chunks": len(rag_context.legal_chunks) if rag_context else 0,
            "rag_vendor_chunks": len(rag_context.vendor_chunks) if rag_context else 0,
            "rag_warnings": rag_warnings,
            "vendor_profile_matched": vendor_profile is not None,
            "rate_validation": validate_rate(
                evidence.rate, evidence.jurisdiction, evidence.tax_base, evidence.tax_amount,
            ).message,
        }
        return result, metadata
