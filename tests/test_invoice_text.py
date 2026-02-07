from __future__ import annotations

from pathlib import Path

from refund_engine import invoice_text as invoice_text_module


def test_extract_invoice_text_uses_direct_pdf_text_when_sufficient(tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "invoice.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        invoice_text_module,
        "_extract_text_pdfplumber",
        lambda _path, _max_pages: ("A" * 300, 1, []),
    )

    ocr_called = {"value": False}

    def fake_ocr(_path, _max_pages, _dpi):
        ocr_called["value"] = True
        return ("OCR text", 1, [])

    monkeypatch.setattr(invoice_text_module, "_extract_text_ocr", fake_ocr)

    result = invoice_text_module.extract_invoice_text(pdf_path, min_direct_text_chars=200)

    assert result.method == "pdf_text"
    assert result.text == "A" * 300
    assert ocr_called["value"] is False


def test_extract_invoice_text_falls_back_to_ocr_when_pdf_text_is_sparse(
    tmp_path: Path, monkeypatch
):
    pdf_path = tmp_path / "invoice.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        invoice_text_module,
        "_extract_text_pdfplumber",
        lambda _path, _max_pages: ("too short", 1, []),
    )
    monkeypatch.setattr(
        invoice_text_module,
        "_extract_text_ocr",
        lambda _path, _max_pages, _dpi: ("OCR recovered text", 2, []),
    )

    result = invoice_text_module.extract_invoice_text(pdf_path, min_direct_text_chars=200)

    assert result.method == "ocr_fallback"
    assert "OCR recovered text" in result.text
    assert result.pages_processed == 2


def test_extract_invoice_text_returns_missing_for_absent_file(tmp_path: Path):
    missing_pdf = tmp_path / "missing.pdf"

    result = invoice_text_module.extract_invoice_text(missing_pdf)

    assert result.method == "missing"
    assert result.text == ""
    assert "invoice file not found" in result.warnings
