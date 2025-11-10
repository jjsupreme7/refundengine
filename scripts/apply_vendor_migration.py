#!/usr/bin/env python3
"""
Apply Vendor Metadata Migration to Supabase
Executes the migration SQL file via Supabase Management API
"""

import os
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def apply_migration():
    """Apply the vendor metadata migration"""

    # Read migration SQL
    migration_path = (
        Path(__file__).parent.parent
        / "database"
        / "schema"
        / "migration_vendor_metadata.sql"
    )

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    with open(migration_path, "r") as f:
        migration_sql = f.read()

    # Get credentials
    project_ref = "yzycrptfkxszeutvhuhm"  # From SUPABASE_URL
    access_token = os.getenv("SUPABASE_ACCESS_TOKEN")

    if not access_token:
        print("❌ SUPABASE_ACCESS_TOKEN not found in .env")
        return False

    print("=" * 80)
    print("VENDOR METADATA MIGRATION")
    print("=" * 80)
    print(f"📋 Migration file: {migration_path.name}")
    print(f"🌐 Project: {project_ref}")
    print()

    # Use Supabase Management API
    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {"query": migration_sql}

    print("🔄 Applying migration via Supabase Management API...")
    print()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code in [200, 201]:
            print("✅ Migration applied successfully!")
            print()
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                print(f"📊 Executed {len(result)} statements")
            return True
        else:
            print(f"❌ Error applying migration (HTTP {response.status_code})")
            print()
            print("Response:")
            print(response.text)
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False


if __name__ == "__main__":
    print()
    success = apply_migration()
    print()
    print("=" * 80)

    if success:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print()
        print("New vendor metadata fields added:")
        print("  • industry")
        print("  • business_model")
        print("  • primary_products")
        print("  • typical_delivery")
        print("  • tax_notes")
        print("  • confidence_score")
        print("  • data_source")
        print()
        print("Next steps:")
        print("  1. Build vendor research script")
        print("  2. Update ingestion scripts")
        print("  3. Populate vendor metadata")
    else:
        print("❌ MIGRATION FAILED")
        print()
        print("Alternative: Run migration manually via Supabase SQL Editor")
        print(
            "  1. Go to: https://supabase.com/dashboard/project/yzycrptfkxszeutvhuhm/sql/new"
        )
        print("  2. Copy SQL from: database/schema/migration_vendor_metadata.sql")
        print("  3. Paste and click 'Run'")

    print("=" * 80)
    print()

    sys.exit(0 if success else 1)
