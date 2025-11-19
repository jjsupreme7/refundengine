"""
Rules Page - Tax rules and guidance

Browse tax rules, regulations, and guidance documents.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.utils.data_loader import get_tax_rules

# Page configuration
st.set_page_config(
    page_title="Rules & Guidance - TaxDesk", page_icon="📚", layout="wide"
)

# AUTHENTICATION
from core.auth import require_authentication

if not require_authentication():
    st.stop()

# Header
st.markdown(
    '<div class="main-header">📚 Rules & Guidance</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="main-subtitle">Browse tax rules, regulations, and guidance documents</div>',
    unsafe_allow_html=True,
)

# Search and filters
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "🔍 Search rules and guidance",
        placeholder="e.g., software, SaaS, digital automated services...",
    )

with col2:
    filter_category = st.selectbox(
        "Category",
        ["All", "Statute", "Regulation", "Legislation", "Guidance", "Determination"],
    )

with col3:
    filter_jurisdiction = st.selectbox(
        "Jurisdiction", ["All", "Washington", "Oregon", "California"]
    )

st.markdown("---")

# Load rules
rules = get_tax_rules()

# Display rules
st.markdown(f"### 📋 Tax Rules & Guidance ({len(rules)})")

# Group by category
categories = {}
for rule in rules:
    cat = rule["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(rule)

# Display by category
for category, category_rules in sorted(categories.items()):
    with st.expander(f"📂 {category} ({len(category_rules)})", expanded=True):
        for rule in category_rules:
            st.markdown(
                f"""
            <div class="section-card">
                <h4 style="margin: 0; color: #1a202c;">📄 {rule['title']}</h4>
                <p style="margin-top: 0.5rem; color: #4a5568; font-size: 0.875rem;">
                    {rule['summary']}
                </p>
                <p style="margin-top: 0.5rem; font-size: 0.75rem;">
                    <span class="badge info">{rule['category']}</span>
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
            with col1:
                if st.button(
                    "👁️ View Full Text",
                    key=f"view_{rule['id']}",
                    use_container_width=True,
                ):
                    st.info(f"Viewing {rule['title']}")

            with col2:
                if st.button(
                    "📚 Related Docs",
                    key=f"related_{rule['id']}",
                    use_container_width=True,
                ):
                    st.info("Related documents coming soon")

            with col3:
                if st.button(
                    "🔗 Copy Citation",
                    key=f"copy_{rule['id']}",
                    use_container_width=True,
                ):
                    st.success(f"Copied: {rule['id']}")

            st.markdown("<br>", unsafe_allow_html=True)

# Quick access section
st.markdown("---")
st.markdown("### ⚡ Quick Access")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
    <div class="section-card">
        <h4>📘 ESSB 5814</h4>
        <p style="color: #4a5568; font-size: 0.875rem;">
            New service taxation rules effective Oct 1, 2025
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if st.button("View ESSB 5814 Resources", use_container_width=True):
        st.info("Navigate to ESSB 5814 resources")

with col2:
    st.markdown(
        """
    <div class="section-card">
        <h4>💻 Digital Services</h4>
        <p style="color: #4a5568; font-size: 0.875rem;">
            DAS, SaaS, and digital goods rules
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if st.button("View Digital Services Rules", use_container_width=True):
        st.info("Navigate to digital services rules")

with col3:
    st.markdown(
        """
    <div class="section-card">
        <h4>📋 Exemptions</h4>
        <p style="color: #4a5568; font-size: 0.875rem;">
            Common exemptions and exclusions
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if st.button("View Exemptions", use_container_width=True):
        st.info("Navigate to exemptions")

# Footer
st.markdown("---")
st.caption("📚 Rules & Guidance | TaxDesk Platform")
