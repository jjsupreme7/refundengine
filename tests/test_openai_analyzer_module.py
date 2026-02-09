from __future__ import annotations

from refund_engine.analysis.openai_analyzer import (
    InvoiceEvidence,
    RowEvidence,
    _analysis_prompt,
    _parse_json_object,
    _to_output_row,
)
from refund_engine.rag import RAGChunk, RAGContext


def test_parse_json_object_handles_embedded_json():
    text = "Here is output:\n```json\n{\"final_decision\":\"REVIEW\"}\n```"
    parsed = _parse_json_object(text)
    assert parsed["final_decision"] == "REVIEW"


def test_to_output_row_builds_reasoning_with_token():
    payload = {
        "invoice_number": "INV-1",
        "invoice_date": "2026-01-01",
        "ship_to_address": "Seattle WA",
        "matched_line_item": "Security service",
        "vendor_research": "Vendor does security testing.",
        "product_description": "Security testing services",
        "service_classification": "Service",
        "product_type": "Service",
        "refund_basis": "Professional Services",
        "citation": "WAC 458-20-111",
        "citation_source": "https://app.leg.wa.gov/",
        "taxability_reasoning": "Professional services are generally non-retail.",
        "final_decision": "NO REFUND",
        "confidence": 0.7,
        "estimated_refund": 0.0,
        "explanation": "Likely taxable status was correct.",
        "follow_up_questions": "",
        "tax_category": "Services",
        "methodology": "Non-taxable",
        "sales_use_tax": "Use",
    }
    evidence = RowEvidence(
        dataset_id="use_tax_2024",
        row_index=4,
        vendor="ACME",
        description="security testing",
        tax_amount=100.0,
        tax_base=None,
        invoice_number="INV-1",
        po_number="PO-1",
        invoice_1=InvoiceEvidence(
            filename="inv.pdf",
            path="/tmp/inv.pdf",
            extraction_method="pdf_text",
            text_preview="invoice preview",
        ),
        invoice_2=None,
    )
    output = _to_output_row(payload, evidence)
    assert output["Final_Decision"] == "NO REFUND"
    assert output["Tax_Category"] == "Services"
    assert output["Methodology"] == "Non-taxable"
    assert output["Sales_Use_Tax"] == "Use"
    assert "Refund_Source" in output
    assert "INVOICE VERIFIED:" in output["AI_Reasoning"]
    assert "Tax Category: Services" in output["AI_Reasoning"]
    assert "Methodology: Non-taxable" in output["AI_Reasoning"]
    assert "ENFORCED_PROCESS|" in output["AI_Reasoning"]


def test_analysis_prompt_includes_rag_sections():
    evidence = RowEvidence(
        dataset_id="use_tax_2024",
        row_index=1,
        vendor="ACME",
        description="Security testing",
        tax_amount=50.0,
        tax_base=None,
        invoice_number="INV-7",
        po_number="PO-9",
        invoice_1=InvoiceEvidence(
            filename="inv.pdf",
            path="/tmp/inv.pdf",
            extraction_method="pdf_text",
            text_preview="invoice preview",
        ),
        invoice_2=None,
    )
    rag_context = RAGContext(
        legal_chunks=(
            RAGChunk(
                text="WAC guidance about professional services.",
                citation="WAC 458-20-155",
                source="WA DOR",
                similarity=0.91,
                url="https://app.leg.wa.gov",
                category="wac",
            ),
        ),
        vendor_chunks=(
            RAGChunk(
                text="Vendor background says security consulting.",
                source="Vendor profile",
                similarity=0.88,
            ),
        ),
    )

    prompt = _analysis_prompt(
        evidence,
        rag_context=rag_context,
        max_rag_chunk_chars=200,
    )

    assert "Internal RAG retrieval context:" in prompt
    assert "RAG legal context:" in prompt
    assert "WAC 458-20-155" in prompt
    assert "RAG vendor context:" in prompt


def test_analysis_prompt_includes_vendor_profile():
    evidence = RowEvidence(
        dataset_id="sales_tax_2024",
        row_index=1,
        vendor="ACME",
        description="Cloud service",
        tax_amount=1000.0,
        tax_base=None,
        invoice_number="INV-1",
        po_number="PO-1",
        invoice_1=None,
        invoice_2=None,
    )
    profile_text = "VENDOR PROFILE: ACME sells cloud services, typically MPU basis."
    prompt = _analysis_prompt(evidence, vendor_profile=profile_text)
    assert "Historical vendor profile:" in prompt
    assert "ACME sells cloud services" in prompt


def test_analysis_prompt_omits_vendor_profile_when_none():
    evidence = RowEvidence(
        dataset_id="sales_tax_2024",
        row_index=1,
        vendor="ACME",
        description="Cloud service",
        tax_amount=1000.0,
        tax_base=None,
        invoice_number="INV-1",
        po_number="PO-1",
        invoice_1=None,
        invoice_2=None,
    )
    prompt = _analysis_prompt(evidence, vendor_profile=None)
    assert "Historical vendor profile:" not in prompt


def test_analysis_prompt_includes_rate_validation_for_wa():
    evidence = RowEvidence(
        dataset_id="sales_tax_2024",
        row_index=1,
        vendor="ACME",
        description="Cloud service",
        tax_amount=1035.0,
        tax_base=10000.0,
        invoice_number="INV-1",
        po_number="PO-1",
        invoice_1=None,
        invoice_2=None,
        rate=0.1035,
        jurisdiction="WA",
    )
    prompt = _analysis_prompt(evidence)
    assert "Rate validation context:" in prompt
    assert "Charged rate:" in prompt


def test_analysis_prompt_omits_rate_validation_for_non_wa():
    evidence = RowEvidence(
        dataset_id="sales_tax_2024",
        row_index=1,
        vendor="ACME",
        description="Cloud service",
        tax_amount=625.0,
        tax_base=10000.0,
        invoice_number="INV-1",
        po_number="PO-1",
        invoice_1=None,
        invoice_2=None,
        rate=0.0625,
        jurisdiction="CA",
    )
    prompt = _analysis_prompt(evidence)
    assert "Rate validation context:" not in prompt


def test_analysis_prompt_includes_line_item_matching():
    evidence = RowEvidence(
        dataset_id="sales_tax_2024",
        row_index=1,
        vendor="ACME",
        description="Cloud service",
        tax_amount=1000.0,
        tax_base=10000.0,
        invoice_number="INV-1",
        po_number="PO-1",
        invoice_1=None,
        invoice_2=None,
    )
    prompt = _analysis_prompt(evidence)
    assert "Line item matching guidance:" in prompt
    assert "$10,000.00" in prompt
