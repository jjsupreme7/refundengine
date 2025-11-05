#!/usr/bin/env python3
"""
Refund Analysis for Washington State Tax Refund Engine

CRITICAL: Uses vector search across ALL legal documents to find relevant exemptions.
Analysis is driven by retrieved documents, not hardcoded rules.

Usage:
    python scripts/analyze_refund.py --line_item_id 1
    python scripts/analyze_refund.py --invoice_id 1
"""

import argparse
import sys
import os
import sqlite3
import json
from pathlib import Path

# Vector search
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# AI
from anthropic import Anthropic
from dotenv import load_dotenv

# Import product identification
sys.path.insert(0, str(Path(__file__).parent))
from identify_product import identify_product

load_dotenv()

# Global models
embedding_model = None

def get_embedding_model():
    """Lazy load embedding model."""
    global embedding_model
    if embedding_model is None:
        print("🔄 Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    return embedding_model

def get_database_connection():
    """Get database connection."""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "refund_engine.db"
    return sqlite3.connect(str(db_path))

def get_chromadb_client():
    """Get ChromaDB client."""
    project_root = Path(__file__).parent.parent
    chroma_path = project_root / "vector_db" / "chroma"

    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=Settings(anonymized_telemetry=False)
    )

    return client

def analyze_line_item_for_refund(line_item_id, conn):
    """
    Analyze line item for refund eligibility using vector search.

    CRITICAL: Searches ALL legal documents and applies relevant exemptions.
    """
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"REFUND ANALYSIS - Line Item {line_item_id}")
    print(f"{'='*70}\n")

    # Get complete context
    cursor.execute("""
        SELECT
            li.item_description,
            li.line_total,
            li.sales_tax_on_line,
            li.product_category,
            li.is_digital,
            li.is_service,
            li.primarily_human_effort,
            i.vendor_name,
            i.invoice_date,
            i.invoice_number,
            i.ship_to_city,
            i.ship_to_state,
            i.sales_tax_charged,
            c.client_name,
            c.industry_classification,
            pi.product_name,
            pi.automation_level,
            pi.evidence_json
        FROM invoice_line_items li
        JOIN invoices i ON li.invoice_id = i.id
        JOIN clients c ON i.client_id = c.id
        LEFT JOIN product_identifications pi ON li.id = pi.line_item_id
        WHERE li.id = ?
    """, (line_item_id,))

    row = cursor.fetchone()
    if not row:
        print(f"❌ Line item {line_item_id} not found")
        return None

    (item_description, line_total, sales_tax, product_category, is_digital, is_service,
     primarily_human_effort, vendor_name, invoice_date, invoice_number, ship_to_city,
     ship_to_state, invoice_sales_tax, client_name, industry, product_name,
     automation_level, evidence_json) = row

    print(f"📦 Product: {item_description[:80]}")
    print(f"💰 Amount: ${line_total:.2f}")
    print(f"💵 Sales Tax: ${sales_tax or 0:.2f}")
    print(f"🏢 Vendor: {vendor_name}")

    # If product not identified, identify it first
    if product_category is None:
        print(f"\n⚠️  Product not yet identified. Running identification first...")
        identify_product(line_item_id, conn)

        # Re-query to get updated data
        cursor.execute("""
            SELECT product_category, is_digital, is_service, primarily_human_effort
            FROM invoice_line_items WHERE id = ?
        """, (line_item_id,))
        row2 = cursor.fetchone()
        if row2:
            product_category, is_digital, is_service, primarily_human_effort = row2

    # Build vector search query
    search_terms = []

    if product_category:
        search_terms.append(product_category)

    if is_service:
        search_terms.append("service")
        if primarily_human_effort:
            search_terms.append("primarily human effort")

    if is_digital:
        search_terms.append("digital")

    search_terms.append(item_description[:50])
    search_terms.append("Washington sales tax exemption")

    search_query = " ".join(search_terms)

    print(f"\n🔍 Vector Search Query: {search_query[:100]}...")

    # Search ChromaDB for relevant legal documents
    try:
        chroma_client = get_chromadb_client()
        collection = chroma_client.get_collection("legal_knowledge")

        # Generate query embedding
        model = get_embedding_model()
        query_embedding = model.encode([search_query])[0]

        # Search for top 10 most relevant chunks
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=10
        )

        # Extract retrieved documents
        retrieved_docs = []
        if results and results['documents'] and len(results['documents']) > 0:
            for i, doc_text in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0

                # Convert distance to similarity percentage
                similarity = max(0, 100 * (1 - distance))

                if similarity > 30:  # Only include if reasonably similar
                    retrieved_docs.append({
                        'text': doc_text,
                        'citation': metadata.get('citation', 'Unknown'),
                        'document_type': metadata.get('document_type', 'Unknown'),
                        'title': metadata.get('title', ''),
                        'similarity': similarity
                    })

        print(f"✅ Retrieved {len(retrieved_docs)} relevant legal document sections\n")

        if retrieved_docs:
            print("📚 Top Retrieved Documents:")
            for i, doc in enumerate(retrieved_docs[:5], 1):
                print(f"  {i}. [{doc['citation']}] (Similarity: {doc['similarity']:.1f}%)")
                print(f"     {doc['text'][:100]}...")

    except Exception as e:
        print(f"  ⚠️  Vector search failed: {e}")
        print(f"  Proceeding with rule-based analysis only...")
        retrieved_docs = []

    # Get applicable legal rules from database
    cursor.execute("SELECT * FROM legal_rules")
    legal_rules = cursor.fetchall()

    # Build comprehensive AI analysis prompt
    prompt = f"""You are a Washington State tax expert analyzing transactions for potential sales/use tax refunds.

PRODUCT/SERVICE INFORMATION:
- Description: {item_description}
- Product Name: {product_name or 'Unknown'}
- Category: {product_category or 'Unknown'}
- Is Digital: {is_digital}
- Is Service: {is_service}
- Primarily Human Effort: {primarily_human_effort}
- Automation Level: {automation_level or 'Unknown'}

TRANSACTION DETAILS:
- Vendor: {vendor_name}
- Invoice Date: {invoice_date}
- Invoice Number: {invoice_number}
- Ship To: {ship_to_city}, {ship_to_state}
- Line Item Amount: ${line_total:.2f}
- Sales Tax Charged on Line: ${sales_tax or 0:.2f}
- Client: {client_name}
- Client Industry: {industry or 'Unknown'}

RELEVANT LEGAL AUTHORITIES FROM KNOWLEDGE BASE:

The following legal document sections were retrieved by semantic search as most relevant to this transaction.
These are the TOP {len(retrieved_docs)} most similar legal sections from the Washington State tax law knowledge base.

CRITICAL: Base your analysis primarily on these retrieved documents. They were selected because they are
semantically similar to this transaction, so they likely contain relevant exemptions or rules.

"""

    # Add retrieved documents
    for i, doc in enumerate(retrieved_docs, 1):
        prompt += f"\n[{i}] {doc['citation']} (Similarity: {doc['similarity']:.1f}%)\n"
        prompt += f"Document Type: {doc['document_type']}\n"
        prompt += f"{doc['text']}\n"
        prompt += "---\n"

    # Add sample rules from database
    prompt += f"""
SAMPLE EXEMPTIONS IN DATABASE (for reference, but prioritize retrieved documents above):

"""

    for rule in legal_rules:
        prompt += f"""
- {rule[1]}: {rule[3]} ({rule[2]})
  Requirements: {rule[5][:200] if rule[5] else 'See statute'}
"""

    prompt += f"""

YOUR ANALYSIS TASK:

1. TAXABILITY DETERMINATION:
   - Is this product/service subject to Washington sales tax under current law?
   - Consider: product type, service classification, location, date
   - Reference: ESSB 5814 (effective Jan 2024) changed taxation of digital products/services

2. WAS TAX CORRECTLY CHARGED?
   - Based on applicable law at the time of this transaction ({invoice_date})
   - Should sales tax have been charged on this item?

3. EXEMPTION ANALYSIS - SEARCH-DRIVEN APPROACH:

   CRITICAL INSTRUCTION: Your analysis must be driven by the RETRIEVED LEGAL DOCUMENTS above.

   The retrieved documents were selected by semantic similarity to this transaction. If a retrieved
   document discusses an exemption, carefully evaluate whether it applies.

   DO NOT IGNORE retrieved documents just because they're not in the sample list below.
   DO NOT LIMIT your analysis to only the sample exemptions.
   DO CONSIDER any exemption mentioned in the retrieved documents.

   Common exemptions to consider (IF RELEVANT DOCUMENTS WERE RETRIEVED):

   a) Manufacturing Equipment Exemption (RCW 82.08.02565)
   b) Reseller Permit Exemption (RCW 82.08.0251)
   c) Interstate Commerce Exemption (RCW 82.08.0264)
   d) Service Taxability - Primarily Human Effort Test (ESSB 5814 / RCW 82.04.050)
   e) Agricultural Exemption (RCW 82.08.0259)
   f) ANY OTHER EXEMPTION mentioned in the retrieved documents

   For EACH relevant exemption found in retrieved documents:
   - Evaluate if the transaction meets the requirements
   - Cite the specific retrieved document
   - Explain your reasoning

4. REFUND CALCULATION:
   - If tax was incorrectly charged, calculate refund amount
   - Formula: sales_tax_charged × (refund_percentage / 100)

5. DOCUMENTATION REQUIREMENTS:
   - What documentation is needed to support the refund claim?

6. RED FLAGS:
   - Any concerns or uncertainties?

7. CONFIDENCE ASSESSMENT:
   - How confident are you in this analysis? (0-100)

Return ONLY valid JSON (no markdown, no backticks):
{{
  "taxable": true/false,
  "tax_correctly_charged": true/false,
  "refund_eligible": true/false,
  "refund_amount": number,
  "refund_calculation_method": "explanation",
  "applicable_exemption": "exemption name or null",
  "applicable_statute": "RCW/WAC citation or null",
  "criteria_met": ["array of requirements satisfied"],
  "criteria_failed": ["array of requirements not satisfied"],
  "criteria_uncertain": ["array of unclear requirements"],
  "documentation_needed": ["array of required documents"],
  "red_flags": ["array of concerns"],
  "reasoning": "detailed explanation referencing retrieved documents",
  "confidence_score": 0-100,
  "citations_used": ["array of RCW/WAC from retrieved documents"]
}}"""

    # Call Claude API
    try:
        print(f"\n🤖 Running AI analysis...")

        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        analysis = json.loads(result_text)

        print(f"\n{'='*70}")
        print("ANALYSIS RESULTS")
        print(f"{'='*70}\n")

        print(f"⚖️  Taxable: {analysis.get('taxable')}")
        print(f"✅ Tax Correctly Charged: {analysis.get('tax_correctly_charged')}")
        print(f"💰 Refund Eligible: {analysis.get('refund_eligible')}")
        print(f"💵 Refund Amount: ${analysis.get('refund_amount', 0):.2f}")

        if analysis.get('applicable_exemption'):
            print(f"📜 Exemption: {analysis['applicable_exemption']}")
            print(f"📖 Statute: {analysis['applicable_statute']}")

        print(f"\n🎯 Confidence: {analysis.get('confidence_score', 0)}%")
        print(f"\n💭 Reasoning:\n{analysis.get('reasoning', 'N/A')[:500]}...")

        if analysis.get('documentation_needed'):
            print(f"\n📋 Documentation Needed:")
            for doc in analysis['documentation_needed']:
                print(f"  - {doc}")

        if analysis.get('red_flags'):
            print(f"\n🚩 Red Flags:")
            for flag in analysis['red_flags']:
                print(f"  - {flag}")

        # Determine legal_rule_id if applicable
        legal_rule_id = None
        if analysis.get('applicable_statute'):
            cursor.execute("""
                SELECT id FROM legal_rules
                WHERE statute_citation LIKE ?
                LIMIT 1
            """, (f"%{analysis['applicable_statute']}%",))
            rule_row = cursor.fetchone()
            if rule_row:
                legal_rule_id = rule_row[0]

        # Get invoice_id
        cursor.execute("SELECT invoice_id FROM invoice_line_items WHERE id = ?", (line_item_id,))
        invoice_id = cursor.fetchone()[0]

        # Insert into refund_analysis table
        cursor.execute("""
            INSERT INTO refund_analysis (
                invoice_id, line_item_id, legal_rule_id, potentially_eligible,
                confidence_score, estimated_refund_amount, refund_calculation_method,
                criteria_matching_json, documentation_gaps, red_flags, next_steps,
                reviewed_by_human
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            line_item_id,
            legal_rule_id,
            analysis.get('refund_eligible'),
            analysis.get('confidence_score', 0),
            analysis.get('refund_amount', 0),
            analysis.get('refund_calculation_method'),
            json.dumps({
                'criteria_met': analysis.get('criteria_met', []),
                'criteria_failed': analysis.get('criteria_failed', []),
                'criteria_uncertain': analysis.get('criteria_uncertain', []),
                'citations_used': analysis.get('citations_used', [])
            }),
            ','.join(analysis.get('criteria_uncertain', [])),
            ','.join(analysis.get('red_flags', [])),
            ','.join(analysis.get('documentation_needed', [])),
            1 if analysis.get('confidence_score', 0) < 60 else 0  # Flag for review if low confidence
        ))

        conn.commit()

        print(f"\n✅ Analysis saved to database")
        print(f"{'='*70}\n")

        return analysis

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return None

def batch_analyze_invoice(invoice_id, conn):
    """Analyze all line items on an invoice."""
    print(f"\n📊 Analyzing all line items for invoice {invoice_id}...\n")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, item_description, line_total
        FROM invoice_line_items
        WHERE invoice_id = ?
    """, (invoice_id,))

    line_items = cursor.fetchall()

    print(f"Found {len(line_items)} line items\n")

    results = []
    for line_item_id, description, total in line_items:
        print(f"\n{'#'*70}")
        print(f"Line Item {line_item_id}: {description[:60]}")
        print(f"{'#'*70}")

        result = analyze_line_item_for_refund(line_item_id, conn)
        if result:
            results.append(result)

    # Print summary
    print(f"\n{'='*70}")
    print("INVOICE ANALYSIS SUMMARY")
    print(f"{'='*70}\n")

    eligible_count = sum(1 for r in results if r.get('refund_eligible'))
    total_refund = sum(r.get('refund_amount', 0) for r in results)

    print(f"✅ Analyzed: {len(results)} line items")
    print(f"💰 Refund Eligible: {eligible_count} line items")
    print(f"💵 Total Potential Refund: ${total_refund:.2f}")

    print(f"\n{'='*70}\n")

    return results

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze refund eligibility using vector search and AI"
    )
    parser.add_argument('--line_item_id', type=int, help="Specific line item ID")
    parser.add_argument('--invoice_id', type=int, help="Process all items on invoice")

    args = parser.parse_args()

    if not args.line_item_id and not args.invoice_id:
        print("❌ Error: Must specify either --line_item_id or --invoice_id")
        return 1

    conn = get_database_connection()

    if args.line_item_id:
        analyze_line_item_for_refund(args.line_item_id, conn)
    elif args.invoice_id:
        batch_analyze_invoice(args.invoice_id, conn)

    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
