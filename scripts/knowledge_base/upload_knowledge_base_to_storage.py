"""
Upload Knowledge Base Documents to Supabase Storage

This script uploads PDFs from knowledge_base/ to Supabase Storage,
making them accessible from any computer with clickable links in the UI.

Strategy:
- PDFs (WTD): Upload to Supabase Storage for clickable links
- HTML (RCW/WAC): Keep as external links to WA Legislature (official source)

Usage:
    python scripts/upload_knowledge_base_to_storage.py [--dry-run]
"""

from core.database import get_supabase_client
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

# Import centralized Supabase client

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
                        "application/pd",
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
            storage_path,
            file_data,
            {"content-type": "application/pd", "upsert": "true"},
        )

        # Get public URL (even though bucket is private, this is the path)
        file_url = f"{os.getenv('SUPABASE_URL')
                      }/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"

        print(f"  ✓ Uploaded: {storage_path}")
        return file_url

    except Exception as e:
        print(f"  ✗ Failed to upload {storage_path}: {e}")
        return None


def upload_knowledge_base(dry_run=False):
    """Upload PDFs from knowledge_base/ directory"""
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"

    if not knowledge_base_dir.exists():
        print(f"❌ Knowledge base directory not found: {knowledge_base_dir}")
        return

    # Find all PDFs (only PDFs - HTML files will link to WA Legislature)
    pdf_files = list(knowledge_base_dir.rglob("*.pd"))

    if not pdf_files:
        print(f"⚠️  No PDF files found in {knowledge_base_dir}")
        return

    print(f"\n📁 Found {len(pdf_files)} PDF files to upload")
    print(
        f"   Total size: {
            sum(f.stat().st_size for f in pdf_files) / 1024 / 1024:.1f} MB"
    )

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be uploaded")
        print("\nFiles that would be uploaded:")
        for i, file_path in enumerate(pdf_files[:10], 1):
            relative_path = file_path.relative_to(knowledge_base_dir)
            print(f"  {i}. {relative_path}")
        if len(pdf_files) > 10:
            print(f"  ... and {len(pdf_files) - 10} more files")
        return

    print("=" * 80)

    uploaded_count = 0
    failed_count = 0

    for i, file_path in enumerate(pdf_files, 1):
        # Create storage path relative to knowledge_base/
        relative_path = file_path.relative_to(knowledge_base_dir)
        storage_path = str(relative_path).replace("\\", "/")

        # Progress indicator
        progress = f"[{i}/{len(pdf_files)}]"
        print(f"{progress} {relative_path}...", end=" ", flush=True)

        file_url = upload_file(file_path, storage_path)

        if file_url:
            uploaded_count += 1
            print("✓")
        else:
            failed_count += 1
            print("✗")

    print("\n" + "=" * 80)
    print("\n✅ Upload complete!")
    print(f"   Uploaded: {uploaded_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {len(pdf_files)}")

    print(
        "\n💡 Next steps:\n"
        "   1. Update document_urls.py to generate Storage URLs\n"
        "   2. Run populate_file_urls.py to update database\n"
        "   3. Test clickable links in web chatbot\n"
        "   4. Monitor storage usage with check_storage_usage.py"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload PDFs to Supabase Storage")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without uploading",
    )
    args = parser.parse_args()

    print("🚀 Knowledge Base Upload to Supabase Storage")
    print("=" * 80)

    if not args.dry_run:
        # Create bucket
        create_storage_bucket_if_not_exists()

    # Upload files
    upload_knowledge_base(dry_run=args.dry_run)
