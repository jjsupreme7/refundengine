#!/usr/bin/env python3
"""
Deploy Feedback Schema to Supabase using Python
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client


def deploy_schema():
    """Deploy feedback schema to Supabase"""

    print("=" * 80)
    print("Deploying Feedback & Learning Schema")
    print("=" * 80)
    print()

    # Get Supabase client
    print("Step 1: Connecting to Supabase...")
    try:
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

    print()
    print("Step 2: Creating tables...")

    # Read SQL file
    sql_path = Path(__file__).parent.parent / "database/feedback_schema.sql"

    if not sql_path.exists():
        print(f"❌ SQL file not found: {sql_path}")
        return False

    with open(sql_path, "r") as f:
        sql_content = f.read()

    # Split into individual statements
    # Remove comments and split by semicolons
    statements = []
    current_statement = []

    for line in sql_content.split("\n"):
        # Skip comment-only lines
        if line.strip().startswith("--"):
            continue

        current_statement.append(line)

        # If line ends with semicolon, it's the end of a statement
        if line.strip().endswith(";"):
            statement = "\n".join(current_statement).strip()
            if statement and not statement.startswith("--"):
                statements.append(statement)
            current_statement = []

    print(f"Found {len(statements)} SQL statements to execute")
    print()

    # Execute each statement using Supabase RPC
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        # Skip empty statements
        if not statement.strip():
            continue

        # Get first few words for display
        preview = " ".join(statement.split()[:5])
        print(f"  [{i}/{len(statements)}] Executing: {preview}...", end=" ")

        try:
            # Use Supabase's rpc to execute raw SQL
            # Note: This may not work with all Supabase tiers
            # Alternative: Use PostgreSQL connection

            # For now, let's execute table creation statements directly
            if "CREATE TABLE" in statement:
                # Extract table name
                table_name = (
                    statement.split("CREATE TABLE")[1].split("(")[0].strip().split()[-1]
                )
                print(f"(Table: {table_name})", end=" ")

            # Try to execute via RPC
            try:
                result = supabase.rpc("exec_sql", {"sql": statement}).execute()
                print("✅")
                success_count += 1
            except:
                # If RPC doesn't work, we'll need direct PostgreSQL access
                # For now, just mark as needing manual execution
                print("⚠️  (Needs manual execution)")
                error_count += 1

        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            error_count += 1

    print()
    print("=" * 80)

    if error_count > 0:
        print(f"⚠️  Schema deployment incomplete")
        print(f"   Successfully executed: {success_count}")
        print(f"   Failed/Skipped: {error_count}")
        print()
        print("ALTERNATIVE: Execute the SQL file manually:")
        print(f"   File: {sql_path}")
        print("   Use Supabase Dashboard > SQL Editor")
        print("   Or use psql command line tool")
    else:
        print("✅ Schema deployment complete!")
        print(f"   Successfully executed all {success_count} statements")

    print()
    print("Tables that should be created:")
    print("  - user_feedback")
    print("  - learned_improvements")
    print("  - golden_qa_pairs")
    print("  - citation_preferences")
    print("  - answer_templates")
    print()

    # Verify tables exist
    print("Step 3: Verifying tables...")
    tables_to_check = [
        "user_feedback",
        "learned_improvements",
        "golden_qa_pairs",
        "citation_preferences",
        "answer_templates",
    ]

    for table in tables_to_check:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"  ✅ {table} exists")
        except Exception as e:
            print(f"  ❌ {table} not found - needs manual creation")

    print()
    print("=" * 80)
    print()

    return True


if __name__ == "__main__":
    deploy_schema()
