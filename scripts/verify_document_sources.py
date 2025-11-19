#!/usr/bin/env python3
"""
Verify Document Sources - Check all documents have accessible sources
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize Supabase
supabase = get_supabase_client()

print("=" * 80)
print("Document Source Verification Report")
print("=" * 80)
print()

# Fetch all documents
result = (
    supabase.table("knowledge_documents")
    .select("id, title, citation, file_url, source_file")
    .execute()
)

total_docs = len(result.data)
docs_with_online_url = 0
docs_with_local_file = 0
docs_with_verified_local_file = 0
docs_with_no_source = 0
docs_with_missing_local_file = 0

print(f"📊 Total documents in database: {total_docs}")
print()

# Track documents by category
online_only = []
local_only = []
both = []
no_source = []
missing_files = []

for doc in result.data:
    doc_id = doc["id"]
    title = doc.get("title", "N/A")
    citation = doc.get("citation", "N/A")
    file_url = doc.get("file_url")
    source_file = doc.get("source_file")

    has_online = bool(file_url)
    has_local = bool(source_file)

    # Check if local file actually exists
    local_file_exists = False
    if source_file:
        # Try both as absolute path and relative to project root
        abs_path = (
            source_file
            if os.path.isabs(source_file)
            else os.path.join(os.getcwd(), source_file)
        )
        local_file_exists = os.path.exists(abs_path)

    # Categorize
    if has_online and has_local and local_file_exists:
        both.append((citation, file_url, source_file))
        docs_with_online_url += 1
        docs_with_local_file += 1
        docs_with_verified_local_file += 1
    elif has_online and has_local and not local_file_exists:
        both.append((citation, file_url, source_file))
        docs_with_online_url += 1
        docs_with_local_file += 1
        docs_with_missing_local_file += 1
        missing_files.append((citation, source_file))
    elif has_online and not has_local:
        online_only.append((citation, file_url))
        docs_with_online_url += 1
    elif not has_online and has_local and local_file_exists:
        local_only.append((citation, source_file))
        docs_with_local_file += 1
        docs_with_verified_local_file += 1
    elif not has_online and has_local and not local_file_exists:
        local_only.append((citation, source_file))
        docs_with_local_file += 1
        docs_with_missing_local_file += 1
        missing_files.append((citation, source_file))
    else:
        no_source.append((citation, title))
        docs_with_no_source += 1

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(
    f"✅ Documents with online URL: {docs_with_online_url} ({docs_with_online_url/total_docs*100:.1f}%)"
)
print(
    f"📄 Documents with local file path: {docs_with_local_file} ({docs_with_local_file/total_docs*100:.1f}%)"
)
print(f"✓  Local files verified to exist: {docs_with_verified_local_file}")
print(f"❌ Local files missing: {docs_with_missing_local_file}")
print(
    f"⚠️  Documents with NO source: {docs_with_no_source} ({docs_with_no_source/total_docs*100:.1f}%)"
)
print()

print("=" * 80)
print("BREAKDOWN")
print("=" * 80)
print(f"🔗 Online URL only: {len(online_only)}")
print(f"📄 Local file only: {len(local_only)}")
print(f"🔗📄 Both online + local: {len(both)}")
print(f"❌ No source at all: {len(no_source)}")
print()

if no_source:
    print("=" * 80)
    print("⚠️  DOCUMENTS WITH NO SOURCE")
    print("=" * 80)
    for i, (citation, title) in enumerate(no_source, 1):
        print(f"{i}. {citation}")
        print(f"   Title: {title}")
        print()

if missing_files:
    print("=" * 80)
    print("❌ DOCUMENTS WITH MISSING LOCAL FILES")
    print("=" * 80)
    for i, (citation, source_file) in enumerate(missing_files, 1):
        print(f"{i}. {citation}")
        print(f"   Missing file: {source_file}")
        print()

# Final verdict
print("=" * 80)
print("VERDICT")
print("=" * 80)

accessible_docs = docs_with_online_url + docs_with_verified_local_file - len(both)
accessible_percentage = (accessible_docs / total_docs * 100) if total_docs > 0 else 0

if docs_with_no_source == 0 and docs_with_missing_local_file == 0:
    print("✅ ALL DOCUMENTS HAVE ACCESSIBLE SOURCES!")
    print(f"   100% of documents can be sourced")
elif docs_with_no_source == 0:
    print(
        f"⚠️  ALL DOCUMENTS HAVE SOURCE PATHS, but {docs_with_missing_local_file} local files are missing"
    )
    print(
        f"   {accessible_percentage:.1f}% of documents have verified accessible sources"
    )
else:
    print(f"❌ {docs_with_no_source} documents have NO SOURCE AT ALL")
    print(
        f"   Only {accessible_percentage:.1f}% of documents have verified accessible sources"
    )
    print()
    print("   Action required:")
    print("   - Add file_url or source_file to documents with no source")
    if docs_with_missing_local_file > 0:
        print(
            f"   - Locate or re-ingest {docs_with_missing_local_file} missing local files"
        )

print()
print("=" * 80)
