#!/usr/bin/env python3
"""Clear old schema tables"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# Import centralized Supabase client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.database import get_supabase_client
supabase = get_supabase_client()

print("\n" + "=" * 80)
print("CLEARING OLD SCHEMA")
print("=" * 80)

# Clear document_chunks first (has foreign key)
try:
    result = supabase.table("document_chunks").select("id", count="exact").execute()
    count = result.count
    print(f"\ndocument_chunks: {count} rows")

    if count > 0:
        supabase.table("document_chunks").delete().gte("id", 0).execute()
        print(f"✓ Deleted all {count} chunks")
except Exception as e:
    print(f"✗ Error: {e}")

# Clear legal_documents
try:
    result = supabase.table("legal_documents").select("id", count="exact").execute()
    count = result.count
    print(f"\nlegal_documents: {count} rows")

    if count > 0:
        supabase.table("legal_documents").delete().gte("id", 0).execute()
        print(f"✓ Deleted all {count} documents")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("✓ Old data cleared!")
print("=" * 80 + "\n")
