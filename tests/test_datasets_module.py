from __future__ import annotations

import pandas as pd

from refund_engine.datasets import (
    coerce_float,
    filter_unanalyzed_rows,
    get_dataset_config,
    load_datasets_config,
    select_rows,
)


def test_load_datasets_config_contains_expected_ids():
    configs = load_datasets_config()
    assert "sales_2024" in configs
    assert "use_tax_2023" in configs
    assert "use_tax_2024" in configs


def test_filter_unanalyzed_rows_handles_blank_strings():
    config = get_dataset_config("use_tax_2024")
    cols = config.columns
    df = pd.DataFrame(
        [
            {
                cols.vendor: "A",
                cols.invoice_1: "a.pdf",
                cols.analysis_col: "",
                "INDICATOR": "Remit",
            },
            {
                cols.vendor: "B",
                cols.invoice_1: "b.pdf",
                cols.analysis_col: None,
                "INDICATOR": "Remit",
            },
            {
                cols.vendor: "C",
                cols.invoice_1: "c.pdf",
                cols.analysis_col: "done",
                "INDICATOR": "Remit",
            },
        ]
    )
    filtered = filter_unanalyzed_rows(df, config)
    assert list(filtered.index) == [0, 1]


def test_select_rows_vendor_and_amount_filters():
    config = get_dataset_config("use_tax_2024")
    cols = config.columns
    df = pd.DataFrame(
        [
            {cols.vendor: "Acme", cols.tax_amount: "100.00", cols.invoice_1: "a.pdf", cols.analysis_col: ""},
            {cols.vendor: "Acme Corp", cols.tax_amount: "2,500.50", cols.invoice_1: "b.pdf", cols.analysis_col: ""},
            {cols.vendor: "Other", cols.tax_amount: "3000", cols.invoice_1: "c.pdf", cols.analysis_col: ""},
        ]
    )
    filtered = select_rows(df, config, vendor="acme", min_amount=500, limit=10)
    assert list(filtered.index) == [1]


def test_coerce_float_handles_currency_strings():
    assert coerce_float("$1,234.56") == 1234.56
    assert coerce_float("") is None
