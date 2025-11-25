"""
Projects Page - Manage tax refund projects

View all projects, create new projects, and track progress.
"""

from core.auth import require_authentication
from core.database import get_supabase_client
from core.excel_versioning import ExcelVersionManager
from core.ai_change_summarizer import generate_change_summary
from dashboard.utils.data_loader import get_projects_from_db
import sys
from pathlib import Path
from datetime import datetime
import os

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Initialize clients
supabase = get_supabase_client()
excel_manager = ExcelVersionManager()


# Page configuration
st.set_page_config(page_title="Projects - TaxDesk", page_icon="📁", layout="wide")

# AUTHENTICATION

if not require_authentication():
    st.stop()

# Header
st.markdown('<div class="main-header">📁 Projects</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Manage your tax refund analysis projects</div>',
    unsafe_allow_html=True,
)

# Action buttons
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("➕ Create New Project", type="primary", use_container_width=True):
        st.session_state.show_create_project = True

with col2:
    if st.button("📥 Import Project", use_container_width=True):
        st.info("Import functionality coming soon")

st.markdown("---")

# Create project form
if st.session_state.get("show_create_project", False):
    with st.expander("✨ Create New Project", expanded=True):
        with st.form("create_project_form"):
            col1, col2 = st.columns(2)

            with col1:
                project_name = st.text_input(
                    "Project Name*", placeholder="e.g., WA Sales Tax Review 2024"
                )
                state_code = st.selectbox(
                    "State*", ["WA", "OR", "CA", "TX", "NY", "Multi-State"]
                )
                tax_type = st.selectbox(
                    "Tax Type*", ["sales_tax", "use_tax", "bno_tax", "mixed"]
                )

            with col2:
                tax_year = st.number_input(
                    "Tax Year*", min_value=2020, max_value=2030, value=2024, step=1
                )
                client_name = st.text_input(
                    "Client Name", placeholder="Optional"
                )
                est_refund = st.number_input(
                    "Est. Refund Amount ($)", min_value=0.0, value=0.0, step=1000.0
                )

            description = st.text_area(
                "Description", placeholder="Brief description of the project scope..."
            )

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ Create Project", type="primary", use_container_width=True)

            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit:
                # Validate required fields
                if not project_name:
                    st.error("❌ Project name is required")
                elif not tax_year:
                    st.error("❌ Tax year is required")
                else:
                    try:
                        # Insert into database
                        user_email = st.session_state.get("user_email", "user@example.com")

                        result = supabase.table("projects").insert({
                            "name": project_name,
                            "description": description if description else None,
                            "tax_type": tax_type,
                            "tax_year": tax_year,
                            "state_code": state_code,
                            "client_name": client_name if client_name else None,
                            "status": "active",
                            "estimated_refund_amount": est_refund if est_refund > 0 else None,
                            "created_by": user_email,
                        }).execute()

                        if result.data:
                            new_project_id = result.data[0]["id"]
                            st.success(f"✅ Project '{project_name}' created successfully!")
                            st.session_state.show_create_project = False
                            # Auto-open the new project
                            st.session_state.current_project = new_project_id
                            st.session_state.show_project_detail = True
                            st.rerun()
                        else:
                            st.error("❌ Failed to create project")
                    except Exception as e:
                        st.error(f"❌ Error creating project: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

            if cancel:
                st.session_state.show_create_project = False
                st.rerun()

    st.markdown("---")

# Load projects
projects = get_projects_from_db()

# Display projects
st.markdown("### 📊 All Projects")

if not projects:
    st.info("📂 No projects yet. Click '➕ Create New Project' above to get started!")
else:
    st.markdown(f"**{len(projects)} project{'s' if len(projects) != 1 else ''}**")
    st.markdown("")
    # Show projects as cards
    for project in projects:
        with st.container():
            st.markdown(
                """
            <div class="section-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin: 0; color: #1a202c;">{project['name']}</h3>
                        <p style="color: #718096; font-size: 0.875rem; margin-top: 0.25rem;">
                            {project['period']} | Status: <span class="badge {'success' if project['status'] == 'Complete' else 'info'}">{project['status']}</span>
                        </p>
                        <p style="color: #4a5568; margin-top: 0.5rem; font-size: 0.875rem;">
                            {project.get('description', 'No description provided')}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #38a169;">
                            ${project['est_refund']:,}
                        </div>
                        <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase;">
                            Est. Refund
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
            with col1:
                if st.button(
                    "👁️ View Details",
                    key=f"view_{project['id']}",
                    use_container_width=True,
                ):
                    st.session_state.current_project = project["id"]
                    st.session_state.show_project_detail = True
                    st.rerun()

            with col2:
                if st.button(
                    "📊 Analytics",
                    key=f"analytics_{project['id']}",
                    use_container_width=True,
                ):
                    st.info("Analytics view coming soon")

            with col3:
                if st.button(
                    "⚙️ Settings",
                    key=f"settings_{project['id']}",
                    use_container_width=True,
                ):
                    st.info("Project settings coming soon")

            st.markdown("<br>", unsafe_allow_html=True)

# Project detail view
if st.session_state.get("show_project_detail", False):
    current_project_id = st.session_state.get("current_project")
    current_project = next((p for p in projects if p["id"] == current_project_id), None)

    if current_project:
        st.markdown("---")

        # Back button at top
        if st.button("🔙 Back to Projects"):
            st.session_state.show_project_detail = False
            st.rerun()

        st.markdown(f"### 📋 {current_project['name']}")

        # Project header with key stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Est. Refund", f"${current_project['est_refund']:,}")
        with col2:
            st.metric("Status", current_project['status'])
        with col3:
            st.metric("Period", current_project['period'])
        with col4:
            st.metric("Files", "0")  # Will query from DB later

        st.markdown("---")

        # Tabs for project sections
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 Overview", "📤 Upload Files", "📄 Files & Versions", "📋 Activity"]
        )

        # TAB 1: Overview
        with tab1:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### Project Details")
                st.markdown(
                    f"""
                <div class="section-card">
                    <p><strong>Description:</strong> {current_project.get('description', 'No description')}</p>
                    <p><strong>Period:</strong> {current_project['period']}</p>
                    <p><strong>Status:</strong> <span class="badge info">{current_project['status']}</span></p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown("#### Quick Actions")
                if st.button("📊 Run Analysis", use_container_width=True):
                    st.info("Analysis functionality coming soon")
                if st.button("📥 Download Results", use_container_width=True):
                    st.info("Download functionality coming soon")
                if st.button("⚙️ Project Settings", use_container_width=True):
                    st.info("Settings functionality coming soon")

        # TAB 2: Upload Files (PROJECT-SCOPED)
        with tab2:
            st.markdown("### 📤 Upload Files")
            st.info(f"📁 All files uploaded here will be associated with: **{current_project['name']}**")

            # Excel file upload
            st.markdown("#### Step 1: Upload Excel File")
            excel_file = st.file_uploader(
                "Upload Master Excel",
                type=["xlsx", "xls"],
                help="Upload your master Excel file with invoice data",
                key=f"excel_upload_{current_project_id}",
            )

            # Invoice files upload
            st.markdown("#### Step 2: Upload Invoice/PO Files (Optional)")
            col1, col2 = st.columns(2)

            with col1:
                invoice_files = st.file_uploader(
                    "Upload Invoice Files",
                    type=["pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx"],
                    accept_multiple_files=True,
                    help="Upload invoice files (PDF, images, Excel, Word)",
                    key=f"invoice_upload_{current_project_id}",
                )

            with col2:
                po_files = st.file_uploader(
                    "Upload Purchase Order Files",
                    type=["pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx"],
                    accept_multiple_files=True,
                    help="Upload PO files (PDF, images, Excel, Word)",
                    key=f"po_upload_{current_project_id}",
                )

            # Change summary
            st.markdown("#### Step 3: Change Summary")

            use_ai_summary = st.checkbox(
                "🤖 Auto-generate summary with AI",
                value=True,
                help="AI will analyze changes and create a detailed summary",
                key=f"use_ai_{current_project_id}",
            )

            if not use_ai_summary:
                change_summary = st.text_area(
                    "What changed in this version?",
                    placeholder="e.g., 'Corrected vendor names in rows 45-89'",
                    key=f"change_summary_{current_project_id}",
                )
            else:
                st.info("💡 AI will generate a detailed summary after analyzing the changes")

            # Upload button
            if st.button("📤 Upload Files", type="primary", use_container_width=True, key=f"upload_btn_{current_project_id}"):
                if not excel_file:
                    st.error("❌ Please upload an Excel file")
                else:
                    try:
                        user_email = st.session_state.get("user_email", "user@example.com")

                        with st.spinner("Uploading files..."):
                            # Save Excel file temporarily
                            temp_dir = Path("/tmp/excel_uploads")
                            temp_dir.mkdir(exist_ok=True)

                            excel_path = temp_dir / excel_file.name
                            with open(excel_path, "wb") as f:
                                f.write(excel_file.getbuffer())

                            # PROJECT-SCOPED file matching: Check if file exists in THIS project
                            existing_file = (
                                supabase.table("excel_file_tracking")
                                .select("id")
                                .eq("file_name", excel_file.name)
                                .eq("project_id", current_project_id)  # PROJECT-SCOPED
                                .execute()
                            )

                            if existing_file.data and len(existing_file.data) > 0:
                                # File exists in this project - create new version
                                file_id = existing_file.data[0]["id"]

                                # Create new version
                                version_id = excel_manager.create_version(
                                    file_id=file_id,
                                    file_path=str(excel_path),
                                    user_email=user_email,
                                    change_summary="",  # Will be filled by AI
                                )
                                st.success(f"✅ Created new version for: {excel_file.name}")
                            else:
                                # New file in this project - upload it
                                file_id = excel_manager.upload_file(
                                    file_path=str(excel_path),
                                    project_id=current_project_id,  # PROJECT-SCOPED
                                    user_email=user_email,
                                )
                                st.success(f"✅ Uploaded new file: {excel_file.name}")

                            # TODO: Handle invoice/PO files upload to storage
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
                                        summary_text = generate_change_summary(changes_response.data)

                                        # Update version with AI summary
                                        supabase.table("excel_file_versions").update(
                                            {"change_summary": summary_text}
                                        ).eq("id", version_id).execute()

                                        st.info(f"✅ AI summary generated! ({len(changes_response.data)} changes detected)")
                                    else:
                                        if version_number == 1:
                                            summary_text = "Initial upload"
                                        else:
                                            summary_text = "No changes detected"
                        else:
                            summary_text = change_summary if 'change_summary' in locals() and change_summary else "No summary provided"

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

                        # Show upload summary
                        st.markdown("**📊 Upload Summary:**")
                        st.markdown(f"- Excel file: `{excel_file.name}`")
                        st.markdown(f"- Project: `{current_project['name']}`")
                        st.markdown(f"- Invoice files: {invoice_count}")
                        st.markdown(f"- PO files: {po_count}")

                        if summary_text and summary_text != "No summary provided":
                            st.markdown("**📝 Change Summary:**")
                            st.markdown(summary_text)

                        # Clean up
                        if excel_path.exists():
                            os.remove(excel_path)

                    except Exception as e:
                        st.error(f"❌ Error uploading files: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

        # TAB 3: Files & Versions
        with tab3:
            st.markdown("### 📄 Files & Versions")
            st.info(f"📁 Showing files for: **{current_project['name']}**")
            st.info("Files list will be loaded from database - implementation coming next")

        # TAB 4: Activity
        with tab4:
            st.markdown("### 📋 Activity Log")
            st.info(f"📁 Showing activity for: **{current_project['name']}**")
            st.info("Activity log will be loaded from database - implementation coming next")

# Footer
st.markdown("---")
st.caption("💼 Project Management | TaxDesk Platform")
