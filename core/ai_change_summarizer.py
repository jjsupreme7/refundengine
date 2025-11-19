"""
AI Change Summarizer for Excel Files

Generates detailed, human-readable summaries of Excel file changes
using AI to analyze cell-level modifications.
"""

import os
from collections import defaultdict
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_change_summary(
    changes: List[Dict[str, Any]], max_detail: int = None
) -> str:
    """
    Generate an AI-powered summary of Excel file changes

    Args:
        changes: List of cell changes from excel_cell_changes table
        max_detail: Maximum number of individual changes to include in detail
                   (auto-scaled based on total changes if None)

    Returns:
        Formatted markdown summary of changes
    """

    if not changes:
        return "No changes detected"

    # Auto-scale detail level based on number of changes
    if max_detail is None:
        if len(changes) <= 10:
            max_detail = len(changes)  # Show all for small sets
        elif len(changes) <= 50:
            max_detail = 10  # Show 10 for medium sets
        else:
            max_detail = 5  # Show only 5 for large sets

    # Group changes by type and column
    changes_by_column = defaultdict(list)
    changes_by_type = defaultdict(int)
    rows_affected = set()

    for change in changes:
        column = change.get("column_name", "Unknown")
        change_type = change.get("change_type", "modified")
        row_idx = change.get("row_index", 0)

        changes_by_column[column].append(change)
        changes_by_type[change_type] += 1
        rows_affected.add(row_idx)

    # Build structured data for AI
    summary_data = {
        "total_changes": len(changes),
        "rows_affected": len(rows_affected),
        "changes_by_type": dict(changes_by_type),
        "changes_by_column": {
            col: len(changes) for col, changes in changes_by_column.items()
        },
        "sample_changes": [],
    }

    # Add detailed samples (up to max_detail)
    for i, change in enumerate(changes[:max_detail]):
        summary_data["sample_changes"].append(
            {
                "row": change.get("row_index"),
                "column": change.get("column_name"),
                "old_value": str(change.get("old_value", ""))[
                    :100
                ],  # Truncate long values
                "new_value": str(change.get("new_value", ""))[:100],
                "type": change.get("change_type"),
            }
        )

    # Create prompt for AI (adjust verbosity based on change count)
    if len(changes) > 100:
        # Very concise for large change sets
        prompt = f"""Analyze {summary_data['total_changes']} Excel changes across {summary_data['rows_affected']} rows.

Changes by Column: {format_dict(summary_data['changes_by_column'])}

Create a 2-3 sentence executive summary focusing on:
- Which columns were most affected
- Overall pattern or purpose of changes

Be extremely concise."""
    else:
        # More detailed for smaller change sets
        prompt = f"""Analyze these Excel file changes and create a concise, professional summary.

Total Changes: {summary_data['total_changes']}
Rows Affected: {summary_data['rows_affected']}

Changes by Type:
{format_dict(summary_data['changes_by_type'])}

Changes by Column:
{format_dict(summary_data['changes_by_column'])}

Sample Changes (first {len(summary_data['sample_changes'])}):
{format_sample_changes(summary_data['sample_changes'])}

Create a summary that:
1. Starts with high-level overview (X cells changed in Y rows)
2. Groups changes by category (e.g., "Product Classifications", "Refund Estimates", "Vendor Information")
3. Highlights significant changes (large value changes, important field updates)
4. Uses bullet points for readability
5. Keeps it concise (3-5 sentences max)

Format the response as plain text with bullet points."""

    try:
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Faster and cheaper for summaries
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analyst creating concise summaries of spreadsheet changes. Focus on what changed and why it matters, not technical details.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent summaries
            max_tokens=300,
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        # Fallback to basic summary if AI fails
        print(f"⚠️ AI summary generation failed: {e}")
        return generate_basic_summary(summary_data)


def generate_basic_summary(data: Dict[str, Any]) -> str:
    """
    Generate a basic summary without AI (fallback)

    Args:
        data: Structured summary data

    Returns:
        Basic text summary
    """
    lines = [
        f"Modified {data['total_changes']} cells across {data['rows_affected']} rows"
    ]

    # Add changes by type
    if data["changes_by_type"]:
        type_summary = []
        for change_type, count in data["changes_by_type"].items():
            type_summary.append(f"{count} {change_type}")
        lines.append(f"Changes: {', '.join(type_summary)}")

    # Add top changed columns
    if data["changes_by_column"]:
        top_columns = sorted(
            data["changes_by_column"].items(), key=lambda x: x[1], reverse=True
        )[:5]

        column_summary = [f"{col} ({count})" for col, count in top_columns]
        lines.append(f"Columns: {', '.join(column_summary)}")

    return "\n".join(lines)


def format_dict(d: Dict) -> str:
    """Format dictionary for prompt"""
    return "\n".join([f"  - {k}: {v}" for k, v in d.items()])


def format_sample_changes(samples: List[Dict]) -> str:
    """Format sample changes for prompt"""
    lines = []
    for sample in samples:
        old_val = sample["old_value"] or "(empty)"
        new_val = sample["new_value"] or "(empty)"
        lines.append(
            f"  Row {sample['row']}, {sample['column']}: "
            f"{old_val} → {new_val} [{sample['type']}]"
        )
    return "\n".join(lines)


def generate_snapshot_summary(
    version_data: Dict[str, Any], changes: List[Dict[str, Any]]
) -> str:
    """
    Generate a summary for a manual snapshot (more contextual)

    Args:
        version_data: Version metadata (version number, created_by, etc.)
        changes: List of cell changes

    Returns:
        Snapshot summary with context
    """

    # Get change summary
    change_summary = generate_change_summary(changes)

    # Add snapshot context
    version_num = version_data.get("version_number", "Unknown")
    created_by = version_data.get("created_by", "Unknown")

    summary = f"""Snapshot #{version_num} created by {created_by}

{change_summary}

This snapshot represents a milestone in the analysis workflow."""

    return summary


# Example usage and testing
if __name__ == "__main__":
    # Test with sample changes
    sample_changes = [
        {
            "row_index": 23,
            "column_name": "Product_Type",
            "old_value": "SaaS",
            "new_value": "Professional Services",
            "change_type": "modified",
        },
        {
            "row_index": 45,
            "column_name": "Estimated_Refund",
            "old_value": "5000",
            "new_value": "8500",
            "change_type": "modified",
        },
        {
            "row_index": 67,
            "column_name": "Your_Answer",
            "old_value": "",
            "new_value": "85% of users outside WA",
            "change_type": "added",
        },
    ]

    print("Testing AI Change Summarizer...")
    print("=" * 60)
    summary = generate_change_summary(sample_changes)
    print(summary)
    print("=" * 60)
