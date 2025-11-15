#!/usr/bin/env python3
"""Deploy file_url update to search_tax_law RPC function"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Use pooler host from env
db_host = os.getenv('SUPABASE_HOST', 'aws-0-us-west-1.pooler.supabase.com')
db_port = int(os.getenv('SUPABASE_PORT', 6543))
db_user = os.getenv('SUPABASE_USER', 'postgres.xjuymnnrkggklajzlaxz')
db_name = os.getenv('SUPABASE_DB', 'postgres')

# Read SQL
with open('database/migrations/add_file_url_to_search_tax_law.sql', 'r') as f:
    sql = f.read()

print("🚀 Deploying file_url update to search_tax_law function...")
print(f"   Connecting to {db_host}:{db_port}...")

# Connect and execute
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=os.getenv('SUPABASE_DB_PASSWORD')
)

cursor = conn.cursor()
cursor.execute(sql)
conn.commit()
cursor.close()
conn.close()

print("✅ Successfully deployed file_url update!")
print("   The search_tax_law function now returns file_url for clickable citations.")
