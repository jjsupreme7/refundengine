"""
Stat Card Component - Dark Theme
================================

Reusable stat card component for dashboard metrics.
Styled with glass morphism and optional progress bars.
"""

import streamlit as st
from typing import Optional, Literal

# Color variants for dark theme
VARIANTS = {
    "success": {
        "border": "#22c55e",
        "icon_bg": "rgba(34, 197, 94, 0.2)",
        "icon_color": "#86efac",
        "value_color": "#86efac",
    },
    "warning": {
        "border": "#f59e0b",
        "icon_bg": "rgba(245, 158, 11, 0.2)",
        "icon_color": "#fcd34d",
        "value_color": "#fcd34d",
    },
    "danger": {
        "border": "#ef4444",
        "icon_bg": "rgba(239, 68, 68, 0.2)",
        "icon_color": "#fca5a5",
        "value_color": "#fca5a5",
    },
    "info": {
        "border": "#3b82f6",
        "icon_bg": "rgba(59, 130, 246, 0.2)",
        "icon_color": "#93c5fd",
        "value_color": "#93c5fd",
    },
    "purple": {
        "border": "#8b5cf6",
        "icon_bg": "rgba(139, 92, 246, 0.2)",
        "icon_color": "#c4b5fd",
        "value_color": "#c4b5fd",
    },
    "emerald": {
        "border": "#10b981",
        "icon_bg": "rgba(16, 185, 129, 0.2)",
        "icon_color": "#6ee7b7",
        "value_color": "#6ee7b7",
    },
    "default": {
        "border": "#6366f1",
        "icon_bg": "rgba(99, 102, 241, 0.2)",
        "icon_color": "#a5b4fc",
        "value_color": "#ffffff",
    },
}

# Icons (SVG paths for common dashboard icons)
ICONS = {
    "trending_up": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>""",
    "file_text": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>""",
    "alert_circle": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>""",
    "arrow_up_right": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>""",
    "dollar": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>""",
    "check_circle": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>""",
    "clock": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>""",
    "activity": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>""",
    "database": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>""",
    "users": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>""",
}


def render_stat_card(
    label: str,
    value: str,
    subtitle: Optional[str] = None,
    change: Optional[str] = None,
    icon: str = "trending_up",
    variant: Literal["success", "warning", "danger", "info", "purple", "emerald", "default"] = "default",
    progress: Optional[float] = None,
) -> None:
    """
    Render a stat card with icon, value, and optional change indicator.

    Args:
        label: Card label (e.g., "Est. B&O Liability")
        value: Main value to display (e.g., "$12,450")
        subtitle: Optional subtitle text
        change: Optional change indicator (e.g., "+2.4%")
        icon: Icon name from ICONS dict
        variant: Color variant
        progress: Optional progress value (0-100) to show a progress bar
    """
    colors = VARIANTS.get(variant, VARIANTS["default"])
    icon_svg = ICONS.get(icon, ICONS["trending_up"])

    # Determine change color
    change_color = "#86efac" if change and change.startswith("+") else "#fca5a5" if change else "#9ca3af"

    # Progress bar HTML if provided
    progress_html = ""
    if progress is not None:
        progress_variant = "success" if progress >= 75 else "warning" if progress >= 50 else "danger"
        progress_html = f"""
        <div style="
            height: 4px;
            background: rgba(49, 46, 129, 0.5);
            border-radius: 9999px;
            overflow: hidden;
            margin-top: 0.75rem;
        ">
            <div style="
                width: {progress}%;
                height: 100%;
                background: linear-gradient(90deg, {colors['border']}, {colors['icon_color']});
                border-radius: 9999px;
            "></div>
        </div>
        """

    # Build the HTML
    html = f"""
    <div style="
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(49, 46, 129, 0.4);
        border-radius: 0.75rem;
        padding: 1.25rem;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s ease;
    " onmouseover="this.style.boxShadow='0 0 25px rgba(139, 92, 246, 0.3)'; this.style.transform='translateY(-2px)';"
       onmouseout="this.style.boxShadow='none'; this.style.transform='translateY(0)';">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="
                padding: 0.625rem;
                border-radius: 0.75rem;
                background: {colors['icon_bg']};
                color: {colors['icon_color']};
            ">
                {icon_svg}
            </div>
            {f'<span style="font-size: 0.75rem; font-weight: 500; color: {change_color}; background: rgba(255,255,255,0.05); padding: 0.25rem 0.5rem; border-radius: 9999px;">{change}</span>' if change else ''}
        </div>
        <div>
            <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 0.25rem;">
                {label}
            </div>
            <div style="font-size: 1.75rem; font-weight: 700; color: {colors['value_color']}; line-height: 1.2;">
                {value}
            </div>
            {f'<div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''}
            {progress_html}
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_stat_grid(stats: list[dict]) -> None:
    """
    Render a grid of stat cards using Streamlit columns.

    Args:
        stats: List of stat card configurations
    """
    cols = st.columns(len(stats[:4]))

    for idx, stat in enumerate(stats[:4]):
        with cols[idx]:
            colors = VARIANTS.get(stat.get("variant", "default"), VARIANTS["default"])
            icon_name = stat.get("icon", "trending_up")
            icon_svg = ICONS.get(icon_name, ICONS["trending_up"])
            change = stat.get("change", "")
            subtitle = stat.get("subtitle", "")
            label = stat.get("label", "")
            value = stat.get("value", "")

            change_color = "#86efac" if change.startswith("+") else "#fca5a5" if change.startswith("-") else "#9ca3af"

            # Build HTML without multiline strings
            html = '<div style="background:rgba(30,27,75,0.3);backdrop-filter:blur(12px);border:1px solid rgba(49,46,129,0.4);border-radius:0.75rem;padding:1.25rem;min-height:160px;">'
            html += '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;">'
            html += f'<div style="padding:0.625rem;border-radius:0.75rem;background:{colors["icon_bg"]};color:{colors["icon_color"]};">{icon_svg}</div>'
            if change:
                html += f'<span style="font-size:0.75rem;font-weight:500;color:{change_color};background:rgba(255,255,255,0.05);padding:0.25rem 0.5rem;border-radius:9999px;">{change}</span>'
            html += '</div>'
            html += f'<div style="font-size:0.7rem;color:#9ca3af;text-transform:uppercase;font-weight:600;letter-spacing:0.05em;margin-bottom:0.25rem;">{label}</div>'
            html += f'<div style="font-size:1.75rem;font-weight:700;color:{colors["value_color"]};line-height:1.2;">{value}</div>'
            if subtitle:
                html += f'<div style="font-size:0.75rem;color:#6b7280;margin-top:0.25rem;">{subtitle}</div>'
            html += '</div>'

            st.markdown(html, unsafe_allow_html=True)


def render_summary_cards(stats: list[dict]) -> None:
    """
    Render summary cards like Nebula Transactions page (Income, Expenses, Net Flow).

    Args:
        stats: List of summary card configs with:
            - label: str
            - value: str
            - change: Optional[str]
            - variant: str ("success", "danger", "info")
    """
    cols = st.columns(len(stats))

    for idx, stat in enumerate(stats):
        variant = stat.get("variant", "info")
        colors = VARIANTS.get(variant, VARIANTS["default"])
        change = stat.get("change", "")
        change_color = "#86efac" if change.startswith("+") else "#fca5a5" if change.startswith("-") else "#9ca3af"

        with cols[idx]:
            st.markdown(f"""
            <div style="
                background: rgba(30, 27, 75, 0.3);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(49, 46, 129, 0.4);
                border-radius: 0.75rem;
                padding: 1.25rem;
                transition: all 0.3s ease;
            " onmouseover="this.style.boxShadow='0 0 25px rgba(139, 92, 246, 0.3)'; this.style.transform='translateY(-2px)';"
               onmouseout="this.style.boxShadow='none'; this.style.transform='translateY(0)';">
                <div style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.5rem;">{stat.get('label', '')}</div>
                <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                    <span style="font-size: 1.75rem; font-weight: 700; color: {colors['value_color']};">{stat.get('value', '')}</span>
                    <span style="font-size: 0.75rem; color: {change_color};">{change}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# Export
__all__ = ["render_stat_card", "render_stat_grid", "render_summary_cards", "ICONS", "VARIANTS"]
