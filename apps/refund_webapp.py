#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd
import streamlit as st

from refund_engine.config import get_openai_settings
from refund_engine.web_analysis import (
    ColumnMapping,
    analyze_rows_dataframe,
    parse_row_selection,
    suggest_column_mapping,
)
from refund_engine.workbook_repository import (
    DEFAULT_REPOSITORY_ROOT,
    get_workbook_metadata,
    import_uploaded_invoice_files,
    import_uploaded_workbook,
    list_uploaded_invoice_files,
    list_workbooks,
    read_diff_summary,
    read_sheet_dataframe,
    get_invoice_upload_dir,
    write_updated_sheet_as_new_version,
)


st.set_page_config(page_title="Refund Engine Webapp", layout="wide")
st.title("Refund Engine Local Webapp")
st.caption("Upload workbooks, track versions, and run targeted OpenAI row analysis.")


def _version_entry(metadata: dict, version_id: str) -> dict | None:
    for entry in metadata.get("versions", []):
        if entry.get("version_id") == version_id:
            return entry
    return None


@st.cache_data(show_spinner=False)
def _load_sheet(repo_root: str, workbook_id: str, version_id: str, sheet_name: str) -> pd.DataFrame:
    return read_sheet_dataframe(
        workbook_id,
        version_id,
        sheet_name,
        root=repo_root,
    )


def _mapping_select(
    label: str,
    columns: list[str],
    default_value: str | None,
    *,
    required: bool = True,
) -> str | None:
    options = ["<none>"] + columns
    default_index = options.index(default_value) if default_value in options else 0
    value = st.selectbox(label, options, index=default_index)
    if value == "<none>":
        return None
    if required and not value:
        return None
    return value


defaults = get_openai_settings()

with st.sidebar:
    st.header("Settings")
    repo_root = st.text_input("Repository Root", str(DEFAULT_REPOSITORY_ROOT))
    managed_invoice_dir = str(get_invoice_upload_dir(root=repo_root))
    if "invoice_dir" not in st.session_state:
        st.session_state["invoice_dir"] = managed_invoice_dir
    invoice_dir = st.text_input("Invoice Directory", key="invoice_dir")
    st.caption(f"Managed uploads folder: `{managed_invoice_dir}`")
    if st.button("Use Managed Invoice Folder"):
        st.session_state["invoice_dir"] = managed_invoice_dir
        st.rerun()
    model = st.text_input("Model", defaults.model_analysis)
    reasoning_effort = st.selectbox(
        "Reasoning Effort",
        ["low", "medium", "high"],
        index=["low", "medium", "high"].index(defaults.reasoning_effort),
    )
    verbosity = st.selectbox(
        "Verbosity",
        ["low", "medium", "high"],
        index=["low", "medium", "high"].index(defaults.text_verbosity),
    )
    max_invoice_pages = st.slider("Max Invoice Pages", min_value=1, max_value=20, value=4)


tab_upload, tab_analyze = st.tabs(["Upload / Versions", "Analyze Rows"])

with tab_upload:
    st.subheader("Upload Workbook")
    uploaded = st.file_uploader(
        "Upload Excel workbook",
        type=["xlsx", "xlsb"],
        accept_multiple_files=False,
    )
    workbook_name = st.text_input("Workbook Name (optional)")
    if st.button("Import Workbook Version", type="primary", disabled=uploaded is None):
        data = uploaded.getvalue() if uploaded else b""
        ref = import_uploaded_workbook(
            data,
            filename=uploaded.name if uploaded else "upload.xlsx",
            workbook_name=workbook_name or None,
            root=repo_root,
        )
        st.session_state["workbook_id"] = ref.workbook_id
        st.session_state["version_id"] = ref.version_id
        st.success(f"Imported as workbook `{ref.workbook_id}` version `{ref.version_id}`.")

    st.divider()
    st.subheader("Upload Invoice Files")
    invoice_uploads = st.file_uploader(
        "Upload invoice files (PDF/images)",
        type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "webp", "bmp"],
        accept_multiple_files=True,
    )
    overwrite_invoice_files = st.checkbox("Overwrite existing filenames", value=True)
    if st.button(
        "Import Invoice Files",
        type="primary",
        disabled=not invoice_uploads,
    ):
        payloads = [(f.name, f.getvalue()) for f in invoice_uploads if f]
        stored_files = import_uploaded_invoice_files(
            payloads,
            root=repo_root,
            overwrite=overwrite_invoice_files,
        )
        managed_dir = str(get_invoice_upload_dir(root=repo_root))
        st.session_state["invoice_dir"] = managed_dir
        st.success(
            f"Imported {len(stored_files)} file(s) to `{managed_dir}`. "
            "Invoice Directory updated automatically."
        )

    uploaded_invoice_files = list_uploaded_invoice_files(root=repo_root, limit=150)
    if uploaded_invoice_files:
        st.caption("Recently uploaded invoice files")
        st.dataframe(pd.DataFrame(uploaded_invoice_files), use_container_width=True)
    else:
        st.caption("No invoice files uploaded yet.")

    st.divider()
    st.subheader("Workbook Versions")
    workbooks = list_workbooks(root=repo_root)
    if not workbooks:
        st.info("No workbooks imported yet.")
    else:
        workbook_options = [w["workbook_id"] for w in workbooks]
        selected_workbook = st.selectbox(
            "Workbook",
            workbook_options,
            index=workbook_options.index(st.session_state.get("workbook_id"))
            if st.session_state.get("workbook_id") in workbook_options
            else 0,
        )
        st.session_state["workbook_id"] = selected_workbook
        metadata = get_workbook_metadata(selected_workbook, root=repo_root)

        versions = metadata.get("versions", [])
        if versions:
            version_ids = [v["version_id"] for v in versions]
            selected_version = st.selectbox(
                "Version",
                version_ids,
                index=version_ids.index(st.session_state.get("version_id"))
                if st.session_state.get("version_id") in version_ids
                else len(version_ids) - 1,
            )
            st.session_state["version_id"] = selected_version

            version_table = pd.DataFrame(
                [
                    {
                        "version_id": v.get("version_id"),
                        "created_at": v.get("created_at"),
                        "filename": v.get("filename"),
                        "sheet_count": len(v.get("sheet_names", [])),
                    }
                    for v in versions
                ]
            )
            st.dataframe(version_table, use_container_width=True)

            diff = read_diff_summary(selected_workbook, selected_version, root=repo_root)
            if diff:
                st.markdown("**Change Summary (sampled)**")
                st.json(diff)
            else:
                st.caption("No diff summary for this version (first version or unavailable).")


with tab_analyze:
    st.subheader("Analyze Specific Rows")
    workbook_id = st.session_state.get("workbook_id")
    version_id = st.session_state.get("version_id")
    if not workbook_id or not version_id:
        st.info("Import or select a workbook/version in the first tab.")
    else:
        metadata = get_workbook_metadata(workbook_id, root=repo_root)
        version = _version_entry(metadata, version_id)
        if version is None:
            st.error("Selected version not found.")
        else:
            sheets = version.get("sheet_names", [])
            if not sheets:
                st.error("No sheets found in selected version.")
            else:
                sheet = st.selectbox("Sheet", sheets)
                df = _load_sheet(repo_root, workbook_id, version_id, sheet)
                st.caption(f"Rows: {len(df):,} | Columns: {len(df.columns)}")
                st.dataframe(df.head(200), use_container_width=True)

                suggestions = suggest_column_mapping(list(df.columns))

                st.markdown("### Column Mapping")
                col1, col2, col3 = st.columns(3)
                with col1:
                    vendor_col = _mapping_select(
                        "Vendor Column",
                        list(df.columns),
                        suggestions.get("vendor"),
                    )
                    description_col = _mapping_select(
                        "Description Column",
                        list(df.columns),
                        suggestions.get("description"),
                    )
                    invoice_1_col = _mapping_select(
                        "Invoice 1 Column",
                        list(df.columns),
                        suggestions.get("invoice_1"),
                    )
                with col2:
                    tax_amount_col = _mapping_select(
                        "Tax Amount Column",
                        list(df.columns),
                        suggestions.get("tax_amount"),
                    )
                    analysis_col = _mapping_select(
                        "Analysis Column",
                        list(df.columns),
                        suggestions.get("analysis_col"),
                    )
                    invoice_2_col = _mapping_select(
                        "Invoice 2 Column",
                        list(df.columns),
                        suggestions.get("invoice_2"),
                        required=False,
                    )
                with col3:
                    tax_base_col = _mapping_select(
                        "Tax Base Column (optional)",
                        list(df.columns),
                        suggestions.get("tax_base"),
                        required=False,
                    )
                    invoice_number_col = _mapping_select(
                        "Invoice Number Column (optional)",
                        list(df.columns),
                        suggestions.get("invoice_number"),
                        required=False,
                    )
                    po_number_col = _mapping_select(
                        "PO Number Column (optional)",
                        list(df.columns),
                        suggestions.get("po_number"),
                        required=False,
                    )

                st.markdown("### Row Selection")
                row_selection = st.text_input(
                    "Rows to analyze (e.g. 12,15,20-25)",
                    value="",
                )
                try:
                    selected_rows = parse_row_selection(row_selection, max_rows=len(df))
                    st.caption(f"Selected rows: {selected_rows[:20]}{' ...' if len(selected_rows) > 20 else ''}")
                except Exception as exc:
                    selected_rows = []
                    st.error(f"Invalid row selection: {exc}")

                can_analyze = all(
                    [
                        vendor_col,
                        tax_amount_col,
                        description_col,
                        invoice_1_col,
                        analysis_col,
                        len(selected_rows) > 0,
                    ]
                )

                if st.button("Analyze Selected Rows", type="primary", disabled=not can_analyze):
                    mapping = ColumnMapping(
                        vendor=vendor_col,
                        tax_amount=tax_amount_col,
                        description=description_col,
                        invoice_1=invoice_1_col,
                        analysis_col=analysis_col,
                        invoice_2=invoice_2_col,
                        tax_base=tax_base_col,
                        invoice_number=invoice_number_col,
                        po_number=po_number_col,
                    )
                    with st.spinner("Running OpenAI analysis..."):
                        analyzed_df, events = analyze_rows_dataframe(
                            df,
                            mapping=mapping,
                            row_indices=selected_rows,
                            invoice_dir=invoice_dir,
                            model=model or None,
                            reasoning_effort=reasoning_effort,
                            verbosity=verbosity,
                            max_invoice_pages=max_invoice_pages,
                        )

                    st.session_state["analyzed_df"] = analyzed_df
                    st.session_state["analysis_events"] = events
                    st.session_state["analysis_context"] = {
                        "workbook_id": workbook_id,
                        "version_id": version_id,
                        "sheet": sheet,
                    }
                    st.success(f"Analyzed {len(selected_rows)} rows.")

                events = st.session_state.get("analysis_events")
                analyzed_df = st.session_state.get("analyzed_df")
                context = st.session_state.get("analysis_context", {})
                context_matches = (
                    context.get("workbook_id") == workbook_id
                    and context.get("version_id") == version_id
                    and context.get("sheet") == sheet
                )

                if events and analyzed_df is not None and context_matches:
                    st.markdown("### Analysis Results")
                    st.dataframe(pd.DataFrame(events), use_container_width=True)

                    if st.button("Save Analyzed Rows as New Version"):
                        new_ref = write_updated_sheet_as_new_version(
                            workbook_id,
                            version_id,
                            sheet,
                            analyzed_df,
                            note="analyzed",
                            root=repo_root,
                        )
                        st.session_state["version_id"] = new_ref.version_id
                        st.success(
                            "Saved new version "
                            f"`{new_ref.version_id}` for workbook `{new_ref.workbook_id}`."
                        )
