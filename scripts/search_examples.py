"""
Flexible Search Examples for Data Platform Knowledge Graph.

Demonstrates semantic search across all entity types stored in ChromaDB.

Run:
    python scripts/search_examples.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph.knowledge_graph import KnowledgeGraph
from rag.vectorstore import VectorStore
from graph.graph_queries import queryRelationshipsBySearch
from utils.formatting import printHeader, printSubHeader
from pipeline.bronze_layer import bronze_pipelines, bronze_tables, bronze_columns
from pipeline.silver_layer import silver_pipelines, silver_tables, silver_columns
from pipeline.gold_layer import gold_pipelines, gold_tables, gold_columns
from pipeline.ingestion import ingestAllData
from dictionary.data_dictionary import (
    confluencePages, jiraTickets, alerts, dataQualityRules, environments
)


def main():
    print("Setting up Knowledge Graph for search examples...\n")

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
        'environments': environments
    }

    ingestAllData(kg, vectorDb, data)

    printHeader("FLEXIBLE SEARCH EXAMPLES")

    printSubHeader("Example 1: Find Jira tickets about data quality")
    queryRelationshipsBySearch(kg, vectorDb, query="data quality", entityType="Jira", k=3)

    printSubHeader("Example 2: Find pipelines processing payment data")
    queryRelationshipsBySearch(kg, vectorDb, query="payment processing pluggable framework", entityType="Pipeline", k=3)

    printSubHeader("Example 3: Find tables with customer data")
    queryRelationshipsBySearch(kg, vectorDb, query="customer orders transactions", entityType="Table", k=3)

    printSubHeader("Example 4: Find anything related to fraud detection")
    queryRelationshipsBySearch(kg, vectorDb, query="fraud detection ML security", entityType=None, k=5)

    printSubHeader("Example 5: Find Confluence docs about payment framework")
    queryRelationshipsBySearch(kg, vectorDb, query="payment framework architecture integration", entityType="Confluence", k=3)


if __name__ == "__main__":
    main()
