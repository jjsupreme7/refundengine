"""
Data Table Component - Dark Theme
=================================

Styled transaction tables with status badges, category tags, and pagination.
Inspired by Nebula Transactions UI.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Literal


# Status badge colors for dark theme
STATUS_COLORS = {
    "completed": ("rgba(34, 197, 94, 0.2)", "#86efac"),
    "approved": ("rgba(34, 197, 94, 0.2)", "#86efac"),
    "success": ("rgba(34, 197, 94, 0.2)", "#86efac"),
    "pending": ("rgba(234, 179, 8, 0.2)", "#fde047"),
    "review": ("rgba(234, 179, 8, 0.2)", "#fde047"),
    "processing": ("rgba(59, 130, 246, 0.2)", "#93c5fd"),
    "draft": ("rgba(99, 102, 241, 0.2)", "#a5b4fc"),
    "error": ("rgba(239, 68, 68, 0.2)", "#fca5a5"),
    "rejected": ("rgba(239, 68, 68, 0.2)", "#fca5a5"),
    "flagged": ("rgba(239, 68, 68, 0.2)", "#fca5a5"),
}

# Category badge colors
CATEGORY_COLORS = {
    "transport": ("rgba(234, 179, 8, 0.2)", "#fde047"),
    "food": ("rgba(139, 92, 246, 0.2)", "#c4b5fd"),
    "shopping": ("rgba(234, 179, 8, 0.2)", "#fde047"),
    "utilities": ("rgba(59, 130, 246, 0.2)", "#93c5fd"),
    "income": ("rgba(34, 197, 94, 0.2)", "#86efac"),
    "software": ("rgba(99, 102, 241, 0.2)", "#a5b4fc"),
    "hardware": ("rgba(16, 185, 129, 0.2)", "#6ee7b7"),
    "services": ("rgba(139, 92, 246, 0.2)", "#c4b5fd"),
    "default": ("rgba(99, 102, 241, 0.2)", "#a5b4fc"),
}


def _get_status_badge(status: str) -> str:
    """Generate HTML for a status badge."""
    status_lower = status.lower() if status else "pending"
    bg_color, text_color = STATUS_COLORS.get(status_lower, STATUS_COLORS["pending"])

    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        background: {bg_color};
        color: {text_color};
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    ">
        <span style="width: 6px; height: 6px; background: {text_color}; border-radius: 50%;"></span>
        {status.title() if status else 'Pending'}
    </span>
    """


def _get_category_badge(category: str) -> str:
    """Generate HTML for a category badge."""
    cat_lower = category.lower() if category else "default"
    bg_color, text_color = CATEGORY_COLORS.get(cat_lower, CATEGORY_COLORS["default"])

    return f"""
    <span style="
        padding: 0.25rem 0.5rem;
        background: {bg_color};
        color: {text_color};
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    ">{category if category else 'Uncategorized'}</span>
    """


def _format_amount(amount: float, is_positive: bool = None) -> str:
    """Format amount with color coding."""
    if is_positive is None:
        is_positive = amount >= 0

    color = "#86efac" if is_positive else "#fca5a5"
    prefix = "+" if is_positive and amount != 0 else ""

    return f"""
    <span style="
        color: {color};
        font-family: monospace;
        font-weight: 500;
    ">{prefix}${abs(amount):,.2f}</span>
    """


def render_transaction_table(
    data: list[dict],
    columns: list[str] = None,
    show_pagination: bool = True,
    page_size: int = 10,
    current_page: int = 1,
) -> None:
    """
    Render a styled transaction table.

    Args:
        data: List of transaction dictionaries
        columns: List of column keys to display (default: all)
        show_pagination: Whether to show pagination controls
        page_size: Number of rows per page
        current_page: Current page number (1-indexed)

    Expected data format:
        [
            {
                "date": "May 21, 2023",
                "description": "Uber Ride",
                "category": "Transport",
                "status": "Completed",
                "amount": -24.50,
            },
            ...
        ]
    """
    if not data:
        st.markdown("""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 2rem;
            text-align: center;
            color: #9ca3af;
        ">
            No transactions to display.
        </div>
        """, unsafe_allow_html=True)
        return

    # Default columns if not specified
    if columns is None:
        columns = list(data[0].keys())

    # Calculate pagination
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    page_data = data[start_idx:end_idx]

    # Build table header
    header_cells = ""
    for col in columns:
        header_cells += f'<th style="padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em;">{col.replace("_", " ").title()}</th>'

    # Build table rows
    rows_html = ""
    for row in page_data:
        cells = ""
        for col in columns:
            value = row.get(col, "")

            # Special formatting for known column types
            if col.lower() in ["status"]:
                cell_content = _get_status_badge(value)
            elif col.lower() in ["category", "type"]:
                cell_content = _get_category_badge(value)
            elif col.lower() in ["amount", "total", "tax", "refund"]:
                is_income = row.get("is_income", None)
                if is_income is None and col.lower() == "amount":
                    is_income = value >= 0 if isinstance(value, (int, float)) else True
                cell_content = _format_amount(float(value) if value else 0, is_income)
            else:
                cell_content = f'<span style="color: #ffffff;">{value}</span>'

            cells += f'<td style="padding: 1rem; font-size: 0.875rem;">{cell_content}</td>'

        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(49, 46, 129, 0.2); transition: background 0.2s ease;"
            onmouseover="this.style.background='rgba(99, 102, 241, 0.1)';"
            onmouseout="this.style.background='transparent';">
            {cells}
        </tr>
        """

    # Build complete table
    table_html = f"""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        overflow: hidden;
    ">
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="border-bottom: 1px solid rgba(49, 46, 129, 0.4);">
                    <tr>{header_cells}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    """

    # Add pagination footer
    if show_pagination and total_pages > 1:
        table_html += f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border-top: 1px solid rgba(49, 46, 129, 0.4);
        ">
            <div style="font-size: 0.875rem; color: #9ca3af;">
                Showing {start_idx + 1}-{end_idx} of {total_items} transactions
            </div>
            <div style="display: flex; gap: 0.25rem;">
        """

        # Previous button
        table_html += f"""
        <button style="
            width: 2rem; height: 2rem;
            display: flex; align-items: center; justify-content: center;
            border-radius: 0.5rem;
            background: rgba(30, 27, 75, 0.5);
            border: 1px solid rgba(49, 46, 129, 0.4);
            color: #9ca3af;
            cursor: {'pointer' if current_page > 1 else 'not-allowed'};
            opacity: {'1' if current_page > 1 else '0.5'};
        ">&#8249;</button>
        """

        # Page numbers
        for page in range(1, min(total_pages + 1, 6)):
            is_active = page == current_page
            table_html += f"""
            <button style="
                width: 2rem; height: 2rem;
                display: flex; align-items: center; justify-content: center;
                border-radius: 0.5rem;
                background: {'#6366f1' if is_active else 'rgba(30, 27, 75, 0.5)'};
                border: 1px solid {'#6366f1' if is_active else 'rgba(49, 46, 129, 0.4)'};
                color: {'white' if is_active else '#9ca3af'};
                cursor: pointer;
                font-size: 0.875rem;
            ">{page}</button>
            """

        # Next button
        table_html += f"""
        <button style="
            width: 2rem; height: 2rem;
            display: flex; align-items: center; justify-content: center;
            border-radius: 0.5rem;
            background: rgba(30, 27, 75, 0.5);
            border: 1px solid rgba(49, 46, 129, 0.4);
            color: #9ca3af;
            cursor: {'pointer' if current_page < total_pages else 'not-allowed'};
            opacity: {'1' if current_page < total_pages else '0.5'};
        ">&#8250;</button>
            </div>
        </div>
        """

    table_html += "</div>"

    st.markdown(table_html, unsafe_allow_html=True)


def render_dataframe_styled(
    df: pd.DataFrame,
    status_column: str = None,
    category_column: str = None,
    amount_columns: list[str] = None,
    height: int = 400,
) -> None:
    """
    Render a pandas DataFrame with dark theme styling.

    This uses Streamlit's native dataframe with custom styling overrides.

    Args:
        df: DataFrame to display
        status_column: Column name containing status values
        category_column: Column name containing category values
        amount_columns: List of column names containing monetary amounts
        height: Height of the dataframe in pixels
    """
    if df is None or df.empty:
        st.markdown("""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 2rem;
            text-align: center;
            color: #9ca3af;
        ">
            No data to display.
        </div>
        """, unsafe_allow_html=True)
        return

    # Container with dark styling
    st.markdown("""
    <style>
    .dataframe-container {
        background: rgba(30, 27, 75, 0.3);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 0.5rem;
    }
    </style>
    <div class="dataframe-container">
    """, unsafe_allow_html=True)

    # Build column config
    column_config = {}

    if amount_columns:
        for col in amount_columns:
            if col in df.columns:
                column_config[col] = st.column_config.NumberColumn(
                    col.replace("_", " ").title(),
                    format="$%.2f",
                )

    st.dataframe(
        df,
        use_container_width=True,
        height=height,
        column_config=column_config,
    )

    st.markdown("</div>", unsafe_allow_html=True)


def render_simple_table(
    headers: list[str],
    rows: list[list],
    title: str = None,
) -> None:
    """
    Render a simple dark-themed table.

    Args:
        headers: List of column headers
        rows: List of row data (each row is a list of values)
        title: Optional table title
    """
    header_cells = "".join([
        f'<th style="padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em;">{h}</th>'
        for h in headers
    ])

    rows_html = ""
    for row in rows:
        cells = "".join([
            f'<td style="padding: 1rem; color: #ffffff; font-size: 0.875rem;">{cell}</td>'
            for cell in row
        ])
        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(49, 46, 129, 0.2);"
            onmouseover="this.style.background='rgba(99, 102, 241, 0.1)';"
            onmouseout="this.style.background='transparent';">
            {cells}
        </tr>
        """

    title_html = f"""
    <div style="padding: 1rem 1.5rem; border-bottom: 1px solid rgba(49, 46, 129, 0.4);">
        <h3 style="margin: 0; color: #ffffff; font-size: 1.125rem; font-weight: 600;">{title}</h3>
    </div>
    """ if title else ""

    st.markdown(f"""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        overflow: hidden;
    ">
        {title_html}
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="border-bottom: 1px solid rgba(49, 46, 129, 0.4);">
                    <tr>{header_cells}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Export
__all__ = [
    "render_transaction_table",
    "render_dataframe_styled",
    "render_simple_table",
    "STATUS_COLORS",
    "CATEGORY_COLORS",
]
