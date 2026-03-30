"""
Vector Store module using ChromaDB.

Provides semantic search capabilities for knowledge graph entities.
Each entity (pipeline, table, column, Confluence page, etc.) is embedded
as a 384-dimensional vector using all-MiniLM-L6-v2. ChromaDB stores these
vectors and answers cosine-similarity queries at search time.

Storage: in-memory (non-persistent) — rebuilt on every session start.
This is intentional: the KG data is small (~100–200 nodes) and fast to ingest,
so persistence adds complexity without meaningful startup savings.
"""

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    """Vector database for semantic search using ChromaDB."""

    def __init__(self):
        # In-memory ChromaDB client — no disk persistence required for this KG size
        self.client = chromadb.Client(
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                is_persistent=False
            )
        )

        # all-MiniLM-L6-v2: 384-dim, fast, good quality for English domain text.
        # Runs locally via sentence-transformers — no API key required.
        self.embeddingFn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Single collection holds all entity types — entityType stored in metadata
        # for filtering. Using one collection simplifies cross-type queries.
        self.collection = self.client.get_or_create_collection(
            name="sdlc_knowledge",
            embedding_function=self.embeddingFn
        )

    def add(self, docId: str, text: str, metadata: dict) -> None:
        """
        Add a single document to the vector store.

        The text is embedded immediately and stored alongside the metadata.
        Called for short documents (pipelines, tables, columns, KPIs) that
        fit within a single embedding window.

        Args:
            docId:    Unique document identifier — must match the KG node ID
                      so search results can be joined back to the graph.
            text:     Text content to embed (description, name, tags, etc.)
            metadata: Dict stored alongside the vector for filtering/display.
                      Must include "type" key (e.g. "Pipeline") for entity
                      type filtering in the Retriever.
        """
        self.collection.add(
            ids=[docId],
            documents=[text],
            metadatas=[metadata]
        )

    def addChunked(self, docId: str, text: str, metadata: dict) -> None:
        """
        Add a document, splitting into overlapping chunks if it exceeds the chunk size.

        Why chunked ingestion:
            Embedding a long Confluence page as a single vector averages out its
            meaning. A query about "GDPR retention" may not surface a page whose
            summary is about architecture even if it has a GDPR section.
            Chunking ensures each embedding is semantically focused.

        Behaviour for short documents:
            If chunkText() returns a single chunk (text <= CHUNK_SIZE), this
            method behaves identically to add() — no overhead for short content.

        Chunk storage:
            Chunks are stored as <docId>_chunk_0, <docId>_chunk_1, ...
            Each chunk's metadata includes:
                parentId    — the original docId (KG node ID) for resolution
                chunkIndex  — 0-based position within the document
                totalChunks — total number of chunks for this document

        Args:
            docId:    Unique document identifier (becomes the KG node ID / parentId)
            text:     Full document text to embed
            metadata: Metadata dict — copied with parentId added for each chunk
        """
        from rag.chunker import chunkText
        chunks = chunkText(text)

        # Short document — store as-is, no chunk overhead
        if len(chunks) == 1:
            self.add(docId, chunks[0], metadata)
            return

        # Long document — store each chunk with parentId for later resolution
        for i, chunk in enumerate(chunks):
            chunkMeta = {
                **metadata,
                "parentId":    docId,         # resolves chunk → KG node
                "chunkIndex":  str(i),         # ChromaDB metadata must be str/int/float/bool
                "totalChunks": str(len(chunks))
            }
            self.collection.add(
                ids=[f"{docId}_chunk_{i}"],
                documents=[chunk],
                metadatas=[chunkMeta]
            )

    def search(self, query: str, k: int = 5) -> dict:
        """
        Search for similar documents using cosine similarity.

        Returns raw ChromaDB results (ids, distances, metadatas).
        For scored, filtered, and reranked results use rag.retriever.Retriever.

        Args:
            query: Search query text
            k:     Number of results to return (default: 5)

        Returns:
            ChromaDB result dict with keys: ids, distances, documents, metadatas
            (each value is a list-of-lists, one sub-list per query)
        """
        return self.collection.query(
            query_texts=[query],
            n_results=k
        )

    # Alias for backwards compatibility with code that imports embedding_fn
    embedding_fn = property(lambda self: self.embeddingFn)
