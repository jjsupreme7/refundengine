#!/usr/bin/env python3
"""
Fix Vendor Background Chunks

This script generates chunks and embeddings for existing vendor documents
that were ingested into knowledge_documents but never chunked.

Problem: Vendor documents exist in knowledge_documents but have 0 chunks
Solution: Generate meaningful text from vendor metadata, chunk it, embed it
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

from core.database import get_supabase_client

# Load environment
load_dotenv()

# Initialize clients
supabase = get_supabase_client()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_vendor_text(vendor_doc: Dict) -> str:
    """
    Generate comprehensive text from vendor metadata
    This creates a rich, searchable description of the vendor
    """
    vendor_name = vendor_doc.get("vendor_name", "Unknown Vendor")
    industry = vendor_doc.get("industry", "")
    business_model = vendor_doc.get("business_model", "")
    primary_products = vendor_doc.get("primary_products", [])
    typical_delivery = vendor_doc.get("typical_delivery", "")
    tax_notes = vendor_doc.get("tax_notes", "")

    # Build comprehensive vendor description
    text_parts = []

    # Header
    text_parts.append(f"# Vendor: {vendor_name}\n")

    # Industry and business model
    if industry:
        text_parts.append(
            f"## Industry\n{vendor_name} operates in the {industry} industry.\n"
        )

    if business_model:
        text_parts.append(
            f"## Business Model\n{vendor_name} follows a {business_model} business model.\n"
        )

    # Primary products/services
    if primary_products and len(primary_products) > 0:
        text_parts.append(f"## Primary Products and Services\n")
        text_parts.append(
            f"{vendor_name} provides the following products and services:\n"
        )
        for product in primary_products:
            if isinstance(product, str):
                text_parts.append(f"- {product}\n")

    # Delivery method
    if typical_delivery:
        text_parts.append(f"## Typical Delivery Method\n")
        text_parts.append(
            f"{vendor_name} typically delivers products/services via {typical_delivery}.\n"
        )

    # Tax treatment notes
    if tax_notes:
        text_parts.append(f"## Tax Treatment Notes\n")
        text_parts.append(f"{tax_notes}\n")

    # Additional searchable keywords for RAG
    text_parts.append(f"\n## Vendor Summary\n")
    text_parts.append(
        f"When analyzing invoices or purchase orders from {vendor_name}, consider "
    )
    text_parts.append(
        f"their {business_model} model " if business_model else "their business model "
    )
    text_parts.append(
        f"and typical {typical_delivery} delivery method. "
        if typical_delivery
        else "delivery methods. "
    )

    if primary_products:
        products_str = ", ".join([str(p) for p in primary_products[:3]])
        text_parts.append(f"Common products include: {products_str}. ")

    return "\n".join(text_parts)


def create_embedding(text: str) -> List[float]:
    """
    Generate embedding using OpenAI text-embedding-3-small
    """
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small", input=text, dimensions=1536
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  ❌ Error creating embedding: {e}")
        return None


def chunk_vendor_text(text: str, vendor_name: str) -> List[Dict]:
    """
    Create chunks from vendor text
    For vendors, we typically want 1-2 chunks maximum since the data is compact
    """
    chunks = []

    # For most vendors, the entire text is small enough for one chunk
    if len(text) < 1500:
        chunks.append(
            {
                "chunk_text": text,
                "chunk_number": 1,
                "document_category": "vendor_profile",
            }
        )
    else:
        # If text is longer, split into logical sections
        sections = text.split("## ")
        current_chunk = []
        chunk_num = 1
        current_length = 0

        for section in sections:
            if not section.strip():
                continue

            section_text = f"## {section}"
            section_length = len(section_text)

            if current_length + section_length > 1500 and current_chunk:
                # Save current chunk
                chunks.append(
                    {
                        "chunk_text": "\n\n".join(current_chunk),
                        "chunk_number": chunk_num,
                        "document_category": "vendor_profile",
                    }
                )
                chunk_num += 1
                current_chunk = [section_text]
                current_length = section_length
            else:
                current_chunk.append(section_text)
                current_length += section_length

        # Add remaining chunk
        if current_chunk:
            chunks.append(
                {
                    "chunk_text": "\n\n".join(current_chunk),
                    "chunk_number": chunk_num,
                    "document_category": "vendor_profile",
                }
            )

    return chunks


def process_vendor(vendor_doc: Dict) -> bool:
    """
    Process a single vendor: generate text, create chunks, embed, and insert
    """
    vendor_name = vendor_doc.get("vendor_name", "Unknown")
    doc_id = vendor_doc["id"]

    print(f"\n📦 Processing: {vendor_name}")

    # Check if chunks already exist
    existing_chunks = (
        supabase.table("vendor_background_chunks")
        .select("id", count="exact")
        .eq("document_id", doc_id)
        .execute()
    )

    if existing_chunks.count > 0:
        print(f"  ℹ️  Already has {existing_chunks.count} chunks, skipping...")
        return True

    # Generate vendor text
    print(f"  📝 Generating descriptive text...")
    vendor_text = generate_vendor_text(vendor_doc)

    if not vendor_text or len(vendor_text) < 50:
        print(f"  ⚠️  Insufficient data to create meaningful chunks")
        return False

    # Create chunks
    print(f"  ✂️  Creating chunks...")
    chunks = chunk_vendor_text(vendor_text, vendor_name)
    print(f"  📊 Created {len(chunks)} chunk(s)")

    # Process each chunk
    for chunk_data in chunks:
        chunk_text = chunk_data["chunk_text"]
        chunk_num = chunk_data["chunk_number"]

        print(f"  🔢 Processing chunk {chunk_num}/{len(chunks)}...")

        # Generate embedding
        print(f"     🧮 Generating embedding...")
        embedding = create_embedding(chunk_text)

        if not embedding:
            print(f"     ❌ Failed to create embedding for chunk {chunk_num}")
            continue

        # Insert into database
        try:
            insert_data = {
                "document_id": doc_id,
                "chunk_text": chunk_text,
                "chunk_number": chunk_num,
                "vendor_name": vendor_name,
                "vendor_category": vendor_doc.get("vendor_category"),
                "document_category": chunk_data["document_category"],
                "embedding": embedding,
            }

            result = (
                supabase.table("vendor_background_chunks").insert(insert_data).execute()
            )
            print(f"     ✅ Chunk {chunk_num} inserted successfully")

        except Exception as e:
            print(f"     ❌ Error inserting chunk {chunk_num}: {e}")
            return False

    # Update document metadata
    try:
        supabase.table("knowledge_documents").update(
            {"total_chunks": len(chunks), "processing_status": "completed"}
        ).eq("id", doc_id).execute()
        print(f"  ✅ Document metadata updated")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not update document metadata: {e}")

    return True


def main():
    """Main function to fix all vendor chunks"""

    print("=" * 70)
    print("FIX VENDOR BACKGROUND CHUNKS")
    print("=" * 70)
    print()

    # Get all vendor documents
    print("📂 Fetching vendor documents from database...")

    try:
        vendor_docs = (
            supabase.table("knowledge_documents")
            .select("*")
            .eq("document_type", "vendor_background")
            .execute()
        )

        vendors = vendor_docs.data
        print(f"📊 Found {len(vendors)} vendor documents")

    except Exception as e:
        print(f"❌ Error fetching vendor documents: {e}")
        return 1

    # Process each vendor
    success_count = 0
    skip_count = 0
    error_count = 0

    for vendor_doc in vendors:
        try:
            result = process_vendor(vendor_doc)
            if result:
                success_count += 1
            else:
                skip_count += 1
        except Exception as e:
            vendor_name = vendor_doc.get("vendor_name", "Unknown")
            print(f"  ❌ Error processing {vendor_name}: {e}")
            error_count += 1

    # Summary
    print()
    print("=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully processed: {success_count} vendors")
    print(f"⊙ Skipped (already processed): {skip_count} vendors")
    print(f"❌ Errors: {error_count} vendors")
    print()

    # Verify final state
    print("🔍 Verifying final state...")
    try:
        chunk_count = (
            supabase.table("vendor_background_chunks")
            .select("id", count="exact")
            .execute()
        )
        print(f"📊 Total vendor chunks in database: {chunk_count.count}")
    except Exception as e:
        print(f"⚠️  Could not verify chunk count: {e}")

    print()
    print("✅ All done! Your vendor background RAG should now work properly.")

    return 0


if __name__ == "__main__":
    exit(main())
