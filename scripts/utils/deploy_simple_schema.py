#!/usr/bin/env python3
"""Deploy simple schema using psycopg2"""

import os
from pathlib import Path
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')

if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
    print("Error: Missing Supabase credentials")
    exit(1)

# Extract connection details
project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
db_host = f"db.{project_ref}.supabase.co"

print("\n" + "="*80)
print("DEPLOYING SIMPLE KNOWLEDGE BASE SCHEMA")
print("="*80 + "\n")

# Read schema file
schema_path = Path(__file__).parent.parent.parent / 'database' / 'schema_simple.sql'
with open(schema_path) as f:
    schema_sql = f.read()

# Connect and execute
try:
    conn = psycopg2.connect(
        host=db_host,
        database="postgres",
        user="postgres",
        password=SUPABASE_DB_PASSWORD,
        port=5432
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(schema_sql)

    print("✓ Schema deployed successfully!\n")

    # Verify tables created
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('knowledge_documents', 'tax_law_chunks', 'vendor_background_chunks')
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print("Tables created:")
    for (table,) in tables:
        print(f"  ✓ {table}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

print("\n" + "="*80 + "\n")
