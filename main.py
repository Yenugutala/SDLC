"""
Main entry point for Data Platform Knowledge Graph creation and analysis.

Orchestrates the full pipeline:
    1. Build the KnowledgeGraph (NetworkX DiGraph) and VectorStore (ChromaDB)
    2. Ingest all pipeline, table, column, and cross-system entities
    3. Run all predefined traversal and semantic search queries

Run:
    python main.py
"""

# Pipeline layer data — split by Bronze/Silver/Gold for clarity
from pipeline.bronze_layer import bronze_pipelines, bronze_tables, bronze_columns
from pipeline.silver_layer import silver_pipelines, silver_tables, silver_columns
from pipeline.gold_layer   import gold_pipelines, gold_tables, gold_columns

# Ingestion orchestrator — populates KG + VectorStore from the layer data
from pipeline.ingestion import ingestAllData

# Cross-system metadata: Confluence, Jira, Alerts, DQ Rules, Environments,
# Power BI dashboards/KPIs, and the Data Dictionary ontology
from dictionary.data_dictionary import (
    confluencePages, jiraTickets, alerts, dataQualityRules,
    environments, powerBIDashboards, powerBIKPIs, dataDictionary
)

# Core infrastructure
from graph.knowledge_graph import KnowledgeGraph
from rag.vectorstore import VectorStore

# Query runner — executes all predefined graph traversal and semantic queries
from graph.graph_queries import runAllQueries
from utils.formatting import printHeader


def main():
    """Build and analyse the Data Platform Knowledge Graph."""
    print("Starting Data Platform Knowledge Graph creation...\n")

    # Initialise empty stores — both are in-memory and rebuilt each session
    kg       = KnowledgeGraph()
    vectorDb = VectorStore()

    # Combine layer data for ingestion — pipelines/tables/columns span all three layers
    data = {
        'pipelines': bronze_pipelines + silver_pipelines + gold_pipelines,
        'tables':    bronze_tables    + silver_tables    + gold_tables,
        'columns':   bronze_columns   + silver_columns   + gold_columns,

        # Cross-system entities (not layer-specific)
        'confluencePages':   confluencePages,
        'jiraTickets':       jiraTickets,
        'alerts':            alerts,
        'dataQualityRules':  dataQualityRules,
        'environments':      environments,
        'powerBIDashboards': powerBIDashboards,
        'powerBIKPIs':       powerBIKPIs,
        'dataDictionary':    dataDictionary
    }

    # Populate both KG and VectorStore — ingestion order matters (see ingestion.py)
    ingestAllData(kg, vectorDb, data)

    printHeader("DATA PLATFORM KNOWLEDGE GRAPH SUCCESSFULLY CREATED")

    # Run all predefined traversal queries + semantic search demos
    runAllQueries(kg, vectorDb, data)


if __name__ == "__main__":
    main()
