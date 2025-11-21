"""
Excel Versioning Module

Handles Excel file uploads, versioning, change tracking, and storage management.

Key Features:
- Upload files to Supabase Storage
- Create and track versions
- Generate diffs between versions
- File locking for concurrent editing
- Change tracking at cell level

Usage:
    from core.excel_versioning import ExcelVersionManager

    # Uses centralized Supabase client automatically
    manager = ExcelVersionManager()

    # Upload new file
    file_id = manager.upload_file(
        file_path="Master_Refunds.xlsx",
        project_id="abc-123",
        user_email="analyst@company.com"
    )

    # Create new version
    version_id = manager.create_version(
        file_id=file_id,
        file_path="Master_Refunds_updated.xlsx",
        user_email="analyst@company.com",
        change_summary="Updated 45 refund amounts"
    )

    # Get diff between versions
    diff = manager.get_version_diff(file_id, version_1=1, version_2=2)
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import openpyxl
import pandas as pd
from openpyxl import load_workbook
from storage3.exceptions import StorageApiError
from supabase import Client

from core.database import get_supabase_client


class ExcelVersionManager:
    """Manages Excel file versioning in Supabase"""

    def __init__(self, supabase_client: Client = None):
        """Initialize the version manager

        Args:
            supabase_client: Optional Supabase client (defaults to centralized singleton)
        """
        self.supabase: Client = supabase_client or get_supabase_client()

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file

        Args:
            file_path: Path to file

        Returns:
            SHA256 hex digest
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def upload_file(
        self,
        file_path: str,
        project_id: str,
        user_email: str,
        file_name: Optional[str] = None,
    ) -> str:
        """Upload Excel file and create initial version

        Args:
            file_path: Path to local Excel file
            project_id: Project UUID
            user_email: Email of user uploading
            file_name: Optional custom filename (defaults to file_path basename)

        Returns:
            file_id (UUID)
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file metadata
        file_name = file_name or file_path_obj.name
        file_size = file_path_obj.stat().st_size
        file_hash = self.calculate_file_hash(file_path)

        # Read Excel to get row count
        df = pd.read_excel(file_path)
        row_count = len(df)

        # Generate storage path: {project_id}/current/{filename}
        storage_path = f"{project_id}/current/{file_name}"

        # Upload to Supabase Storage (upsert to handle re-uploads)
        with open(file_path, "rb") as f:
            self.supabase.storage.from_("excel-files").upload(
                path=storage_path,
                file=f,
                file_options={
                    "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "upsert": "true",  # Allow overwriting if file already exists
                },
            )

        # Create database record
        result = (
            self.supabase.table("excel_file_tracking")
            .insert(
                {
                    "file_path": storage_path,
                    "file_name": file_name,
                    "file_hash": file_hash,
                    "storage_bucket": "excel-files",
                    "storage_path": storage_path,
                    "current_version": 1,
                    "row_count": row_count,
                    "file_size_bytes": file_size,
                    "project_id": project_id,
                    "processing_status": "completed",
                    "last_processed": datetime.utcnow().isoformat(),
                }
            )
            .execute()
        )

        file_id = result.data[0]["id"]

        # Create initial version
        version_storage_path = f"{file_id}/v1/{file_name}"

        # Copy to versions bucket
        with open(file_path, "rb") as f:
            self.supabase.storage.from_("excel-versions").upload(
                path=version_storage_path,
                file=f,
                file_options={
                    "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "upsert": "true",  # Allow overwriting during testing
                },
            )

        # Create version record
        self.supabase.table("excel_file_versions").insert(
            {
                "file_id": file_id,
                "version_number": 1,
                "storage_path": version_storage_path,
                "file_hash": file_hash,
                "created_by": user_email,
                "change_summary": "Initial upload",
                "rows_added": row_count,
                "rows_modified": 0,
                "rows_deleted": 0,
                "file_size_bytes": file_size,
                "row_count": row_count,
            }
        ).execute()

        print(f"✅ Uploaded file: {file_name} (ID: {file_id})")
        print(f"   - Size: {file_size:,} bytes")
        print(f"   - Rows: {row_count}")
        print("   - Version: 1")

        return file_id

    def create_version(
        self, file_id: str, file_path: str, user_email: str, change_summary: str
    ) -> str:
        """Create new version of existing file

        Args:
            file_id: UUID of existing file
            file_path: Path to new version of file
            user_email: Email of user creating version
            change_summary: Description of changes

        Returns:
            version_id (UUID)
        """
        # Get current file record
        file_record = (
            self.supabase.table("excel_file_tracking")
            .select("*")
            .eq("id", file_id)
            .single()
            .execute()
        )
        file_data = file_record.data

        # Calculate new file hash
        new_hash = self.calculate_file_hash(file_path)
        file_size = Path(file_path).stat().st_size

        # Read new file
        df_new = pd.read_excel(file_path)
        row_count_new = len(df_new)

        # Get next version number by checking what actually exists in the database
        # (in case of partial uploads, current_version might be out of sync)
        existing_versions = (
            self.supabase.table("excel_file_versions")
            .select("version_number")
            .eq("file_id", file_id)
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        )

        if existing_versions.data:
            current_version = existing_versions.data[0]["version_number"]
        else:
            current_version = 0

        next_version = current_version + 1

        # Upload to versions bucket (or update if exists)
        version_storage_path = f"{file_id}/v{next_version}/{file_data['file_name']}"

        # Upload to versions bucket with upsert to allow overwriting during testing
        with open(file_path, "rb") as f:
            self.supabase.storage.from_("excel-versions").upload(
                path=version_storage_path,
                file=f,
                file_options={
                    "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "upsert": "true",  # Allow overwriting if version already exists
                },
            )

        # Calculate changes (basic version - can be enhanced)
        row_count_old = file_data["row_count"]
        rows_added = max(0, row_count_new - row_count_old)
        rows_deleted = max(0, row_count_old - row_count_new)
        rows_modified = 0  # Will be calculated by diff

        # Create version record directly (not using RPC)
        version_insert_result = (
            self.supabase.table("excel_file_versions")
            .insert(
                {
                    "file_id": file_id,
                    "version_number": next_version,
                    "storage_path": version_storage_path,
                    "file_hash": new_hash,
                    "created_by": user_email,
                    "change_summary": change_summary or "",
                    "rows_added": rows_added,
                    "rows_modified": rows_modified,
                    "rows_deleted": rows_deleted,
                    "file_size_bytes": file_size,
                    "row_count": row_count_new,
                }
            )
            .execute()
        )

        version_id = version_insert_result.data[0]["id"]

        # Detect cell-level changes between previous and current version
        if current_version > 0:
            # Download previous version to compare
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                prev_version_path = tmp.name
                try:
                    self.download_version(file_id, current_version, prev_version_path)
                    df_old = pd.read_excel(prev_version_path)

                    # Track which rows were modified
                    modified_rows = set()
                    cell_changes = []

                    # Compare common rows
                    min_rows = min(len(df_old), len(df_new))
                    for row_idx in range(min_rows):
                        for col in df_old.columns:
                            if col not in df_new.columns:
                                continue

                            old_val = df_old.iloc[row_idx][col]
                            new_val = df_new.iloc[row_idx][col]

                            # Check if values differ (handle NaN properly)
                            values_differ = False
                            if pd.isna(old_val) and pd.isna(new_val):
                                continue
                            elif pd.isna(old_val) or pd.isna(new_val):
                                values_differ = True
                            elif old_val != new_val:
                                values_differ = True

                            if values_differ:
                                modified_rows.add(row_idx)
                                cell_changes.append(
                                    {
                                        "file_id": file_id,
                                        "version_id": version_id,
                                        "sheet_name": "Sheet1",  # Default sheet name for Excel files
                                        "row_index": row_idx,
                                        "column_name": col,
                                        "old_value": (
                                            str(old_val)
                                            if not pd.isna(old_val)
                                            else None
                                        ),
                                        "new_value": (
                                            str(new_val)
                                            if not pd.isna(new_val)
                                            else None
                                        ),
                                        "change_type": "modified",
                                        "changed_by": user_email,
                                    }
                                )

                    # Insert cell changes into database
                    if cell_changes:
                        self.supabase.table("excel_cell_changes").insert(
                            cell_changes
                        ).execute()
                        rows_modified = len(modified_rows)

                        # Update version record with correct rows_modified count
                        self.supabase.table("excel_file_versions").update(
                            {"rows_modified": rows_modified}
                        ).eq("id", version_id).execute()

                finally:
                    # Clean up temp file
                    if os.path.exists(prev_version_path):
                        os.unlink(prev_version_path)

        # Update current version in file tracking
        self.supabase.table("excel_file_tracking").update(
            {
                "current_version": next_version,
                "file_hash": new_hash,
                "row_count": row_count_new,
                "file_size_bytes": file_size,
            }
        ).eq("id", file_id).execute()

        # Update current file in excel-files bucket
        current_storage_path = file_data["storage_path"]

        # Upload new current version (upsert to overwrite)
        with open(file_path, "rb") as f:
            self.supabase.storage.from_("excel-files").upload(
                path=current_storage_path,
                file=f,
                file_options={
                    "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "upsert": "true",  # Overwrite the current file
                },
            )

        print(f"✅ Created version {next_version} for file {file_data['file_name']}")
        print(f"   - Version ID: {version_id}")
        print(f"   - Changes: {change_summary}")

        return version_id

    def acquire_lock(self, file_id: str, user_email: str) -> bool:
        """Acquire exclusive lock on file

        Args:
            file_id: UUID of file
            user_email: Email of user requesting lock

        Returns:
            True if lock acquired, False if already locked by someone else
        """
        result = self.supabase.rpc(
            "acquire_file_lock",
            {"file_id_param": file_id, "user_email_param": user_email},
        ).execute()

        return result.data

    def release_lock(self, file_id: str, user_email: str) -> bool:
        """Release lock on file

        Args:
            file_id: UUID of file
            user_email: Email of user releasing lock

        Returns:
            True if lock released, False otherwise
        """
        result = self.supabase.rpc(
            "release_file_lock",
            {"file_id_param": file_id, "user_email_param": user_email},
        ).execute()

        return result.data

    def get_version_history(self, file_id: str) -> List[Dict]:
        """Get version history for a file

        Args:
            file_id: UUID of file

        Returns:
            List of version records
        """
        result = (
            self.supabase.table("excel_file_versions")
            .select("*")
            .eq("file_id", file_id)
            .order("version_number", desc=True)
            .execute()
        )

        return result.data

    def download_version(
        self, file_id: str, version_number: int, output_path: str
    ) -> str:
        """Download a specific version of a file

        Args:
            file_id: UUID of file
            version_number: Version number to download
            output_path: Path to save file

        Returns:
            Path to downloaded file
        """
        # Get version record
        version_record = (
            self.supabase.table("excel_file_versions")
            .select("*")
            .eq("file_id", file_id)
            .eq("version_number", version_number)
            .single()
            .execute()
        )

        if not version_record.data:
            raise ValueError(f"Version {version_number} not found for file {file_id}")

        storage_path = version_record.data["storage_path"]

        # Download from storage
        file_bytes = self.supabase.storage.from_("excel-versions").download(
            storage_path
        )

        # Save to disk
        with open(output_path, "wb") as f:
            f.write(file_bytes)

        print(f"✅ Downloaded version {version_number} to {output_path}")

        return output_path

    def get_version_diff(
        self,
        file_id: str,
        version_1: int,
        version_2: int,
        critical_columns: List[str] = None,
    ) -> Dict:
        """Generate diff between two versions

        Args:
            file_id: UUID of file
            version_1: First version number (older)
            version_2: Second version number (newer)
            critical_columns: List of column names to track as critical

        Returns:
            Dict with diff information
        """
        import tempfile

        # Download both versions to temp files
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf1:
            file1_path = tf1.name
            self.download_version(file_id, version_1, file1_path)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf2:
            file2_path = tf2.name
            self.download_version(file_id, version_2, file2_path)

        # Read both files
        df1 = pd.read_excel(file1_path)
        df2 = pd.read_excel(file2_path)

        # Calculate differences
        diff_summary = {
            "version_1": version_1,
            "version_2": version_2,
            "rows_added": len(df2) - len(df1) if len(df2) > len(df1) else 0,
            "rows_deleted": len(df1) - len(df2) if len(df1) > len(df2) else 0,
            "rows_modified": 0,
            "cells_changed": [],
            "critical_changes": [],
        }

        critical_columns = critical_columns or []

        # Compare common rows
        min_rows = min(len(df1), len(df2))

        for row_idx in range(min_rows):
            row_changed = False

            for col in df1.columns:
                if col not in df2.columns:
                    continue

                val1 = df1.iloc[row_idx][col]
                val2 = df2.iloc[row_idx][col]

                # Check if values are different (handle NaN)
                if pd.isna(val1) and pd.isna(val2):
                    continue
                elif pd.isna(val1) or pd.isna(val2) or val1 != val2:
                    row_changed = True

                    change_record = {
                        "row_index": row_idx,
                        "column": col,
                        "old_value": str(val1) if not pd.isna(val1) else None,
                        "new_value": str(val2) if not pd.isna(val2) else None,
                        "is_critical": col in critical_columns,
                    }

                    diff_summary["cells_changed"].append(change_record)

                    if col in critical_columns:
                        diff_summary["critical_changes"].append(change_record)

            if row_changed:
                diff_summary["rows_modified"] += 1

        # Clean up temp files
        os.unlink(file1_path)
        os.unlink(file2_path)

        return diff_summary


# Convenience functions


def upload_excel_file(file_path: str, project_id: str, user_email: str) -> str:
    """Upload Excel file (convenience function)

    Args:
        file_path: Path to Excel file
        project_id: Project UUID
        user_email: User email

    Returns:
        file_id
    """
    manager = ExcelVersionManager()
    return manager.upload_file(file_path, project_id, user_email)


def create_new_version(
    file_id: str, file_path: str, user_email: str, change_summary: str
) -> str:
    """Create new version (convenience function)

    Args:
        file_id: File UUID
        file_path: Path to new version
        user_email: User email
        change_summary: Description of changes

    Returns:
        version_id
    """
    manager = ExcelVersionManager()
    return manager.create_version(file_id, file_path, user_email, change_summary)
