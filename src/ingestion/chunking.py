"""
chunking.py

Splits document text into overlapping chunks suitable for indexing.
Chunks are the unit of retrieval in the Azure AI Search index.
"""

from typing import List
import re


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    min_chunk_size: int = 50
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The source text to chunk.
        chunk_size: Target number of words per chunk.
        chunk_overlap: Number of words to overlap between consecutive chunks.
        min_chunk_size: Minimum words required to create a chunk (discard smaller fragments).

    Returns:
        List of text chunks.
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text.strip())

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]

        if len(chunk_words) >= min_chunk_size:
            chunks.append(" ".join(chunk_words))

        # Move forward by (chunk_size - chunk_overlap) to create overlapping windows
        advance = max(1, chunk_size - chunk_overlap)
        start += advance

        # If we're near the end and the remaining content is small,
        # include it in the last chunk instead of creating a tiny orphan chunk
        if start < len(words) and (len(words) - start) < min_chunk_size:
            # Append remaining words to the last chunk if possible
            if chunks:
                remaining = " ".join(words[start:])
                chunks[-1] = chunks[-1] + " " + remaining
            break

    return chunks


def chunk_pages(
    pages: List[str],
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[dict]:
    """
    Chunk a list of pages (one string per page) into indexed chunks.

    Args:
        pages: List of page text strings (index = page number, 0-based).
        chunk_size: Target words per chunk.
        chunk_overlap: Overlap words between chunks.

    Returns:
        List of dicts with 'text', 'page', and 'chunkIndex' keys.
    """
    results = []
    chunk_index = 0

    for page_num, page_text in enumerate(pages, start=1):
        page_chunks = chunk_text(page_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for chunk in page_chunks:
            results.append({
                "text": chunk,
                "page": page_num,
                "chunkIndex": chunk_index
            })
            chunk_index += 1

    return results
