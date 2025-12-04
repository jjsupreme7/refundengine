"""
Search & Filter Component - Dark Theme
======================================

Search bar and filter dropdowns styled for dark theme.
Inspired by Nebula Transactions filter bar.
"""

import streamlit as st
from typing import Optional


def render_search_bar(
    placeholder: str = "Search...",
    key: str = "search",
    show_shortcut: bool = True,
) -> str:
    """
    Render a styled search input.

    Args:
        placeholder: Placeholder text
        key: Unique key for the input
        show_shortcut: Whether to show keyboard shortcut hint

    Returns:
        The search query string
    """
    # Visual search bar (decorative header)
    st.markdown("""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
    ">
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([6, 1] if show_shortcut else [1])

    with col1:
        search_value = st.text_input(
            "Search",
            placeholder=placeholder,
            label_visibility="collapsed",
            key=key,
        )

    if show_shortcut:
        with col2:
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

    st.markdown("</div>", unsafe_allow_html=True)

    return search_value


def render_filter_bar(
    filters: dict[str, list[str]],
    key_prefix: str = "filter",
) -> dict[str, str]:
    """
    Render a filter bar with multiple dropdowns.

    Args:
        filters: Dictionary of filter_name -> options list
        key_prefix: Prefix for unique keys

    Returns:
        Dictionary of filter_name -> selected_value

    Example:
        filters = render_filter_bar({
            "Category": ["All Categories", "Food", "Transport", "Shopping"],
            "Date Range": ["Last 30 Days", "Last 90 Days", "This Year"],
            "Status": ["All", "Completed", "Pending", "Flagged"],
        })
    """
    st.markdown("""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
    """, unsafe_allow_html=True)

    cols = st.columns(len(filters))
    selected = {}

    for idx, (name, options) in enumerate(filters.items()):
        with cols[idx]:
            selected[name] = st.selectbox(
                name,
                options,
                key=f"{key_prefix}_{name.lower().replace(' ', '_')}",
                label_visibility="collapsed",
            )

    st.markdown("</div>", unsafe_allow_html=True)

    return selected


def render_search_filter_bar(
    search_placeholder: str = "Search transactions...",
    filters: dict[str, list[str]] = None,
    key_prefix: str = "sf",
) -> tuple[str, dict[str, str]]:
    """
    Render a combined search and filter bar.

    Args:
        search_placeholder: Placeholder for search input
        filters: Dictionary of filter_name -> options list
        key_prefix: Prefix for unique keys

    Returns:
        Tuple of (search_query, filter_selections)
    """
    st.markdown("""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
    """, unsafe_allow_html=True)

    # Calculate column widths
    num_filters = len(filters) if filters else 0
    search_cols = 3 if num_filters > 0 else 1

    if num_filters > 0:
        cols = st.columns([search_cols] + [1] * num_filters)
    else:
        cols = st.columns([1])

    # Search input
    with cols[0]:
        search_query = st.text_input(
            "Search",
            placeholder=search_placeholder,
            label_visibility="collapsed",
            key=f"{key_prefix}_search",
        )

    # Filter dropdowns
    selected_filters = {}
    if filters:
        for idx, (name, options) in enumerate(filters.items()):
            with cols[idx + 1]:
                selected_filters[name] = st.selectbox(
                    name,
                    options,
                    key=f"{key_prefix}_{name.lower().replace(' ', '_')}",
                    label_visibility="collapsed",
                )

    st.markdown("</div>", unsafe_allow_html=True)

    return search_query, selected_filters


def render_filter_pills(
    options: list[str],
    selected: str = None,
    key: str = "pills",
) -> str:
    """
    Render filter pills/buttons.

    Args:
        options: List of filter options
        selected: Currently selected option
        key: Unique key prefix

    Returns:
        The selected option
    """
    if selected is None:
        selected = options[0] if options else None

    # Initialize session state
    state_key = f"{key}_selected"
    if state_key not in st.session_state:
        st.session_state[state_key] = selected

    # Create columns for pills
    cols = st.columns(len(options))

    for idx, option in enumerate(options):
        with cols[idx]:
            is_active = st.session_state[state_key] == option
            btn_type = "primary" if is_active else "secondary"

            if st.button(option, key=f"{key}_{idx}", type=btn_type, use_container_width=True):
                st.session_state[state_key] = option
                st.rerun()

    return st.session_state[state_key]


def render_filter_pills_html(
    options: list[str],
    selected: str = None,
) -> None:
    """
    Render filter pills as HTML (non-interactive, for display).

    Args:
        options: List of filter options
        selected: Currently selected option
    """
    pills_html = ""
    for option in options:
        is_active = option == selected
        if is_active:
            pills_html += f"""
            <span style="
                display: inline-flex;
                padding: 0.375rem 1rem;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 500;
                background: linear-gradient(135deg, #8b5cf6, #6366f1);
                color: white;
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
            ">{option}</span>
            """
        else:
            pills_html += f"""
            <span style="
                display: inline-flex;
                padding: 0.375rem 1rem;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 500;
                background: rgba(30, 27, 75, 0.5);
                border: 1px solid rgba(49, 46, 129, 0.4);
                color: #9ca3af;
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
                cursor: pointer;
            ">{option}</span>
            """

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        {pills_html}
    </div>
    """, unsafe_allow_html=True)


# Export
__all__ = [
    "render_search_bar",
    "render_filter_bar",
    "render_search_filter_bar",
    "render_filter_pills",
    "render_filter_pills_html",
]
