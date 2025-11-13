#!/usr/bin/env python3
"""
Add file_url column to knowledge_documents table using Python
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Use psycopg2 for direct SQL execution
import psycopg2

def add_file_url_column():
    """Add file_url column to knowledge_documents table"""

    # Get connection parameters from environment
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    supabase_url = os.getenv('SUPABASE_URL')

    if not db_password or not supabase_url:
        print("❌ Error: Missing SUPABASE_DB_PASSWORD or SUPABASE_URL")
        sys.exit(1)

    # Extract project ID from URL
    project_id = supabase_url.split('//')[1].split('.')[0]

    # Connection parameters
    conn_params = {
        'host': f'aws-0-us-west-1.pooler.supabase.com',
        'port': 6543,
        'database': 'postgres',
        'user': f'postgres.{project_id}',
        'password': db_password
    }

    print("🔄 Connecting to Supabase...")
    print(f"   Host: {conn_params['host']}")
    print(f"   User: {conn_params['user']}")
    print()

    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        print("✅ Connected successfully")
        print()
        print("🔄 Adding file_url column...")

        # Add column
        cursor.execute("""
            ALTER TABLE knowledge_documents
            ADD COLUMN IF NOT EXISTS file_url text;
        """)

        print("✅ Column added successfully!")
        print()

        # Add comment
        cursor.execute("""
            COMMENT ON COLUMN knowledge_documents.file_url IS
            'URL to access the original source document (for clickable links in UI)';
        """)

        print("✅ Column comment added!")
        print()

        # Verify
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'knowledge_documents'
            AND column_name = 'file_url';
        """)

        result = cursor.fetchone()
        if result:
            print(f"✅ Verification successful: {result[0]} ({result[1]})")
        else:
            print("⚠️  Warning: Column not found in verification")

        cursor.close()
        conn.close()

        print()
        print("="*60)
        print("✅ Migration complete! You can now run the ingestion.")
        print("="*60)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    add_file_url_column()
