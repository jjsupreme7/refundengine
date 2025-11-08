#!/usr/bin/env python3
"""Check what tables exist in Supabase"""

import os
from pathlib import Path
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE credentials not found")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try to query existing tables
tables_to_check = [
    'legal_documents', 'legal_rules', 'document_chunks',
    'knowledge_documents', 'tax_law_chunks', 'vendor_background_chunks'
]

print("\n" + "="*80)
print("SUPABASE TABLES CHECK")
print("="*80 + "\n")

for table in tables_to_check:
    try:
        result = supabase.table(table).select('*', count='exact').limit(0).execute()
        count = result.count if hasattr(result, 'count') else '?'
        print(f"✓ {table:30} exists (rows: {count})")
    except Exception as e:
        print(f"✗ {table:30} does not exist")

print("\n" + "="*80 + "\n")
