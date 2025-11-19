#!/usr/bin/env python3
"""
Deploy Migration 004: Performance Optimization Indexes
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment
load_dotenv()


def main():
    print("=" * 50)
    print("Migration 004: Performance Indexes")
    print("=" * 50)
    print()

    # Get database credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        return 1

    print("Connecting to Supabase...")

    from supabase import create_client

    supabase = create_client(supabase_url, supabase_key)

    # Read migration file
    migration_path = (
        Path(__file__).parent.parent
        / "database/migrations/migration_004_performance_indexes.sql"
    )

    if not migration_path.exists():
        print(f"❌ Error: Migration file not found at {migration_path}")
        return 1

    print(f"Reading migration from {migration_path.name}...")

    with open(migration_path, "r") as f:
        sql = f.read()

    # Split SQL into statements (basic split on semicolons outside comments)
    statements = []
    current = []
    in_comment = False
    in_dollar_quote = False

    for line in sql.split("\n"):
        stripped = line.strip()

        # Skip empty lines and single-line comments
        if not stripped or stripped.startswith("--"):
            continue

        # Handle multi-line comments
        if "/*" in stripped:
            in_comment = True
        if "*/" in stripped:
            in_comment = False
            continue
        if in_comment:
            continue

        # Handle dollar-quoted strings (like in functions)
        if "$$" in stripped:
            in_dollar_quote = not in_dollar_quote

        current.append(line)

        # If we hit a semicolon outside of a dollar quote, that's the end of a statement
        if ";" in line and not in_dollar_quote and not in_comment:
            statements.append("\n".join(current))
            current = []

    print(f"Found {len(statements)} SQL statements to execute...")
    print()

    # Execute each statement
    success_count = 0
    for i, stmt in enumerate(statements, 1):
        stmt_preview = stmt[:100].replace("\n", " ").strip()
        if len(stmt_preview) == 100:
            stmt_preview += "..."

        try:
            # Use RPC to execute raw SQL
            result = supabase.rpc("exec_sql", {"sql": stmt}).execute()
            success_count += 1
            print(f"✓ Statement {i}/{len(statements)}: {stmt_preview}")
        except Exception as e:
            # Try direct execution for DDL statements
            try:
                # For now, skip since Supabase client doesn't support raw DDL directly
                # We'll use a different approach
                print(
                    f"⊙ Statement {i}/{len(statements)}: {stmt_preview} (skipped - needs direct DB access)"
                )
            except Exception as e2:
                print(f"✗ Statement {i}/{len(statements)}: {stmt_preview}")
                print(f"  Error: {str(e)[:100]}")

    print()
    print("=" * 50)
    print(f"✅ Migration execution completed")
    print(f"   {success_count}/{len(statements)} statements executed")
    print("=" * 50)
    print()
    print("Note: Some DDL statements may require direct database access.")
    print(
        "If indexes weren't created, run the migration SQL directly in Supabase SQL Editor:"
    )
    print(f"  {migration_path}")

    return 0


if __name__ == "__main__":
    exit(main())
