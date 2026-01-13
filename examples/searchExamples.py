"""
Example script demonstrating flexible search capabilities.
Shows how to query anything stored in the vector database without modifying code.

To perform your own searches, use:

from queries import queryRelationshipsBySearch

queryRelationshipsBySearch(
    kg, vectorDb,
    query="your search query here",
    entityType="Jira",  # or None for all types
    k=5  # number of results
)

Available entity types:
- Jira           : Jira tickets
- Pipeline       : Data pipelines
- Table          : Database tables
- Column         : Table columns
- Confluence     : Confluence documentation
- DataQualityRule: Data quality rules
- Alert          : Alert configurations
- Environment    : Environments
- None           : Search across all types

The search will:
1. Find entities matching your query using semantic search
2. Filter by entity type if specified
3. Show the entity details and all its relationships in the graph
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore
from src.queries.queryEngine import queryRelationshipsBySearch
from src.utils.formatting import printHeader, printSubHeader
from src.data.mockData import (
    pipelines, tables, columns, confluencePages,
    jiraTickets, alerts, dataQualityRules, environments
)
from src.data.dataIngestion import ingestAllData


def main():
    """Demonstrate flexible search capabilities."""
    print("Setting up Knowledge Graph for search examples...\n")

    # Initialize and populate
    kg = KnowledgeGraph()
    vectorDb = VectorStore()

    data = {
        'pipelines': pipelines,
        'tables': tables,
        'columns': columns,
        'confluencePages': confluencePages,
        'jiraTickets': jiraTickets,
        'alerts': alerts,
        'dataQualityRules': dataQualityRules,
        'environments': environments
    }

    ingestAllData(kg, vectorDb, data)

    printHeader("FLEXIBLE SEARCH EXAMPLES")

    # Example 1: Find Jira tickets about data quality
    printSubHeader("Example 1: Find Jira tickets about data quality")
    queryRelationshipsBySearch(
        kg, vectorDb,
        query="data quality",
        entityType="Jira",
        k=3
    )

    # Example 2: Find pipelines related to payment processing
    printSubHeader("Example 2: Find pipelines processing payment data")
    queryRelationshipsBySearch(
        kg, vectorDb,
        query="payment processing pluggable framework",
        entityType="Pipeline",
        k=3
    )

    # Example 3: Find tables with customer data
    printSubHeader("Example 3: Find tables with customer data")
    queryRelationshipsBySearch(
        kg, vectorDb,
        query="customer orders transactions",
        entityType="Table",
        k=3
    )

    # Example 4: Find anything related to fraud detection
    printSubHeader("Example 4: Find anything related to fraud detection")
    queryRelationshipsBySearch(
        kg, vectorDb,
        query="fraud detection ML security",
        entityType=None,  # Search all types
        k=5
    )

    # Example 5: Find Confluence documentation
    printSubHeader("Example 5: Find Confluence docs about payment framework")
    queryRelationshipsBySearch(
        kg, vectorDb,
        query="payment framework architecture integration",
        entityType="Confluence",
        k=3
    )


if __name__ == "__main__":
    main()
