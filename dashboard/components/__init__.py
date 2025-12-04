"""
Dashboard Components - Dark Theme
=================================

Reusable UI components for the NexusTax dashboard.
All components styled for dark theme with glass morphism effects.
"""

from .stat_card import render_stat_card, render_stat_grid, render_summary_cards, ICONS, VARIANTS
from .ai_chat import render_ai_chat, get_ai_response, render_chat_button, ChatMessage
from .upload_zone import render_upload_zone, render_file_list, save_uploaded_files
from .data_table import (
    render_transaction_table,
    render_dataframe_styled,
    render_simple_table,
    STATUS_COLORS,
    CATEGORY_COLORS,
)
from .search_filter import (
    render_search_bar,
    render_filter_bar,
    render_search_filter_bar,
    render_filter_pills,
    render_filter_pills_html,
)

__all__ = [
    # Stat cards
    "render_stat_card",
    "render_stat_grid",
    "render_summary_cards",
    "ICONS",
    "VARIANTS",
    # AI Chat
    "render_ai_chat",
    "get_ai_response",
    "render_chat_button",
    "ChatMessage",
    # Upload zone
    "render_upload_zone",
    "render_file_list",
    "save_uploaded_files",
    # Data tables
    "render_transaction_table",
    "render_dataframe_styled",
    "render_simple_table",
    "STATUS_COLORS",
    "CATEGORY_COLORS",
    # Search & Filter
    "render_search_bar",
    "render_filter_bar",
    "render_search_filter_bar",
    "render_filter_pills",
    "render_filter_pills_html",
]
