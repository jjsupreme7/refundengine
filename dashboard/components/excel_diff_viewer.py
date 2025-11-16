"""
Excel Diff Viewer Component

GitHub-style diff viewer for Excel cell changes.
Shows old → new values with color coding and filtering.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime


def render_diff_viewer(
    version_id: str,
    changes: List[Dict[str, Any]],
    file_name: str,
    version_number: int,
    created_by: str,
    created_at: datetime
):
    """
    Render a GitHub-style diff viewer for Excel changes

    Args:
        version_id: UUID of the version
        changes: List of cell changes from excel_cell_changes table
        file_name: Name of the Excel file
        version_number: Version number
        created_by: Email of user who made changes
        created_at: Timestamp of changes
    """
    st.markdown(f"## 📋 Changes in Version {version_number}")
    st.markdown(f"**File:** {file_name}")
    st.markdown(f"**Changed by:** {created_by}")
    st.markdown(f"**Date:** {created_at.strftime('%B %d, %Y at %I:%M %p')}")

    if not changes:
        st.info("ℹ️ No changes detected in this version")
        return

    st.markdown("---")

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)

    added = len([c for c in changes if c.get('change_type') == 'added'])
    modified = len([c for c in changes if c.get('change_type') == 'modified'])
    deleted = len([c for c in changes if c.get('change_type') == 'deleted'])

    with col1:
        st.metric("Total Changes", len(changes))
    with col2:
        st.metric("Added", added, delta=None, delta_color="normal")
    with col3:
        st.metric("Modified", modified, delta=None, delta_color="normal")
    with col4:
        st.metric("Deleted", deleted, delta=None, delta_color="normal")

    st.markdown("---")

    # Filters
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Get unique rows
        unique_rows = sorted(set(c['row_index'] for c in changes))
        row_filter = st.multiselect(
            "Filter by Row",
            options=unique_rows,
            default=[],
            help="Select specific rows to view"
        )

    with col2:
        # Get unique columns
        unique_columns = sorted(set(c['column_name'] for c in changes))
        column_filter = st.multiselect(
            "Filter by Column",
            options=unique_columns,
            default=[],
            help="Select specific columns to view"
        )

    with col3:
        change_type_filter = st.selectbox(
            "Filter by Type",
            options=["All", "Added", "Modified", "Deleted"],
            help="Filter by change type"
        )

    # Apply filters
    filtered_changes = changes

    if row_filter:
        filtered_changes = [c for c in filtered_changes if c['row_index'] in row_filter]

    if column_filter:
        filtered_changes = [c for c in filtered_changes if c['column_name'] in column_filter]

    if change_type_filter != "All":
        filtered_changes = [c for c in filtered_changes if c.get('change_type') == change_type_filter.lower()]

    st.markdown(f"**Showing {len(filtered_changes)} of {len(changes)} changes**")

    st.markdown("---")

    # Group changes by row
    changes_by_row = {}
    for change in filtered_changes:
        row_idx = change['row_index']
        if row_idx not in changes_by_row:
            changes_by_row[row_idx] = []
        changes_by_row[row_idx].append(change)

    # Display changes row by row
    for row_idx in sorted(changes_by_row.keys()):
        row_changes = changes_by_row[row_idx]

        # Row header
        st.markdown(f"### 📍 Row {row_idx}")

        # Create DataFrame for better display
        change_data = []
        for change in row_changes:
            old_val = change.get('old_value', '(empty)')
            new_val = change.get('new_value', '(empty)')
            change_type = change.get('change_type', 'unknown')

            # Truncate long values
            if old_val and len(str(old_val)) > 100:
                old_val = str(old_val)[:100] + "..."
            if new_val and len(str(new_val)) > 100:
                new_val = str(new_val)[:100] + "..."

            change_data.append({
                'Column': change['column_name'],
                'Old Value': old_val,
                'New Value': new_val,
                'Type': change_type.upper()
            })

        # Display as table
        if change_data:
            df = pd.DataFrame(change_data)

            # Color code based on change type
            def highlight_changes(row):
                if row['Type'] == 'ADDED':
                    return ['background-color: #d4edda'] * len(row)
                elif row['Type'] == 'DELETED':
                    return ['background-color: #f8d7da'] * len(row)
                elif row['Type'] == 'MODIFIED':
                    return ['background-color: #fff3cd'] * len(row)
                return [''] * len(row)

            styled_df = df.style.apply(highlight_changes, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Alternative: Side-by-side view
        with st.expander(f"📊 Side-by-Side View - Row {row_idx}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Before (Old Values)**")
                for change in row_changes:
                    st.markdown(f"**{change['column_name']}:** {change.get('old_value', '(empty)')}")

            with col2:
                st.markdown("**After (New Values)**")
                for change in row_changes:
                    new_val = change.get('new_value', '(empty)')
                    # Highlight if changed
                    if change.get('change_type') == 'modified':
                        st.markdown(f"**{change['column_name']}:** ⚡ {new_val}")
                    else:
                        st.markdown(f"**{change['column_name']}:** {new_val}")

        st.markdown("---")

    # Export options
    st.markdown("### 📥 Export Changes")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Export to CSV", key=f"export_csv_{version_id}"):
            # Create CSV of all changes
            export_data = []
            for change in filtered_changes:
                export_data.append({
                    'Row': change['row_index'],
                    'Column': change['column_name'],
                    'Old Value': change.get('old_value', ''),
                    'New Value': change.get('new_value', ''),
                    'Change Type': change.get('change_type', ''),
                    'Changed By': change.get('changed_by', ''),
                    'Changed At': change.get('changed_at', '')
                })

            if export_data:
                df_export = pd.DataFrame(export_data)
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"changes_v{version_number}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    with col2:
        if st.button("📋 Copy Summary", key=f"copy_summary_{version_id}"):
            summary = f"""
Version {version_number} Changes Summary
File: {file_name}
Changed by: {created_by}
Date: {created_at.strftime('%Y-%m-%d %H:%M')}

Total Changes: {len(changes)}
- Added: {added}
- Modified: {modified}
- Deleted: {deleted}

Changes by Row:
"""
            for row_idx in sorted(changes_by_row.keys()):
                summary += f"\nRow {row_idx}:\n"
                for change in changes_by_row[row_idx]:
                    summary += f"  - {change['column_name']}: {change.get('old_value', '(empty)')} → {change.get('new_value', '(empty)')}\n"

            st.code(summary, language=None)


def render_compact_change_summary(changes: List[Dict[str, Any]], max_display: int = 5):
    """
    Render a compact summary of changes (for display in lists)

    Args:
        changes: List of cell changes
        max_display: Maximum number of changes to display
    """
    if not changes:
        st.info("No changes detected")
        return

    st.markdown(f"**{len(changes)} cells changed**")

    # Show first few changes
    for i, change in enumerate(changes[:max_display]):
        old_val = str(change.get('old_value', '(empty)'))
        new_val = str(change.get('new_value', '(empty)'))

        # Truncate long values
        if len(old_val) > 30:
            old_val = old_val[:30] + "..."
        if len(new_val) > 30:
            new_val = new_val[:30] + "..."

        # Icon based on change type
        change_type = change.get('change_type', 'modified')
        if change_type == 'added':
            icon = "✨"
        elif change_type == 'deleted':
            icon = "🗑️"
        else:
            icon = "✏️"

        st.markdown(
            f"{icon} Row {change['row_index']}, `{change['column_name']}`: "
            f"`{old_val}` → `{new_val}`"
        )

    if len(changes) > max_display:
        st.markdown(f"*...and {len(changes) - max_display} more changes*")


def compare_two_versions(
    version1_id: str,
    version2_id: str,
    version1_data: Dict,
    version2_data: Dict,
    supabase_client
):
    """
    Compare two versions side-by-side

    Args:
        version1_id: UUID of first version
        version2_id: UUID of second version
        version1_data: Version 1 metadata
        version2_data: Version 2 metadata
        supabase_client: Supabase client instance
    """
    st.markdown("## 🔄 Version Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### Version {version1_data['version_number']}")
        st.markdown(f"**Date:** {version1_data['created_at']}")
        st.markdown(f"**By:** {version1_data['created_by']}")

    with col2:
        st.markdown(f"### Version {version2_data['version_number']}")
        st.markdown(f"**Date:** {version2_data['created_at']}")
        st.markdown(f"**By:** {version2_data['created_by']}")

    st.markdown("---")

    # Get changes for both versions
    changes1_response = supabase_client.table('excel_cell_changes')\
        .select('*')\
        .eq('version_id', version1_id)\
        .execute()

    changes2_response = supabase_client.table('excel_cell_changes')\
        .select('*')\
        .eq('version_id', version2_id)\
        .execute()

    changes1 = changes1_response.data if changes1_response.data else []
    changes2 = changes2_response.data if changes2_response.data else []

    # TODO: Implement more sophisticated comparison logic
    st.info("Detailed comparison view coming soon!")
    st.markdown(f"Version {version1_data['version_number']} has {len(changes1)} changes")
    st.markdown(f"Version {version2_data['version_number']} has {len(changes2)} changes")
