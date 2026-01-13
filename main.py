"""
Main entry point for Data Platform Knowledge Graph creation and analysis.
"""

from src.data.mockData import (
    pipelines, tables, columns, confluencePages,
    jiraTickets, alerts, dataQualityRules, environments
)
from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore
from src.data.dataIngestion import ingestAllData
from src.queries.queryEngine import runAllQueries
from src.utils.formatting import printHeader


def main():
    """Main function to create and analyze the knowledge graph."""
    print("Starting Data Platform Knowledge Graph creation...\n")

    # Initialize graph and vector store
    kg = KnowledgeGraph()
    vectorDb = VectorStore()

    # Prepare all data
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

    # Ingest all data into the knowledge graph and vector store
    ingestAllData(kg, vectorDb, data)

    printHeader("DATA PLATFORM KNOWLEDGE GRAPH SUCCESSFULLY CREATED")

    # Run all queries and analysis
    runAllQueries(kg, vectorDb, data)


if __name__ == "__main__":
    main()
