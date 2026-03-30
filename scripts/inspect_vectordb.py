"""
Inspect the ChromaDB Vector Store contents at runtime.

Shows:
  1. Total documents stored
  2. All documents with their text, metadata, and embedding vector (first 8 dims)
  3. Filter by entity type
  4. Run a sample similarity search and show distances
  5. Show the raw embedding for any single document

Run:
    python scripts/inspect_vectordb.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph.knowledge_graph import KnowledgeGraph
from rag.vectorstore import VectorStore
from pipeline.bronze_layer import bronze_pipelines, bronze_tables, bronze_columns
from pipeline.silver_layer import silver_pipelines, silver_tables, silver_columns
from pipeline.gold_layer import gold_pipelines, gold_tables, gold_columns
from pipeline.ingestion import ingestAllData
from dictionary.data_dictionary import (
    confluencePages, jiraTickets, alerts, dataQualityRules,
    environments, powerBIDashboards, powerBIKPIs, dataDictionary
)
from utils.formatting import console, colorScore, colorEntityType, printHeader, printSubHeader


def buildStores():
    kg = KnowledgeGraph()
    vectorDb = VectorStore()
    data = {
        'pipelines': bronze_pipelines + silver_pipelines + gold_pipelines,
        'tables': bronze_tables + silver_tables + gold_tables,
        'columns': bronze_columns + silver_columns + gold_columns,
        'confluencePages': confluencePages,
        'jiraTickets': jiraTickets,
        'alerts': alerts,
        'dataQualityRules': dataQualityRules,
        'environments': environments,
        'powerBIDashboards': powerBIDashboards,
        'powerBIKPIs': powerBIKPIs,
        'dataDictionary': dataDictionary
    }
    ingestAllData(kg, vectorDb, data)
    return kg, vectorDb


def showSummary(vectorDb: VectorStore):
    printHeader("VECTOR DB SUMMARY")

    all_docs = vectorDb.collection.get(include=["metadatas"])
    total = len(all_docs["ids"])
    console.print(f"\n  Total documents (embeddings) stored: [bold cyan]{total}[/bold cyan]")
    console.print(f"  Collection name: [dim]{vectorDb.collection.name}[/dim]")
    console.print(f"  Embedding model: [dim]all-MiniLM-L6-v2  (384-dimensional vectors)[/dim]\n")

    # Count documents per entity type
    type_counts = {}
    for meta in all_docs["metadatas"]:
        t = meta.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    console.print("  Breakdown by entity type:")
    for entity_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        console.print(f"    {colorEntityType(entity_type):<30} [bold]{count:>3}[/bold]  [cyan]{bar}[/cyan]")


def showAllDocuments(vectorDb: VectorStore, limit: int = 10):
    printHeader(f"ALL STORED DOCUMENTS (showing first {limit})")

    all_docs = vectorDb.collection.get(include=["documents", "metadatas", "embeddings"])
    ids = all_docs["ids"]
    documents = all_docs["documents"]
    metadatas = all_docs["metadatas"]
    embeddings = all_docs["embeddings"]

    for i, (doc_id, text, meta, vec) in enumerate(zip(ids, documents, metadatas, embeddings)):
        if i >= limit:
            console.print(f"\n  [dim]... and {len(ids) - limit} more. Increase `limit` to see all.[/dim]")
            break
        entity_type = meta.get("type", "N/A")
        console.print(f"\n  [bold cyan][{i+1}][/bold cyan] [dim]ID:[/dim] {doc_id}")
        console.print(f"       [dim]Type    :[/dim] {colorEntityType(entity_type)}")
        console.print(f"       [dim]Text    :[/dim] {text[:100]}{'...' if len(text) > 100 else ''}")
        console.print(f"       [dim]Metadata:[/dim] {meta}")
        vec_preview = [round(v, 4) for v in vec[:8]]
        console.print(f"       [dim]Vector  :[/dim] {vec_preview} [dim]... (384 dims total)[/dim]")


def showByType(vectorDb: VectorStore, entity_type: str):
    printHeader(f"DOCUMENTS OF TYPE: {entity_type}")

    results = vectorDb.collection.get(
        where={"type": entity_type},
        include=["documents", "metadatas", "embeddings"]
    )

    ids = results["ids"]
    if not ids:
        console.print(f"\n  [yellow]No documents found with type='{entity_type}'[/yellow]")
        return

    console.print(f"\n  Found [bold]{len(ids)}[/bold] document(s):\n")
    for doc_id, text, meta, vec in zip(ids, results["documents"], results["metadatas"], results["embeddings"]):
        console.print(f"  [dim]ID      :[/dim] {doc_id}")
        console.print(f"  [dim]Text    :[/dim] {text[:120]}{'...' if len(text) > 120 else ''}")
        vec_preview = [round(v, 4) for v in vec[:6]]
        console.print(f"  [dim]Vector  :[/dim] {vec_preview} [dim]... (384 dims)[/dim]")
        console.print()


def showSimilaritySearch(vectorDb: VectorStore, query: str, k: int = 5):
    printSubHeader(f"SIMILARITY SEARCH: '{query}'")

    results = vectorDb.collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances", "embeddings"]
    )

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    embeddings = results["embeddings"][0]

    console.print(f"\n  Top {k} results (sorted by similarity):\n")
    for rank, (doc_id, text, meta, dist, vec) in enumerate(
        zip(ids, documents, metadatas, distances, embeddings), 1
    ):
        similarity = round((1 - dist / 2) * 100, 1)
        entity_type = meta.get("type", "N/A")
        console.print(f"  [bold cyan][{rank}][/bold cyan] [dim]{doc_id}[/dim]")
        console.print(f"       [dim]Type       :[/dim] {colorEntityType(entity_type)}")
        console.print(f"       [dim]Similarity :[/dim] {colorScore(similarity)}  [dim](cosine distance: {round(dist, 4)})[/dim]")
        console.print(f"       [dim]Text       :[/dim] {text[:100]}{'...' if len(text) > 100 else ''}")
        vec_preview = [round(v, 4) for v in vec[:6]]
        console.print(f"       [dim]Vector     :[/dim] {vec_preview} [dim]...[/dim]")
        console.print()


if __name__ == "__main__":
    console.print("[dim]Loading knowledge graph and building embeddings...[/dim]")
    kg, vectorDb = buildStores()
    console.print("[green]Done.[/green]\n")

    showSummary(vectorDb)
    showAllDocuments(vectorDb, limit=10)
    showByType(vectorDb, "PowerBIKPI")
    showSimilaritySearch(vectorDb, "Which KPIs measure revenue for Reckitt Nutrition?", k=5)
    showSimilaritySearch(vectorDb, "Which dashboards break if a column changes?", k=5)
