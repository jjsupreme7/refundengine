"""
Upload Knowledge Base Documents to Supabase Storage

This script uploads PDFs from knowledge_base/ to Supabase Storage,
making them accessible from any computer. The RAG system will continue
to work from the database embeddings, but originals are backed up in cloud.

Usage:
    python scripts/upload_knowledge_base_to_storage.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

# Import centralized Supabase client
from core.database import get_supabase_client
supabase = get_supabase_client()

# Storage bucket name
BUCKET_NAME = "knowledge-base"


def create_storage_bucket_if_not_exists():
    """Create the storage bucket if it doesn't exist"""
    try:
        # Try to get bucket
        supabase.storage.get_bucket(BUCKET_NAME)
        print(f"✓ Bucket '{BUCKET_NAME}' already exists")
    except Exception:
        # Create bucket if doesn't exist
        try:
            supabase.storage.create_bucket(
                BUCKET_NAME,
                options={
                    "public": False,  # Private bucket for security
                    "file_size_limit": 52428800,  # 50MB limit
                    "allowed_mime_types": [
                        "application/pdf",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "application/vnd.ms-excel",
                    ],
                },
            )
            print(f"✓ Created bucket '{BUCKET_NAME}'")
        except Exception as e:
            print(f"⚠️  Could not create bucket: {e}")
            print("   You may need to create it manually in Supabase dashboard")


def upload_file(local_path: Path, storage_path: str):
    """Upload a file to Supabase Storage"""
    try:
        with open(local_path, "rb") as f:
            file_data = f.read()

        # Upload to Supabase Storage
        supabase.storage.from_(BUCKET_NAME).upload(
            storage_path, file_data, {"content-type": "application/pdf", "upsert": "true"}
        )

        # Get public URL (even though bucket is private, this is the path)
        file_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"

        print(f"  ✓ Uploaded: {storage_path}")
        return file_url

    except Exception as e:
        print(f"  ✗ Failed to upload {storage_path}: {e}")
        return None


def upload_knowledge_base():
    """Upload all PDFs from knowledge_base/ directory"""
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"

    if not knowledge_base_dir.exists():
        print(f"❌ Knowledge base directory not found: {knowledge_base_dir}")
        return

    # Find all PDFs
    pdf_files = list(knowledge_base_dir.rglob("*.pdf"))
    excel_files = list(knowledge_base_dir.rglob("*.xlsx"))
    all_files = pdf_files + excel_files

    if not all_files:
        print(f"⚠️  No PDF or Excel files found in {knowledge_base_dir}")
        return

    print(f"\n📁 Found {len(pdf_files)} PDFs and {len(excel_files)} Excel files")
    print("=" * 80)

    uploaded_count = 0
    failed_count = 0

    for file_path in all_files:
        # Create storage path relative to knowledge_base/
        relative_path = file_path.relative_to(knowledge_base_dir)
        storage_path = str(relative_path).replace("\\", "/")

        print(f"\n📄 Processing: {relative_path}")

        file_url = upload_file(file_path, storage_path)

        if file_url:
            uploaded_count += 1
        else:
            failed_count += 1

    print("\n" + "=" * 80)
    print(f"\n✅ Upload complete!")
    print(f"   Uploaded: {uploaded_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {len(all_files)}")

    print(
        "\n💡 Next steps:\n"
        "   1. Your documents are now backed up in Supabase Storage\n"
        "   2. You can access them from any computer\n"
        "   3. The RAG system still uses database embeddings (no changes needed)\n"
        "   4. To re-ingest on another computer, download from Storage first"
    )


if __name__ == "__main__":
    print("🚀 Knowledge Base Upload to Supabase Storage")
    print("=" * 80)

    # Create bucket
    create_storage_bucket_if_not_exists()

    # Upload files
    upload_knowledge_base()
