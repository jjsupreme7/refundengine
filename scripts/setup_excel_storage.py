#!/usr/bin/env python3
"""
Setup Supabase Storage buckets for Excel file versioning

This script creates the necessary storage buckets and sets up RLS policies.

Usage:
    python scripts/setup_excel_storage.py
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment
load_dotenv()

def setup_storage_buckets():
    """Create Supabase Storage buckets for Excel files"""

    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)

    supabase: Client = create_client(supabase_url, supabase_key)

    print("🚀 Setting up Supabase Storage buckets for Excel versioning...")
    print()

    # Bucket configurations
    buckets = [
        {
            "id": "excel-files",
            "name": "excel-files",
            "public": False,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ]
        },
        {
            "id": "excel-versions",
            "name": "excel-versions",
            "public": False,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ]
        },
        {
            "id": "excel-exports",
            "name": "excel-exports",
            "public": False,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/pdf",
                "application/json"
            ]
        }
    ]

    for bucket_config in buckets:
        try:
            # Try to create bucket
            result = supabase.storage.create_bucket(
                bucket_config["id"],
                options={
                    "public": bucket_config["public"],
                    "fileSizeLimit": bucket_config["file_size_limit"],
                    "allowedMimeTypes": bucket_config["allowed_mime_types"]
                }
            )
            print(f"✅ Created bucket: {bucket_config['name']}")

        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                print(f"ℹ️  Bucket already exists: {bucket_config['name']}")
            else:
                print(f"❌ Error creating bucket {bucket_config['name']}: {e}")

    print()
    print("📋 Storage RLS Policies")
    print("=" * 60)
    print("""
The following RLS policies should be applied via Supabase Dashboard
or SQL migration:

-- Policy: Users can read their own files
CREATE POLICY "Users can view own excel files"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'excel-files' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can upload their own files
CREATE POLICY "Users can upload excel files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'excel-files' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can update their own files
CREATE POLICY "Users can update own excel files"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    bucket_id = 'excel-files' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can delete their own files
CREATE POLICY "Users can delete own excel files"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'excel-files' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Versions bucket (read-only for users)
CREATE POLICY "Users can view version history"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'excel-versions');

-- Exports bucket
CREATE POLICY "Users can read exports"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'excel-exports' AND
    (storage.foldername(name))[1] = auth.uid()::text
);
    """)

    print()
    print("✅ Storage setup complete!")
    print()
    print("📁 Bucket Structure:")
    print("  excel-files/")
    print("    ├── {user_id}/{project_id}/current/file.xlsx")
    print("    └── {user_id}/{project_id}/drafts/file_draft.xlsx")
    print()
    print("  excel-versions/")
    print("    └── {file_id}/v{version_number}/file_v{version}.xlsx")
    print()
    print("  excel-exports/")
    print("    ├── {user_id}/audit_reports/{filename}.pdf")
    print("    ├── {user_id}/change_history/{filename}.xlsx")
    print("    └── {user_id}/exports/{filename}.json")
    print()

if __name__ == "__main__":
    setup_storage_buckets()
