from __future__ import annotations

from refund_engine.web_analysis import parse_row_selection, suggest_column_mapping


def test_parse_row_selection_handles_ranges_and_values():
    rows = parse_row_selection("1,3-5,9", max_rows=20)
    assert rows == [1, 3, 4, 5, 9]


def test_parse_row_selection_filters_out_of_bounds():
    rows = parse_row_selection("0,2,100-103", max_rows=5)
    assert rows == [0, 2]


def test_suggest_column_mapping_prefers_known_names():
    cols = [
        "Vendor Name",
        "Tax Remit",
        "Description",
        "Inv-1PDF",
        "Inv-2 PDF",
        "KOM Analysis & Notes",
        "INVNO",
        "PO Number",
    ]
    mapping = suggest_column_mapping(cols)
    assert mapping["vendor"] == "Vendor Name"
    assert mapping["tax_amount"] == "Tax Remit"
    assert mapping["invoice_1"] == "Inv-1PDF"
    assert mapping["analysis_col"] == "KOM Analysis & Notes"
