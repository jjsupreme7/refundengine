#!/usr/bin/env python3
"""
Unified Document Ingestion Script
Single script for ingesting both tax law and vendor/product documents

Features:
- AI metadata suggestions
- Excel export/import workflow for metadata review
- Canonical chunking (consistent, deterministic)
- Supports both tax law and vendor document types
- Stores in knowledge_documents schema

Usage:

    STEP 1: Export metadata to Excel for review
    python scripts/ingest_documents.py --type tax_law --folder knowledge_base/wa_tax_law --export-metadata outputs/Tax_Metadata.xlsx
    python scripts/ingest_documents.py --type vendor --folder knowledge_base/vendors --export-metadata outputs/Vendor_Metadata.xlsx

    STEP 2: Review and edit the Excel file, then import
    python scripts/ingest_documents.py --import-metadata outputs/Tax_Metadata.xlsx

Options:
    --type: Document type (required for export): tax_law or vendor
    --folder: Path to folder containing PDFs
    --export-metadata: Export AI metadata suggestions to Excel (no ingestion)
    --import-metadata: Import edited Excel and ingest to Supabase
    --limit: Number of documents to process (default: all)
"""

import os
import sys
import re
import argparse
from pathlib import Path
import pdfplumber
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from tqdm import tqdm
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

# Import canonical chunking and cost tracker
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.chunking import chunk_legal_document, get_chunking_stats
from core.chunking_with_pages import chunk_document_with_pages, format_section_with_page

# Try to import cost tracker, create simple fallback if not available
try:
    from cost_tracker import CostTracker
except ImportError:
    # Simple fallback cost tracker
    class CostTracker:
        def __init__(self, name):
            self.name = name
        def add_gpt_call(self, model, prompt_tokens, completion_tokens):
            pass
        def add_embedding_call(self, model, tokens):
            pass
        def add_document_processed(self):
            pass
        def print_summary(self):
            print("  (Cost tracking not available)")

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Initialize cost tracker
cost_tracker = CostTracker("document_ingestion")


def extract_text_from_pdf(pdf_path: str, max_pages: int = 3) -> tuple[str, int]:
    """
    Extract text from PDF using pdfplumber
    Returns: (text, total_pages)
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            # Extract first few pages for metadata analysis
            text = ""
            for page in pdf.pages[:max_pages]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            return text, total_pages
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return "", 0


def suggest_metadata_simple(pdf_path: str, total_pages: int, document_type: str) -> Dict[str, Any]:
    """
    Generate simple metadata from filename for large documents
    (Used when AI extraction would fail due to document size)
    """
    filename = Path(pdf_path).stem

    # Basic metadata from filename
    metadata = {
        "document_title": filename.replace('_', ' ').replace('-', ' - '),
        "document_summary": f"Large document ({total_pages} pages) - metadata extracted from filename"
    }

    if document_type == 'tax_law':
        # Try to extract citation from filename
        citation_match = re.search(r'((?:WAC|RCW)\s*[\d\-\.]+)', filename, re.IGNORECASE)
        metadata.update({
            "citation": citation_match.group(1) if citation_match else filename,
            "law_category": "general",
            "effective_date": None,
            "topic_tags": ["retail sales", "use tax"] if "retail" in filename.lower() else ["general"],
            "tax_types": ["sales tax", "use tax"],
            "industries": ["general"],
            "keywords": [],
            "referenced_statutes": []
        })
    else:  # vendor
        metadata.update({
            "vendor_name": "Unknown",
            "vendor_category": "general",
            "document_category": "general",
            "product_types": [],
            "industries": [],
            "keywords": [],
            "industry": None,
            "business_model": None,
            "primary_products": [],
            "typical_delivery": None,
            "tax_notes": None,
            "confidence_score": 50.0,
            "data_source": "filename"
        })

    return metadata


def suggest_metadata_with_ai(pdf_path: str, sample_text: str, document_type: str, total_pages: int = 0) -> Dict[str, Any]:
    """
    Use GPT-4 to analyze document and suggest metadata based on type

    Args:
        pdf_path: Path to PDF file
        sample_text: Sample text from PDF
        document_type: 'tax_law' or 'vendor'
    """
    filename = Path(pdf_path).name

    if document_type == 'tax_law':
        prompt = f"""Analyze this Washington State tax law document and extract metadata.

Filename: {filename}

First few pages:
{sample_text[:3000]}

Return JSON with these fields:
{{
  "document_title": "Full descriptive title",
  "citation": "WAC 458-20-101 or RCW 82.04",
  "law_category": "exemption" | "rate" | "definition" | "compliance" | "general",
  "effective_date": "2020-01-01 or null",
  "topic_tags": ["registration", "licensing"],
  "tax_types": ["sales tax", "use tax"],
  "industries": ["general", "retail"],
  "keywords": ["key", "terms"],
  "referenced_statutes": ["RCW 82.04"],
  "document_summary": "1-2 sentence summary"
}}

Be specific and accurate. Extract actual information from the text."""

    else:  # vendor
        prompt = f"""Analyze this vendor/product document and extract metadata.

Filename: {filename}

First few pages:
{sample_text[:3000]}

Return JSON with these fields:
{{
  "document_title": "Full descriptive title",
  "vendor_name": "Company name",
  "vendor_category": "manufacturer" | "distributor" | "service_provider" | "retailer",
  "document_category": "profile" | "catalog" | "contract" | "terms" | "specification",
  "product_types": ["software", "hardware", "services"],
  "industries": ["retail", "manufacturing"],
  "keywords": ["key", "terms"],
  "document_summary": "1-2 sentence summary",
  "industry": "Primary industry sector (e.g., Technology, Professional Services, Manufacturing)",
  "business_model": "Business model (e.g., B2B SaaS, B2C Retail, Manufacturing, Consulting)",
  "primary_products": ["Main products or services"],
  "typical_delivery": "How products/services delivered (e.g., Cloud-based, On-premise, In-person, Physical goods)",
  "tax_notes": "Tax-relevant notes (e.g., Digital automated services, Tangible personal property, Professional services)",
  "confidence_score": 85.0
}}

Be specific and accurate. Extract actual information from the text."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert at analyzing {'tax law' if document_type == 'tax_law' else 'vendor/product'} documents. Extract metadata accurately."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Track cost
        usage = response.usage
        cost_tracker.add_gpt_call('gpt-4o', usage.prompt_tokens, usage.completion_tokens)

        metadata = json.loads(response.choices[0].message.content)
        return metadata

    except Exception as e:
        print(f"❌ AI metadata extraction failed: {e}")
        return {}


def generate_embedding(text: str) -> List[float]:
    """
    Generate OpenAI embedding for text
    """
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Limit to 8k chars
        )

        # Track cost (estimate ~500 tokens per embedding)
        cost_tracker.add_embedding_call('text-embedding-3-small', tokens=500)

        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None


def export_metadata_to_excel(pdf_files: List[Path], document_type: str, output_excel: str, limit: int = None):
    """
    Extract metadata from PDFs and export to Excel for review
    Automatically handles large files by using simpler metadata extraction
    """
    if limit:
        pdf_files = pdf_files[:limit]

    print(f"\n🔍 Extracting metadata from {len(pdf_files)} {document_type} PDFs...")
    print("This will NOT ingest to database yet - just export to Excel for your review\n")

    metadata_rows = []

    for pdf_path in tqdm(pdf_files, desc="Analyzing PDFs"):
        try:
            # Extract sample text
            sample_text, total_pages = extract_text_from_pdf(str(pdf_path), max_pages=3)

            if not sample_text:
                print(f"⚠️  Skipping {pdf_path.name} - could not extract text")
                continue

            # Auto-detect large files (100+ pages) and use simple metadata
            if total_pages >= 100:
                print(f"\n  📄 Large file detected ({total_pages} pages) - using filename-based metadata")
                suggested_metadata = suggest_metadata_simple(str(pdf_path), total_pages, document_type)
            else:
                # Get AI metadata suggestions for normal-sized files
                suggested_metadata = suggest_metadata_with_ai(str(pdf_path), sample_text, document_type, total_pages)

            if not suggested_metadata:
                print(f"⚠️  Skipping {pdf_path.name} - AI metadata failed")
                continue

            # Track document processed
            cost_tracker.add_document_processed()

            # Build row for Excel
            row = {
                'File_Name': pdf_path.name,
                'File_Path': str(pdf_path),
                'Total_Pages': total_pages,
                'Document_Type': document_type,
                'Status': 'Review',  # User can change to: Review, Approved, Skip
                'document_title': suggested_metadata.get('document_title', ''),
                'document_summary': suggested_metadata.get('document_summary', ''),
                'AI_Confidence': 'High'
            }

            # Add type-specific fields
            if document_type == 'tax_law':
                row.update({
                    'citation': suggested_metadata.get('citation', ''),
                    'law_category': suggested_metadata.get('law_category', ''),
                    'effective_date': suggested_metadata.get('effective_date', ''),
                    'topic_tags': ', '.join(suggested_metadata.get('topic_tags', [])),
                    'tax_types': ', '.join(suggested_metadata.get('tax_types', [])),
                    'industries': ', '.join(suggested_metadata.get('industries', [])),
                    'keywords': ', '.join(suggested_metadata.get('keywords', [])),
                    'referenced_statutes': ', '.join(suggested_metadata.get('referenced_statutes', []))
                })
            else:  # vendor
                row.update({
                    'vendor_name': suggested_metadata.get('vendor_name', ''),
                    'vendor_category': suggested_metadata.get('vendor_category', ''),
                    'document_category': suggested_metadata.get('document_category', ''),
                    'industry': suggested_metadata.get('industry', ''),
                    'business_model': suggested_metadata.get('business_model', ''),
                    'primary_products': ', '.join(suggested_metadata.get('primary_products', [])),
                    'typical_delivery': suggested_metadata.get('typical_delivery', ''),
                    'tax_notes': suggested_metadata.get('tax_notes', ''),
                    'product_types': ', '.join(suggested_metadata.get('product_types', [])),
                    'industries': ', '.join(suggested_metadata.get('industries', [])),
                    'keywords': ', '.join(suggested_metadata.get('keywords', [])),
                    'confidence_score': suggested_metadata.get('confidence_score', 80.0)
                })

            metadata_rows.append(row)

        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}")
            continue

    # Create DataFrame
    df = pd.DataFrame(metadata_rows)

    # Reorder columns for better Excel layout
    if document_type == 'tax_law':
        column_order = [
            'File_Name', 'Status', 'Document_Type', 'document_title', 'citation',
            'law_category', 'effective_date', 'topic_tags', 'tax_types', 'industries',
            'keywords', 'referenced_statutes', 'document_summary', 'AI_Confidence',
            'Total_Pages', 'File_Path'
        ]
    else:  # vendor
        column_order = [
            'File_Name', 'Status', 'Document_Type', 'document_title', 'vendor_name',
            'vendor_category', 'industry', 'business_model', 'primary_products',
            'typical_delivery', 'tax_notes', 'document_category', 'product_types',
            'industries', 'keywords', 'confidence_score', 'document_summary',
            'AI_Confidence', 'Total_Pages', 'File_Path'
        ]

    df = df[column_order]

    # Export to Excel
    output_path = Path(output_excel)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use ExcelWriter for better formatting
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Metadata', index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Metadata']

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap at 50
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"\n{'='*70}")
    print(f"✅ Metadata exported to Excel!")
    print(f"{'='*70}")
    print(f"📁 File: {output_path}")
    print(f"📊 Exported {len(df)} documents")

    # Show cost summary
    cost_tracker.print_summary()

    print(f"\n📋 Next steps:")
    print(f"  1. Open {output_path}")
    print(f"  2. Review AI suggestions in each row")
    print(f"  3. Edit any fields you want to change")
    print(f"  4. Update 'Status' column:")
    print(f"     - 'Approved' = Ready to ingest")
    print(f"     - 'Skip' = Don't ingest this document")
    print(f"  5. Save the Excel file")
    print(f"  6. Run: python scripts/ingest_documents.py --import-metadata {output_path}")
    print(f"{'='*70}\n")


def import_metadata_from_excel(excel_path: str, auto_confirm: bool = False):
    """
    Import edited metadata from Excel and ingest to Supabase
    """
    print(f"\n📂 Loading metadata from Excel: {excel_path}")

    try:
        df = pd.read_excel(excel_path, sheet_name='Metadata')
    except Exception as e:
        print(f"❌ Could not read Excel file: {e}")
        return

    print(f"✅ Loaded {len(df)} documents from Excel\n")

    # Filter to only 'Approved' status
    approved_df = df[df['Status'] == 'Approved']
    skipped_df = df[df['Status'] == 'Skip']
    review_df = df[df['Status'].isin(['Review'])]

    print(f"📊 Document status:")
    print(f"  ✅ Approved (will ingest): {len(approved_df)}")
    print(f"  ⏭️  Skip: {len(skipped_df)}")
    print(f"  ⚠️  Still in Review: {len(review_df)}")

    if len(review_df) > 0:
        print(f"\n⚠️  Warning: {len(review_df)} documents still marked as Review")
        print("These will NOT be ingested. Change status to 'Approved' to ingest them.\n")

    if len(approved_df) == 0:
        print("\n❌ No documents marked as 'Approved'. Nothing to ingest.")
        print("Please edit the Excel file and set Status='Approved' for documents you want to ingest.")
        return

    # Confirm before ingesting
    print(f"\n{'='*70}")
    print(f"Ready to ingest {len(approved_df)} approved documents to Supabase")
    print(f"{'='*70}")

    if not auto_confirm:
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("❌ Ingestion cancelled")
            return
    else:
        print("Auto-confirming ingestion (--yes flag provided)")

    # Process approved documents
    successful = 0
    failed = 0
    skipped_duplicates = 0

    # Check for existing documents to avoid duplicates (by filename only)
    print("\n🔍 Checking for duplicates...")
    existing_docs = supabase.table('knowledge_documents').select('source_file').execute()
    existing_filenames = {doc['source_file'].split('/')[-1] for doc in existing_docs.data}
    print(f"Found {len(existing_filenames)} existing documents in database")

    for idx, row in approved_df.iterrows():
        try:
            pdf_path = row['File_Path']
            document_type = row['Document_Type']

            # Check if this is a manual entry (no PDF file)
            is_manual_entry = (pd.isna(pdf_path) or str(pdf_path).strip() == '' or
                             str(pdf_path) == 'N/A' or str(pdf_path).endswith('.manual'))

            if is_manual_entry:
                # Manual entry - use the synthetic filename from Excel or generate one
                if str(pdf_path).endswith('.manual'):
                    synthetic_filename = pdf_path
                else:
                    vendor_name = row.get('vendor_name', 'Unknown Vendor')
                    synthetic_filename = f"{vendor_name.replace(' ', '_').replace('/', '_').replace('\\', '_')}.manual"

                vendor_name = row.get('vendor_name', 'Unknown Vendor')

                # Check for duplicates by synthetic filename
                if synthetic_filename in existing_filenames:
                    print(f"\n⏭️  Skipping {vendor_name} - already exists in database")
                    skipped_duplicates += 1
                    continue

                print(f"\n{'='*70}")
                print(f"Processing (Manual Entry): {vendor_name}")
                print(f"Type: {document_type}")
                print(f"{'='*70}")

                # For manual entries, use the document summary as the "text"
                full_text = row.get('document_summary', '')
                total_pages = 0
                pdf_path = synthetic_filename  # Use synthetic path for database

            else:
                # PDF-based entry
                if not Path(pdf_path).exists():
                    print(f"❌ File not found: {pdf_path}")
                    failed += 1
                    continue

                # Check if document already exists (by filename)
                filename = Path(pdf_path).name
                if filename in existing_filenames:
                    print(f"\n⏭️  Skipping {filename} - already exists in database")
                    skipped_duplicates += 1
                    continue

                print(f"\n{'='*70}")
                print(f"Processing: {row['File_Name']}")
                print(f"Type: {document_type}")
                print(f"{'='*70}")

                # Extract full text
                print("📄 Extracting full document text...")
                full_text, total_pages = extract_text_from_pdf(pdf_path, max_pages=999)

                if not full_text:
                    print("❌ Could not extract text")
                    failed += 1
                    continue

            print(f"✅ Extracted {len(full_text)} characters from {total_pages} pages")

            # Prepare metadata from Excel (user-edited)
            doc_data = {
                'document_type': document_type,
                'title': row['document_title'],
                'source_file': pdf_path,
                'processing_status': 'processing'
            }

            # Add type-specific metadata
            if document_type == 'tax_law':
                # Helper function to parse comma-separated strings to arrays
                def parse_array(value):
                    if pd.isna(value) or value == '':
                        return []
                    return [x.strip() for x in str(value).split(',') if x.strip()]

                doc_data.update({
                    'citation': row.get('citation', ''),
                    'law_category': row.get('law_category', 'general'),
                    'effective_date': row.get('effective_date') if pd.notna(row.get('effective_date')) else None,
                    'topic_tags': parse_array(row.get('topic_tags', '')),
                    'tax_types': parse_array(row.get('tax_types', '')),
                    'industries': parse_array(row.get('industries', '')),
                    'referenced_statutes': parse_array(row.get('referenced_statutes', ''))
                })
            else:  # vendor
                # Helper function to parse comma-separated strings to arrays
                def parse_array(value):
                    if pd.isna(value) or value == '':
                        return []
                    return [x.strip() for x in str(value).split(',') if x.strip()]

                doc_data.update({
                    'vendor_name': row.get('vendor_name', ''),
                    'vendor_category': row.get('vendor_category', ''),
                    'industry': row.get('industry') if pd.notna(row.get('industry')) else None,
                    'business_model': row.get('business_model') if pd.notna(row.get('business_model')) else None,
                    'primary_products': parse_array(row.get('primary_products', '')),
                    'typical_delivery': row.get('typical_delivery') if pd.notna(row.get('typical_delivery')) else None,
                    'tax_notes': row.get('tax_notes') if pd.notna(row.get('tax_notes')) else None,
                    'confidence_score': float(row.get('confidence_score', 80.0)) if pd.notna(row.get('confidence_score')) else 80.0,
                    'data_source': 'pdf_extraction'
                })

            # Store document in Supabase
            print("💾 Storing document in Supabase...")
            result = supabase.table('knowledge_documents').insert(doc_data).execute()
            document_id = result.data[0]['id']
            print(f"✅ Document stored (ID: {document_id})")

            # Smart chunk text using canonical chunking WITH PAGE NUMBERS
            print("✂️  Chunking text intelligently (with page number tracking)...")
            chunks, total_pages_processed = chunk_document_with_pages(
                pdf_path,
                target_words=800,
                max_words=1500,
                min_words=150
            )

            stats = get_chunking_stats(chunks)
            print(f"✅ Created {len(chunks)} chunks from {total_pages_processed} pages")
            print(f"   Average: {stats['avg_words']:.0f} words, Range: {stats['min_words']}-{stats['max_words']} words")

            # Update total_chunks
            supabase.table('knowledge_documents').update({
                'total_chunks': len(chunks)
            }).eq('id', document_id).execute()

            # Generate embeddings and store chunks
            print("🧠 Generating embeddings and storing chunks...")
            successful_chunks = 0

            chunk_table = 'tax_law_chunks' if document_type == 'tax_law' else 'vendor_background_chunks'

            for chunk in tqdm(chunks, desc="Processing chunks", leave=False):
                try:
                    embedding = generate_embedding(chunk['chunk_text'])

                    if embedding:
                        chunk_data = {
                            "document_id": document_id,
                            "chunk_number": chunk['chunk_index'] + 1,  # 1-indexed
                            "chunk_text": chunk['chunk_text'],
                            "embedding": embedding
                        }

                        # Add type-specific fields
                        if document_type == 'tax_law':
                            # Parse array fields (use same helper function)
                            def parse_array(value):
                                if pd.isna(value) or value == '':
                                    return []
                                return [x.strip() for x in str(value).split(',') if x.strip()]

                            # Combine section_id with page_reference for section_title
                            section_id = chunk.get('section_id', '')
                            page_ref = chunk.get('page_reference', '')
                            combined_section_title = format_section_with_page(section_id, page_ref)

                            chunk_data.update({
                                'citation': row.get('citation', ''),
                                'law_category': row.get('law_category', 'general'),
                                'section_title': combined_section_title,  # Now includes page numbers!
                                'topic_tags': parse_array(row.get('topic_tags', '')),
                                'tax_types': parse_array(row.get('tax_types', '')),
                                'industries': parse_array(row.get('industries', '')),
                                'referenced_statutes': parse_array(row.get('referenced_statutes', ''))
                            })
                        else:  # vendor
                            chunk_data.update({
                                'vendor_name': row.get('vendor_name', ''),
                                'vendor_category': row.get('vendor_category', ''),
                                'document_category': row.get('document_category', 'general')
                            })

                        supabase.table(chunk_table).insert(chunk_data).execute()
                        successful_chunks += 1

                except Exception as e:
                    print(f"⚠️  Failed to process chunk {chunk['chunk_index']}: {e}")
                    continue

            print(f"✅ Stored {successful_chunks}/{len(chunks)} chunks with embeddings")

            # Mark as completed
            supabase.table('knowledge_documents').update({
                'processing_status': 'completed'
            }).eq('id', document_id).execute()

            print(f"✅ Document ingestion complete!\n")

            successful += 1

        except Exception as e:
            print(f"❌ Error ingesting {row['File_Name']}: {e}")
            failed += 1
            continue

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 INGESTION SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Successfully ingested: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped duplicates (already in DB): {skipped_duplicates}")
    print(f"⏭️  Skipped (marked Skip): {len(skipped_df)}")
    print(f"⚠️  Not processed (still in Review): {len(review_df)}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Unified document ingestion for tax law and vendor documents")
    parser.add_argument("--type", choices=['tax_law', 'vendor'], help="Document type (required for --export-metadata)")
    parser.add_argument("--folder", help="Folder containing PDF files")
    parser.add_argument("--export-metadata", help="Export AI metadata to Excel (no ingestion)")
    parser.add_argument("--import-metadata", help="Import edited Excel and ingest to Supabase")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm ingestion without prompting")

    args = parser.parse_args()

    # MODE 1: Export metadata to Excel
    if args.export_metadata:
        if not args.type:
            print("❌ --type required when using --export-metadata")
            print("   Use: --type tax_law or --type vendor")
            return

        if not args.folder:
            print("❌ --folder required when using --export-metadata")
            return

        folder_path = Path(args.folder).expanduser()

        if not folder_path.exists():
            print(f"❌ Folder not found: {folder_path}")
            return

        # Find all PDFs
        pdf_files = list(folder_path.glob("*.pdf"))

        if not pdf_files:
            print(f"❌ No PDF files found in {folder_path}")
            return

        print(f"\n🔍 Found {len(pdf_files)} PDF files")

        export_metadata_to_excel(pdf_files, args.type, args.export_metadata, args.limit)
        return

    # MODE 2: Import metadata from Excel and ingest
    elif args.import_metadata:
        if not Path(args.import_metadata).exists():
            print(f"❌ Excel file not found: {args.import_metadata}")
            return

        import_metadata_from_excel(args.import_metadata, auto_confirm=args.yes)
        return

    else:
        print("❌ Invalid usage. Use one of:")
        print("\n  Step 1 - Export metadata to Excel:")
        print("    python scripts/ingest_documents.py --type tax_law --folder knowledge_base/wa_tax_law --export-metadata outputs/Tax_Metadata.xlsx")
        print("    python scripts/ingest_documents.py --type vendor --folder knowledge_base/vendors --export-metadata outputs/Vendor_Metadata.xlsx")
        print("\n  Step 2 - Import edited Excel:")
        print("    python scripts/ingest_documents.py --import-metadata outputs/Tax_Metadata.xlsx")


if __name__ == "__main__":
    main()
