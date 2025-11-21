"""
Download Knowledge Base Documents from Supabase Storage

This script downloads PDFs from Supabase Storage to your local knowledge_base/
directory when setting up on a new computer.

Usage:
    python scripts/download_knowledge_base_from_storage.py
"""

from core.database import get_supabase_client
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


def download_file(storage_path: str, local_path: Path):
    """Download a file from Supabase Storage"""
    try:
        # Download from Supabase Storage
        file_data = supabase.storage.from_(BUCKET_NAME).download(storage_path)

        # Create parent directory if doesn't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(local_path, "wb") as f:
            f.write(file_data)

        print(f"  ✓ Downloaded: {storage_path}")
        return True

    except Exception as e:
        print(f"  ✗ Failed to download {storage_path}: {e}")
        return False


def download_knowledge_base():
    """Download all files from Supabase Storage"""
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"

    print(f"\n📁 Downloading to: {knowledge_base_dir}")
    print("=" * 80)

    try:
        # List all files in the bucket
        files = supabase.storage.from_(BUCKET_NAME).list()

        if not files:
            print("⚠️  No files found in Supabase Storage")
            return

        print(f"\n📄 Found {len(files)} items in storage")

        downloaded_count = 0
        failed_count = 0

        for file_info in files:
            storage_path = file_info["name"]
            local_path = knowledge_base_dir / storage_path

            print(f"\n📥 Downloading: {storage_path}")

            if download_file(storage_path, local_path):
                downloaded_count += 1
            else:
                failed_count += 1

        print("\n" + "=" * 80)
        print("\n✅ Download complete!")
        print(f"   Downloaded: {downloaded_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Total: {len(files)}")

        print(
            "\n💡 Next steps:\n"
            "   1. Your knowledge base is now available locally\n"
            "   2. You can run ingestion scripts if needed\n"
            "   3. The RAG system will work immediately (uses Supabase database)"
        )

    except Exception as e:
        print(f"❌ Error listing files: {e}")
        print("   Make sure the bucket exists and you have permissions")


def list_files_in_storage():
    """List all files currently in Supabase Storage"""
    try:
        files = supabase.storage.from_(BUCKET_NAME).list()

        if not files:
            print("📭 No files in storage")
            return

        print(f"\n📚 Files in Supabase Storage ({len(files)} total):")
        print("=" * 80)

        for file_info in files:
            name = file_info["name"]
            size = file_info.get("metadata", {}).get("size", 0)
            size_mb = size / (1024 * 1024) if size else 0
            print(f"  • {name} ({size_mb:.2f} MB)")

    except Exception as e:
        print(f"❌ Error listing files: {e}")


if __name__ == "__main__":
    print("🚀 Knowledge Base Download from Supabase Storage")
    print("=" * 80)

    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(
        description="Download knowledge base from Supabase Storage"
    )
    parser.add_argument(
        "--list-only", action="store_true", help="List files without downloading"
    )
    args = parser.parse_args()

    if args.list_only:
        list_files_in_storage()
    else:
        # Download files
        download_knowledge_base()
