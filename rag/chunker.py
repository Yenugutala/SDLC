"""
Text chunker for long documents.

Used at ingestion time to split Confluence pages and Jira descriptions
into overlapping chunks for better semantic search recall.

Why chunking matters:
    Embedding a 3,000-character Confluence page as a single vector averages out
    its meaning — specific sections become hard to retrieve. Splitting into smaller
    overlapping chunks means each embedding is semantically focused, so a targeted
    query like "GDPR data retention" can surface the right paragraph even if the
    rest of the page is about architecture.

Chunk IDs: <docId>_chunk_<n>
Each chunk's metadata includes parentId so retrieved chunks can be
resolved back to their KG node ID.
"""

from typing import List

# ~256 tokens at 5 chars/token — fits comfortably in all-MiniLM-L6-v2's 512-token window
CHUNK_SIZE = 1280
# ~32-token overlap — ensures context is not lost at chunk boundaries
OVERLAP    = 160
# Discard trailing chunks shorter than this — they are likely noise/whitespace
MIN_CHARS  = 80


def chunkText(text: str, chunkSize: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks, preferring sentence boundaries.

    Returns a single-element list unchanged if text fits within one chunk.
    This makes the function a no-op for short documents (pipelines, tables,
    columns) without any branching logic in the caller.

    Args:
        text:      Input text to split
        chunkSize: Maximum characters per chunk
        overlap:   Character overlap between consecutive chunks — preserves
                   context across the boundary so retrieval doesn't miss
                   sentences that straddle a split point

    Returns:
        List of chunk strings (at least one element)
    """
    # Short documents fit in a single embedding — no splitting needed
    if len(text) <= chunkSize:
        return [text]

    chunks = []
    start  = 0

    while start < len(text):
        end   = start + chunkSize
        chunk = text[start:end]

        # Try to break at a natural boundary rather than mid-word or mid-sentence.
        # Priority: sentence end ". " > paragraph break "\n\n" > line break "\n" > word space " "
        # Only accept a boundary if it's past the halfway point — prevents very small chunks.
        if end < len(text):
            for sep in ('. ', '.\n', '\n\n', '\n', ' '):
                pos = chunk.rfind(sep)
                if pos > chunkSize // 2:
                    chunk = chunk[:pos + len(sep)]
                    break

        stripped = chunk.strip()
        if len(stripped) >= MIN_CHARS:
            chunks.append(stripped)

        # Advance by chunk length minus overlap so consecutive chunks share a window
        advance = len(chunk) - overlap
        if advance <= 0:
            # Safety valve: if somehow chunk is shorter than overlap, skip forward by
            # chunkSize to avoid an infinite loop
            advance = chunkSize
        start += advance

    # Guard: if all chunks were filtered out (e.g. text is all whitespace), return original
    return chunks or [text]
