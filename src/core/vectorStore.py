"""
Vector Store module using ChromaDB.
Provides semantic search capabilities for knowledge graph entities.
"""

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    """Vector database for semantic search using ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client with sentence transformers."""
        self.client = chromadb.Client(
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                is_persistent=False
            )
        )

        self.embeddingFn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name="sdlc_knowledge",
            embedding_function=self.embeddingFn
        )

    def add(self, docId, text, metadata):
        """
        Add a document to the vector store.

        Args:
            docId: Unique document identifier
            text: Text content to embed
            metadata: Metadata dictionary for the document
        """
        self.collection.add(
            ids=[docId],
            documents=[text],
            metadatas=[metadata]
        )

    def search(self, query, k=5):
        """
        Search for similar documents using semantic similarity.

        Args:
            query: Search query text
            k: Number of results to return (default: 5)

        Returns:
            Dictionary containing search results with ids, distances, and metadata
        """
        return self.collection.query(
            query_texts=[query],
            n_results=k
        )

    # Maintain backwards compatibility with snake_case naming
    embedding_fn = property(lambda self: self.embeddingFn)
