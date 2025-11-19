#!/usr/bin/env python3
"""
Check Supabase Storage Usage

Monitors storage usage in the 'knowledge-base' bucket and provides
periodic updates on how much storage is being used.

Usage:
    python scripts/check_storage_usage.py
    python scripts/check_storage_usage.py --detailed  # Show file breakdown
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_supabase_client

BUCKET_NAME = "knowledge-base"
FREE_TIER_LIMIT_GB = 1.0  # Supabase free tier: 1GB


def format_bytes(bytes_value):
    """Format bytes into human-readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def get_storage_usage(detailed=False):
    """Get storage usage statistics"""
    supabase = get_supabase_client()

    print("\n" + "=" * 80)
    print("📊 SUPABASE STORAGE USAGE REPORT")
    print("=" * 80)
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Free Tier Limit: {FREE_TIER_LIMIT_GB} GB")
    print()

    try:
        # List all files recursively
        files = list_files_recursive(supabase, "", [])

        if not files:
            print("⚠️  No files found in bucket")
            return

        # Calculate totals
        total_size = sum(f.get("metadata", {}).get("size", 0) for f in files)
        total_count = len(files)

        # Breakdown by type
        pdf_files = [f for f in files if f["name"].endswith(".pdf")]
        html_files = [f for f in files if f["name"].endswith((".html", ".htm"))]
        other_files = [
            f for f in files if not f["name"].endswith((".pdf", ".html", ".htm"))
        ]

        pdf_size = sum(f.get("metadata", {}).get("size", 0) for f in pdf_files)
        html_size = sum(f.get("metadata", {}).get("size", 0) for f in html_files)
        other_size = sum(f.get("metadata", {}).get("size", 0) for f in other_files)

        # Display summary
        print("📈 SUMMARY")
        print("-" * 80)
        print(f"Total Files: {total_count:,}")
        print(f"Total Size: {format_bytes(total_size)}")
        print()

        # Usage percentage
        usage_percent = (total_size / (FREE_TIER_LIMIT_GB * 1024**3)) * 100
        print(f"Storage Used: {usage_percent:.1f}% of free tier")
        print()

        # Progress bar
        bar_width = 50
        filled = int(bar_width * usage_percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"[{bar}] {usage_percent:.1f}%")
        print()

        # Breakdown
        print("📁 FILE TYPE BREAKDOWN")
        print("-" * 80)
        print(f"PDFs:  {len(pdf_files):>6,} files  |  {format_bytes(pdf_size):>12}")
        if html_files:
            print(
                f"HTML:  {len(html_files):>6,} files  |  {format_bytes(html_size):>12}"
            )
        if other_files:
            print(
                f"Other: {len(other_files):>6,} files  |  {format_bytes(other_size):>12}"
            )
        print()

        # Space remaining
        remaining_bytes = (FREE_TIER_LIMIT_GB * 1024**3) - total_size
        print(
            f"💾 Space Remaining: {format_bytes(remaining_bytes)} ({100 - usage_percent:.1f}%)"
        )
        print()

        # Warnings
        if usage_percent > 80:
            print("⚠️  WARNING: Storage usage above 80%!")
            print("   Consider upgrading to Supabase Pro or cleaning up old files")
        elif usage_percent > 50:
            print("ℹ️  INFO: Storage usage above 50%")
        else:
            print("✅ Storage usage healthy")

        # Detailed breakdown
        if detailed:
            print("\n" + "=" * 80)
            print("📋 DETAILED FILE LISTING")
            print("=" * 80)

            # Group by folder
            folders = {}
            for f in files:
                path_parts = f["name"].split("/")
                folder = "/".join(path_parts[:-1]) if len(path_parts) > 1 else "root"
                if folder not in folders:
                    folders[folder] = []
                folders[folder].append(f)

            for folder, folder_files in sorted(folders.items()):
                folder_size = sum(
                    f.get("metadata", {}).get("size", 0) for f in folder_files
                )
                print(f"\n📁 {folder}/")
                print(
                    f"   Files: {len(folder_files):,}  |  Size: {format_bytes(folder_size)}"
                )

                if len(folder_files) <= 10:
                    for f in folder_files:
                        file_size = f.get("metadata", {}).get("size", 0)
                        print(
                            f"      • {Path(f['name']).name} ({format_bytes(file_size)})"
                        )
                else:
                    for f in folder_files[:5]:
                        file_size = f.get("metadata", {}).get("size", 0)
                        print(
                            f"      • {Path(f['name']).name} ({format_bytes(file_size)})"
                        )
                    print(f"      ... and {len(folder_files) - 5} more files")

        print("\n" + "=" * 80)
        print("✅ Report Complete")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"❌ Error checking storage: {e}")
        import traceback

        traceback.print_exc()


def list_files_recursive(supabase, path, files_list):
    """Recursively list all files in bucket"""
    try:
        items = supabase.storage.from_(BUCKET_NAME).list(path)

        for item in items:
            item_name = item["name"]
            item_path = f"{path}/{item_name}" if path else item_name

            # Check if it's a folder (id is null for folders)
            if item.get("id") is None:
                # It's a folder, recurse into it
                list_files_recursive(supabase, item_path, files_list)
            else:
                # It's a file, add it
                files_list.append(
                    {"name": item_path, "metadata": item.get("metadata", {})}
                )

        return files_list

    except Exception as e:
        print(f"⚠️  Error listing path '{path}': {e}")
        return files_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Supabase Storage usage")
    parser.add_argument(
        "--detailed",
        "-d",
        action="store_true",
        help="Show detailed file breakdown by folder",
    )

    args = parser.parse_args()

    get_storage_usage(detailed=args.detailed)
