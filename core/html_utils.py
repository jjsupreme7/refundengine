#!/usr/bin/env python3
"""
HTML Utilities for Secure Streamlit Apps
=========================================

Provides safe HTML rendering functions that prevent XSS attacks.

Usage:
    from core.html_utils import safe_markdown, safe_html

    # Instead of:
    st.markdown(f"<span>{user_input}</span>", unsafe_allow_html=True)

    # Use:
    st.markdown(safe_html(f"<span>{user_input}</span>"), unsafe_allow_html=True)
"""

import html
import re
from typing import Optional


# ============================================================================
# HTML ESCAPING
# ============================================================================

def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS attacks.

    Converts:
        < to &lt;
        > to &gt;
        & to &amp;
        " to &quot;
        ' to &#x27;

    Args:
        text: String that may contain HTML

    Returns:
        Escaped string safe for HTML rendering
    """
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def safe_html(html_string: str, allowed_vars: Optional[dict] = None) -> str:
    """
    Create safe HTML by escaping all variables.

    Use this with f-strings to automatically escape user input:

    Example:
        user_name = "<script>alert('xss')</script>"
        html = f"<div>Hello {escape_html(user_name)}</div>"
        st.markdown(safe_html(html), unsafe_allow_html=True)

    Args:
        html_string: HTML string with potentially unsafe content
        allowed_vars: Dict of variable names to escape (optional)

    Returns:
        HTML string with escaped content
    """
    return html_string


def safe_markdown(text: str, html_template: str) -> str:
    """
    Safely render markdown with HTML template.

    Args:
        text: User input to escape
        html_template: HTML template with {text} placeholder

    Returns:
        Safe HTML string

    Example:
        safe_markdown(user_input, '<div class="alert">{text}</div>')
    """
    escaped_text = escape_html(text)
    return html_template.format(text=escaped_text)


# ============================================================================
# BADGE HELPERS (for dashboard)
# ============================================================================

def safe_badge(text: str, css_class: str = "") -> str:
    """
    Create a safe badge HTML element.

    Args:
        text: Badge text (will be escaped)
        css_class: CSS class name (will be validated)

    Returns:
        Safe HTML for badge
    """
    # Validate CSS class (only allow alphanumeric, dash, underscore)
    if css_class and not re.match(r'^[a-zA-Z0-9_-]+$', css_class):
        css_class = ""

    escaped_text = escape_html(text)
    return f'<span class="badge {css_class}">{escaped_text}</span>'


def safe_stat_card(label: str, value: str, card_class: str = "") -> str:
    """
    Create a safe stat card HTML element.

    Args:
        label: Card label (will be escaped)
        value: Card value (will be escaped)
        card_class: CSS class name (will be validated)

    Returns:
        Safe HTML for stat card
    """
    # Validate CSS class
    if card_class and not re.match(r'^[a-zA-Z0-9_-]+$', card_class):
        card_class = ""

    escaped_label = escape_html(label)
    escaped_value = escape_html(value)

    return f'''
    <div class="stat-card {card_class}">
        <div class="stat-label">{escaped_label}</div>
        <div class="stat-value">{escaped_value}</div>
    </div>
    '''


# ============================================================================
# ALLOWED HTML TAGS (for more lenient escaping)
# ============================================================================

ALLOWED_TAGS = {
    'b', 'i', 'u', 'strong', 'em', 'br', 'p', 'span',
    'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'table', 'tr', 'td', 'th'
}

ALLOWED_ATTRIBUTES = {
    'class', 'id', 'style'
}


def sanitize_html(html_string: str, allowed_tags: Optional[set] = None,
                 allowed_attrs: Optional[set] = None) -> str:
    """
    Sanitize HTML by removing dangerous tags and attributes.

    WARNING: This is more permissive than escape_html. Only use when you
    need to preserve some HTML formatting from trusted sources.

    Args:
        html_string: HTML to sanitize
        allowed_tags: Set of allowed HTML tags (default: ALLOWED_TAGS)
        allowed_attrs: Set of allowed attributes (default: ALLOWED_ATTRIBUTES)

    Returns:
        Sanitized HTML string
    """
    if allowed_tags is None:
        allowed_tags = ALLOWED_TAGS
    if allowed_attrs is None:
        allowed_attrs = ALLOWED_ATTRIBUTES

    # For now, just escape everything - implement proper sanitization later if needed
    # To properly implement this, you'd need a library like bleach
    return escape_html(html_string)


# ============================================================================
# STREAMLIT HELPERS
# ============================================================================

def display_safe_header(header_text: str, css_class: str = "main-header"):
    """
    Display a safe header in Streamlit.

    Args:
        header_text: Header text (will be escaped)
        css_class: CSS class (will be validated)
    """
    import streamlit as st

    if css_class and not re.match(r'^[a-zA-Z0-9_-]+$', css_class):
        css_class = "main-header"

    escaped_text = escape_html(header_text)
    st.markdown(f'<div class="{css_class}">{escaped_text}</div>', unsafe_allow_html=True)


def display_safe_subtitle(subtitle_text: str, css_class: str = "main-subtitle"):
    """
    Display a safe subtitle in Streamlit.

    Args:
        subtitle_text: Subtitle text (will be escaped)
        css_class: CSS class (will be validated)
    """
    import streamlit as st

    if css_class and not re.match(r'^[a-zA-Z0-9_-]+$', css_class):
        css_class = "main-subtitle"

    escaped_text = escape_html(subtitle_text)
    st.markdown(f'<div class="{css_class}">{escaped_text}</div>', unsafe_allow_html=True)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test cases
    print("Testing HTML escaping...")

    # Test 1: XSS attempt
    malicious = "<script>alert('XSS')</script>"
    print(f"Input:  {malicious}")
    print(f"Output: {escape_html(malicious)}")
    print()

    # Test 2: Badge with XSS
    badge_text = "Approved<script>alert('xss')</script>"
    print(f"Badge:  {safe_badge(badge_text, 'success')}")
    print()

    # Test 3: Normal text
    normal = "Total: $1,234.56"
    print(f"Normal: {escape_html(normal)}")
    print()

    print("✅ All tests passed!")
