#!/usr/bin/env python3
"""
Enhanced Chunking with Page Number Tracking

Extracts text page-by-page and maps chunks to original page numbers.
"""

import pdfplumber
from typing import List, Dict, Tuple
from core.chunking import chunk_legal_document


def extract_text_with_page_mapping(pdf_path: str) -> Tuple[str, List[Dict], int]:
    """
    Extract text from PDF while tracking which text came from which page.

    Returns:
        - full_text: All text concatenated
        - page_map: List of {page_num, start_char, end_char, text}
        - total_pages: Total number of pages
    """

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        full_text = ""
        page_map = []

        for i, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()

            if page_text:
                start_char = len(full_text)
                full_text += page_text + "\n\n"
                end_char = len(full_text)

                page_map.append({
                    'page_num': i,
                    'start_char': start_char,
                    'end_char': end_char,
                    'text': page_text
                })

        return full_text, page_map, total_pages


def find_chunk_page_numbers(chunk_text: str, full_text: str, page_map: List[Dict]) -> List[int]:
    """
    Find which page(s) a chunk came from by matching character positions.

    Returns:
        List of page numbers (e.g., [5] or [5, 6] if chunk spans pages)
    """

    # Find where this chunk appears in the full text
    chunk_start = full_text.find(chunk_text)

    if chunk_start == -1:
        return []

    chunk_end = chunk_start + len(chunk_text)

    # Find which pages overlap with this chunk
    pages = []
    for page_info in page_map:
        # Check if chunk overlaps with this page
        if (chunk_start < page_info['end_char'] and
            chunk_end > page_info['start_char']):
            pages.append(page_info['page_num'])

    return pages


def chunk_document_with_pages(
    pdf_path: str,
    target_words: int = 800,
    max_words: int = 1500,
    min_words: int = 150
) -> Tuple[List[Dict], int]:
    """
    Chunk a PDF document and include page numbers for each chunk.

    Returns:
        - chunks: List of chunk dicts with 'page_numbers' field added
        - total_pages: Total pages in document
    """

    # Extract with page tracking
    full_text, page_map, total_pages = extract_text_with_page_mapping(pdf_path)

    # Chunk using canonical chunking
    chunks = chunk_legal_document(
        full_text,
        target_words=target_words,
        max_words=max_words,
        min_words=min_words,
        preserve_sections=True
    )

    # Add page numbers to each chunk
    for chunk in chunks:
        page_nums = find_chunk_page_numbers(chunk['chunk_text'], full_text, page_map)
        chunk['page_numbers'] = page_nums

        # Format page reference for display
        if page_nums:
            if len(page_nums) == 1:
                chunk['page_reference'] = f"Page {page_nums[0]}"
            else:
                chunk['page_reference'] = f"Pages {page_nums[0]}-{page_nums[-1]}"
        else:
            chunk['page_reference'] = ""

    return chunks, total_pages


def format_section_with_page(section_id: str, page_reference: str) -> str:
    """
    Combine section ID and page reference for section_title field.

    Examples:
        format_section_with_page("(401)", "Page 15") → "(401) - Page 15"
        format_section_with_page("", "Page 15") → "Page 15"
        format_section_with_page("(401)", "") → "(401)"
    """

    if section_id and page_reference:
        return f"{section_id} - {page_reference}"
    elif section_id:
        return section_id
    elif page_reference:
        return page_reference
    else:
        return ""


# Test function
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python chunking_with_pages.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print(f"Testing page-aware chunking on: {pdf_path}\n")

    chunks, total_pages = chunk_document_with_pages(pdf_path)

    print(f"Total Pages: {total_pages}")
    print(f"Total Chunks: {len(chunks)}\n")

    # Show first 3 chunks
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"Chunk {i}:")
        print(f"  Section: {chunk.get('section_id', 'N/A')}")
        print(f"  Pages: {chunk.get('page_numbers', [])}")
        print(f"  Page Ref: {chunk.get('page_reference', 'N/A')}")
        print(f"  Combined: {format_section_with_page(chunk.get('section_id', ''), chunk.get('page_reference', ''))}")
        print(f"  Preview: {chunk['chunk_text'][:100]}...")
        print()
