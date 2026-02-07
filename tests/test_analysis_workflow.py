from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.analyze_row import AnalysisForm, filter_unanalyzed
from scripts.check_process_token import is_modified
from scripts.validate_analysis import is_valid_citation, validate_row


def _populate_required_fields(form: AnalysisForm):
    form.invoice_number = "INV-1"
    form.invoice_date = "2026-01-01"
    form.pdf_filename = "invoice.pdf"
    form.ship_to_address = "123 Main St, Seattle WA 98101"
    form.matched_invoice_line = "Line 1"
    form.vendor_description = "Vendor description"
    form.vendor_business_model = "Vendor business model"
    form.product_description = "Product description"
    form.product_how_it_works = "Product works like this"
    form.why_taxable_or_not = "Tax reasoning"
    form.product_type = "DAS"
    form.citation = "RCW 82.12.0208"
    form.final_decision = "REFUND"
    form.confidence = 0.9
    form.excel_amount = 100.0


def test_to_output_row_uses_vendor_research_url_as_fallback():
    form = AnalysisForm()
    _populate_required_fields(form)
    form.vendor_research_url = "https://example.com/vendor"

    output = form.to_output_row()

    assert output["Citation_Source"] == "https://example.com/vendor"
    assert "ENFORCED_PROCESS|" in output["AI_Reasoning"]


def test_filter_unanalyzed_includes_blank_analysis_cells():
    df = pd.DataFrame(
        [
            {"Inv 1": "a.pdf", "Recon Analysis": ""},
            {"Inv 1": "b.pdf", "Recon Analysis": None},
            {"Inv 1": "c.pdf", "Recon Analysis": "already analyzed"},
        ]
    )
    config = {
        "columns": {"invoice_1": "Inv 1", "analysis_col": "Recon Analysis"},
        "filters": {},
    }

    filtered = filter_unanalyzed(df, config)

    assert list(filtered.index) == [0, 1]


def test_wac_citation_validation_is_strict():
    assert is_valid_citation("WAC 458-20-170")
    assert not is_valid_citation("WAC totally fake")
    assert not is_valid_citation("WAC 123")


def test_validate_row_requires_citation_for_refund():
    row = {
        "AI_Reasoning": (
            "INVOICE VERIFIED: Invoice #123 dated 2026-01-01\n"
            "SHIP-TO: 123 Main St, Seattle WA 98101\n"
            "MATCHED LINE ITEM: Test @ $100"
        ),
        "Citation": "",
        "Final_Decision": "REFUND",
        "Confidence": 0.8,
    }

    valid, errors = validate_row(row)

    assert not valid
    assert any("Missing citation for REFUND decision" in err for err in errors)


def test_is_modified_bootstraps_then_detects_content_changes(tmp_path: Path):
    state: dict[str, str] = {}
    file_path = tmp_path / "output.xlsx"
    file_path.write_bytes(b"v1")

    first_modified, _ = is_modified(file_path, state)
    second_modified, _ = is_modified(file_path, state)

    file_path.write_bytes(b"v2")
    third_modified, _ = is_modified(file_path, state)

    assert first_modified is False
    assert second_modified is False
    assert third_modified is True
