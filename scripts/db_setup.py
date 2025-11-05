#!/usr/bin/env python3
"""
Database Setup Script for Washington State Tax Refund Engine

This script initializes the database, creates all tables, and seeds with sample data.

Usage:
    python scripts/db_setup.py
"""

import sqlite3
import os
import sys
import json
from pathlib import Path
import chromadb
from chromadb.config import Settings

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def initialize_database():
    """Initialize SQLite database with schema."""
    project_root = get_project_root()
    db_path = project_root / "database" / "refund_engine.db"
    schema_path = project_root / "database" / "schema.sql"

    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database if present
    if db_path.exists():
        print(f"⚠️  Removing existing database at {db_path}")
        db_path.unlink()

    print(f"📊 Creating new database at {db_path}")

    # Read schema SQL
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Create database and execute schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Execute schema (split by semicolon to handle multiple statements)
    cursor.executescript(schema_sql)

    conn.commit()
    print("✅ Database schema created successfully")

    return conn

def seed_legal_rules(conn):
    """Seed database with sample legal rules."""
    print("\n📚 Seeding legal rules...")

    cursor = conn.cursor()

    # Rule 1: Manufacturing Equipment Exemption
    rule1 = {
        "refund_category": "Manufacturing Equipment Exemption",
        "statute_citation": "RCW 82.08.02565",
        "effective_date": "2017-07-01",
        "rule_summary": "Machinery and equipment used directly in manufacturing operations are exempt from sales tax",
        "requirements_json": json.dumps({
            "must_have": [
                "Used directly in manufacturing",
                "Machinery or equipment classification",
                "Purchased after July 1, 2017"
            ],
            "cannot_have": [
                "Used for general business purposes",
                "Office equipment"
            ],
            "documentation_required": [
                "Invoice with detailed description",
                "Manufacturing process documentation"
            ]
        }),
        "statute_of_limitations_years": 4,
        "typical_refund_percentage": 100,
        "industry_tags": "manufacturing,food_processing,aerospace"
    }

    # Rule 2: Reseller Permit Exemption
    rule2 = {
        "refund_category": "Reseller Permit Exemption",
        "statute_citation": "RCW 82.08.0251",
        "effective_date": "1935-01-01",
        "rule_summary": "Items purchased for resale are exempt from sales tax with valid reseller permit",
        "requirements_json": json.dumps({
            "must_have": [
                "Valid reseller permit",
                "Item purchased for resale",
                "Not used by purchaser"
            ],
            "cannot_have": [
                "Item consumed by purchaser",
                "Item used in business operations"
            ],
            "documentation_required": [
                "Reseller permit certificate",
                "Invoice showing resale item"
            ]
        }),
        "statute_of_limitations_years": 4,
        "typical_refund_percentage": 100,
        "industry_tags": "retail,wholesale,distribution"
    }

    # Rule 3: Interstate/Foreign Commerce Exemption
    rule3 = {
        "refund_category": "Interstate Commerce Exemption",
        "statute_citation": "RCW 82.08.0264",
        "effective_date": "1935-01-01",
        "rule_summary": "Sales tax does not apply to items shipped out of Washington State",
        "requirements_json": json.dumps({
            "must_have": [
                "Item shipped out of state",
                "Shipping documentation",
                "Delivery to out-of-state location"
            ],
            "cannot_have": [
                "Item used in Washington",
                "Delivery to WA address"
            ],
            "documentation_required": [
                "Shipping records",
                "Bill of lading",
                "Proof of delivery out of state"
            ]
        }),
        "statute_of_limitations_years": 4,
        "typical_refund_percentage": 100,
        "industry_tags": "all"
    }

    # Rule 4: Primarily Human Effort Service Exemption
    rule4 = {
        "refund_category": "Primarily Human Effort Service Exemption",
        "statute_citation": "ESSB 5814 / RCW 82.04.050",
        "effective_date": "2024-01-01",
        "rule_summary": "Services that are primarily human effort are not subject to sales tax, even if delivered digitally",
        "requirements_json": json.dumps({
            "must_have": [
                "Service is primarily human effort",
                "Not automated/software-based",
                "Custom work performed by humans"
            ],
            "cannot_have": [
                "Automated service",
                "Software subscription",
                "Pre-built digital product"
            ],
            "documentation_required": [
                "Service agreement",
                "Statement of work showing human involvement",
                "Description of services performed"
            ]
        }),
        "statute_of_limitations_years": 4,
        "typical_refund_percentage": 100,
        "industry_tags": "software,consulting,professional_services"
    }

    # Rule 5: Agricultural Exemption
    rule5 = {
        "refund_category": "Agricultural Exemption",
        "statute_citation": "RCW 82.08.0259",
        "effective_date": "1935-01-01",
        "rule_summary": "Certain agricultural products and equipment are exempt from sales tax",
        "requirements_json": json.dumps({
            "must_have": [
                "Used in farming operation",
                "Agricultural product or equipment",
                "Qualifying farm activity"
            ],
            "cannot_have": [
                "Used for non-farm purposes",
                "Retail sale items"
            ],
            "documentation_required": [
                "Farm registration",
                "Invoice showing agricultural use"
            ]
        }),
        "statute_of_limitations_years": 4,
        "typical_refund_percentage": 100,
        "industry_tags": "agriculture,farming"
    }

    rules = [rule1, rule2, rule3, rule4, rule5]

    for i, rule in enumerate(rules, 1):
        cursor.execute("""
            INSERT INTO legal_rules (
                refund_category, statute_citation, effective_date, rule_summary,
                requirements_json, statute_of_limitations_years, typical_refund_percentage,
                industry_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule["refund_category"],
            rule["statute_citation"],
            rule["effective_date"],
            rule["rule_summary"],
            rule["requirements_json"],
            rule["statute_of_limitations_years"],
            rule["typical_refund_percentage"],
            rule["industry_tags"]
        ))
        print(f"  ✅ Rule {i}: {rule['refund_category']} ({rule['statute_citation']})")

    conn.commit()
    print(f"\n✅ Seeded {len(rules)} legal rules")

def initialize_vector_db():
    """Initialize ChromaDB for vector storage."""
    print("\n🔍 Initializing ChromaDB vector database...")

    project_root = get_project_root()
    chroma_path = project_root / "vector_db" / "chroma"

    # Ensure directory exists
    chroma_path.mkdir(parents=True, exist_ok=True)

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Delete existing collection if present
    try:
        client.delete_collection("legal_knowledge")
        print("  ⚠️  Deleted existing 'legal_knowledge' collection")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name="legal_knowledge",
        metadata={"description": "Washington State tax law documents and legal authorities"}
    )

    print("  ✅ Created 'legal_knowledge' collection")
    print(f"  📁 ChromaDB path: {chroma_path}")

    return client

def print_success_summary():
    """Print success message with next steps."""
    print("\n" + "="*70)
    print("🎉 WASHINGTON STATE TAX REFUND ENGINE - DATABASE INITIALIZED")
    print("="*70)

    project_root = get_project_root()

    print("\n📊 Database Status:")
    print(f"  ✅ SQLite database created")
    print(f"  ✅ All tables created")
    print(f"  ✅ Test client seeded (client_id=1)")
    print(f"  ✅ 5 sample legal rules seeded")
    print(f"  ✅ ChromaDB vector database initialized")

    print("\n📂 Key Paths:")
    print(f"  Database: {project_root}/database/refund_engine.db")
    print(f"  Vector DB: {project_root}/vector_db/chroma/")

    print("\n📚 NEXT STEPS:")
    print("\n  1. INGEST LEGAL DOCUMENTS:")
    print("     - Place RCW documents in: knowledge_base/statutes/rcw/")
    print("     - Place WAC documents in: knowledge_base/statutes/wac/")
    print("     - Place WTD documents in: knowledge_base/guidance/wtd/")
    print("     - Place ETA documents in: knowledge_base/guidance/eta/")
    print("     - Run: python scripts/ingest_legal_docs.py --folder knowledge_base/")

    print("\n  2. PROCESS CLIENT DOCUMENTS:")
    print("     - Place ALL client documents in: client_documents/uploads/")
    print("     - Run: python scripts/ingest_client_docs.py --folder client_documents/uploads --client_id 1")

    print("\n  3. RUN FULL ANALYSIS PIPELINE:")
    print("     - Run: python scripts/process_pipeline.py --client_id 1 --invoices client_documents/uploads/")

    print("\n  4. INDIVIDUAL SCRIPTS:")
    print("     - Classify document: python scripts/document_classifier.py --file path/to/doc.pdf")
    print("     - Extract metadata: python scripts/metadata_extractor.py --file path/to/doc.pdf --type invoice")
    print("     - Identify product: python scripts/identify_product.py --invoice_id 1")
    print("     - Analyze refund: python scripts/analyze_refund.py --invoice_id 1")

    print("\n" + "="*70)
    print("✨ System ready for use!")
    print("="*70 + "\n")

def main():
    """Main setup function."""
    try:
        print("\n" + "="*70)
        print("WASHINGTON STATE TAX REFUND ENGINE - DATABASE SETUP")
        print("="*70 + "\n")

        # Initialize SQLite database
        conn = initialize_database()

        # Seed legal rules
        seed_legal_rules(conn)

        # Close database connection
        conn.close()

        # Initialize ChromaDB
        initialize_vector_db()

        # Print success summary
        print_success_summary()

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
