#!/usr/bin/env python3
"""
TaxDesk - Multi-Page Tax Refund Analysis Dashboard

Main entry point for the Streamlit multi-page application.
Navigate between Dashboard, Projects, Documents, Review Queue, Claims, and more.

Usage:
    streamlit run dashboard_app.py --server.port 5001
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="TaxDesk - Refund Analysis Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "TaxDesk - AI-Powered Tax Refund Analysis Platform"
    }
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-blue: #3182ce;
        --primary-blue-hover: #2c5282;
        --success-green: #38a169;
        --warning-yellow: #d69e2e;
        --danger-red: #e53e3e;
        --gray-50: #f7fafc;
        --gray-100: #edf2f7;
        --gray-200: #e2e8f0;
        --gray-500: #718096;
        --gray-700: #4a5568;
        --gray-900: #1a202c;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom header styling */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: var(--gray-900);
        margin-bottom: 0.5rem;
    }

    .main-subtitle {
        font-size: 0.9rem;
        color: var(--gray-500);
        margin-bottom: 2rem;
    }

    /* Stat card styling */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-blue);
    }

    .stat-card.success {
        border-left-color: var(--success-green);
    }

    .stat-card.warning {
        border-left-color: var(--warning-yellow);
    }

    .stat-card.danger {
        border-left-color: var(--danger-red);
    }

    .stat-label {
        font-size: 0.75rem;
        color: var(--gray-500);
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--gray-900);
    }

    .stat-value.green {
        color: var(--success-green);
    }

    .stat-value.red {
        color: var(--danger-red);
    }

    .stat-value.blue {
        color: var(--primary-blue);
    }

    .stat-sublabel {
        font-size: 0.75rem;
        color: var(--gray-500);
        margin-top: 0.25rem;
    }

    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge.success {
        background-color: #c6f6d5;
        color: #22543d;
    }

    .badge.warning {
        background-color: #feebc8;
        color: #7c2d12;
    }

    .badge.danger {
        background-color: #fed7d7;
        color: #742a2a;
    }

    .badge.info {
        background-color: #bee3f8;
        color: #2c5282;
    }

    .badge.neutral {
        background-color: #e2e8f0;
        color: #4a5568;
    }

    /* Section styling */
    .section-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--gray-900);
        margin-bottom: 0.5rem;
    }

    .section-subtitle {
        font-size: 0.875rem;
        color: var(--gray-500);
        margin-bottom: 1rem;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 0.375rem;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }

    .stButton > button[kind="primary"] {
        background-color: var(--primary-blue);
        border-color: var(--primary-blue);
    }

    .stButton > button[kind="primary"]:hover {
        background-color: var(--primary-blue-hover);
        border-color: var(--primary-blue-hover);
    }

    /* Table styling */
    .dataframe {
        font-size: 0.875rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 2rem;
    }

    /* Navigation styling */
    .nav-link {
        display: block;
        padding: 0.75rem 1rem;
        color: var(--gray-700);
        text-decoration: none;
        border-radius: 0.375rem;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }

    .nav-link:hover {
        background-color: var(--gray-100);
        color: var(--gray-900);
    }

    .nav-link.active {
        background-color: var(--primary-blue);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Analyst'  # Default role

if 'current_project' not in st.session_state:
    st.session_state.current_project = 'WA-UT-2022_2024'

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 📊 TaxDesk")
    st.markdown(f"**Logged in as:** {st.session_state.user_role}")
    st.markdown("---")

    # Navigation info
    st.info("""
    **Navigation:**

    Use the sidebar to navigate between different sections of the dashboard.

    - **Dashboard**: Overview and key metrics
    - **1_Projects**: Manage tax refund projects
    - **2_Documents**: Upload and review documents
    - **3_Review_Queue**: Review flagged transactions
    - **4_Claims**: Draft and finalize claims
    - **5_Rules**: Tax rules and guidance
    """)

    st.markdown("---")

    # Quick stats
    st.markdown("### 📈 Quick Stats")
    st.metric("Open Projects", "2")
    st.metric("Pending Reviews", "12")
    st.metric("Est. Total Refund", "$184,230")

# Main content
def main():
    """Main dashboard landing page"""

    # Header
    st.markdown('<div class="main-header">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Welcome back, analyst. Here\'s a summary of your portal.</div>', unsafe_allow_html=True)

    # Action button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("➕ Create New Project", type="primary", use_container_width=True):
            st.info("Navigate to Projects page to create a new project")

    st.markdown("---")

    # Summary statistics cards
    st.markdown("### 📊 Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Open Projects</div>
            <div class="stat-value">2</div>
            <div class="stat-sublabel">Across 2 jurisdictions</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Projects →", key="view_projects"):
            st.info("Navigate to '1_Projects' in the sidebar")

    with col2:
        st.markdown("""
        <div class="stat-card warning">
            <div class="stat-label">Documents Awaiting Review</div>
            <div class="stat-value">1</div>
            <div class="stat-sublabel">Pending analysis</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Documents →", key="view_docs"):
            st.info("Navigate to '2_Documents' in the sidebar")

    with col3:
        st.markdown("""
        <div class="stat-card danger">
            <div class="stat-label">Exceptions to Review</div>
            <div class="stat-value red">2</div>
            <div class="stat-sublabel">Below 90% confidence</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Review Queue →", key="view_review"):
            st.info("Navigate to '3_Review_Queue' in the sidebar")

    with col4:
        st.markdown("""
        <div class="stat-card success">
            <div class="stat-label">Draft Claims</div>
            <div class="stat-value">1</div>
            <div class="stat-sublabel">Ready for submission</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Claims →", key="view_claims"):
            st.info("Navigate to '4_Claims' in the sidebar")

    st.markdown("<br>", unsafe_allow_html=True)

    # Project Spotlight Section
    st.markdown("### ⭐ Project Spotlight: WA Use Tax 2022–2024")
    st.markdown("""
    <div class="section-card">
        <div class="section-subtitle">Quick actions for your most active project.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("👁️ View Project", use_container_width=True):
            st.session_state.current_project = 'WA-UT-2022_2024'
            st.info("Navigate to '1_Projects' to view project details")

    with col2:
        if st.button("🔍 Open Review Queue (2)", use_container_width=True):
            st.info("Navigate to '3_Review_Queue' to review flagged items")

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent Activity
    st.markdown("### 📋 Recent Activity")
    st.markdown("""
    <div class="section-card">
        <ul style="color: #4a5568; line-height: 2;">
            <li><strong>2 hours ago</strong>: Analyzed 25 transactions from Red Bison Tech Services</li>
            <li><strong>1 day ago</strong>: Created project "WA Use Tax 2022-2024"</li>
            <li><strong>2 days ago</strong>: Flagged 2 transactions for manual review</li>
            <li><strong>3 days ago</strong>: Ingested new ESSB 5814 guidance documents</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.caption("🧠 Powered by Enhanced RAG + AI Analysis | 📚 Washington State Tax Law Database")

if __name__ == "__main__":
    main()
