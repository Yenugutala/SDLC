"""
Retriever — semantic search with score filtering, keyword reranking,
and chunk deduplication.

Why not just use raw ChromaDB results?
    ChromaDB returns cosine distances but applies no quality floor — a result
    with 15% similarity looks the same as one with 90%. Without filtering, low-
    quality matches pollute the LLM context and degrade answer quality.

    Additionally, pure vector similarity can miss exact keyword matches that
    are highly relevant (e.g. "col_rn_gd_revenue" matches "revenue" via term
    overlap even if the embedding distance is moderate). Blending vector and
    keyword scores improves precision.

Pipeline:
    1. Vector search   — ChromaDB cosine similarity, wide net (k=20)
    2. Score filter    — drop candidates below MIN_SIMILARITY %
    3. Keyword rerank  — term-overlap score combined with vector score
    4. Deduplicate     — chunk IDs resolved to parent IDs; highest-scoring
                         chunk kept when the same document matches multiple chunks
    5. Return top-N    — sorted by combinedScore descending

Score formula:
    combinedScore = 0.7 × vectorScore + 0.3 × keywordScore

    The 70/30 split favours semantic understanding while giving keyword overlap
    a meaningful boost for exact-match queries (e.g. a pipeline name).

Result format (per item):
    {
        id:            str   — KG node ID (parent, not chunk)
        text:          str   — matched document text
        metadata:      dict
        vectorScore:   float — cosine similarity %  [0–100]
        keywordScore:  float — term-overlap %        [0–100]
        combinedScore: float — weighted combination  [0–100]
    }
"""

import re
from typing import Dict, List, Optional, Any
from rag.vectorstore import VectorStore

# How many candidates to fetch from ChromaDB before filtering/reranking.
# Wider net compensates for the score filter removing low-quality results.
SEARCH_K       = 20

# Number of results passed to the context builder after reranking.
# 8 nodes × ~10 lines each ≈ ~80 lines — fits comfortably in the LLM prompt.
TOP_N          = 8

# Cosine similarity floor. Below 25% the result is essentially noise —
# ChromaDB always returns k results even if none are actually relevant.
MIN_SIMILARITY = 25.0

# Blend weights — must sum to 1.0
VECTOR_WEIGHT  = 0.7    # semantic understanding (embedding cosine similarity)
KEYWORD_WEIGHT = 0.3    # exact term overlap (BM25-style)

# Common English stop words stripped before computing keyword overlap.
# Kept minimal — domain stop words (e.g. "data", "pipeline") are intentionally
# NOT excluded because they carry meaning in this codebase.
_STOP_WORDS = frozenset({
    'the', 'a', 'an', 'is', 'in', 'of', 'to', 'and', 'or', 'for',
    'what', 'which', 'how', 'are', 'do', 'does', 'if', 'on', 'at',
    'this', 'that', 'with', 'from', 'by', 'be', 'as', 'it', 'its',
    'me', 'my', 'we', 'our', 'you', 'your', 'show', 'find', 'get',
    'give', 'tell', 'list',
})


def distanceToSimilarity(distance: float) -> float:
    """
    Convert ChromaDB cosine distance [0, 2] → similarity percentage [0, 100].

    ChromaDB uses the formula: distance = 1 - cosine_similarity
    Cosine similarity ∈ [-1, 1], so distance ∈ [0, 2].
    Mapping back: similarity = (1 - distance/2) × 100

    Examples:
        distance=0.0 → 100% (identical vectors)
        distance=1.0 → 50%  (orthogonal — unrelated)
        distance=2.0 → 0%   (opposite directions)
    """
    return round((1.0 - distance / 2.0) * 100.0, 1)


def keywordScore(query: str, text: str) -> float:
    """
    Term-overlap score: fraction of meaningful query tokens present in the document.

    Why this complements vector search:
        Embedding models encode semantic meaning but can give moderate similarity
        scores to documents that don't literally contain the query terms. Keyword
        overlap rewards exact matches — useful when querying by pipeline ID,
        column name, or Jira ticket key.

    Algorithm:
        1. Tokenise query and document with a simple word regex
        2. Remove stop words and single-character tokens from query
        3. Return |query_tokens ∩ doc_tokens| / |query_tokens|

    Returns 0.0–1.0 (not a percentage — multiply by 100 before blending).
    """
    # Extract meaningful tokens from the query, excluding stop words and noise
    queryTokens = {
        t for t in re.findall(r'\w+', query.lower())
        if t not in _STOP_WORDS and len(t) > 1
    }
    # If every query word was a stop word, skip keyword scoring entirely
    if not queryTokens:
        return 0.0
    docTokens = set(re.findall(r'\w+', text.lower()))
    # Jaccard-like score: overlap / query size (not symmetric — query drives it)
    return len(queryTokens & docTokens) / len(queryTokens)


class Retriever:
    """
    Wraps VectorStore with filtering, reranking, and chunk deduplication.

    Args:
        vectorDb:      Populated VectorStore instance
        topN:          Number of results after reranking (default 8)
        minSimilarity: Minimum cosine similarity % (default 25.0)
    """

    def __init__(self, vectorDb: VectorStore,
                 topN: int = TOP_N,
                 minSimilarity: float = MIN_SIMILARITY):
        self.vectorDb      = vectorDb
        self.topN          = topN
        self.minSimilarity = minSimilarity

    def retrieve(self, query: str,
                 entityType: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search, filter, rerank, deduplicate, and return top-N results.

        Args:
            query:      Natural language query string
            entityType: Optional ChromaDB metadata filter (e.g. "Pipeline").
                        Uses the "type" field set during ingestion. When supplied,
                        ChromaDB pre-filters before returning candidates —
                        cheaper than post-filtering.

        Returns:
            List of result dicts ordered by combinedScore descending.
        """
        # Pass entityType directly to ChromaDB's where clause for efficient pre-filtering
        whereClause = {"type": entityType} if entityType else None

        # Guard: empty collection causes ChromaDB to raise, not return empty
        collectionSize = self.vectorDb.collection.count()
        if collectionSize == 0:
            return []

        # Cap n_results at the actual collection size — ChromaDB errors if n_results > count
        nResults = min(SEARCH_K, collectionSize)

        try:
            raw = self.vectorDb.collection.query(
                query_texts=[query],
                n_results=nResults,
                where=whereClause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            # Any ChromaDB error (e.g. filter returns 0 matches) → return empty
            return []

        # Unpack the nested list — ChromaDB returns one sub-list per query text
        ids       = raw["ids"][0]
        documents = raw["documents"][0]
        metadatas = raw["metadatas"][0]
        distances = raw["distances"][0]

        # seen: parentId → best result so far (deduplication across chunks)
        # Using a dict keyed by parentId ensures that if a Confluence page was split
        # into 3 chunks and 2 of them match, only the highest-scoring chunk is kept.
        seen: Dict[str, Dict[str, Any]] = {}

        for docId, text, meta, dist in zip(ids, documents, metadatas, distances):
            # Convert ChromaDB distance to human-readable similarity percentage
            vScore = distanceToSimilarity(dist)

            # Apply similarity floor — skip anything below the threshold
            if vScore < self.minSimilarity:
                continue

            kScore   = keywordScore(query, text)
            # Blend: 70% vector + 30% keyword (keyword is 0–1, scale to 0–100 first)
            combined = VECTOR_WEIGHT * vScore + KEYWORD_WEIGHT * (kScore * 100.0)

            # Chunks are stored as "conf_rn_001_chunk_2" — resolve back to "conf_rn_001"
            # so the result ID maps to an actual KG node.
            parentId = meta.get("parentId", docId)

            result = {
                "id":            parentId,
                "text":          text,
                "metadata":      meta,
                "vectorScore":   vScore,
                "keywordScore":  round(kScore * 100.0, 1),
                "combinedScore": round(combined, 1),
            }

            # Deduplication: keep only the best chunk per parent document
            if parentId not in seen or combined > seen[parentId]["combinedScore"]:
                seen[parentId] = result

        # Sort by combined score descending and return top-N
        ranked = sorted(seen.values(), key=lambda x: x["combinedScore"], reverse=True)
        return ranked[:self.topN]
