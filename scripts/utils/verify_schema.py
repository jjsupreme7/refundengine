#!/usr/bin/env python3
"""Verify schema by querying directly with psycopg2"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    exit(1)

# Get Supabase connection details
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')

if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
    print("Error: SUPABASE_URL and SUPABASE_DB_PASSWORD required")
    exit(1)

# Extract project ref from URL
project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
db_host = f"db.{project_ref}.supabase.co"

# Connect
conn = psycopg2.connect(
    host=db_host,
    database="postgres",
    user="postgres",
    password=SUPABASE_DB_PASSWORD,
    port=5432
)

cursor = conn.cursor()

# Query for tables
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")

tables = cursor.fetchall()

print("\n" + "="*80)
print("SUPABASE SCHEMA VERIFICATION")
print("="*80 + "\n")

print("All tables in public schema:")
for (table,) in tables:
    # Count rows
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"  ✓ {table:40} ({count} rows)")

cursor.close()
conn.close()

print("\n" + "="*80 + "\n")
