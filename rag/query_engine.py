"""Query Engine: Search ChromaDB and use Claude API to generate answers."""

import os
import anthropic
import chromadb


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_DIR = os.path.join(PROJECT_DIR, "chroma_db")

COLLECTIONS = ["data_dictionary", "ontology", "lineage", "code"]


def search_vectorstore(question, top_k=5):
    """Search all ChromaDB collections and return relevant chunks."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    all_results = []

    for collection_name in COLLECTIONS:
        try:
            collection = client.get_collection(collection_name)
            results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                all_results.append({
                    "collection": collection_name,
                    "document": doc,
                    "metadata": metadata,
                })
        except Exception as e:
            print(f"[Query] Warning: Could not search {collection_name}: {e}")

    return all_results


def ask_claude(question, context_chunks):
    """Send question + context to Claude API and return the response."""
    client = anthropic.Anthropic()

    context = "\n\n---\n\n".join(
        f"[{chunk['collection']}] {chunk['document']}" for chunk in context_chunks
    )

    system_prompt = (
        "You are a data analyst assistant for a healthcare data pipeline. "
        "The pipeline has three layers: Bronze (raw ingestion), Silver (obfuscated column names), "
        "and Gold (views with different obfuscated names). "
        "Use the provided context from the data dictionary, ontology, lineage, and code "
        "to answer questions accurately. When referring to obfuscated column names, "
        "always explain what the original/meaningful column name is."
    )

    message = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Context from the data catalog:\n\n{context}\n\n---\n\nQuestion: {question}",
            }
        ],
    )

    return message.content[0].text


def query(question):
    """Full RAG pipeline: search -> retrieve -> generate."""
    print(f"\n[Query] Searching for: {question}")

    # Retrieve relevant context
    context_chunks = search_vectorstore(question)
    if not context_chunks:
        return "No relevant information found in the data catalog."

    print(f"[Query] Found {len(context_chunks)} relevant chunks")

    # Generate answer with Claude
    answer = ask_claude(question, context_chunks)
    return answer


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    else:
        q = "What does col_x1a mean in the silver layer?"
    print(query(q))
