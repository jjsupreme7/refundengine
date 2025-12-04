#!/usr/bin/env python3
"""
Research Hub Page - Dark Theme
==============================

Explore RCWs, WACs, and Legislative Updates.
Styled with dark theme and glass morphism effects.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

# Page config
st.set_page_config(
    page_title="Research Hub | NexusTax",
    page_icon="",
    layout="wide",
)

# Auth
from core.auth import require_authentication
if not require_authentication():
    st.stop()

# Import styles
from dashboard.styles import inject_css
from dashboard.components import render_filter_pills

inject_css()

# =============================================================================
# MOCK DATA FOR RESEARCH DOCUMENTS
# =============================================================================
MOCK_RESEARCH = [
    {
        "id": "1",
        "type": "RCW",
        "number": "82.04.290",
        "title": "Tax on Retailers",
        "summary": "Upon every person engaging within this state in the business of making sales at retail, as to such persons, the amount of tax with respect to such business is equal to the gross proceeds of sales of the business.",
        "tags": ["retail", "sales", "b&o"],
    },
    {
        "id": "2",
        "type": "WAC",
        "number": "458-20-19301",
        "title": "Multiple Activities Tax Credits",
        "summary": "This rule explains how multiple activities tax credits (MATC) apply when a taxpayer is subject to the B&O tax under two or more tax classifications.",
        "tags": ["matc", "credits", "b&o"],
    },
    {
        "id": "3",
        "type": "Bill",
        "number": "ESSB 5814",
        "title": "Workforce Education Investment Surcharge",
        "summary": "Establishes a workforce education investment surcharge on certain businesses with advanced computing or advanced manufacturing business activity.",
        "tags": ["surcharge", "education", "technology"],
    },
    {
        "id": "4",
        "type": "RCW",
        "number": "82.08.020",
        "title": "Retail Sales Tax Rate",
        "summary": "There is levied and collected a tax equal to six and five-tenths percent of the selling price on each retail sale in this state.",
        "tags": ["sales tax", "rate", "retail"],
    },
    {
        "id": "5",
        "type": "WAC",
        "number": "458-20-193",
        "title": "Inbound and Outbound Interstate Sales",
        "summary": "This rule explains how Washington's B&O tax applies to sales of goods shipped from locations in Washington to locations outside the state.",
        "tags": ["interstate", "shipping", "nexus"],
    },
    {
        "id": "6",
        "type": "RCW",
        "number": "82.12.020",
        "title": "Use Tax Imposed",
        "summary": "There is hereby levied and collected from every person in this state a use tax for the privilege of using within this state tangible personal property.",
        "tags": ["use tax", "personal property"],
    },
]

# =============================================================================
# PAGE HEADER
# =============================================================================
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <h1 style="
        font-size: 1.875rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    ">Research Hub</h1>
    <p style="color: #9ca3af; margin-top: 0.25rem;">
        Explore RCWs, WACs, and Legislative Updates.
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SEARCH BAR
# =============================================================================
search_col, shortcut_col = st.columns([6, 1])

with search_col:
    search_term = st.text_input(
        "Search",
        placeholder="Search for statutes, rules, or keywords (e.g. 'Software Service', 'Manufacturing B&O')...",
        label_visibility="collapsed",
    )

with shortcut_col:
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        height: 38px;
        background: rgba(30, 27, 75, 0.5);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 6px;
        font-size: 0.75rem;
        color: #6b7280;
        font-family: monospace;
    ">CMD+K</div>
    """, unsafe_allow_html=True)

# =============================================================================
# FILTER PILLS
# =============================================================================
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

filter_options = ["All", "RCW", "WAC", "ETA", "Court Decisions", "ESSB 5814"]

# Initialize filter state
if "research_filter" not in st.session_state:
    st.session_state.research_filter = "All"

selected_filter = render_filter_pills(filter_options, st.session_state.research_filter, key="research_pills")
st.session_state.research_filter = selected_filter

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# =============================================================================
# CONTENT AREA
# =============================================================================
col_results, col_nav = st.columns([3, 1])

# Filter documents
filtered_docs = MOCK_RESEARCH
if search_term:
    search_lower = search_term.lower()
    filtered_docs = [
        doc for doc in filtered_docs
        if search_lower in doc["title"].lower()
        or search_lower in doc["summary"].lower()
        or any(search_lower in tag for tag in doc["tags"])
    ]

if st.session_state.research_filter != "All":
    if st.session_state.research_filter == "ESSB 5814":
        filtered_docs = [doc for doc in filtered_docs if "5814" in doc["number"]]
    else:
        filtered_docs = [doc for doc in filtered_docs if doc["type"] == st.session_state.research_filter]

# =============================================================================
# RESULTS LIST
# =============================================================================
with col_results:
    if not filtered_docs:
        st.markdown("""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 2rem;
            text-align: center;
            color: #9ca3af;
        ">
            No documents match your search criteria.
        </div>
        """, unsafe_allow_html=True)
    else:
        for doc in filtered_docs:
            # Badge color based on type (dark theme)
            badge_colors = {
                "RCW": ("rgba(99, 102, 241, 0.2)", "#a5b4fc"),
                "WAC": ("rgba(234, 179, 8, 0.2)", "#fde047"),
                "Bill": ("rgba(34, 197, 94, 0.2)", "#86efac"),
                "ETA": ("rgba(239, 68, 68, 0.2)", "#fca5a5"),
            }
            bg_color, text_color = badge_colors.get(doc["type"], ("rgba(99, 102, 241, 0.2)", "#a5b4fc"))

            st.markdown(f"""
            <div style="
                background: rgba(30, 27, 75, 0.3);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(49, 46, 129, 0.4);
                border-radius: 0.75rem;
                padding: 1.25rem;
                margin-bottom: 1rem;
                transition: all 0.2s ease;
                cursor: pointer;
            " onmouseover="this.style.borderColor='#8b5cf6'; this.style.boxShadow='0 0 20px rgba(139, 92, 246, 0.3)';"
               onmouseout="this.style.borderColor='rgba(49, 46, 129, 0.4)'; this.style.boxShadow='none';">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="
                            padding: 0.25rem 0.5rem;
                            font-size: 0.65rem;
                            font-weight: 700;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            background: {bg_color};
                            color: {text_color};
                            border-radius: 4px;
                        ">{doc['type']}</span>
                        <span style="font-size: 0.875rem; font-family: monospace; color: #6b7280;">{doc['number']}</span>
                    </div>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" style="cursor: pointer;">
                        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">{doc['title']}</h3>
                <p style="font-size: 0.875rem; color: #9ca3af; line-height: 1.5; margin-bottom: 0.75rem;">{doc['summary']}</p>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    {''.join([f'<span style="font-size: 0.75rem; color: #9ca3af; background: rgba(49, 46, 129, 0.5); padding: 0.25rem 0.5rem; border-radius: 4px;">#{tag}</span>' for tag in doc['tags']])}
                </div>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# QUICK NAVIGATION SIDEBAR
# =============================================================================
with col_nav:
    st.markdown("""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 1.25rem;
        position: sticky;
        top: 1rem;
    ">
        <h4 style="
            font-size: 0.65rem;
            font-weight: 700;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 1rem;
        ">Quick Navigation</h4>
    """, unsafe_allow_html=True)

    nav_items = [
        ("Business & Occupation Tax", True),
        ("Retail Sales Tax", False),
        ("Use Tax", False),
        ("Public Utility Tax", False),
    ]

    for item, is_active in nav_items:
        color = "#8b5cf6" if is_active else "#6b7280"
        font_weight = "500" if is_active else "400"
        text_color = "#ffffff" if is_active else "#9ca3af"

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0;
            cursor: pointer;
            color: {text_color};
            font-size: 0.875rem;
            font-weight: {font_weight};
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2">
                <path d="M12 3v18M3 12h18"></path>
            </svg>
            {item}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="
            border-top: 1px solid rgba(49, 46, 129, 0.4);
            margin-top: 0.75rem;
            padding-top: 0.75rem;
        ">
            <a href="#" style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 0.75rem;
                color: #8b5cf6;
                font-weight: 500;
                text-decoration: none;
            ">
                View ESSB 5814 Hub
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="
    font-size: 0.75rem;
    color: #6b7280;
    text-align: center;
">Washington State Tax Law Database | Updated November 2024</div>
""", unsafe_allow_html=True)
