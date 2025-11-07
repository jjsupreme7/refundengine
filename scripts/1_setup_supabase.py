"""
Setup Supabase Database for Tax Refund Engine

This script:
1. Connects to Supabase
2. Executes the schema SQL to create all tables
3. Enables pgvector extension
4. Creates indexes and helper functions
5. Verifies setup

Usage:
    python scripts/1_setup_supabase.py
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def setup_database():
    """Setup Supabase database with complete schema"""

    print("🚀 Starting Supabase Database Setup...")
    print(f"📍 URL: {SUPABASE_URL}")

    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("✅ Connected to Supabase")

    # Read schema SQL
    schema_path = Path(__file__).parent.parent / "database" / "supabase_schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    print("📄 Schema SQL loaded")

    # Note: Supabase REST API doesn't support raw SQL execution directly
    # You have two options:

    print("\n" + "="*60)
    print("IMPORTANT: Schema Setup Instructions")
    print("="*60)
    print("\nThe schema SQL needs to be executed via Supabase SQL Editor.")
    print("\n📋 Steps:")
    print("1. Go to: https://supabase.com/dashboard/project/yzycrptfkxszeutvhuhm/sql")
    print("2. Click 'New Query'")
    print(f"3. Copy the contents of: {schema_path}")
    print("4. Paste into the SQL Editor")
    print("5. Click 'Run'")
    print("\n✨ Alternatively, run this script with --auto flag to attempt automatic setup via psycopg2")
    print("="*60 + "\n")

    # Check if user wants automatic setup
    import sys
    if "--auto" in sys.argv:
        print("\n🔧 Attempting automatic setup via direct PostgreSQL connection...")
        setup_via_psycopg2(schema_sql)
    else:
        print("\n💡 Tip: Run 'python scripts/1_setup_supabase.py --auto' to try automatic setup")

    # Verify tables exist (via REST API)
    print("\n🔍 Verifying table setup...")
    try:
        # Try to query a table
        result = supabase.table('clients').select("*").limit(0).execute()
        print("✅ Tables are accessible via REST API")
        print("✅ Setup verification passed!")

        # List all tables
        print("\n📊 Verifying database structure...")
        tables_to_check = [
            'clients', 'client_documents', 'legal_documents',
            'document_chunks', 'document_metadata', 'invoices',
            'invoice_line_items', 'refund_analysis'
        ]

        for table in tables_to_check:
            try:
                supabase.table(table).select("*").limit(0).execute()
                print(f"  ✓ {table}")
            except Exception as e:
                print(f"  ✗ {table} - {str(e)}")

    except Exception as e:
        print(f"⚠️  Could not verify tables: {e}")
        print("Please run the schema SQL manually via Supabase dashboard")

    print("\n✅ Setup complete!")
    print("\n📖 Next steps:")
    print("  1. Verify tables in Supabase dashboard")
    print("  2. Run: python scripts/2_ingest_legal_docs.py")


def setup_via_psycopg2(schema_sql):
    """Setup via direct PostgreSQL connection using psycopg2"""
    try:
        import psycopg2
        from urllib.parse import urlparse

        # Parse Supabase URL to get connection string
        # Format: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
        parsed = urlparse(SUPABASE_URL)
        host = parsed.hostname.replace("https://", "").replace("http://", "")

        # Get database password from env
        db_password = os.getenv("SUPABASE_DB_PASSWORD")

        if not db_password:
            print("⚠️  SUPABASE_DB_PASSWORD not found in .env")
            print("   Add it to .env file to use automatic setup")
            return

        # Construct connection string
        # Supabase host: yzycrptfkxszeutvhuhm.supabase.co
        # Database host: db.yzycrptfkxszeutvhuhm.supabase.co
        db_host = f"db.{host}"
        conn_string = f"postgresql://postgres.{host.split('.')[0]}:{db_password}@{db_host}:5432/postgres"

        print(f"🔌 Connecting to PostgreSQL at: {db_host}")

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        print("✅ Connected to PostgreSQL")
        print("📝 Executing schema SQL...")

        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()

        print("✅ Schema executed successfully!")

        # Verify pgvector
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if cursor.fetchone():
            print("✅ pgvector extension enabled")
        else:
            print("⚠️  pgvector not found, attempting to enable...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            print("✅ pgvector enabled")

        cursor.close()
        conn.close()

        print("✅ Automatic setup complete!")

    except ImportError:
        print("⚠️  psycopg2 not installed")
        print("   Install with: pip install psycopg2-binary")
    except Exception as e:
        print(f"❌ Automatic setup failed: {e}")
        print("   Please use manual setup via Supabase dashboard")


if __name__ == "__main__":
    setup_database()
