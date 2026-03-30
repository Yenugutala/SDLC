"""
Natural Language Query Examples for Data Platform Knowledge Graph.

Demonstrates OpenRouter integration for querying the knowledge graph
using plain English questions with semantic search capabilities.

Run:
    python scripts/query_examples.py
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
    confluencePages, jiraTickets, alerts, dataQualityRules, environments
)
from rag.query_engine import NaturalLanguageQueryEngine, askQuestion
from utils.formatting import printHeader, printSubHeader


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

    from rag.query_engine import askQuestion

    # Simple usage
    answer = askQuestion(kg, vectorDb, "Your question here")

    # Or with the full engine
    queryEngine = NaturalLanguageQueryEngine()
    answer = queryEngine.query(kg, vectorDb, "Your question")

    # With reasoning
    result = queryEngine.queryWithReasoning(kg, vectorDb, "Your question")
    print(result['answer'])
    print(result['reasoning'])

Run scripts/interactive_query.py for an interactive chat interface!
"""


def initializeKnowledgeGraph() -> tuple:
    print("Setting up Knowledge Graph...\n")

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
    return kg, vectorDb


class QueryExecutor:
    def __init__(self, kg: KnowledgeGraph, vectorDb: VectorStore):
        self.kg = kg
        self.vectorDb = vectorDb
        self.engine = NaturalLanguageQueryEngine()

    def executeSimpleQuery(self, question: str) -> None:
        print(f"Question: {question}\n")
        answer = askQuestion(self.kg, self.vectorDb, question)
        print(f"Answer: {answer}")

    def executeStandardQuery(self, question: str) -> None:
        print(f"Question: {question}\n")
        answer = self.engine.query(self.kg, self.vectorDb, question)
        print(f"Answer: {answer}")

    def executeReasoningQuery(self, question: str) -> None:
        print(f"Question: {question}\n")
        result = self.engine.queryWithReasoning(self.kg, self.vectorDb, question)
        print(f"Answer: {result['answer']}\n")
        if result['reasoning']:
            print(f"Reasoning: {result['reasoning']}\n")
        if result['sources']:
            print(f"Sources: {result['sources']}")

    def execute(self, question: str, method: str) -> None:
        methods = {
            "simple": self.executeSimpleQuery,
            "standard": self.executeStandardQuery,
            "reasoning": self.executeReasoningQuery
        }
        methods.get(method, self.executeStandardQuery)(question)


def runExamples() -> None:
    kg, vectorDb = initializeKnowledgeGraph()
    executor = QueryExecutor(kg, vectorDb)

    printHeader("NATURAL LANGUAGE QUERY EXAMPLES")

    for idx, example in enumerate(EXAMPLE_QUERIES, start=1):
        printSubHeader(f"EXAMPLE {idx}: {example['title']}")
        executor.execute(example["question"], example["method"])

    printHeader("QUERY EXAMPLES COMPLETE")
    print(USAGE_GUIDE)


def main() -> None:
    runExamples()


if __name__ == "__main__":
    main()
