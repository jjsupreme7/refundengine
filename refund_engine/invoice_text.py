from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class InvoiceTextResult:
    pdf_path: str
    text: str
    method: str
    pages_processed: int
    warnings: tuple[str, ...] = ()

    def preview(self, max_chars: int = 800) -> str:
        compact = " ".join((self.text or "").split())
        if len(compact) <= max_chars:
            return compact
        return compact[: max_chars - 3] + "..."


def _extract_text_pdfplumber(pdf_path: Path, max_pages: int) -> tuple[str, int, list[str]]:
    warnings: list[str] = []
    chunks: list[str] = []

    try:
        import pdfplumber
    except Exception as exc:
        return "", 0, [f"pdfplumber unavailable: {exc}"]

    pages_processed = 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_processed = min(total_pages, max_pages)

            for idx in range(pages_processed):
                try:
                    text = pdf.pages[idx].extract_text() or ""
                    text = text.strip()
                    if text:
                        chunks.append(text)
                except Exception as exc:
                    warnings.append(f"pdf text extraction failed on page {idx + 1}: {exc}")
    except Exception as exc:
        warnings.append(f"unable to open PDF for text extraction: {exc}")
        return "", 0, warnings

    return "\n\n".join(chunks), pages_processed, warnings


def _extract_text_ocr(pdf_path: Path, max_pages: int, dpi: int) -> tuple[str, int, list[str]]:
    warnings: list[str] = []
    chunks: list[str] = []

    if shutil.which("tesseract") is None:
        return "", 0, [
            "tesseract binary not found; install it to enable OCR fallback"
        ]

    try:
        import pypdfium2 as pdfium
    except Exception as exc:
        return "", 0, [f"pypdfium2 unavailable: {exc}"]

    try:
        import pytesseract
    except Exception as exc:
        return "", 0, [f"pytesseract unavailable: {exc}"]

    pages_processed = 0
    doc = None
    try:
        doc = pdfium.PdfDocument(str(pdf_path))
        pages_processed = min(len(doc), max_pages)
        render_scale = max(float(dpi) / 72.0, 1.0)

        for idx in range(pages_processed):
            try:
                page = doc[idx]
                bitmap = page.render(scale=render_scale)
                image = bitmap.to_pil()
                text = pytesseract.image_to_string(image) or ""
                text = text.strip()
                if text:
                    chunks.append(text)
            except Exception as exc:
                warnings.append(f"OCR failed on page {idx + 1}: {exc}")
    except Exception as exc:
        warnings.append(f"unable to open PDF for OCR: {exc}")
        return "", 0, warnings
    finally:
        try:
            if doc is not None:
                doc.close()
        except Exception:
            pass

    return "\n\n".join(chunks), pages_processed, warnings


def extract_invoice_text(
    pdf_path: str | Path,
    *,
    max_pages: int = 4,
    min_direct_text_chars: int = 200,
    ocr_dpi: int = 300,
) -> InvoiceTextResult:
    """
    Extract text from an invoice PDF with OCR fallback.

    Flow:
    1) Try normal PDF text extraction (fast, best fidelity)
    2) If extracted text is sparse, run OCR on rendered pages
    """
    path = Path(pdf_path).expanduser()
    if not path.exists():
        return InvoiceTextResult(
            pdf_path=str(path),
            text="",
            method="missing",
            pages_processed=0,
            warnings=("invoice file not found",),
        )

    direct_text, direct_pages, direct_warnings = _extract_text_pdfplumber(path, max_pages)
    warnings = list(direct_warnings)

    if len(" ".join(direct_text.split())) >= min_direct_text_chars:
        return InvoiceTextResult(
            pdf_path=str(path),
            text=direct_text,
            method="pdf_text",
            pages_processed=direct_pages,
            warnings=tuple(warnings),
        )

    ocr_text, ocr_pages, ocr_warnings = _extract_text_ocr(path, max_pages, ocr_dpi)
    warnings.extend(ocr_warnings)

    if ocr_text.strip():
        combined = direct_text.strip()
        if combined:
            combined = f"{combined}\n\n{ocr_text.strip()}"
        else:
            combined = ocr_text.strip()

        return InvoiceTextResult(
            pdf_path=str(path),
            text=combined,
            method="ocr_fallback",
            pages_processed=max(direct_pages, ocr_pages),
            warnings=tuple(warnings),
        )

    fallback_method = "pdf_text_sparse" if direct_text.strip() else "none"
    return InvoiceTextResult(
        pdf_path=str(path),
        text=direct_text.strip(),
        method=fallback_method,
        pages_processed=direct_pages,
        warnings=tuple(warnings),
    )
