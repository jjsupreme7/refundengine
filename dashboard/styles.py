"""
Dashboard Styles - NexusTax Dark Theme
======================================

Dark theme inspired by Nebula UI templates.
Glass morphism effects with indigo/purple accents.
"""

# Color constants - Dark Theme
BG_PRIMARY = "#0f172a"           # Main background
BG_SECONDARY = "rgba(30, 27, 75, 0.3)"  # Card backgrounds (indigo-900/30)
BORDER_COLOR = "rgba(49, 46, 129, 0.4)"  # Borders (indigo-800/40)

# Accent colors
WA_EMERALD = "#10b981"
WA_EMERALD_LIGHT = "#34d399"
WA_EMERALD_DARK = "#059669"
ACCENT_PURPLE = "#8b5cf6"
ACCENT_INDIGO = "#6366f1"

# Text colors
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#9ca3af"       # gray-400
TEXT_MUTED = "#6b7280"           # gray-500

# Status colors
STATUS_SUCCESS = "#22c55e"
STATUS_WARNING = "#f59e0b"
STATUS_DANGER = "#ef4444"
STATUS_INFO = "#3b82f6"

# Legacy aliases for compatibility
WA_NAVY = "#1e293b"
WA_NAVY_LIGHT = "#334155"

# Main CSS theme
THEME_CSS = """
<style>
    /* =========================================================================
       ROOT VARIABLES - Dark Theme
       ========================================================================= */
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: rgba(30, 27, 75, 0.3);
        --bg-tertiary: rgba(30, 27, 75, 0.5);
        --border-color: rgba(49, 46, 129, 0.4);
        --border-light: rgba(99, 102, 241, 0.2);

        --text-primary: #ffffff;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;

        --accent-emerald: #10b981;
        --accent-purple: #8b5cf6;
        --accent-indigo: #6366f1;

        --status-success: #22c55e;
        --status-warning: #f59e0b;
        --status-danger: #ef4444;
        --status-info: #3b82f6;

        --glow-purple: rgba(139, 92, 246, 0.3);
        --glow-emerald: rgba(16, 185, 129, 0.3);
    }

    /* =========================================================================
       STREAMLIT OVERRIDES
       ========================================================================= */

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Main app background - dark */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0c1425 100%);
        background-attachment: fixed;
    }

    /* Sidebar styling - darker navy */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--border-color) !important;
    }

    /* Fix text colors in main content */
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: var(--text-primary);
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }

    /* Streamlit widgets dark theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {
        background-color: var(--bg-tertiary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-purple) !important;
        box-shadow: 0 0 0 2px var(--glow-purple) !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: rgba(99, 102, 241, 0.3) !important;
        border-color: var(--accent-indigo) !important;
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-indigo) 100%) !important;
        border: none !important;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 20px var(--glow-purple);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary);
        border-radius: 0.75rem;
        padding: 0.25rem;
        gap: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 0.5rem;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0.75rem !important;
        color: var(--text-primary) !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 0.75rem 0.75rem !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    /* Dataframe */
    .stDataFrame {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0.75rem !important;
    }

    /* Alerts */
    .stAlert {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: var(--bg-tertiary) !important;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-purple), var(--accent-indigo)) !important;
    }

    /* =========================================================================
       GLASS PANEL - Core Component
       ========================================================================= */
    .glass-panel {
        background: var(--bg-secondary);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .glass-panel:hover {
        box-shadow: 0 0 25px var(--glow-purple);
        transform: translateY(-2px);
    }

    /* =========================================================================
       STAT CARDS - Dashboard Metrics
       ========================================================================= */
    .stat-card {
        background: var(--bg-secondary);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        box-shadow: 0 0 25px var(--glow-purple);
        transform: translateY(-2px);
    }

    .stat-card.success { border-left: 3px solid var(--status-success); }
    .stat-card.warning { border-left: 3px solid var(--status-warning); }
    .stat-card.danger { border-left: 3px solid var(--status-danger); }
    .stat-card.info { border-left: 3px solid var(--status-info); }
    .stat-card.purple { border-left: 3px solid var(--accent-purple); }

    .stat-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }

    .stat-value.emerald { color: var(--accent-emerald); }
    .stat-value.success { color: var(--status-success); }
    .stat-value.warning { color: var(--status-warning); }
    .stat-value.danger { color: var(--status-danger); }
    .stat-value.purple { color: var(--accent-purple); }

    .stat-subtitle {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }

    /* =========================================================================
       SECTION CARD - Content Containers
       ========================================================================= */
    .section-card {
        background: var(--bg-secondary);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }

    /* =========================================================================
       PROGRESS BARS
       ========================================================================= */
    .progress-bar {
        height: 4px;
        background: rgba(49, 46, 129, 0.5);
        border-radius: 9999px;
        overflow: hidden;
        margin-top: 0.75rem;
    }

    .progress-bar-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }

    .progress-bar-fill.gradient {
        background: linear-gradient(90deg, var(--accent-purple), var(--accent-indigo));
    }

    .progress-bar-fill.success {
        background: linear-gradient(90deg, #22c55e, #10b981);
    }

    .progress-bar-fill.warning {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
    }

    .progress-bar-fill.danger {
        background: linear-gradient(90deg, #ef4444, #f87171);
    }

    /* Confidence bar (compatibility) */
    .confidence-bar {
        height: 6px;
        background: rgba(49, 46, 129, 0.5);
        border-radius: 9999px;
        overflow: hidden;
    }

    .confidence-bar-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }

    .confidence-bar-fill.high { background: var(--status-success); }
    .confidence-bar-fill.medium { background: var(--status-warning); }
    .confidence-bar-fill.low { background: var(--status-danger); }

    /* =========================================================================
       BADGES - Status & Category
       ========================================================================= */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Dark theme badges */
    .badge-completed, .badge-success {
        background: rgba(34, 197, 94, 0.2);
        color: #86efac;
    }

    .badge-pending, .badge-warning {
        background: rgba(234, 179, 8, 0.2);
        color: #fde047;
    }

    .badge-error, .badge-danger {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
    }

    .badge-info {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
    }

    .badge-purple {
        background: rgba(139, 92, 246, 0.2);
        color: #c4b5fd;
    }

    /* Category badges */
    .badge-taxable {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
    }

    .badge-exempt {
        background: rgba(34, 197, 94, 0.2);
        color: #86efac;
    }

    .badge-review {
        background: rgba(234, 179, 8, 0.2);
        color: #fde047;
    }

    .badge-rcw {
        background: rgba(99, 102, 241, 0.2);
        color: #a5b4fc;
    }

    .badge-wac {
        background: rgba(234, 179, 8, 0.2);
        color: #fde047;
    }

    .badge-bill {
        background: rgba(34, 197, 94, 0.2);
        color: #86efac;
    }

    /* =========================================================================
       STATUS DOTS
       ========================================================================= */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.ok, .status-dot.completed {
        background-color: var(--status-success);
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
    }

    .status-dot.flagged, .status-dot.pending {
        background-color: var(--status-warning);
        box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
    }

    .status-dot.error {
        background-color: var(--status-danger);
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
    }

    .status-dot.processing {
        background-color: var(--status-info);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* =========================================================================
       UPLOAD ZONE
       ========================================================================= */
    .upload-zone {
        border: 2px dashed var(--border-color);
        border-radius: 1rem;
        padding: 3rem 2rem;
        text-align: center;
        background: var(--bg-secondary);
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .upload-zone:hover {
        border-color: var(--accent-purple);
        background: var(--bg-tertiary);
        box-shadow: 0 0 30px var(--glow-purple);
    }

    /* =========================================================================
       TABLES - Dark Theme
       ========================================================================= */
    .dark-table {
        width: 100%;
        border-collapse: collapse;
    }

    .dark-table thead {
        border-bottom: 1px solid var(--border-color);
    }

    .dark-table th {
        padding: 0.75rem 1rem;
        text-align: left;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .dark-table tbody tr {
        border-bottom: 1px solid rgba(49, 46, 129, 0.2);
        transition: background 0.2s ease;
    }

    .dark-table tbody tr:hover {
        background: rgba(99, 102, 241, 0.1);
    }

    .dark-table td {
        padding: 1rem;
        color: var(--text-primary);
        font-size: 0.875rem;
    }

    /* =========================================================================
       SEARCH & FILTER BAR
       ========================================================================= */
    .search-filter-bar {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }

    .search-input {
        width: 100%;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        padding: 0.75rem 1rem 0.75rem 2.5rem;
        color: var(--text-primary);
        font-size: 0.875rem;
    }

    .search-input::placeholder {
        color: var(--text-muted);
    }

    .search-input:focus {
        outline: none;
        border-color: var(--accent-purple);
        box-shadow: 0 0 0 3px var(--glow-purple);
    }

    /* =========================================================================
       FILTER PILLS
       ========================================================================= */
    .filter-pill {
        display: inline-flex;
        padding: 0.375rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        transition: all 0.2s ease;
        cursor: pointer;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .filter-pill:hover {
        border-color: var(--accent-purple);
        color: var(--accent-purple);
    }

    .filter-pill.active {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-indigo));
        color: white;
        border-color: transparent;
    }

    /* =========================================================================
       RESEARCH CARDS
       ========================================================================= */
    .research-card {
        background: var(--bg-secondary);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        transition: all 0.2s ease;
        cursor: pointer;
        margin-bottom: 1rem;
    }

    .research-card:hover {
        border-color: var(--accent-purple);
        box-shadow: 0 0 20px var(--glow-purple);
        transform: translateY(-2px);
    }

    /* =========================================================================
       AI CHAT STYLING
       ========================================================================= */
    .ai-message {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        border-top-left-radius: 0;
        padding: 1rem;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }

    .user-message {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-indigo));
        border-radius: 1rem;
        border-top-right-radius: 0;
        padding: 1rem;
        margin-bottom: 1rem;
        color: white;
    }

    /* =========================================================================
       URGENT ACTION ITEMS
       ========================================================================= */
    .urgent-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 0.75rem;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        margin-bottom: 0.5rem;
    }

    .urgent-item.info {
        background: rgba(59, 130, 246, 0.15);
        border-color: rgba(59, 130, 246, 0.3);
    }

    .urgent-item.warning {
        background: rgba(234, 179, 8, 0.15);
        border-color: rgba(234, 179, 8, 0.3);
    }

    /* =========================================================================
       ACTION BUTTONS
       ========================================================================= */
    .action-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        cursor: pointer;
        border: none;
    }

    .action-btn-primary {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-indigo));
        color: white;
    }

    .action-btn-primary:hover {
        box-shadow: 0 0 20px var(--glow-purple);
        transform: translateY(-1px);
    }

    .action-btn-secondary {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .action-btn-secondary:hover {
        border-color: var(--accent-purple);
        background: rgba(139, 92, 246, 0.1);
    }

    /* =========================================================================
       PAGINATION
       ========================================================================= */
    .pagination {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        margin-top: 1.5rem;
    }

    .pagination-btn {
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 0.5rem;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .pagination-btn:hover {
        border-color: var(--accent-purple);
        color: var(--text-primary);
    }

    .pagination-btn.active {
        background: var(--accent-indigo);
        border-color: var(--accent-indigo);
        color: white;
    }

    /* =========================================================================
       AMOUNT DISPLAY
       ========================================================================= */
    .amount-positive {
        color: #86efac;
        font-family: monospace;
        font-weight: 500;
    }

    .amount-negative {
        color: #fca5a5;
        font-family: monospace;
        font-weight: 500;
    }

    /* =========================================================================
       FLOATING AI BUTTON
       ========================================================================= */
    .ai-float-btn {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-indigo));
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 9999px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 4px 20px var(--glow-purple);
        cursor: pointer;
        z-index: 1000;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .ai-float-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 30px var(--glow-purple);
    }

    /* =========================================================================
       ICON CONTAINERS
       ========================================================================= */
    .icon-container {
        width: 40px;
        height: 40px;
        border-radius: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .icon-container.purple {
        background: rgba(139, 92, 246, 0.2);
        color: #c4b5fd;
    }

    .icon-container.emerald {
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
    }

    .icon-container.blue {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
    }

    .icon-container.amber {
        background: rgba(245, 158, 11, 0.2);
        color: #fcd34d;
    }

    .icon-container.red {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
    }
</style>
"""


def inject_css():
    """Inject the CSS theme into the Streamlit app."""
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def stat_card_html(label: str, value: str, subtitle: str = "", variant: str = "") -> str:
    """Generate HTML for a stat card.

    Args:
        label: The card label (e.g., "Pending Invoices")
        value: The main value (e.g., "23")
        subtitle: Optional subtitle text
        variant: Optional variant class ("warning", "danger", "info", "success", "purple")
    """
    card_class = f"stat-card {variant}" if variant else "stat-card"
    value_class = f"stat-value {variant}" if variant else "stat-value"

    return f"""
    <div class="{card_class}">
        <div class="stat-label">{label}</div>
        <div class="{value_class}">{value}</div>
        {f'<div class="stat-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """


def badge_html(text: str, variant: str = "info") -> str:
    """Generate HTML for a badge.

    Args:
        text: Badge text
        variant: "success", "warning", "danger", "info", "purple", "taxable", "exempt", "review", "rcw", "wac", "bill"
    """
    return f'<span class="badge badge-{variant}">{text}</span>'


def status_dot_html(status: str = "ok") -> str:
    """Generate HTML for a status dot.

    Args:
        status: "ok", "completed", "flagged", "pending", "error", "processing"
    """
    return f'<span class="status-dot {status}"></span>'


def confidence_bar_html(confidence: float) -> str:
    """Generate HTML for a confidence bar.

    Args:
        confidence: Value between 0 and 1
    """
    percentage = int(confidence * 100)
    level = "high" if confidence >= 0.9 else "medium" if confidence >= 0.7 else "low"

    return f"""
    <div class="confidence-bar">
        <div class="confidence-bar-fill {level}" style="width: {percentage}%"></div>
    </div>
    <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem;">{percentage}%</span>
    """


def progress_bar_html(percentage: float, variant: str = "gradient") -> str:
    """Generate HTML for a progress bar.

    Args:
        percentage: Value between 0 and 100
        variant: "gradient", "success", "warning", "danger"
    """
    return f"""
    <div class="progress-bar">
        <div class="progress-bar-fill {variant}" style="width: {percentage}%"></div>
    </div>
    """
