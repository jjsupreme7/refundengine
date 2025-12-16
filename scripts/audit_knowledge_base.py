#!/usr/bin/env python3
"""
Audit Knowledge Base: Find files not in Supabase

Compares local knowledge_base files with knowledge_documents table.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client

load_dotenv()

PROJECT_ROOT = Path("/Users/jacoballen/Desktop/refund-engine")

def normalize_path(path_str):
    """Normalize a path to relative form for comparison."""
    if not path_str:
        return None

    # Convert to Path object
    p = Path(path_str)

    # If absolute, make relative to project root
    if p.is_absolute():
        try:
            return str(p.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(p)

    return str(p)

def get_local_files():
    """Get all PDF and HTML files from knowledge_base as relative paths."""
    kb_path = PROJECT_ROOT / "knowledge_base"
    files = []

    for ext in ["*.pdf", "*.html"]:
        for f in kb_path.rglob(ext):
            # Store as relative path from project root
            rel_path = str(f.relative_to(PROJECT_ROOT))
            files.append(rel_path)

    return files

def get_supabase_documents():
    """Get all documents from Supabase with their source files."""
    supabase = get_supabase_client()

    all_docs = []
    offset = 0
    batch_size = 500

    while True:
        # Use order + limit + offset for reliable pagination
        result = supabase.table("knowledge_documents").select(
            "id, title, source_file, citation, total_chunks"
        ).order("created_at").limit(batch_size).offset(offset).execute()

        if not result.data:
            break

        all_docs.extend(result.data)
        offset += batch_size

        if len(result.data) < batch_size:
            break

    return all_docs

def main():
    print("=" * 70)
    print("Knowledge Base Audit")
    print("=" * 70)

    # Get local files (relative paths)
    print("\nScanning local knowledge_base directory...")
    local_files = get_local_files()
    print(f"  Found {len(local_files)} local files (PDF + HTML)")

    # Get Supabase documents
    print("\nQuerying Supabase knowledge_documents...")
    supabase_docs = get_supabase_documents()
    print(f"  Found {len(supabase_docs)} documents in Supabase")

    # Build lookup sets - normalize all paths
    supabase_source_files = set()
    docs_without_source = []
    docs_with_zero_chunks = []

    for doc in supabase_docs:
        sf = normalize_path(doc.get("source_file"))
        if sf:
            supabase_source_files.add(sf)
        else:
            docs_without_source.append(doc)

        if doc.get("total_chunks", 0) == 0:
            docs_with_zero_chunks.append(doc)

    # Find files NOT in Supabase
    local_files_set = set(local_files)
    missing_from_supabase = local_files_set - supabase_source_files

    # Also find source_files in Supabase that don't exist locally
    supabase_only = supabase_source_files - local_files_set

    # Categorize missing files
    missing_by_type = {}
    for f in missing_from_supabase:
        f_lower = f.lower()
        if "/rcw/" in f_lower:
            cat = "RCW"
        elif "/wac/" in f_lower:
            cat = "WAC"
        elif "/eta" in f_lower:
            cat = "ETA"
        elif "/det" in f_lower or "wtd" in f_lower:
            cat = "DET/WTD"
        elif "/guidance/" in f_lower:
            cat = "Guidance"
        else:
            cat = "Other"

        if cat not in missing_by_type:
            missing_by_type[cat] = []
        missing_by_type[cat].append(f)

    # Report
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n📁 Local files:              {len(local_files)}")
    print(f"📊 Supabase documents:       {len(supabase_docs)}")
    print(f"   - With source_file:       {len(supabase_source_files)}")
    print(f"   - Without source_file:    {len(docs_without_source)}")
    print(f"❌ Missing from Supabase:    {len(missing_from_supabase)}")
    print(f"⚠️  Supabase refs missing locally: {len(supabase_only)}")
    print(f"⚠️  Docs with 0 chunks:       {len(docs_with_zero_chunks)}")

    print("\n--- Missing Files by Type ---")
    for cat, files in sorted(missing_by_type.items()):
        print(f"  {cat}: {len(files)}")

    # Show sample of missing files
    if missing_from_supabase:
        print("\n--- Sample Missing Files (first 30) ---")
        for f in sorted(missing_from_supabase)[:30]:
            print(f"  {f}")

    # Show docs with 0 chunks
    if docs_with_zero_chunks:
        print(f"\n--- Docs with 0 Chunks (first 10 of {len(docs_with_zero_chunks)}) ---")
        for doc in docs_with_zero_chunks[:10]:
            print(f"  {doc.get('citation', 'N/A')}: {doc.get('title', 'N/A')[:50]}")

    # Save full list of missing files
    if missing_from_supabase:
        output_file = PROJECT_ROOT / "scripts" / "missing_files.txt"
        with open(output_file, "w") as f:
            for path in sorted(missing_from_supabase):
                f.write(path + "\n")
        print(f"\n📄 Full list saved to: {output_file}")

    return len(missing_from_supabase)

if __name__ == "__main__":
    missing = main()
    sys.exit(0 if missing == 0 else 1)
