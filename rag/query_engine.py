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
        "always explain what the original/meaningful column name is.\n\n"
        "IMPORTANT RULES:\n"
        "1. You have access to column metadata (column names, data types, descriptions, "
        "sample values, null percentages, unique counts) from the data dictionary. "
        "Use this metadata to give accurate answers.\n"
        "2. When the user asks about analysis or dashboards, first identify which columns "
        "in the existing tables COULD be relevant based on their names and metadata. "
        "Clearly state: 'I can see that column X exists in table Y.' "
        "Then explain: 'However, we don't know the exact values it contains. "
        "If it contains [needed info], you can use the following approach... "
        "Otherwise, you would need to populate this information from the source.'\n"
        "3. If the user asks about data or fields that do NOT exist in the pipeline, "
        "clearly state that the data is not available and list what columns/tables ARE available.\n"
        "4. Always be explicit about what you KNOW (column exists, data type, sample values) "
        "vs what you are ASSUMING (the column values contain the needed information).\n"
        "5. When a column might be relevant but its values may not be sufficient, suggest "
        "TWO paths: (a) how to use it IF the values are suitable, and (b) what to do "
        "if the values are not sufficient (e.g., add new columns or get data from source)."
    )

    message = client.messages.create(
        model="claude-3-haiku-20240307",
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
