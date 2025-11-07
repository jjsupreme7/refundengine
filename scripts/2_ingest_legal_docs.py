"""
High-Level Legal Document Ingestion Pipeline

This script uses cutting-edge AI to:
1. Extract text from PDFs (any format)
2. Use GPT-4 to suggest metadata intelligently
3. Present suggestions to you for confirmation
4. Generate embeddings via OpenAI
5. Store everything in Supabase with pgvector

Usage:
    python scripts/2_ingest_legal_docs.py --folder ~/Desktop/"WA Tax Law" --limit 10

Options:
    --folder: Path to folder containing PDFs
    --limit: Number of documents to process (default: all)
    --auto-approve: Skip manual review (not recommended)
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
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


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


def suggest_metadata_with_ai(pdf_path: str, sample_text: str) -> Dict[str, Any]:
    """
    Use GPT-4 to analyze document and suggest metadata
    """
    filename = Path(pdf_path).name

    prompt = f"""Analyze this Washington State tax law document and extract metadata.

Filename: {filename}

First few pages:
{sample_text[:3000]}

Return JSON with these fields:
{{
  "document_title": "Full descriptive title",
  "source_type": "RCW" | "WAC" | "Determination" | "Case Law" | "Guide",
  "year_issued": 2020,
  "statute_number": "458-20-101",
  "citation": "WAC 458-20-101",
  "topic_tags": ["registration", "licensing"],
  "tax_types": ["sales tax", "use tax"],
  "industries": ["general", "retail"],
  "exemption_categories": ["none" or specific categories],
  "product_types": ["software", "services"],
  "keywords": ["key", "terms"],
  "referenced_statutes": ["RCW 82.04"],
  "document_summary": "1-2 sentence summary"
}}

Be specific and accurate. Extract actual information from the text."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Washington State tax law expert. Extract metadata accurately from legal documents."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        metadata = json.loads(response.choices[0].message.content)
        return metadata

    except Exception as e:
        print(f"❌ AI metadata extraction failed: {e}")
        return {}


def review_and_confirm_metadata(pdf_path: str, suggested_metadata: Dict) -> Dict:
    """
    Show suggested metadata to user and allow editing
    """
    print("\n" + "="*70)
    print(f"📄 Document: {Path(pdf_path).name}")
    print("="*70)
    print("\n🤖 AI Suggested Metadata:")
    print(json.dumps(suggested_metadata, indent=2))
    print("="*70)

    print("\nOptions:")
    print("  [Enter] - Accept as-is")
    print("  [e] - Edit metadata")
    print("  [s] - Skip this document")

    choice = input("\nYour choice: ").strip().lower()

    if choice == 's':
        print("⏭️  Skipping document")
        return None
    elif choice == 'e':
        print("\n📝 Edit mode (press Enter to keep current value)")

        edited = {}
        for key, value in suggested_metadata.items():
            new_value = input(f"{key} [{value}]: ").strip()
            if new_value:
                # Try to parse as list if it looks like a list
                if key in ['topic_tags', 'tax_types', 'industries', 'exemption_categories', 'product_types', 'keywords', 'referenced_statutes']:
                    try:
                        edited[key] = json.loads(new_value)
                    except:
                        edited[key] = [x.strip() for x in new_value.split(',')]
                else:
                    edited[key] = new_value
            else:
                edited[key] = value

        return edited
    else:
        print("✅ Metadata accepted")
        return suggested_metadata


def split_by_sections(text: str) -> List[tuple[str, str]]:
    """
    Split legal document by sections, preserving section identifiers
    Returns list of (section_identifier, section_text) tuples
    """
    # Patterns for legal section markers
    patterns = [
        # RCW/WAC style: "82.08.0259" or "458-20-101"
        r'(?:^|\n)(\d+[-\.]\d+[-\.]\d+[A-Za-z]?)\s*[:\.\s]',
        # Section headings: "Section 1.", "SEC. 2."
        r'(?:^|\n)((?:Section|SEC\.|Sec\.)\s+\d+[A-Za-z]?)\s*[\.\:]',
        # Subsection numbering: "(1)", "(2)", "(a)", "(b)"
        r'(?:^|\n)(\(\d+\)|\([a-z]\)|\([ivx]+\))\s+',
        # Numbered headings: "1.1", "2.3.4"
        r'(?:^|\n)(\d+(?:\.\d+)*)\s+[A-Z]',
    ]
    
    sections = []
    combined_pattern = '|'.join(patterns)
    
    # Find all section markers
    matches = list(re.finditer(combined_pattern, text, re.MULTILINE))
    
    if not matches:
        # No sections found, return whole text
        return [("", text)]
    
    # Extract sections between markers
    for i, match in enumerate(matches):
        section_id = match.group(0).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        sections.append((section_id, section_text))
    
    return sections


def split_by_paragraphs(text: str) -> List[str]:
    """
    Split text by paragraphs (double newlines or single newlines with clear breaks)
    """
    # Split on double newlines or newline followed by significant whitespace
    paragraphs = re.split(r'\n\s*\n+|\n(?=\s{4,})', text)
    
    # Clean and filter empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs


def split_by_sentences(text: str) -> List[str]:
    """
    Split text by sentences using basic sentence boundary detection
    """
    # Basic sentence splitting (handles common legal abbreviations)
    # Negative lookbehind for common abbreviations
    sentence_pattern = r'(?<!\bRCW|\bWAC|\bCf|\bSec|\bNo|\bVol|\bEd|\bInc|\bLtd|\bMr|\bMrs|\bDr|\bvs|\bv)[.!?]+\s+'
    sentences = re.split(sentence_pattern, text)
    
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def smart_chunk_legal_document(text: str, max_chunk_words: int = 1500, min_chunk_words: int = 100) -> List[Dict]:
    """
    Intelligently chunk legal documents preserving hierarchical structure
    
    Strategy:
    1. Try to identify and preserve sections
    2. If section too large, split by paragraphs
    3. If paragraph too large, split by sentences and recombine
    4. Always preserve semantic units when possible
    
    Returns list of {chunk_text, chunk_index, section_id}
    """
    chunks = []
    chunk_index = 0
    
    # Step 1: Try to split by sections
    sections = split_by_sections(text)
    
    for section_id, section_text in sections:
        word_count = len(section_text.split())
        
        # If section is reasonably sized, keep it whole
        if min_chunk_words <= word_count <= max_chunk_words:
            chunks.append({
                'chunk_text': section_text,
                'chunk_index': chunk_index,
                'section_id': section_id
            })
            chunk_index += 1
        
        # If section is too large, split by paragraphs
        elif word_count > max_chunk_words:
            paragraphs = split_by_paragraphs(section_text)
            
            # Try to combine small paragraphs into reasonable chunks
            current_chunk = []
            current_word_count = 0
            
            for para in paragraphs:
                para_words = len(para.split())
                
                # If single paragraph is too large, split by sentences
                if para_words > max_chunk_words:
                    # Save current chunk if exists
                    if current_chunk:
                        chunks.append({
                            'chunk_text': '\n\n'.join(current_chunk),
                            'chunk_index': chunk_index,
                            'section_id': section_id
                        })
                        chunk_index += 1
                        current_chunk = []
                        current_word_count = 0
                    
                    # Split large paragraph by sentences
                    sentences = split_by_sentences(para)
                    sent_chunk = []
                    sent_word_count = 0
                    
                    for sent in sentences:
                        sent_words = len(sent.split())
                        
                        if sent_word_count + sent_words > max_chunk_words and sent_chunk:
                            chunks.append({
                                'chunk_text': ' '.join(sent_chunk),
                                'chunk_index': chunk_index,
                                'section_id': section_id
                            })
                            chunk_index += 1
                            sent_chunk = [sent]
                            sent_word_count = sent_words
                        else:
                            sent_chunk.append(sent)
                            sent_word_count += sent_words
                    
                    # Save remaining sentences
                    if sent_chunk:
                        chunks.append({
                            'chunk_text': ' '.join(sent_chunk),
                            'chunk_index': chunk_index,
                            'section_id': section_id
                        })
                        chunk_index += 1
                
                # Try to combine paragraph with current chunk
                elif current_word_count + para_words <= max_chunk_words:
                    current_chunk.append(para)
                    current_word_count += para_words
                
                # Current chunk is full, save it and start new one
                else:
                    if current_chunk:
                        chunks.append({
                            'chunk_text': '\n\n'.join(current_chunk),
                            'chunk_index': chunk_index,
                            'section_id': section_id
                        })
                        chunk_index += 1
                    current_chunk = [para]
                    current_word_count = para_words
            
            # Save any remaining content
            if current_chunk:
                chunks.append({
                    'chunk_text': '\n\n'.join(current_chunk),
                    'chunk_index': chunk_index,
                    'section_id': section_id
                })
                chunk_index += 1
        
        # If section is too small, try to combine with next (handled in next iteration)
        else:
            # For now, just include small sections as-is
            # Could optimize later to combine tiny sections
            chunks.append({
                'chunk_text': section_text,
                'chunk_index': chunk_index,
                'section_id': section_id
            })
            chunk_index += 1
    
    return chunks


def generate_embedding(text: str) -> List[float]:
    """
    Generate OpenAI embedding for text
    """
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text[:8000]  # Limit to 8k chars
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None


def ingest_document(pdf_path: str, auto_approve: bool = False):
    """
    Complete ingestion pipeline for one document
    """
    print(f"\n{'='*70}")
    print(f"Processing: {Path(pdf_path).name}")
    print(f"{'='*70}")

    # Step 1: Extract text
    print("📖 Extracting text from PDF...")
    sample_text, total_pages = extract_text_from_pdf(pdf_path, max_pages=3)

    if not sample_text:
        print("❌ Could not extract text from PDF")
        return False

    print(f"✅ Extracted {len(sample_text)} characters from {total_pages} pages")

    # Step 2: AI metadata suggestion
    print("🤖 Analyzing document with AI...")
    suggested_metadata = suggest_metadata_with_ai(pdf_path, sample_text)

    if not suggested_metadata:
        print("❌ Could not generate metadata")
        return False

    # Step 3: Human review
    if not auto_approve:
        confirmed_metadata = review_and_confirm_metadata(pdf_path, suggested_metadata)
        if confirmed_metadata is None:
            return False
    else:
        confirmed_metadata = suggested_metadata
        print("✅ Auto-approved metadata")

    # Step 4: Extract full text
    print("📄 Extracting full document text...")
    full_text, _ = extract_text_from_pdf(pdf_path, max_pages=999)

    # Step 5: Store document in Supabase
    print("💾 Storing document in Supabase...")
    try:
        doc_data = {
            "document_title": confirmed_metadata.get("document_title"),
            "file_path": str(pdf_path),
            "source_type": confirmed_metadata.get("source_type"),
            "citation": confirmed_metadata.get("citation"),
            "statute_number": confirmed_metadata.get("statute_number"),
            "year_issued": confirmed_metadata.get("year_issued"),
            "document_type": confirmed_metadata.get("source_type"),
            "raw_extracted_text": full_text,
            "file_format": "PDF",
            "file_size_bytes": Path(pdf_path).stat().st_size,
            "is_current": True
        }

        result = supabase.table('legal_documents').insert(doc_data).execute()
        document_id = result.data[0]['id']
        print(f"✅ Document stored (ID: {document_id})")

    except Exception as e:
        print(f"❌ Failed to store document: {e}")
        return False

    # Step 6: Store metadata
    print("📋 Storing metadata...")
    try:
        metadata_data = {
            "document_id": document_id,
            "topic_tags": confirmed_metadata.get("topic_tags", []),
            "industries": confirmed_metadata.get("industries", []),
            "tax_types": confirmed_metadata.get("tax_types", []),
            "exemption_categories": confirmed_metadata.get("exemption_categories", []),
            "product_types": confirmed_metadata.get("product_types", []),
            "keywords": confirmed_metadata.get("keywords", []),
            "referenced_statutes": confirmed_metadata.get("referenced_statutes", []),
            "key_concepts": [confirmed_metadata.get("document_summary", "")]
        }

        supabase.table('document_metadata').insert(metadata_data).execute()
        print("✅ Metadata stored")

    except Exception as e:
        print(f"❌ Failed to store metadata: {e}")

    # Step 7: Smart chunk text (preserving sections/paragraphs)
    print("✂️  Chunking text intelligently...")
    chunks = smart_chunk_legal_document(full_text, max_chunk_words=1500, min_chunk_words=100)
    print(f"✅ Created {len(chunks)} chunks (preserving document structure)")

    # Step 8: Generate embeddings and store chunks
    print("🧠 Generating embeddings and storing chunks...")
    successful_chunks = 0

    for chunk in tqdm(chunks, desc="Processing chunks"):
        try:
            # Generate embedding
            embedding = generate_embedding(chunk['chunk_text'])

            if embedding:
                # Store chunk with embedding
                chunk_data = {
                    "document_id": document_id,
                    "chunk_index": chunk['chunk_index'],
                    "chunk_text": chunk['chunk_text'],
                    "embedding": embedding,
                    "section_heading": chunk.get('section_id', '')  # Store section ID for better citations
                }

                supabase.table('document_chunks').insert(chunk_data).execute()
                successful_chunks += 1

        except Exception as e:
            print(f"⚠️  Failed to process chunk {chunk['chunk_index']}: {e}")
            continue

    print(f"✅ Stored {successful_chunks}/{len(chunks)} chunks with embeddings")

    print(f"\n{'='*70}")
    print(f"✅ Document ingestion complete!")
    print(f"{'='*70}\n")

    return True


def main():
    parser = argparse.ArgumentParser(description="Ingest legal documents into Supabase")
    parser.add_argument("--folder", required=True, help="Folder containing PDF files")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents")
    parser.add_argument("--auto-approve", action="store_true", help="Skip manual review")

    args = parser.parse_args()

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

    if args.limit:
        pdf_files = pdf_files[:args.limit]
        print(f"📊 Processing first {args.limit} files")

    # Process each PDF
    successful = 0
    failed = 0

    for pdf_path in pdf_files:
        try:
            if ingest_document(str(pdf_path), args.auto_approve):
                successful += 1
            else:
                failed += 1
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            failed += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 INGESTION SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total processed: {successful + failed}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
