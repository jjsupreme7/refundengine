from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from refund_engine.constants import PROJECT_ROOT


DEFAULT_REPOSITORY_ROOT = PROJECT_ROOT / "webapp_data"
INVOICE_UPLOADS_DIRNAME = "invoices"


@dataclass(frozen=True)
class VersionRef:
    workbook_id: str
    version_id: str
    file_path: Path


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "workbook"


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _repo_root(root: str | Path | None = None) -> Path:
    return Path(root or DEFAULT_REPOSITORY_ROOT).expanduser()


def _workbooks_dir(root: Path) -> Path:
    return root / "workbooks"


def _workbook_dir(root: Path, workbook_id: str) -> Path:
    return _workbooks_dir(root) / workbook_id


def _metadata_path(root: Path, workbook_id: str) -> Path:
    return _workbook_dir(root, workbook_id) / "metadata.yaml"


def _invoices_dir(root: Path) -> Path:
    return root / INVOICE_UPLOADS_DIRNAME


def _load_metadata(root: Path, workbook_id: str) -> dict[str, Any]:
    path = _metadata_path(root, workbook_id)
    if not path.exists():
        return {
            "workbook_id": workbook_id,
            "display_name": workbook_id,
            "created_at": datetime.now().isoformat(),
            "versions": [],
        }
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _save_metadata(root: Path, workbook_id: str, metadata: dict[str, Any]):
    path = _metadata_path(root, workbook_id)
    _ensure_dir(path.parent)
    with open(path, "w") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)


def _excel_engine(path: Path) -> str | None:
    return "pyxlsb" if path.suffix.lower() == ".xlsb" else None


def _sheet_names(path: Path) -> list[str]:
    engine = _excel_engine(path)
    xls = pd.ExcelFile(path, engine=engine)
    return list(xls.sheet_names)


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip() or "upload.xlsx"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    idx = 1
    while True:
        candidate = path.with_name(f"{stem}_{idx}{suffix}")
        if not candidate.exists():
            return candidate
        idx += 1


def _read_sheet_sample(path: Path, sheet_name: str, max_rows: int) -> pd.DataFrame:
    engine = _excel_engine(path)
    return pd.read_excel(path, sheet_name=sheet_name, engine=engine, nrows=max_rows)


def _compare_sheet_samples(
    old_path: Path,
    new_path: Path,
    sheet_name: str,
    *,
    max_rows: int = 2500,
    max_examples: int = 200,
) -> dict[str, Any]:
    old_df = _read_sheet_sample(old_path, sheet_name, max_rows=max_rows)
    new_df = _read_sheet_sample(new_path, sheet_name, max_rows=max_rows)

    old_rows, new_rows = len(old_df), len(new_df)
    old_cols = list(old_df.columns)
    new_cols = list(new_df.columns)
    common_cols = [c for c in new_cols if c in old_cols]

    truncated = old_rows >= max_rows or new_rows >= max_rows
    compare_rows = min(old_rows, new_rows)
    changed_cells = 0
    changed_rows: list[int] = []

    for row_idx in range(compare_rows):
        row_changed = False
        for col in common_cols:
            old_val = old_df.iloc[row_idx][col]
            new_val = new_df.iloc[row_idx][col]
            old_text = "" if pd.isna(old_val) else str(old_val)
            new_text = "" if pd.isna(new_val) else str(new_val)
            if old_text != new_text:
                changed_cells += 1
                row_changed = True
        if row_changed:
            changed_rows.append(row_idx)
        if len(changed_rows) >= max_examples:
            break

    return {
        "sheet_name": sheet_name,
        "old_rows_sampled": old_rows,
        "new_rows_sampled": new_rows,
        "added_rows_sampled": max(0, new_rows - old_rows),
        "removed_rows_sampled": max(0, old_rows - new_rows),
        "old_columns": old_cols,
        "new_columns": new_cols,
        "added_columns": [c for c in new_cols if c not in old_cols],
        "removed_columns": [c for c in old_cols if c not in new_cols],
        "changed_cells_sampled": changed_cells,
        "changed_rows_sampled": changed_rows,
        "truncated": truncated,
        "max_rows_sampled": max_rows,
    }


def _compute_diff_summary(
    old_path: Path,
    new_path: Path,
    *,
    max_rows: int = 2500,
) -> dict[str, Any]:
    old_sheets = set(_sheet_names(old_path))
    new_sheets = set(_sheet_names(new_path))
    common = sorted(old_sheets & new_sheets)

    per_sheet = [
        _compare_sheet_samples(old_path, new_path, sheet, max_rows=max_rows)
        for sheet in common
    ]

    return {
        "old_file": str(old_path),
        "new_file": str(new_path),
        "created_at": datetime.now().isoformat(),
        "sheets_added": sorted(new_sheets - old_sheets),
        "sheets_removed": sorted(old_sheets - new_sheets),
        "sheets_compared": common,
        "per_sheet": per_sheet,
    }


def list_workbooks(root: str | Path | None = None) -> list[dict[str, Any]]:
    base = _repo_root(root)
    wb_dir = _workbooks_dir(base)
    if not wb_dir.exists():
        return []

    out: list[dict[str, Any]] = []
    for item in sorted(wb_dir.iterdir()):
        if not item.is_dir():
            continue
        metadata = _load_metadata(base, item.name)
        versions = metadata.get("versions", [])
        out.append(
            {
                "workbook_id": metadata.get("workbook_id", item.name),
                "display_name": metadata.get("display_name", item.name),
                "version_count": len(versions),
                "latest_version_id": versions[-1]["version_id"] if versions else None,
                "created_at": metadata.get("created_at"),
            }
        )
    return out


def get_invoice_upload_dir(*, root: str | Path | None = None) -> Path:
    base = _repo_root(root)
    path = _invoices_dir(base)
    _ensure_dir(path)
    return path


def import_uploaded_invoice_files(
    files: list[tuple[str, bytes]],
    *,
    root: str | Path | None = None,
    overwrite: bool = True,
) -> list[Path]:
    out_paths: list[Path] = []
    upload_dir = get_invoice_upload_dir(root=root)
    for original_name, data in files:
        base_name = Path(original_name or "invoice.pdf").name
        safe_name = _sanitize_filename(base_name)
        target = upload_dir / safe_name
        if not overwrite:
            target = _unique_path(target)
        with open(target, "wb") as f:
            f.write(data)
        out_paths.append(target)
    return out_paths


def list_uploaded_invoice_files(
    *,
    root: str | Path | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    upload_dir = get_invoice_upload_dir(root=root)
    files = [p for p in upload_dir.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for path in files[: max(0, int(limit))]:
        stat = path.stat()
        out.append(
            {
                "filename": path.name,
                "size_bytes": int(stat.st_size),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
    return out


def get_workbook_metadata(
    workbook_id: str,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    base = _repo_root(root)
    return _load_metadata(base, workbook_id)


def import_uploaded_workbook(
    file_bytes: bytes,
    filename: str,
    *,
    workbook_name: str | None = None,
    root: str | Path | None = None,
) -> VersionRef:
    base = _repo_root(root)
    _ensure_dir(_workbooks_dir(base))

    display_name = (workbook_name or Path(filename).stem).strip()
    workbook_id = _slugify(display_name)

    wb_root = _workbook_dir(base, workbook_id)
    versions_dir = wb_root / "versions"
    changes_dir = wb_root / "changes"
    _ensure_dir(versions_dir)
    _ensure_dir(changes_dir)

    metadata = _load_metadata(base, workbook_id)
    metadata["workbook_id"] = workbook_id
    metadata["display_name"] = display_name
    metadata.setdefault("created_at", datetime.now().isoformat())
    metadata.setdefault("versions", [])

    sanitized_name = _sanitize_filename(filename)
    version_id = _now_stamp()
    stored_name = f"{version_id}_{sanitized_name}"
    file_path = versions_dir / stored_name
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    sheet_names = _sheet_names(file_path)

    version_entry: dict[str, Any] = {
        "version_id": version_id,
        "filename": sanitized_name,
        "stored_path": str(file_path),
        "created_at": datetime.now().isoformat(),
        "sheet_names": sheet_names,
        "diff_summary_path": None,
    }

    previous_versions = metadata["versions"]
    if previous_versions:
        previous_path = Path(previous_versions[-1]["stored_path"])
        diff_summary = _compute_diff_summary(previous_path, file_path)
        diff_path = changes_dir / f"{version_id}.json"
        with open(diff_path, "w") as f:
            json.dump(diff_summary, f, indent=2)
        version_entry["diff_summary_path"] = str(diff_path)

    metadata["versions"].append(version_entry)
    _save_metadata(base, workbook_id, metadata)

    return VersionRef(workbook_id=workbook_id, version_id=version_id, file_path=file_path)


def read_diff_summary(
    workbook_id: str,
    version_id: str,
    *,
    root: str | Path | None = None,
) -> dict[str, Any] | None:
    metadata = get_workbook_metadata(workbook_id, root=root)
    for entry in metadata.get("versions", []):
        if entry.get("version_id") != version_id:
            continue
        path_str = entry.get("diff_summary_path")
        if not path_str:
            return None
        path = Path(path_str)
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)
    return None


def get_version_ref(
    workbook_id: str,
    version_id: str,
    *,
    root: str | Path | None = None,
) -> VersionRef:
    metadata = get_workbook_metadata(workbook_id, root=root)
    for entry in metadata.get("versions", []):
        if entry.get("version_id") == version_id:
            return VersionRef(
                workbook_id=workbook_id,
                version_id=version_id,
                file_path=Path(entry["stored_path"]),
            )
    raise KeyError(f"Version '{version_id}' not found for workbook '{workbook_id}'")


def read_sheet_dataframe(
    workbook_id: str,
    version_id: str,
    sheet_name: str,
    *,
    root: str | Path | None = None,
) -> pd.DataFrame:
    ref = get_version_ref(workbook_id, version_id, root=root)
    return pd.read_excel(
        ref.file_path,
        sheet_name=sheet_name,
        engine=_excel_engine(ref.file_path),
    )


def write_updated_sheet_as_new_version(
    workbook_id: str,
    base_version_id: str,
    sheet_name: str,
    updated_df: pd.DataFrame,
    *,
    note: str = "analyzed",
    root: str | Path | None = None,
) -> VersionRef:
    base = _repo_root(root)
    base_ref = get_version_ref(workbook_id, base_version_id, root=base)
    metadata = get_workbook_metadata(workbook_id, root=base)

    out_name = f"{metadata.get('display_name', workbook_id)}_{note}.xlsx"
    base_file = base_ref.file_path
    engine = _excel_engine(base_file)
    xls = pd.ExcelFile(base_file, engine=engine)

    temp_path = base_file.parent / f"{_now_stamp()}_{_sanitize_filename(out_name)}"
    with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
        for sheet in xls.sheet_names:
            if sheet == sheet_name:
                df = updated_df
            else:
                df = pd.read_excel(base_file, sheet_name=sheet, engine=engine)
            df.to_excel(writer, sheet_name=sheet, index=False)

    with open(temp_path, "rb") as f:
        data = f.read()
    temp_path.unlink(missing_ok=True)

    return import_uploaded_workbook(
        data,
        filename=out_name,
        workbook_name=metadata.get("display_name", workbook_id),
        root=base,
    )
