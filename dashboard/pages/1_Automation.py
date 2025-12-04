#!/usr/bin/env python3
"""
Invoice Automation Page - Dark Theme
====================================

Import Excel manifests and process invoice/PO documents.
"""

import sys
from pathlib import Path

# Get project root and add to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from project root .env BEFORE any other imports
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="Invoice Automation | NexusTax",
    page_icon="",
    layout="wide",
)

# Auth
from core.auth import require_authentication
if not require_authentication():
    st.stop()

# Import styles
from dashboard.styles import inject_css
inject_css()

# Import data loader functions
from dashboard.utils.data_loader import (
    get_projects_from_db,
    create_project,
    save_analysis_results,
    load_project_analysis,
)

# =============================================================================
# PAGE HEADER
# =============================================================================
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <h1 style="font-size: 1.875rem; font-weight: 700; color: #ffffff; margin: 0;">
        Invoice Automation
    </h1>
    <p style="color: #9ca3af; margin-top: 0.25rem;">
        Import transaction manifests and process documents for tax analysis.
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# PROJECT SELECTOR
# =============================================================================
st.markdown("### Select or Create Project")

# Load existing projects
projects = get_projects_from_db()
project_options = ["+ Create New Project"] + [f"{p['name']} ({p.get('tax_type', 'N/A')})" for p in projects]
project_map = {f"{p['name']} ({p.get('tax_type', 'N/A')})": p for p in projects}

col1, col2 = st.columns([3, 1])

with col1:
    selected_project = st.selectbox(
        "Project",
        project_options,
        key="project_selector",
        label_visibility="collapsed"
    )

with col2:
    if st.session_state.get("current_project_id"):
        st.markdown(f"""
        <div style="background: rgba(34, 197, 94, 0.2); padding: 0.5rem; border-radius: 0.5rem; text-align: center;">
            <span style="color: #86efac; font-size: 0.8rem;">Project Active</span>
        </div>
        """, unsafe_allow_html=True)

# Handle project selection
if selected_project == "+ Create New Project":
    with st.expander("Create New Project", expanded=True):
        new_project_name = st.text_input("Project Name", placeholder="e.g., T-Mobile Q4 2024 Sales Tax")
        col_a, col_b = st.columns(2)
        with col_a:
            new_tax_type = st.selectbox("Tax Type", ["sales_tax", "use_tax"], key="new_project_tax_type")
        with col_b:
            new_client_name = st.text_input("Client Name (optional)", placeholder="e.g., T-Mobile")

        if st.button("Create Project", type="primary"):
            if new_project_name:
                project_id = create_project(
                    name=new_project_name,
                    tax_type=new_tax_type,
                    client_name=new_client_name,
                )
                if project_id:
                    st.session_state.current_project_id = project_id
                    st.session_state.current_project_name = new_project_name
                    st.success(f"Project '{new_project_name}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create project. Check database connection.")
            else:
                st.warning("Please enter a project name.")
elif selected_project in project_map:
    project = project_map[selected_project]
    st.session_state.current_project_id = project["id"]
    st.session_state.current_project_name = project["name"]

    # Check if this project has saved analysis
    saved_df = load_project_analysis(project["id"])
    if not saved_df.empty:
        st.markdown(f"""
        <div style="
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 0.75rem;
            padding: 1rem;
            margin: 0.5rem 0;
        ">
            <div style="color: #93c5fd; font-weight: 600;">
                Project has {len(saved_df)} saved analysis results
            </div>
            <div style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.25rem;">
                Click "Load Saved Results" to continue where you left off
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Load Saved Results"):
            st.session_state.manifest_df = saved_df
            st.session_state.analysis_results = saved_df
            st.success("Loaded saved analysis results!")
            st.rerun()

st.markdown("---")

# =============================================================================
# SECTION 1: EXCEL MANIFEST IMPORT
# =============================================================================
st.markdown("### Step 1: Import Excel Manifest")
st.markdown("""
<div style="font-size: 0.875rem; color: #9ca3af; margin-bottom: 1rem;">
    Upload your SalesTax_Claims.xlsx or UseTax_Claims.xlsx file containing transaction data.
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    manifest_file = st.file_uploader(
        "Upload Excel Manifest",
        type=["xlsx", "xls"],
        key="manifest_upload",
        label_visibility="collapsed"
    )

with col2:
    tax_type = st.selectbox(
        "Tax Type",
        ["Sales Tax", "Use Tax"],
        key="manifest_tax_type"
    )

# Process manifest if uploaded
if manifest_file:
    try:
        manifest_df = pd.read_excel(manifest_file)
        st.session_state.manifest_df = manifest_df
        st.session_state.loaded_tax_type = tax_type

        # Show success and preview
        st.markdown(f"""
        <div style="
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 0.75rem;
            padding: 1rem;
            margin: 1rem 0;
        ">
            <div style="color: #86efac; font-weight: 600;">
                Loaded {len(manifest_df)} transactions from {manifest_file.name}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show the data
        st.dataframe(
            manifest_df,
            use_container_width=True,
            height=300,
            column_config={
                "Initial Amount": st.column_config.NumberColumn(format="$%.2f"),
                "Tax Paid": st.column_config.NumberColumn(format="$%.2f"),
                "Tax Remitted": st.column_config.NumberColumn(format="$%.2f"),
                "Total Amount": st.column_config.NumberColumn(format="$%.2f"),
            }
        )

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transactions", len(manifest_df))
        with col2:
            if "Total Amount" in manifest_df.columns:
                total = manifest_df["Total Amount"].sum()
                st.metric("Total Amount", f"${total:,.2f}")
            elif "Initial Amount" in manifest_df.columns:
                total = manifest_df["Initial Amount"].sum()
                st.metric("Total Amount", f"${total:,.2f}")
        with col3:
            tax_col = "Tax Paid" if "Tax Paid" in manifest_df.columns else "Tax Remitted"
            if tax_col in manifest_df.columns:
                tax_total = manifest_df[tax_col].sum()
                st.metric("Total Tax", f"${tax_total:,.2f}")

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")

st.markdown("---")

# =============================================================================
# SECTION 2: DOCUMENT FOLDERS (OPTIONAL)
# =============================================================================
st.markdown("### Step 2: Link Document Folders (Optional)")
st.markdown("""
<div style="font-size: 0.875rem; color: #9ca3af; margin-bottom: 1rem;">
    Provide paths to your invoice and purchase order folders to validate against the manifest.
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    invoices_path = st.text_input(
        "Invoices Folder",
        placeholder="/Users/jacoballen/Desktop/refund-engine/test_data/sales_tax/invoices",
        key="invoices_folder_path"
    )

with col2:
    po_path = st.text_input(
        "Purchase Orders Folder",
        placeholder="/Users/jacoballen/Desktop/refund-engine/test_data/sales_tax/purchase_orders",
        key="po_folder_path"
    )

SUPPORTED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.xlsx', '.xls', '.docx', '.msg'}

invoice_files = []
po_files = []

# Check folders (strip whitespace from paths)
if invoices_path:
    inv_folder = Path(invoices_path.strip())
    if inv_folder.exists() and inv_folder.is_dir():
        invoice_files = [f for f in inv_folder.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

if po_path:
    po_folder = Path(po_path.strip())
    if po_folder.exists() and po_folder.is_dir():
        po_files = [f for f in po_folder.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

# Show folder status
if invoice_files or po_files:
    st.markdown(f"""
    <div style="
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 0.75rem;
        padding: 1rem;
        margin: 1rem 0;
    ">
        <div style="color: #93c5fd; font-weight: 600;">Document Folders Linked</div>
        <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #93c5fd;">
            <div>Invoices: {len(invoice_files)} files</div>
            <div>Purchase Orders: {len(po_files)} files</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 3: PROCESS & ANALYZE
# =============================================================================
st.markdown("### Step 3: Process Transactions")

if st.session_state.get("manifest_df") is not None:
    manifest_df = st.session_state.manifest_df

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Run AI Analysis", type="primary", use_container_width=True):
            st.session_state.run_analysis = True

    with col2:
        if st.button("Export to Claims", use_container_width=True):
            st.info("Export functionality - transactions will be sent to Claims page")

    # Run analysis if requested
    if st.session_state.get("run_analysis"):
        st.session_state.run_analysis = False

        st.markdown("#### Analysis Results")

        # Get folder paths - read directly from widget keys
        inv_folder = st.session_state.get("invoices_folder_path", "").strip()
        po_folder = st.session_state.get("po_folder_path", "").strip()
        tax_type_raw = st.session_state.get("loaded_tax_type", "Sales Tax")
        tax_type = "sales_tax" if "Sales" in tax_type_raw else "use_tax"

        with st.spinner("Running AI analysis on invoices... This may take a few minutes."):
            try:
                # Import the real analyzer functions
                from analysis.fast_batch_analyzer import (
                    extract_invoice_with_vision,
                    categorize_product,
                    search_legal_docs,
                    analyze_batch,
                )

                analysis_df = manifest_df.copy()
                analysis_results = []

                # Find invoice and PO file columns
                inv_col = None
                for col in ["Inv-1 FileName", "Inv_1_File", "Invoice_File", "Invoice"]:
                    if col in analysis_df.columns:
                        inv_col = col
                        break

                po_col = None
                for col in ["PO_FileName", "PO_File", "Purchase_Order_File", "PO"]:
                    if col in analysis_df.columns:
                        po_col = col
                        break

                progress_bar = st.progress(0)
                status_text = st.empty()

                # Show what we found
                st.info(f"Invoice col: {inv_col} | PO col: {po_col}")

                if inv_col and inv_folder:
                    # Process each row with invoice files
                    total_rows = len(analysis_df)
                    analysis_queue = []
                    files_found = 0
                    files_missing = []
                    extraction_errors = []  # Track extraction failures

                    for idx, row in analysis_df.iterrows():
                        progress = (idx + 1) / total_rows
                        progress_bar.progress(progress)

                        inv_file = row.get(inv_col)
                        if pd.isna(inv_file) or not inv_file:
                            continue

                        # Clean up the filename
                        inv_file = str(inv_file).strip()

                        # Find invoice file path
                        inv_path = Path(inv_folder) / inv_file

                        if not inv_path.exists():
                            files_missing.append(inv_file)
                            continue

                        files_found += 1

                        status_text.text(f"Extracting: {inv_file}")

                        # Extract invoice data
                        inv_data = extract_invoice_with_vision(str(inv_path))
                        if "error" in inv_data:
                            extraction_errors.append(f"{inv_file}: {inv_data.get('error', 'Unknown error')}")
                            continue

                        # Also extract PO data if available
                        po_data = {}
                        if po_col and po_folder:
                            po_file = row.get(po_col)
                            if po_file and not pd.isna(po_file):
                                po_file = str(po_file).strip()
                                po_path = Path(po_folder) / po_file
                                if po_path.exists():
                                    status_text.text(f"Extracting PO: {po_file}")
                                    po_data = extract_invoice_with_vision(str(po_path))
                                    if "error" in po_data:
                                        po_data = {}

                        # Get amount and tax from manifest
                        amount = row.get("Initial Amount", row.get("Amount", 0)) or 0
                        tax = row.get("Tax Paid", row.get("Tax Remitted", row.get("Tax", 0))) or 0

                        # Categorize product - use description from manifest, invoice, or PO
                        manifest_desc = row.get("Description", "")
                        line_items = inv_data.get("line_items", [])
                        inv_desc = line_items[0].get("description", "") if line_items else ""
                        desc = manifest_desc or inv_desc
                        category = categorize_product(desc)

                        # Extract location data from invoice for rate lookup
                        ship_to_city = inv_data.get("ship_to_city", "")
                        ship_to_state = inv_data.get("ship_to_state", "")
                        ship_to_zip = str(inv_data.get("ship_to_zip", ""))
                        invoice_date = inv_data.get("invoice_date", row.get("Date", ""))

                        # Calculate tax rate from invoice
                        subtotal = inv_data.get("subtotal", 0) or amount
                        inv_tax = inv_data.get("tax_amount", tax)
                        tax_rate_charged = round((inv_tax / subtotal * 100), 2) if subtotal > 0 else 0

                        # Look up correct WA tax rate (if we have location)
                        correct_rate = None
                        rate_difference = None
                        if ship_to_city and ship_to_state == "WA":
                            from core.wa_tax_rate_lookup import get_correct_rate
                            correct_rate = get_correct_rate(ship_to_city, ship_to_zip)
                            if correct_rate and tax_rate_charged > 0:
                                rate_difference = round(tax_rate_charged - correct_rate, 2)

                        analysis_queue.append({
                            "excel_row_idx": idx,
                            "vendor": row.get("Vendor", inv_data.get("vendor_name", "Unknown")),
                            "vendor_info": {},
                            "line_item": line_items[0] if line_items else {"description": desc, "amount": amount, "tax": tax},
                            "excel_description": desc,  # Description from manifest
                            "amount": float(amount),
                            "tax": float(tax),
                            "category": category,
                            "po_content": po_data,  # Include PO context for analysis
                            # Location data for Wrong Rate detection
                            "ship_to_city": ship_to_city,
                            "ship_to_state": ship_to_state,
                            "ship_to_zip": ship_to_zip,
                            "invoice_date": str(invoice_date)[:10] if invoice_date else "",
                            "tax_rate_charged": tax_rate_charged,
                            # WA DOR official rate lookup
                            "correct_rate": correct_rate,
                            "rate_difference": rate_difference,
                        })

                    # Show file stats and errors
                    st.info(f"Files found: {files_found} | Missing: {len(files_missing)} | Extraction errors: {len(extraction_errors)} | Queue size: {len(analysis_queue)}")

                    if extraction_errors:
                        with st.expander(f"Show {len(extraction_errors)} extraction errors"):
                            for err in extraction_errors[:20]:  # Show first 20
                                st.warning(err)

                    # Get legal context for unique categories
                    status_text.text("Researching tax law context...")
                    categories = set(item["category"] for item in analysis_queue)
                    legal_context = {}
                    for category in categories:
                        legal_context[category] = search_legal_docs(category, "WA")

                    # Batch analyze
                    if analysis_queue:
                        status_text.text(f"Analyzing {len(analysis_queue)} transactions with Claude...")
                        batch_size = 10
                        total_analyzed = 0
                        batch_errors = []

                        for batch_start in range(0, len(analysis_queue), batch_size):
                            batch = analysis_queue[batch_start:batch_start + batch_size]
                            batch_num = batch_start // batch_size + 1
                            try:
                                analyses = analyze_batch(batch, legal_context, "WA", tax_type)
                                if analyses:
                                    # Process this batch's results immediately (match by index within batch)
                                    for j, analysis in enumerate(analyses):
                                        if j < len(batch):
                                            queue_item = batch[j]
                                            idx = queue_item["excel_row_idx"]
                                            analysis_df.loc[idx, "AI_Confidence"] = analysis.get("confidence_score", 0) / 100
                                            analysis_df.loc[idx, "Taxability"] = "Exempt" if not analysis.get("is_taxable_in_wa", True) else "Taxable"
                                            analysis_df.loc[idx, "Refund_Basis"] = analysis.get("refund_basis", "")
                                            analysis_df.loc[idx, "Refund_Eligible"] = "Yes" if analysis.get("estimated_refund_amount", 0) > 0 else "No"
                                            analysis_df.loc[idx, "Legal_Citation"] = ", ".join(analysis.get("legal_citations", []))
                                            analysis_df.loc[idx, "Explanation"] = analysis.get("explanation", "")
                                            total_analyzed += 1
                                    if len(analyses) < len(batch):
                                        batch_errors.append(f"Batch {batch_num}: got {len(analyses)}/{len(batch)} results")
                                else:
                                    batch_errors.append(f"Batch {batch_num}: returned empty/None")
                            except Exception as batch_ex:
                                batch_errors.append(f"Batch {batch_num}: {str(batch_ex)}")

                        # Show batch analysis results
                        st.info(f"Batch analysis complete: {total_analyzed} results from {len(analysis_queue)} items")
                        if batch_errors:
                            with st.expander(f"Show {len(batch_errors)} batch issues"):
                                for err in batch_errors:
                                    st.warning(err)

                    status_text.text("Analysis complete!")
                else:
                    st.warning("Please provide an invoice folder path and ensure your manifest has an invoice filename column.")
                    # Fallback to basic display
                    analysis_df["AI_Confidence"] = 0
                    analysis_df["Taxability"] = "Not Analyzed"
                    analysis_df["Refund_Eligible"] = "Unknown"

                progress_bar.empty()
                status_text.empty()

            except ImportError as e:
                import traceback
                st.error(f"Could not import analyzer: {e}")
                st.code(traceback.format_exc())
                analysis_df = manifest_df.copy()
                analysis_df["AI_Confidence"] = 0
                analysis_df["Taxability"] = "Import Error"
            except Exception as e:
                import traceback
                st.error(f"Analysis error: {e}")
                st.code(traceback.format_exc())
                analysis_df = manifest_df.copy()
                analysis_df["AI_Confidence"] = 0
                analysis_df["Taxability"] = "Error"

            # Store results
            st.session_state.analysis_results = analysis_df

            # Display results
            st.dataframe(
                analysis_df,
                use_container_width=True,
                column_config={
                    "AI_Confidence": st.column_config.ProgressColumn(
                        "AI Confidence",
                        min_value=0,
                        max_value=1,
                        format="%.0f%%"
                    ),
                    "Initial Amount": st.column_config.NumberColumn(format="$%.2f"),
                    "Tax Paid": st.column_config.NumberColumn(format="$%.2f"),
                    "Tax Remitted": st.column_config.NumberColumn(format="$%.2f"),
                    "Total Amount": st.column_config.NumberColumn(format="$%.2f"),
                }
            )

            # Summary
            if "Taxability" in analysis_df.columns:
                exempt_count = len(analysis_df[analysis_df["Taxability"] == "Exempt"])
                taxable_count = len(analysis_df[analysis_df["Taxability"] == "Taxable"])
                not_analyzed = len(analysis_df) - exempt_count - taxable_count
            else:
                exempt_count = taxable_count = not_analyzed = 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Exempt (Refund Eligible)", exempt_count)
            with col2:
                st.metric("Taxable (No Refund)", taxable_count)
            with col3:
                if "AI_Confidence" in analysis_df.columns:
                    avg_conf = analysis_df["AI_Confidence"].mean()
                    st.metric("Avg Confidence", f"{avg_conf:.0%}")
                else:
                    st.metric("Not Analyzed", not_analyzed)

            # Save Project button
            if st.session_state.get("current_project_id"):
                if st.button("Save Project", type="primary", use_container_width=True):
                    success = save_analysis_results(
                        st.session_state.current_project_id,
                        analysis_df
                    )
                    if success:
                        st.success(f"Project '{st.session_state.get('current_project_name', 'Untitled')}' saved to database!")
                    else:
                        st.error("Failed to save project. Check database connection.")
            else:
                st.warning("Select or create a project to save your analysis results.")

    # =============================================================================
    # SECTION 4: DOWNLOAD & RE-IMPORT (after analysis)
    # =============================================================================
    if st.session_state.get("analysis_results") is not None:
        st.markdown("---")
        st.markdown("### Step 4: Review & Re-import")
        st.markdown("""
        <div style="font-size: 0.875rem; color: #9ca3af; margin-bottom: 1rem;">
            Download the analyzed results, review/edit in Excel, then re-import to detect your changes.
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Download button
            from io import BytesIO
            output = BytesIO()
            st.session_state.analysis_results.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="Download Analyzed Excel",
                data=output,
                file_name="analyzed_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

        with col2:
            st.markdown("""
            <div style="
                background: rgba(59, 130, 246, 0.15);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 0.5rem;
                padding: 0.75rem;
                font-size: 0.8rem;
                color: #93c5fd;
            ">
                <strong>Workflow:</strong><br>
                1. Download → 2. Edit in Excel → 3. Re-import below
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Re-import section
        reimport_file = st.file_uploader(
            "Re-import Edited Excel",
            type=["xlsx", "xls"],
            key="reimport_upload",
            help="Upload your edited Excel file to detect changes"
        )

        if reimport_file:
            try:
                edited_df = pd.read_excel(reimport_file)
                original_df = st.session_state.analysis_results

                # Compare and find changes
                st.markdown("#### Changes Detected")

                # Find rows where INPUT columns changed (requires re-analysis)
                input_cols = ["PO_FileName", "PO_File", "Inv-1 FileName", "Invoice_File"]
                input_changes = []

                for col in input_cols:
                    if col in edited_df.columns and col in original_df.columns:
                        for idx in range(min(len(edited_df), len(original_df))):
                            orig_val = str(original_df.iloc[idx].get(col, "")).strip()
                            new_val = str(edited_df.iloc[idx].get(col, "")).strip()
                            # Check if PO/Invoice was added (was empty, now has value)
                            if (not orig_val or orig_val == "nan") and new_val and new_val != "nan":
                                input_changes.append({
                                    "Row": idx + 1,
                                    "Column": col,
                                    "Change": f"Added: {new_val[:40]}{'...' if len(new_val) > 40 else ''}",
                                    "row_idx": idx,
                                })

                # Show input changes (new PO/invoice detected)
                if input_changes:
                    st.markdown("""
                    <div style="
                        background: rgba(139, 92, 246, 0.15);
                        border: 1px solid rgba(139, 92, 246, 0.3);
                        border-radius: 0.75rem;
                        padding: 1rem;
                        margin-bottom: 1rem;
                    ">
                        <div style="color: #c4b5fd; font-weight: 600;">
                            New Documents Detected - Re-analysis Available
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    input_df = pd.DataFrame([{k: v for k, v in c.items() if k != "row_idx"} for c in input_changes])
                    st.dataframe(input_df, use_container_width=True, hide_index=True)

                    if st.button("Re-analyze Rows with New Documents", type="secondary"):
                        st.info("Re-analysis triggered for rows with new PO/Invoice files. This will use the updated document context.")
                        # Store rows needing re-analysis for when user clicks "Run AI Analysis"
                        st.session_state.reanalyze_rows = [c["row_idx"] for c in input_changes]
                        st.session_state.manifest_df = edited_df
                        st.rerun()

                # Find rows where OUTPUT columns changed (human edits)
                output_cols = ["Refund_Basis", "Taxability", "Refund_Eligible", "Legal_Citation", "Explanation"]
                changes_found = []

                for col in output_cols:
                    if col in edited_df.columns and col in original_df.columns:
                        for idx in range(min(len(edited_df), len(original_df))):
                            orig_val = str(original_df.iloc[idx].get(col, ""))
                            new_val = str(edited_df.iloc[idx].get(col, ""))
                            if orig_val != new_val:
                                changes_found.append({
                                    "Row": idx + 1,
                                    "Column": col,
                                    "Original": orig_val[:50] + "..." if len(orig_val) > 50 else orig_val,
                                    "New Value": new_val[:50] + "..." if len(new_val) > 50 else new_val,
                                })

                if changes_found:
                    changes_df = pd.DataFrame(changes_found)
                    st.dataframe(changes_df, use_container_width=True, hide_index=True)

                    st.markdown(f"""
                    <div style="
                        background: rgba(34, 197, 94, 0.15);
                        border: 1px solid rgba(34, 197, 94, 0.3);
                        border-radius: 0.75rem;
                        padding: 1rem;
                        margin-top: 1rem;
                    ">
                        <div style="color: #86efac; font-weight: 600;">
                            {len(changes_found)} edits detected
                        </div>
                        <div style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.25rem;">
                            These are OUTPUT column changes (your corrections). Click below to save as feedback.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Save corrections to feedback system
                    col_save1, col_save2 = st.columns(2)

                    with col_save1:
                        if st.button("Save Corrections as Feedback", type="primary", use_container_width=True):
                            try:
                                from core.feedback_system import FeedbackSystem
                                feedback_system = FeedbackSystem()

                                saved_count = 0
                                for change in changes_found:
                                    row_idx = change["Row"] - 1  # Convert back to 0-indexed
                                    if row_idx < len(edited_df):
                                        row = edited_df.iloc[row_idx]
                                        orig_row = original_df.iloc[row_idx] if row_idx < len(original_df) else {}

                                        # Build query from row context
                                        vendor = row.get("Vendor", row.get("Vendor_Name", "Unknown"))
                                        description = row.get("Description", "")
                                        query = f"Vendor: {vendor}, Product: {description}"

                                        # Build response text (AI's original output)
                                        response_text = f"Original {change['Column']}: {change['Original']}"

                                        # Build feedback data
                                        feedback_data = {
                                            "feedback_type": "correction",
                                            "rating": 3,  # Neutral - correction made
                                            "suggested_answer": str(change["New Value"]),
                                            "feedback_comment": f"Human corrected {change['Column']} from '{change['Original']}' to '{change['New Value']}'",
                                        }

                                        feedback_system.save_feedback(
                                            query=query,
                                            response_text=response_text,
                                            feedback_data=feedback_data,
                                        )
                                        saved_count += 1

                                st.success(f"Saved {saved_count} corrections to feedback database!")
                            except Exception as e:
                                st.error(f"Failed to save feedback: {e}")

                    with col_save2:
                        # Update session state with edited data
                        if st.button("Apply Changes Only", use_container_width=True):
                            st.session_state.analysis_results = edited_df
                            st.success("Changes applied to current session!")
                            st.rerun()

                    # Audit Trail section
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("View Edit History (Audit Trail)"):
                        st.markdown("""
                        <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.75rem;">
                            Complete record of all corrections made to this analysis.
                        </div>
                        """, unsafe_allow_html=True)

                        # Display changes as audit log
                        audit_df = pd.DataFrame(changes_found)
                        audit_df["Timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        audit_df["Changed By"] = "Current User"  # Would be populated from auth
                        audit_df = audit_df[["Timestamp", "Row", "Column", "Original", "New Value", "Changed By"]]

                        st.dataframe(
                            audit_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Timestamp": st.column_config.TextColumn("When"),
                                "Row": st.column_config.NumberColumn("Row #"),
                                "Column": st.column_config.TextColumn("Field"),
                                "Original": st.column_config.TextColumn("Before"),
                                "New Value": st.column_config.TextColumn("After"),
                                "Changed By": st.column_config.TextColumn("Who"),
                            }
                        )
                else:
                    st.info("No changes detected between original and edited file.")

            except Exception as e:
                st.error(f"Error reading edited file: {e}")

else:
    st.markdown("""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
        color: #9ca3af;
    ">
        Upload an Excel manifest in Step 1 to begin processing.
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="font-size: 0.75rem; color: #6b7280; text-align: center;">
    AI-powered extraction using GPT-4 Vision | Classification via Claude Sonnet
</div>
""", unsafe_allow_html=True)
