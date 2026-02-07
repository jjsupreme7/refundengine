from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

from refund_engine.workbook_repository import (
    get_invoice_upload_dir,
    get_workbook_metadata,
    import_uploaded_invoice_files,
    import_uploaded_workbook,
    list_uploaded_invoice_files,
    list_workbooks,
    read_diff_summary,
    read_sheet_dataframe,
    write_updated_sheet_as_new_version,
)


def _xlsx_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()


def test_import_uploaded_workbook_creates_version(tmp_path: Path):
    df = pd.DataFrame({"Vendor": ["A", "B"], "Tax Remit": [10, 20], "Inv-1PDF": ["a.pdf", "b.pdf"]})
    ref = import_uploaded_workbook(
        _xlsx_bytes(df),
        filename="use-tax.xlsx",
        workbook_name="Use Tax 2024",
        root=tmp_path,
    )

    books = list_workbooks(root=tmp_path)
    assert len(books) == 1
    assert books[0]["workbook_id"] == ref.workbook_id
    assert books[0]["version_count"] == 1


def test_second_version_generates_diff_summary(tmp_path: Path):
    df1 = pd.DataFrame({"Vendor": ["A", "B"], "Tax Remit": [10, 20], "Inv-1PDF": ["a.pdf", "b.pdf"]})
    df2 = pd.DataFrame({"Vendor": ["A", "B"], "Tax Remit": [10, 99], "Inv-1PDF": ["a.pdf", "b.pdf"]})

    ref1 = import_uploaded_workbook(
        _xlsx_bytes(df1),
        filename="use-tax.xlsx",
        workbook_name="Use Tax 2024",
        root=tmp_path,
    )
    ref2 = import_uploaded_workbook(
        _xlsx_bytes(df2),
        filename="use-tax.xlsx",
        workbook_name="Use Tax 2024",
        root=tmp_path,
    )

    diff = read_diff_summary(ref2.workbook_id, ref2.version_id, root=tmp_path)
    assert diff is not None
    assert diff["sheets_compared"] == ["Sheet1"]
    assert diff["per_sheet"][0]["changed_cells_sampled"] >= 1

    metadata = get_workbook_metadata(ref1.workbook_id, root=tmp_path)
    assert len(metadata["versions"]) == 2


def test_write_updated_sheet_as_new_version(tmp_path: Path):
    base_df = pd.DataFrame({"Vendor": ["A", "B"], "Tax Remit": [10, 20], "Inv-1PDF": ["a.pdf", "b.pdf"]})
    ref = import_uploaded_workbook(
        _xlsx_bytes(base_df),
        filename="use-tax.xlsx",
        workbook_name="Use Tax 2024",
        root=tmp_path,
    )

    df = read_sheet_dataframe(ref.workbook_id, ref.version_id, "Sheet1", root=tmp_path)
    df.loc[0, "Tax Remit"] = 55

    ref2 = write_updated_sheet_as_new_version(
        ref.workbook_id,
        ref.version_id,
        "Sheet1",
        df,
        note="edited",
        root=tmp_path,
    )

    metadata = get_workbook_metadata(ref.workbook_id, root=tmp_path)
    assert len(metadata["versions"]) == 2
    assert ref2.version_id != ref.version_id


def test_import_uploaded_invoice_files_and_list(tmp_path: Path):
    files = [
        ("INV-1001.pdf", b"pdf-bytes-1"),
        ("INV-1002.pdf", b"pdf-bytes-2"),
    ]
    stored = import_uploaded_invoice_files(files, root=tmp_path, overwrite=True)
    assert len(stored) == 2

    upload_dir = get_invoice_upload_dir(root=tmp_path)
    assert upload_dir.exists()
    assert (upload_dir / "INV-1001.pdf").exists()
    assert (upload_dir / "INV-1002.pdf").exists()

    listed = list_uploaded_invoice_files(root=tmp_path)
    names = {row["filename"] for row in listed}
    assert "INV-1001.pdf" in names
    assert "INV-1002.pdf" in names


def test_import_uploaded_invoice_files_without_overwrite_creates_unique_name(tmp_path: Path):
    import_uploaded_invoice_files([("INV-2001.pdf", b"original")], root=tmp_path, overwrite=True)
    stored = import_uploaded_invoice_files([("INV-2001.pdf", b"new")], root=tmp_path, overwrite=False)

    assert len(stored) == 1
    assert stored[0].name == "INV-2001_1.pdf"
