#!/usr/bin/env python3
"""
Canonical Chunking Module
Single source of truth for document chunking across all ingestion scripts

This module provides semantic chunking that preserves legal document structure
while maintaining optimal chunk sizes for RAG retrieval.

Strategy:
1. Preserve numbered sections (1), (2), (3) as semantic boundaries
2. If section > max_words, split by subsections (a), (b), (c)
3. If subsection still too large, split by paragraphs
4. Always include section marker in chunk for context

Usage:
    from core.chunking import chunk_legal_document

    chunks = chunk_legal_document(
        text="Your document text...",
        target_words=800,
        max_words=1500,
        min_words=150
    )

    for chunk in chunks:
        print(f"Chunk {chunk['chunk_index']}: {len(chunk['chunk_text'].split())} words")
"""

import re
from typing import Dict, List, Optional


def chunk_legal_document(
    text: str,
    target_words: int = 800,
    max_words: int = 1500,
    min_words: int = 150,
    preserve_sections: bool = True,
    overlap_words: int = 50,
) -> List[Dict[str, any]]:
    """
    Semantically chunk a legal document while preserving structure.

    This is the canonical chunking function used by all ingestion scripts.

    Args:
        text: Full document text to chunk
        target_words: Target chunk size in words (soft limit)
        max_words: Maximum chunk size before forced split (hard limit)
        min_words: Minimum chunk size (avoid tiny fragments)
        preserve_sections: Whether to preserve legal section boundaries
        overlap_words: Number of words to overlap between chunks (default 50 ~120 tokens)

    Returns:
        List of chunk dictionaries with keys:
        - chunk_text: The text content of the chunk
        - chunk_index: Sequential index (0-based)
        - section_id: Section identifier if detected (e.g., "(1)", "(a)")
        - word_count: Number of words in chunk
        - char_count: Number of characters in chunk
        - has_overlap: True if chunk starts with overlap text from previous chunk

    Example:
        >>> text = "(1) This is section one. (2) This is section two."
        >>> chunks = chunk_legal_document(text, target_words=10, max_words=20)
        >>> len(chunks)
        2
        >>> chunks[0]['section_id']
        '(1)'
    """

    if not text or not text.strip():
        return []

    chunks = []

    if preserve_sections:
        # Use hierarchical semantic chunking
        chunks = _chunk_by_hierarchy(text, target_words, max_words, min_words, overlap_words)
    else:
        # Simple paragraph-based chunking
        chunks = _chunk_by_paragraphs(text, target_words, max_words, min_words, overlap_words)

    # Add metadata to each chunk
    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i
        chunk["word_count"] = len(chunk["chunk_text"].split())
        chunk["char_count"] = len(chunk["chunk_text"])
        chunk["chunk_role"] = classify_chunk_role(chunk["chunk_text"])
        # has_overlap is set by chunking functions, default to False
        if "has_overlap" not in chunk:
            chunk["has_overlap"] = False

    return chunks


def _chunk_by_hierarchy(
    text: str, target_words: int, max_words: int, min_words: int, overlap_words: int = 50
) -> List[Dict[str, str]]:
    """
    Chunk by legal document hierarchy: (1) → (a) → (i) → paragraphs
    """

    chunks = []

    # Level 1: Split by numbered sections (1), (2), (3), etc.
    numbered_sections = _split_by_pattern(text, r"(?:^|\n)(\(\d+\))")

    for section_marker, section_text in numbered_sections:
        word_count = len(section_text.split())

        # If section is reasonable size, keep it whole
        if min_words <= word_count <= max_words:
            chunks.append(
                {
                    "chunk_text": section_text,
                    "section_id": section_marker.strip() if section_marker else "",
                }
            )

        # If section is too large, split by subsections (a), (b), (c)
        elif word_count > max_words:
            subsection_chunks = _split_large_section_by_subsections(
                section_marker, section_text, target_words, max_words, min_words, overlap_words
            )
            chunks.extend(subsection_chunks)

        # If section is too small but not empty, keep it anyway
        # (We'll combine small chunks in post-processing if needed)
        elif word_count > 0:
            chunks.append(
                {
                    "chunk_text": section_text,
                    "section_id": section_marker.strip() if section_marker else "",
                }
            )

    return chunks


def _split_large_section_by_subsections(
    section_marker: str,
    section_text: str,
    target_words: int,
    max_words: int,
    min_words: int,
    overlap_words: int = 50,
) -> List[Dict[str, str]]:
    """
    Split a large section by lettered subsections (a), (b), (c), etc.
    """

    chunks = []

    # Split by lettered subsections
    lettered_subsections = _split_by_pattern(section_text, r"(?:^|\n)(\([a-z]\))")

    current_chunk_text = section_marker + "\n" if section_marker else ""
    current_word_count = len(current_chunk_text.split())
    previous_chunk_words = []  # Track words for overlap

    for subsection_marker, subsection_text in lettered_subsections:
        subsection_words = len(subsection_text.split())

        # If subsection itself is huge, split by paragraphs
        if subsection_words > max_words:
            # Save current chunk if exists
            if current_chunk_text.strip() and current_word_count >= min_words:
                chunks.append(
                    {
                        "chunk_text": current_chunk_text.strip(),
                        "section_id": section_marker.strip() if section_marker else "",
                    }
                )
                previous_chunk_words = current_chunk_text.strip().split()[-overlap_words:]
                current_chunk_text = section_marker + "\n" if section_marker else ""
                current_word_count = len(current_chunk_text.split())

            # Split huge subsection by paragraphs
            para_chunks = _chunk_by_paragraphs(
                subsection_marker + subsection_text, target_words, max_words, min_words, overlap_words
            )

            for para_chunk in para_chunks:
                para_chunk["section_id"] = (
                    section_marker.strip() if section_marker else ""
                )

            chunks.extend(para_chunks)
            # Update previous_chunk_words from last para_chunk
            if para_chunks:
                previous_chunk_words = para_chunks[-1]["chunk_text"].split()[-overlap_words:]

        # Try to add subsection to current chunk
        elif current_word_count + subsection_words <= max_words:
            current_chunk_text += subsection_marker + subsection_text
            current_word_count += subsection_words

        # Current chunk is full, start new one with overlap
        else:
            if current_chunk_text.strip() and current_word_count >= min_words:
                chunks.append(
                    {
                        "chunk_text": current_chunk_text.strip(),
                        "section_id": section_marker.strip() if section_marker else "",
                    }
                )
                previous_chunk_words = current_chunk_text.strip().split()[-overlap_words:]

            # Start new chunk with overlap from previous
            overlap_text = " ".join(previous_chunk_words) if previous_chunk_words else ""
            has_overlap = bool(overlap_text)
            current_chunk_text = (
                (overlap_text + "\n\n" if overlap_text else "") +
                section_marker + "\n" + subsection_marker + subsection_text
            )
            current_word_count = len(current_chunk_text.split())

    # Save final chunk
    if current_chunk_text.strip() and current_word_count >= min_words:
        chunks.append(
            {
                "chunk_text": current_chunk_text.strip(),
                "section_id": section_marker.strip() if section_marker else "",
            }
        )

    return chunks


def _chunk_by_paragraphs(
    text: str, target_words: int, max_words: int, min_words: int, overlap_words: int = 50
) -> List[Dict[str, str]]:
    """
    Simple paragraph-based chunking for documents without clear section structure.
    Includes overlap between chunks to preserve context at boundaries.
    """

    chunks = []
    paragraphs = re.split(r"\n\s*\n+", text)

    current_chunk = ""
    current_word_count = 0
    previous_chunk_words = []  # Track words for overlap

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_words = len(para.split())

        # If single paragraph is huge, split it by sentences
        if para_words > max_words:
            # Save current chunk first
            if current_chunk.strip() and current_word_count >= min_words:
                chunks.append({"chunk_text": current_chunk.strip(), "section_id": "", "has_overlap": bool(previous_chunk_words)})
                previous_chunk_words = current_chunk.strip().split()[-overlap_words:]
                current_chunk = ""
                current_word_count = 0

            # Split huge paragraph by sentences
            sentence_chunks = _split_by_sentences(para, target_words, max_words, overlap_words)
            chunks.extend(sentence_chunks)
            # Update previous_chunk_words from last sentence chunk
            if sentence_chunks:
                previous_chunk_words = sentence_chunks[-1]["chunk_text"].split()[-overlap_words:]

        # Try to add paragraph to current chunk
        elif current_word_count + para_words <= max_words:
            current_chunk += "\n\n" + para if current_chunk else para
            current_word_count += para_words

        # Current chunk is full, start new one with overlap
        else:
            has_overlap = False
            if current_chunk.strip() and current_word_count >= min_words:
                chunks.append({"chunk_text": current_chunk.strip(), "section_id": "", "has_overlap": bool(previous_chunk_words)})
                previous_chunk_words = current_chunk.strip().split()[-overlap_words:]

            # Start new chunk with overlap from previous
            if previous_chunk_words:
                overlap_text = " ".join(previous_chunk_words)
                current_chunk = overlap_text + "\n\n" + para
                has_overlap = True
            else:
                current_chunk = para
            current_word_count = len(current_chunk.split())

    # Save final chunk
    if current_chunk.strip() and current_word_count >= min_words:
        chunks.append({"chunk_text": current_chunk.strip(), "section_id": "", "has_overlap": bool(previous_chunk_words) and len(chunks) > 0})

    return chunks


def _split_by_sentences(
    text: str, target_words: int, max_words: int, overlap_words: int = 50
) -> List[Dict[str, str]]:
    """
    Split text by sentences for very large paragraphs.
    Includes overlap between chunks to preserve context at boundaries.
    """

    chunks = []

    # Common legal abbreviations to preserve
    abbreviations = {
        "RCW",
        "WAC",
        "C",
        "Sec",
        "No",
        "Vol",
        "Ed",
        "Inc",
        "Ltd",
        "Mr",
        "Mrs",
        "Dr",
        "vs",
        "v",
    }

    # Split on sentence endings
    sentence_pattern = r"[.!?]+\s+"
    potential_sentences = re.split(sentence_pattern, text)

    # Reconstruct sentences, merging those that ended with abbreviations
    sentences = []
    i = 0
    while i < len(potential_sentences):
        sentence = potential_sentences[i].strip()

        # Check if this sentence ended with an abbreviation
        words = sentence.split()
        if words and i < len(potential_sentences) - 1:
            last_word = words[-1].rstrip(".")
            # If last word is an abbreviation, merge with next sentence
            if last_word in abbreviations:
                if i + 1 < len(potential_sentences):
                    sentence = sentence + ". " + potential_sentences[i + 1].strip()
                    i += 1  # Skip next sentence since we merged it

        if sentence:
            sentences.append(sentence)
        i += 1

    current_chunk = ""
    current_word_count = 0
    previous_chunk_words = []  # Track words for overlap

    for sentence in sentences:
        sentence_words = len(sentence.split())

        if current_word_count + sentence_words <= max_words:
            current_chunk += " " + sentence if current_chunk else sentence
            current_word_count += sentence_words
        else:
            if current_chunk.strip():
                chunks.append({"chunk_text": current_chunk.strip(), "section_id": "", "has_overlap": bool(previous_chunk_words)})
                previous_chunk_words = current_chunk.strip().split()[-overlap_words:]

            # Start new chunk with overlap from previous
            if previous_chunk_words:
                overlap_text = " ".join(previous_chunk_words)
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence
            current_word_count = len(current_chunk.split())

    # Save final chunk
    if current_chunk.strip():
        chunks.append({"chunk_text": current_chunk.strip(), "section_id": "", "has_overlap": bool(previous_chunk_words) and len(chunks) > 0})

    return chunks


def _split_by_pattern(text: str, pattern: str) -> List[tuple[str, str]]:
    r"""
    Split text by a regex pattern, returning (marker, content) tuples.

    Args:
        text: Text to split
        pattern: Regex pattern to split on (must have capturing group)

    Returns:
        List of (marker, content) tuples

    Example:
        >>> _split_by_pattern("(1) First (2) Second", r'(\(\d+\))')
        [('(1)', ' First '), ('(2)', ' Second')]
    """

    parts = re.split(pattern, text, flags=re.MULTILINE)

    if len(parts) <= 1:
        # No matches found, return whole text
        return [("", text)]

    sections = []

    # parts[0] is text before first match (may be empty)
    if parts[0].strip():
        sections.append(("", parts[0]))

    # Pairs: parts[1] is marker, parts[2] is content, parts[3] is marker, etc.
    for i in range(1, len(parts), 2):
        marker = parts[i] if i < len(parts) else ""
        content = parts[i + 1] if i + 1 < len(parts) else ""

        if marker or content.strip():
            sections.append((marker, content))

    return sections


def get_chunking_stats(chunks: List[Dict]) -> Dict[str, any]:
    """
    Get statistics about a set of chunks.

    Args:
        chunks: List of chunk dictionaries from chunk_legal_document()

    Returns:
        Dictionary with statistics:
        - total_chunks: Number of chunks
        - avg_words: Average words per chunk
        - avg_chars: Average characters per chunk
        - min_words: Minimum words in any chunk
        - max_words: Maximum words in any chunk
        - total_words: Total words across all chunks
    """

    if not chunks:
        return {
            "total_chunks": 0,
            "avg_words": 0,
            "avg_chars": 0,
            "min_words": 0,
            "max_words": 0,
            "total_words": 0,
        }

    word_counts = [chunk["word_count"] for chunk in chunks]
    char_counts = [chunk["char_count"] for chunk in chunks]

    return {
        "total_chunks": len(chunks),
        "avg_words": sum(word_counts) / len(word_counts),
        "avg_chars": sum(char_counts) / len(char_counts),
        "min_words": min(word_counts),
        "max_words": max(word_counts),
        "total_words": sum(word_counts),
    }


def classify_chunk_role(chunk_text: str) -> str:
    """
    Classify a chunk's semantic role based on content patterns.

    Roles:
    - definition: Legal definitions of terms
    - rule: Legal rules and requirements (default)
    - example: Examples and illustrations
    - exception: Exceptions and carve-outs
    - procedure: Procedures and processes

    Args:
        chunk_text: The text content of the chunk

    Returns:
        One of: 'definition', 'rule', 'example', 'exception', 'procedure'
    """
    text = chunk_text.lower()

    # Definitions (highest priority)
    definition_patterns = [
        r'["\']\w+["\']\s+means\b',
        r"for purposes of this",
        r"is defined as",
        r"shall mean",
        r"\bdefinition[s]?\s*:",
    ]
    for pattern in definition_patterns:
        if re.search(pattern, text):
            return "definition"

    # Examples
    example_patterns = [
        r"\bexample\s*\d*\s*[:\.]",
        r"\bfor example\b",
        r"\be\.g\.\b",
        r"\billustration\b",
    ]
    for pattern in example_patterns:
        if re.search(pattern, text):
            return "example"

    # Exceptions
    exception_patterns = [
        r"\bdoes not (apply|include)\b",
        r"\bexcept\s+(that|where|when|as)\b",
        r"\bexempt from\b",
        r"\bexclusion\b",
        r"\bnotwithstanding\b",
        r"\bthis section does not\b",
    ]
    for pattern in exception_patterns:
        if re.search(pattern, text):
            return "exception"

    # Procedures
    procedure_patterns = [
        r"\bmust file\b",
        r"\bwithin\s+\d+\s+(days?|months?|years?)\b",
        r"\bdeadline\b",
        r"\bsubmit\s+(a|an|the)\b",
        r"\brequest\s+(for|a|an)\b",
        r"\bclaim\s+(for|a|an)\b",
        r"\bapplication\s+(for|to)\b",
    ]
    for pattern in procedure_patterns:
        if re.search(pattern, text):
            return "procedure"

    # Default to rule
    return "rule"


if __name__ == "__main__":
    # Self-test
    sample_text = """(1) This is section one. It has some content about regulations.

(a) This is subsection a with more details about the regulations.
(b) This is subsection b with even more information.

(2) This is section two. It discusses different aspects of the law.

(a) Subsection a of section two.
(b) Subsection b of section two.
(c) Subsection c of section two.

(3) This is section three with a very long piece of text that goes on and on and keeps going and doesn't stop because we need to test what happens when a section is too large and needs to be split up into multiple chunks so that each chunk remains at a reasonable size for embedding and retrieval purposes."""

    print("Testing canonical chunking module...")
    print("=" * 80)

    chunks = chunk_legal_document(
        sample_text, target_words=50, max_words=80, min_words=10
    )

    print(f"\nTotal chunks created: {len(chunks)}")
    print("\n" + "=" * 80)

    for chunk in chunks:
        print(f"\nChunk {chunk['chunk_index']}")
        print(f"Section ID: {chunk['section_id']}")
        print(f"Words: {chunk['word_count']}, Chars: {chunk['char_count']}")
        print(f"Preview: {chunk['chunk_text'][:100]}...")

    print("\n" + "=" * 80)
    stats = get_chunking_stats(chunks)
    print("\nChunking Statistics:")
    for key, value in stats.items():
        print(
            f"  {key}: {value:.1f}" if isinstance(value, float) else f"  {key}: {value}"
        )
