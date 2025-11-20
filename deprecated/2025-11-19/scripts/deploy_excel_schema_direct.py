#!/usr/bin/env python3
"""
Deploy Excel Versioning Schema using psycopg2

Executes SQL migrations directly against PostgreSQL database
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Load environment
load_dotenv()

print("🚀 Deploying Excel Versioning System - Phase 1")
print("=" * 70)
print()

# Check for psycopg2
try:
    import psycopg2  # noqa: E402

    print("✅ psycopg2 found")
except ImportError:
    print("❌ psycopg2 not installed")
    print()
    print("Please install it:")
    print("  pip install psycopg2-binary")
    print()
    sys.exit(1)

# Get database connection string
db_password = os.getenv("SUPABASE_DB_PASSWORD")
supabase_url = os.getenv("SUPABASE_URL")

if not db_password or not supabase_url:
    print("❌ Missing environment variables")
    print("Required: SUPABASE_URL, SUPABASE_DB_PASSWORD")
    sys.exit(1)

# Extract project ID from Supabase URL
# Format: https://nkxmhicubxltifpdhgby.supabase.co
project_id = supabase_url.replace("https://", "").split(".")[0]

# Build connection string
# Supabase uses pooler: aws-0-us-west-1.pooler.supabase.com
db_host = "aws-0-us-west-1.pooler.supabase.com"
db_name = "postgres"
db_user = f"postgres.{project_id}"
db_port = "5432"

print("📡 Connecting to database...")
print(f"   Host: {db_host}")
print(f"   Database: {db_name}")
print(f"   User: {db_user}")
print()

# Connect to database
try:
    conn = psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password, port=db_port
    )
    conn.autocommit = True
    print("✅ Connected to database")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print()
    print("Troubleshooting:")
    print("1. Check SUPABASE_DB_PASSWORD is correct")
    print("2. Check your IP is allowed in Supabase settings")
    print("3. Verify project ID in SUPABASE_URL")
    sys.exit(1)

# Read SQL file
sql_file = (
    Path(__file__).parent.parent
    / "database"
    / "schema"
    / "migration_excel_versioning.sql"
)

if not sql_file.exists():
    print(f"❌ SQL file not found: {sql_file}")
    sys.exit(1)

print(f"📄 Reading SQL from: {sql_file.name}")
print()

with open(sql_file, "r") as f:
    sql_content = f.read()

# Execute SQL
cursor = conn.cursor()

try:
    print("📊 Executing SQL migration...")
    cursor.execute(sql_content)
    print("✅ Migration executed successfully!")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    sys.exit(1)

# Verify tables were created
print()
print("🔍 Verifying tables...")

tables_to_check = ["excel_file_versions", "excel_cell_changes"]

for table in tables_to_check:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   ✅ {table}: {count} rows")
    except Exception as e:
        print(f"   ❌ {table}: Not found or error - {e}")

# Check functions
print()
print("🔍 Verifying functions...")

functions_to_check = ["acquire_file_lock", "release_file_lock", "create_file_version"]

for func in functions_to_check:
    try:
        cursor.execute(
            """
            SELECT COUNT(*) FROM pg_proc
            WHERE proname = '{func}'
        """
        )
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   ✅ {func}()")
        else:
            print(f"   ⚠️  {func}() not found")
    except Exception as e:
        print(f"   ❌ {func}(): Error checking - {e}")

# Close connection
cursor.close()
conn.close()

print()
print("=" * 70)
print("✅ Excel Versioning System deployed successfully!")
print()
print("Next steps:")
print("1. Set up Supabase Storage buckets:")
print("   python scripts/setup_excel_storage.py")
print()
print("2. Test the system:")
print("   python scripts/test_excel_versioning.py")
print()
print("3. Access Excel Manager in dashboard:")
print("   streamlit run dashboard/Dashboard.py --server.port 5001")
print("   Navigate to: Excel Manager page")
print()
