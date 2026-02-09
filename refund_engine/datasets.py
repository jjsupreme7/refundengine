from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from refund_engine.constants import DEFAULT_DATASETS_PATH


@dataclass(frozen=True)
class DatasetColumns:
    vendor: str
    tax_amount: str
    invoice_1: str
    analysis_col: str
    description: str | None = None
    invoice_2: str | None = None
    tax_base: str | None = None
    invoice_number: str | None = None
    po_number: str | None = None
    rate: str | None = None
    jurisdiction: str | None = None


@dataclass(frozen=True)
class DatasetFilter:
    column: str
    op: str
    value: Any = None


@dataclass(frozen=True)
class DatasetConfig:
    dataset_id: str
    description: str
    source_file: Path
    output_file: Path
    sheet_name: str | None
    invoice_path: Path
    columns: DatasetColumns
    filters: tuple[DatasetFilter, ...]


def _expand_path(path_str: str) -> Path:
    return Path(path_str).expanduser()


def load_datasets_config(config_path: str | Path | None = None) -> dict[str, DatasetConfig]:
    path = Path(config_path or DEFAULT_DATASETS_PATH)
    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    datasets_raw = raw.get("datasets", {})
    configs: dict[str, DatasetConfig] = {}
    for dataset_id, spec in datasets_raw.items():
        columns = DatasetColumns(**spec["columns"])
        filters = tuple(
            DatasetFilter(
                column=item["column"],
                op=item.get("op", "equals"),
                value=item.get("value"),
            )
            for item in spec.get("filters", [])
        )
        configs[dataset_id] = DatasetConfig(
            dataset_id=dataset_id,
            description=spec.get("description", dataset_id),
            source_file=_expand_path(spec["source_file"]),
            output_file=_expand_path(spec["output_file"]),
            sheet_name=spec.get("sheet_name"),
            invoice_path=_expand_path(spec["invoice_path"]),
            columns=columns,
            filters=filters,
        )
    return configs


def get_dataset_config(dataset_id: str, config_path: str | Path | None = None) -> DatasetConfig:
    datasets = load_datasets_config(config_path=config_path)
    if dataset_id not in datasets:
        raise KeyError(
            f"Unknown dataset '{dataset_id}'. Available: {', '.join(sorted(datasets))}"
        )
    return datasets[dataset_id]


def _excel_engine(path: Path) -> str | None:
    return "pyxlsb" if path.suffix.lower() == ".xlsb" else None


def read_excel_dataframe(path: Path, sheet_name: str | None) -> pd.DataFrame:
    engine = _excel_engine(path)
    if sheet_name:
        df = pd.read_excel(path, sheet_name=sheet_name, engine=engine)
    else:
        df = pd.read_excel(path, engine=engine)
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    return df


def read_source_dataframe(config: DatasetConfig) -> pd.DataFrame:
    return read_excel_dataframe(config.source_file, config.sheet_name)


def is_blank(value: Any) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def coerce_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "").replace("$", "")
    try:
        return float(text)
    except ValueError:
        return None


def filter_unanalyzed_rows(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    for rule in config.filters:
        if rule.column not in df.columns:
            continue
        series = df[rule.column]
        if rule.op == "equals":
            mask &= series == rule.value
        elif rule.op == "not_empty":
            mask &= series.notna() & (series.astype(str).str.strip() != "")
        else:
            raise ValueError(f"Unsupported filter op '{rule.op}' for {rule.column}")

    if config.columns.invoice_1 in df.columns:
        invoice_series = df[config.columns.invoice_1]
        mask &= invoice_series.notna() & (invoice_series.astype(str).str.strip() != "")

    if config.columns.analysis_col in df.columns:
        analysis_series = df[config.columns.analysis_col]
        mask &= analysis_series.isna() | (analysis_series.astype(str).str.strip() == "")

    return df[mask]


def select_rows(
    df: pd.DataFrame,
    config: DatasetConfig,
    *,
    limit: int | None = None,
    row_index: int | None = None,
    vendor: str | None = None,
    min_amount: float | None = None,
) -> pd.DataFrame:
    selected = df

    if vendor:
        vendor_col = config.columns.vendor
        if vendor_col in selected.columns:
            selected = selected[
                selected[vendor_col].astype(str).str.contains(vendor, case=False, na=False)
            ]

    if min_amount is not None:
        amount_col = config.columns.tax_amount
        if amount_col in selected.columns:
            values = selected[amount_col].apply(coerce_float)
            selected = selected[values.fillna(0.0) >= float(min_amount)]

    if row_index is not None:
        if row_index in selected.index:
            selected = selected.loc[[row_index]]
        else:
            return selected.iloc[0:0]

    if limit is not None and limit >= 0:
        selected = selected.head(limit)

    return selected
