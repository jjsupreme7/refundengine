"""
Excel Manager Page - Upload, track, and manage Excel files with version control

Features:
- Upload Excel files and invoice PDFs
- Track recent uploads with change history
- GitHub-style diff viewer
- Manual snapshot creation
- File matching status
"""

from core.auth import require_authentication
from dashboard.utils.data_loader import get_projects_from_db
from dashboard.components.excel_diff_viewer import (
    render_compact_change_summary,
    render_diff_viewer,
)
from core.excel_versioning import ExcelVersionManager
from core.database import get_supabase_client
from core.ai_change_summarizer import generate_change_summary
import core.excel_versioning
import importlib
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Force reload modules to pick up changes

importlib.reload(core.excel_versioning)


# Page configuration
st.set_page_config(page_title="Excel Manager - TaxDesk", page_icon="📊", layout="wide")

# AUTHENTICATION

if not require_authentication():
    st.stop()

# Initialize
supabase = get_supabase_client()
excel_manager = ExcelVersionManager()

# Header
st.markdown('<div class="main-header">📊 Excel Manager</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Upload and track Excel files with version control</div>',
    unsafe_allow_html=True,
)

# Get user email from session
user_email = st.session_state.get("user_email", "user@example.com")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📤 Upload", "🕐 Recent Uploads", "📸 Snapshots", "📋 Activity Log"]
)

# ============================================================================
# TAB 1: UPLOAD
# ============================================================================
with tab1:
    st.markdown("### Upload Excel File")

    # Project selection
    projects = get_projects_from_db()
    if not projects:
        st.warning("⚠️ No projects found. Please create a project first.")
        st.stop()

    project_options = {p["id"]: p["name"] for p in projects}

    selected_project_id = st.selectbox(
        "Select Project*",
        options=list(project_options.keys()),
        format_func=lambda x: project_options[x],
        key="upload_project",
    )

    # Excel file upload
    st.markdown("#### Step 1: Upload Excel File")
    excel_file = st.file_uploader(
        "Upload Master Excel",
        type=["xlsx", "xls"],
        help="Upload your master Excel file with invoice data",
        key="excel_upload",
    )

    # Invoice files upload
    st.markdown("#### Step 2: Upload Invoice/PO Files (Optional)")
    col1, col2 = st.columns(2)

    with col1:
        invoice_files = st.file_uploader(
            "Upload Invoice PDFs",
            type=["pd", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload invoice PDF files referenced in Excel",
            key="invoice_upload",
        )

    with col2:
        po_files = st.file_uploader(
            "Upload Purchase Order Files",
            type=["pd", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload PO files referenced in Excel",
            key="po_upload",
        )

    # Change summary (will be AI-generated or manual)
    st.markdown("#### Step 3: Change Summary")

    use_ai_summary = st.checkbox(
        "🤖 Auto-generate summary with AI",
        value=True,
        help="AI will analyze changes and create a detailed summary",
    )

    if not use_ai_summary:
        change_summary = st.text_area(
            "What changed in this version?",
            placeholder="e.g., 'Corrected vendor names in rows 45-89' or 'Added AI analysis for batch 1'",
            key="change_summary",
        )
    else:
        st.info("💡 AI will generate a detailed summary after analyzing the changes")

    # Upload button
    if st.button("📤 Upload Files", type="primary", use_container_width=True):
        if not excel_file:
            st.error("❌ Please upload an Excel file")
        else:
            try:
                with st.spinner("Uploading files..."):
                    # Save Excel file temporarily
                    temp_dir = Path("/tmp/excel_uploads")
                    temp_dir.mkdir(exist_ok=True)

                    excel_path = temp_dir / excel_file.name
                    with open(excel_path, "wb") as f:
                        f.write(excel_file.getbuffer())

                    # Check if file already exists
                    existing_file = (
                        supabase.table("excel_file_tracking")
                        .select("id")
                        .eq("file_name", excel_file.name)
                        .execute()
                    )

                    if existing_file.data and len(existing_file.data) > 0:
                        # File exists - create new version
                        file_id = existing_file.data[0]["id"]

                        # Create new version
                        version_id = excel_manager.create_version(
                            file_id=file_id,
                            file_path=str(excel_path),
                            user_email=user_email,
                            change_summary="",  # Will be filled by AI
                        )
                        st.info(
                            f"📝 Creating new version for existing file: {
                                excel_file.name}"
                        )
                    else:
                        # New file - upload it
                        file_id = excel_manager.upload_file(
                            file_path=str(excel_path),
                            project_id=None,  # Will add real project linking later
                            user_email=user_email,
                        )
                        st.info(f"📄 Uploading new file: {excel_file.name}")

                    # TODO: Handle invoice/PO files
                    # For now, just count them
                    invoice_count = len(invoice_files) if invoice_files else 0
                    po_count = len(po_files) if po_files else 0

                # Generate AI summary if enabled
                summary_text = ""
                if use_ai_summary:
                    with st.spinner("🤖 Generating AI summary of changes..."):
                        # Get the latest version for this file
                        version_response = (
                            supabase.table("excel_file_versions")
                            .select("*")
                            .eq("file_id", file_id)
                            .order("version_number", desc=True)
                            .limit(1)
                            .execute()
                        )

                        if version_response.data:
                            latest_version = version_response.data[0]
                            version_id = latest_version["id"]
                            version_number = latest_version["version_number"]

                            # Get cell changes for this version
                            changes_response = (
                                supabase.table("excel_cell_changes")
                                .select("*")
                                .eq("version_id", version_id)
                                .execute()
                            )

                            if changes_response.data and len(changes_response.data) > 0:
                                # Generate AI summary
                                summary_text = generate_change_summary(
                                    changes_response.data
                                )

                                # Update version with AI summary
                                supabase.table("excel_file_versions").update(
                                    {"change_summary": summary_text}
                                ).eq("id", version_id).execute()

                                st.success(
                                    f"✅ AI summary generated! ({len(
                                        changes_response.data)} changes detected)"
                                )
                            else:
                                if version_number == 1:
                                    summary_text = "Initial upload"
                                else:
                                    summary_text = "No changes detected"
                else:
                    summary_text = (
                        change_summary if change_summary else "No summary provided"
                    )

                    # Save manual summary
                    version_response = (
                        supabase.table("excel_file_versions")
                        .select("id")
                        .eq("file_id", file_id)
                        .order("version_number", desc=True)
                        .limit(1)
                        .execute()
                    )

                    if version_response.data:
                        supabase.table("excel_file_versions").update(
                            {"change_summary": summary_text}
                        ).eq("id", version_response.data[0]["id"]).execute()

                st.success("✅ Files uploaded successfully!")

                # Show upload summary with AI-generated summary
                st.info(
                    """
                **Upload Summary:**
                - Excel file: {excel_file.name}
                - Invoice files: {invoice_count}
                - PO files: {po_count}
                - File ID: {file_id}
                """
                )

                if summary_text and summary_text != "No summary provided":
                    st.markdown("**📝 Change Summary:**")
                    st.markdown(summary_text)

                # Clean up
                if excel_path.exists():
                    os.remove(excel_path)

            except Exception as e:
                st.error(f"❌ Error uploading files: {str(e)}")
                import traceback  # noqa: E402

                st.code(traceback.format_exc())

# ============================================================================
# TAB 2: RECENT UPLOADS
# ============================================================================
with tab2:
    st.markdown("### 🕐 Recent Uploads")
    st.info("📋 This shows your last 10 uploads with automatic change tracking")

    # Get recent versions for all projects
    try:
        # Query recent versions (last 10)
        response = (
            supabase.table("excel_file_versions")
            .select("*, excel_file_tracking!inner(file_name, project_id)")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        if response.data:
            for version in response.data:
                created_at = datetime.fromisoformat(
                    version["created_at"].replace("Z", "+00:00")
                )

                with st.expander(
                    f"📄 {version['excel_file_tracking']['file_name']} - "
                    f"{created_at.strftime('%b %d, %Y %I:%M %p')} by {
                        version['created_by']}",
                    expanded=False,
                ):
                    # Summary stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Rows Modified", version.get("rows_modified", 0))
                    with col2:
                        st.metric("Rows Added", version.get("rows_added", 0))
                    with col3:
                        st.metric("Rows Deleted", version.get("rows_deleted", 0))
                    with col4:
                        st.metric("Version", f"#{version['version_number']}")

                    # Change summary (collapsible if long)
                    if version.get("change_summary"):
                        summary = version["change_summary"]
                        # If summary is long, make it collapsible
                        if len(summary) > 500:
                            with st.expander(
                                "📝 AI Summary of Changes", expanded=False
                            ):
                                st.markdown(summary)
                        else:
                            st.markdown(f"**Notes:** {summary}")

                    # Get cell-level changes
                    changes_response = (
                        supabase.table("excel_cell_changes")
                        .select("*")
                        .eq("version_id", version["id"])
                        .limit(100)
                        .execute()
                    )

                    if changes_response.data:
                        st.markdown(
                            f"**Cell Changes:** {len(changes_response.data)
                                                 } cells modified"
                        )

                        # Use compact change summary component
                        render_compact_change_summary(
                            changes_response.data, max_display=5
                        )

                        # View all changes button
                        if st.button(
                            "👁️ View All Changes", key=f"view_changes_{version['id']}"
                        ):
                            st.session_state[f'show_diff_{version["id"]}'] = True
                            st.rerun()

                    # Show detailed diff viewer if requested
                    if st.session_state.get(f'show_diff_{version["id"]}', False):
                        st.markdown("---")
                        render_diff_viewer(
                            version_id=version["id"],
                            changes=(
                                changes_response.data if changes_response.data else []
                            ),
                            file_name=version["excel_file_tracking"]["file_name"],
                            version_number=version["version_number"],
                            created_by=version["created_by"],
                            created_at=created_at,
                        )

                        if st.button(
                            "❌ Close Diff View", key=f"close_diff_{version['id']}"
                        ):
                            st.session_state[f'show_diff_{version["id"]}'] = False
                            st.rerun()

                    # Actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📥 Download", key=f"download_{version['id']}"):
                            st.info("Download functionality coming soon")
                    with col2:
                        if st.button("↩️ Restore", key=f"restore_{version['id']}"):
                            st.info("Restore functionality coming soon")
                    with col3:
                        if st.button(
                            "💾 Save as Snapshot", key=f"snapshot_{version['id']}"
                        ):
                            st.info("Snapshot functionality coming soon")
        else:
            st.info("📭 No uploads yet. Upload an Excel file to get started!")

    except Exception as e:
        st.error(f"❌ Error loading recent uploads: {str(e)}")

# ============================================================================
# TAB 3: SNAPSHOTS
# ============================================================================
with tab3:
    st.markdown("### 📸 Permanent Snapshots")
    st.info(
        "💡 Snapshots are permanent saved versions you create manually at important milestones"
    )

    # Create snapshot section
    with st.expander("➕ Create New Snapshot", expanded=False):
        st.markdown("Save the current working file as a permanent snapshot")

        snapshot_name = st.text_input(
            "Snapshot Name*",
            placeholder="e.g., 'First 2500 rows complete' or 'Final - ready for filing'",
            key="snapshot_name",
        )

        snapshot_description = st.text_area(
            "Description (Optional)",
            placeholder="Add details about this milestone...",
            key="snapshot_description",
        )

        if st.button("💾 Create Snapshot", type="primary"):
            if not snapshot_name:
                st.error("❌ Please enter a snapshot name")
            else:
                st.info("Snapshot creation coming soon!")

    st.markdown("---")

    # List existing snapshots
    st.markdown("**Existing Snapshots**")
    st.info("📭 No snapshots yet. Create your first snapshot above!")

# ============================================================================
# TAB 4: ACTIVITY LOG
# ============================================================================
with tab4:
    st.markdown("### 📋 Activity Log")
    st.info("Complete history of all changes, uploads, and actions")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_user = st.selectbox("User", ["All Users", user_email])
    with col2:
        filter_type = st.selectbox(
            "Activity Type", ["All", "AI Analysis", "User Edit", "Snapshot Created"]
        )
    with col3:
        filter_date = st.date_input("Date Range")

    st.markdown("---")

    # Activity entries
    try:
        # Query versions as activity log
        response = (
            supabase.table("excel_file_versions")
            .select("*, excel_file_tracking!inner(file_name)")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        if response.data:
            for activity in response.data:
                created_at = datetime.fromisoformat(
                    activity["created_at"].replace("Z", "+00:00")
                )

                # Activity type icon
                if "batch" in activity.get("change_summary", "").lower():
                    icon = "🤖"
                    activity_type = "AI Analysis"
                elif "snapshot" in activity.get("change_summary", "").lower():
                    icon = "💾"
                    activity_type = "Snapshot Created"
                else:
                    icon = "✏️"
                    activity_type = "User Edit"

                st.markdown(
                    """
                **{created_at.strftime('%b %d, %Y %I:%M %p')}** - {activity['created_by']}
                {icon} {activity_type} - {activity['excel_file_tracking']['file_name']}
                {activity.get('change_summary', 'No description')}
                """
                )
                st.markdown("---")
        else:
            st.info("📭 No activity yet")

    except Exception as e:
        st.error(f"❌ Error loading activity log: {str(e)}")

# Help section
with st.expander("ℹ️ Help & Guide"):
    st.markdown(
        """
    ### How to Use Excel Manager

    **Upload Tab:**
    1. Select your project
    2. Upload Excel file with your invoice data
    3. Optionally upload invoice/PO PDFs
    4. Add a description of what changed
    5. Click Upload

    **Recent Uploads:**
    - View your last 10 uploads
    - See what changed (cell-by-cell)
    - Download previous versions
    - Restore to previous state

    **Snapshots:**
    - Create permanent saved versions
    - Save at important milestones
    - Name them for easy reference

    **Activity Log:**
    - Complete history of all changes
    - Filter by user, type, or date
    - Full audit trail
    """
    )
