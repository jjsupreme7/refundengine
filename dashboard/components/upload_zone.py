"""
Upload Zone Component - Dark Theme
==================================

Drag-and-drop file upload component with tax type selection.
Styled for dark theme with glass morphism effects.
"""

import streamlit as st
from typing import Optional, Callable
from pathlib import Path


def render_upload_zone(
    on_upload: Optional[Callable] = None,
    accepted_types: list[str] = ["pdf", "png", "jpg", "jpeg", "xlsx", "xls"],
    key: str = "upload_zone",
) -> tuple[Optional[list], Optional[str]]:
    """
    Render a styled upload zone with tax type selector.

    Args:
        on_upload: Optional callback function when files are uploaded
        accepted_types: List of accepted file extensions
        key: Unique key for the uploader widget

    Returns:
        Tuple of (uploaded_files, tax_type) or (None, None) if nothing uploaded
    """
    # Dark theme upload zone styles
    st.markdown("""
    <style>
    .dark-upload-container {
        border: 2px dashed rgba(99, 102, 241, 0.4);
        border-radius: 1rem;
        padding: 2rem;
        text-align: center;
        background: rgba(30, 27, 75, 0.3);
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    .dark-upload-container:hover {
        border-color: #8b5cf6;
        background: rgba(30, 27, 75, 0.5);
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.3);
    }
    .upload-icon-dark {
        width: 64px;
        height: 64px;
        margin: 0 auto 1rem;
        padding: 1rem;
        background: rgba(139, 92, 246, 0.2);
        border-radius: 50%;
    }
    .upload-title-dark {
        font-size: 1.125rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .upload-subtitle-dark {
        font-size: 0.875rem;
        color: #9ca3af;
        max-width: 400px;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Tax type selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tax_type = st.radio(
            "What type of tax are you analyzing?",
            options=["Sales Tax", "Use Tax"],
            horizontal=True,
            key=f"{key}_tax_type",
            help="Sales Tax: Tax collected at point of sale. Use Tax: Tax on purchases where sales tax wasn't collected."
        )

    # Visual upload zone (decorative)
    st.markdown("""
    <div class="dark-upload-container">
        <div class="upload-icon-dark">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c4b5fd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
        </div>
        <div class="upload-title-dark">Drop invoices or purchase orders here</div>
        <div class="upload-subtitle-dark">
            Supports PDF, Excel, JPG, PNG. Our engine automatically extracts line items and assigns tax codes.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Actual file uploader
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=accepted_types,
        accept_multiple_files=True,
        key=f"{key}_uploader",
        label_visibility="collapsed"
    )

    if uploaded_files:
        # Show upload summary with dark theme
        st.markdown(f"""
        <div style="
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 0.75rem;
            padding: 1rem;
            margin-top: 1rem;
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem; color: #86efac; font-weight: 600;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                {len(uploaded_files)} file(s) ready for {tax_type.lower()} analysis
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #6ee7b7;">
                {''.join([f'<div style="padding: 0.25rem 0;">• {f.name} ({f.size / 1024:.1f} KB)</div>' for f in uploaded_files])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Analyze Documents", type="primary", use_container_width=True, key=f"{key}_analyze"):
                if on_upload:
                    on_upload(uploaded_files, tax_type)
                return uploaded_files, tax_type

        return uploaded_files, tax_type

    return None, None


def render_file_list(
    files: list[dict],
    on_select: Optional[Callable] = None,
) -> Optional[dict]:
    """
    Render a list of processed files with status indicators.

    Args:
        files: List of file dicts with keys: name, status, confidence, category, amount
        on_select: Callback when a file is selected

    Returns:
        Selected file dict or None
    """
    if not files:
        st.markdown("""
        <div style="
            background: rgba(30, 27, 75, 0.3);
            border: 1px solid rgba(49, 46, 129, 0.4);
            border-radius: 0.75rem;
            padding: 2rem;
            text-align: center;
            color: #9ca3af;
        ">
            No documents uploaded yet. Use the upload zone above to add invoices or purchase orders.
        </div>
        """, unsafe_allow_html=True)
        return None

    selected = None

    for idx, file in enumerate(files):
        status = file.get("status", "pending")
        confidence = file.get("confidence", 0)

        # Status colors for dark theme
        status_colors = {
            "completed": ("#22c55e", "rgba(34, 197, 94, 0.2)", "#86efac"),
            "processing": ("#3b82f6", "rgba(59, 130, 246, 0.2)", "#93c5fd"),
            "error": ("#ef4444", "rgba(239, 68, 68, 0.2)", "#fca5a5"),
            "pending": ("#6b7280", "rgba(107, 114, 128, 0.2)", "#9ca3af"),
            "flagged": ("#f59e0b", "rgba(245, 158, 11, 0.2)", "#fcd34d"),
        }
        dot_color, bg_color, text_color = status_colors.get(status, status_colors["pending"])

        # Confidence bar color
        conf_color = "#22c55e" if confidence >= 0.9 else "#f59e0b" if confidence >= 0.7 else "#ef4444"

        # File row
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1.5])

        with col1:
            st.markdown(f"""
            <div style="
                width: 10px;
                height: 10px;
                background: {dot_color};
                border-radius: 50%;
                box-shadow: 0 0 0 3px {bg_color};
                margin-top: 0.75rem;
            "></div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="font-weight: 500; color: #ffffff;">{file.get('name', 'Unknown')}</div>
            <div style="font-size: 0.75rem; color: #9ca3af;">{file.get('category', 'Uncategorized')}</div>
            """, unsafe_allow_html=True)

        with col3:
            if confidence > 0:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                    <div style="
                        flex: 1;
                        height: 6px;
                        background: rgba(49, 46, 129, 0.5);
                        border-radius: 9999px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: {confidence * 100}%;
                            height: 100%;
                            background: {conf_color};
                            border-radius: 9999px;
                        "></div>
                    </div>
                    <span style="font-size: 0.75rem; color: #9ca3af; font-family: monospace;">{int(confidence * 100)}%</span>
                </div>
                """, unsafe_allow_html=True)

        with col4:
            if file.get("amount"):
                st.markdown(f"""
                <div style="
                    font-family: monospace;
                    font-weight: 500;
                    color: #ffffff;
                    text-align: right;
                    margin-top: 0.5rem;
                ">${file['amount']:,.2f}</div>
                """, unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid rgba(49, 46, 129, 0.3);'>", unsafe_allow_html=True)

    return selected


def save_uploaded_files(
    files: list,
    destination: str = "uploads",
) -> list[str]:
    """
    Save uploaded files to disk.

    Args:
        files: List of UploadedFile objects from Streamlit
        destination: Directory to save files to

    Returns:
        List of saved file paths
    """
    dest_path = Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)

    saved_paths = []

    for file in files:
        file_path = dest_path / file.name

        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

        saved_paths.append(str(file_path))

    return saved_paths


# Export
__all__ = [
    "render_upload_zone",
    "render_file_list",
    "save_uploaded_files",
]
