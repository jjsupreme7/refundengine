"""
Projects Page - Manage tax refund projects

View all projects, create new projects, and track progress.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.utils.data_loader import get_projects_from_db

# Page configuration
st.set_page_config(
    page_title="Projects - TaxDesk",
    page_icon="📁",
    layout="wide"
)

# Header
st.markdown('<div class="main-header">📁 Projects</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Manage your tax refund analysis projects</div>', unsafe_allow_html=True)

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
if st.session_state.get('show_create_project', False):
    with st.expander("✨ Create New Project", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            project_name = st.text_input("Project Name*", placeholder="e.g., WA Sales Tax Review 2024")
            jurisdiction = st.selectbox("Jurisdiction*", ["Washington", "Oregon", "California", "Multi-State"])
            tax_type = st.selectbox("Tax Type*", ["Use Tax", "Sales Tax", "B&O Tax", "Multiple"])

        with col2:
            period_start = st.date_input("Period Start*")
            period_end = st.date_input("Period End*")
            est_transactions = st.number_input("Est. Transactions", min_value=0, value=100)

        description = st.text_area("Description", placeholder="Brief description of the project scope...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Create Project", type="primary", use_container_width=True):
                st.success(f"✅ Project '{project_name}' created successfully!")
                st.session_state.show_create_project = False
                st.rerun()

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_create_project = False
                st.rerun()

    st.markdown("---")

# Load projects
projects = get_projects_from_db()

# Display projects
st.markdown("### 📊 All Projects")

if not projects:
    st.info("No projects yet. Create your first project to get started!")
else:
    # Show projects as cards
    for project in projects:
        with st.container():
            st.markdown(f"""
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
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
            with col1:
                if st.button("👁️ View Details", key=f"view_{project['id']}", use_container_width=True):
                    st.session_state.current_project = project['id']
                    st.session_state.show_project_detail = True
                    st.rerun()

            with col2:
                if st.button("📊 Analytics", key=f"analytics_{project['id']}", use_container_width=True):
                    st.info("Analytics view coming soon")

            with col3:
                if st.button("⚙️ Settings", key=f"settings_{project['id']}", use_container_width=True):
                    st.info("Project settings coming soon")

            st.markdown("<br>", unsafe_allow_html=True)

# Project detail view
if st.session_state.get('show_project_detail', False):
    current_project_id = st.session_state.get('current_project')
    current_project = next((p for p in projects if p['id'] == current_project_id), None)

    if current_project:
        st.markdown("---")
        st.markdown("### 📋 Project Details")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"""
            <div class="section-card">
                <h3>{current_project['name']}</h3>
                <p><strong>Period:</strong> {current_project['period']}</p>
                <p><strong>Status:</strong> <span class="badge info">{current_project['status']}</span></p>
                <p><strong>Description:</strong> {current_project.get('description', 'No description')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Project timeline/activity
            st.markdown("#### 📅 Recent Activity")
            st.markdown("""
            <div class="section-card">
                <ul style="line-height: 2; color: #4a5568;">
                    <li><strong>2 hours ago:</strong> Analyzed 25 transactions</li>
                    <li><strong>1 day ago:</strong> Uploaded 5 invoices</li>
                    <li><strong>3 days ago:</strong> Project created</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Project statistics
            st.markdown("#### 📊 Project Stats")

            st.metric("Est. Total Refund", f"${current_project['est_refund']:,}")
            st.metric("Transactions Analyzed", "25")
            st.metric("Pending Reviews", "2")
            st.metric("Confidence Avg", "94%")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔙 Back to Projects", use_container_width=True):
                st.session_state.show_project_detail = False
                st.rerun()

# Footer
st.markdown("---")
st.caption("💼 Project Management | TaxDesk Platform")
