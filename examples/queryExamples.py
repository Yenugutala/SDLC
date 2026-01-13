"""
Natural Language Query Examples for Data Platform Knowledge Graph.

Demonstrates Azure OpenAI integration for querying the knowledge graph
using plain English questions with semantic search capabilities.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore
from src.data.mockData import (
    pipelines, tables, columns, confluencePages,
    jiraTickets, alerts, dataQualityRules, environments
)
from src.data.dataIngestion import ingestAllData
from src.queries.naturalLanguageQuery import NaturalLanguageQueryEngine, askQuestion
from src.utils.formatting import printHeader, printSubHeader


# =============================================================================
# Configuration
# =============================================================================

EXAMPLE_QUERIES = [
    {
        "title": "Simple Question",
        "question": "What Jira tickets are related to data quality?",
        "method": "simple"
    },
    {
        "title": "Pipeline Information",
        "question": "Which pipelines process payment transactions?",
        "method": "standard"
    },
    {
        "title": "PII Data Discovery",
        "question": "Show me all columns that contain PII data",
        "method": "standard"
    },
    {
        "title": "Data Quality Rules",
        "question": "What are the critical data quality rules?",
        "method": "standard"
    },
    {
        "title": "Feature Existence Check",
        "question": "Is payment pluggable framework part of this project?",
        "method": "reasoning"
    },
    {
        "title": "Complex Relationship Query",
        "question": "What is the relationship between Jira tickets and Confluence documentation for the payment pipeline?",
        "method": "standard"
    }
]

USAGE_GUIDE = """
To use natural language queries in your own code:

    from src.queries.naturalLanguageQuery import askQuestion

    # Simple usage
    answer = askQuestion(kg, vectorDb, "Your question here")

    # Or with the full engine
    queryEngine = NaturalLanguageQueryEngine()
    answer = queryEngine.query(kg, vectorDb, "Your question")

    # With reasoning
    result = queryEngine.queryWithReasoning(kg, vectorDb, "Your question")
    print(result['answer'])
    print(result['reasoning'])

Run interactiveQuery.py for an interactive chat interface!
"""


# =============================================================================
# Knowledge Graph Setup
# =============================================================================

def initializeKnowledgeGraph() -> tuple[KnowledgeGraph, VectorStore]:
    """
    Initialize and populate the knowledge graph with mock data.

    Returns:
        Tuple of (KnowledgeGraph, VectorStore) instances
    """
    print("Setting up Knowledge Graph...\n")

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
    return kg, vectorDb


# =============================================================================
# Query Execution
# =============================================================================

class QueryExecutor:
    """Executes different types of natural language queries."""

    def __init__(self, kg: KnowledgeGraph, vectorDb: VectorStore):
        self.kg = kg
        self.vectorDb = vectorDb
        self.engine = NaturalLanguageQueryEngine()

    def executeSimpleQuery(self, question: str) -> None:
        """Execute a simple query using the askQuestion helper."""
        print(f"Question: {question}\n")
        answer = askQuestion(self.kg, self.vectorDb, question)
        print(f"Answer: {answer}")

    def executeStandardQuery(self, question: str) -> None:
        """Execute a standard query using the query engine."""
        print(f"Question: {question}\n")
        answer = self.engine.query(self.kg, self.vectorDb, question)
        print(f"Answer: {answer}")

    def executeReasoningQuery(self, question: str) -> None:
        """Execute a query with detailed reasoning and sources."""
        print(f"Question: {question}\n")
        result = self.engine.queryWithReasoning(self.kg, self.vectorDb, question)

        print(f"Answer: {result['answer']}\n")

        if result['reasoning']:
            print(f"Reasoning: {result['reasoning']}\n")

        if result['sources']:
            print(f"Sources: {result['sources']}")

    def execute(self, question: str, method: str) -> None:
        """Execute a query using the specified method."""
        methods = {
            "simple": self.executeSimpleQuery,
            "standard": self.executeStandardQuery,
            "reasoning": self.executeReasoningQuery
        }

        handler = methods.get(method, self.executeStandardQuery)
        handler(question)


# =============================================================================
# Main Execution
# =============================================================================

def runExamples() -> None:
    """Run all example queries demonstrating different capabilities."""
    kg, vectorDb = initializeKnowledgeGraph()
    executor = QueryExecutor(kg, vectorDb)

    printHeader("NATURAL LANGUAGE QUERY EXAMPLES")

    for idx, example in enumerate(EXAMPLE_QUERIES, start=1):
        printSubHeader(f"EXAMPLE {idx}: {example['title']}")
        executor.execute(example["question"], example["method"])

    printHeader("QUERY EXAMPLES COMPLETE")
    print(USAGE_GUIDE)


def main() -> None:
    """Entry point for the query examples demonstration."""
    runExamples()


if __name__ == "__main__":
    main()
