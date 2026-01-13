"""
Natural Language Query Engine using Azure OpenAI.
Allows querying the Data Platform knowledge graph using plain English questions.
"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Dict, Any, List
from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore

# Load environment variables
load_dotenv()


class NaturalLanguageQueryEngine:
    """Query knowledge graph using natural language with Azure OpenAI."""

    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT").split("/openai/deployments")[0]
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")

    # Constants for context building
    _EXCLUDED_PROPERTIES = frozenset({'type', 'name', 'summary', 'title'})
    _NAME_FIELDS = ('name', 'summary', 'title')
    _MAX_SEARCH_RESULTS = 5
    _MAX_RELATIONSHIPS = 3
    _DEFAULT_RELATION = 'RELATED_TO'

    def _getNodeDisplayName(self, nodeData: Dict[str, Any], fallback: str) -> str:
        """Extract display name from node data."""
        for field in self._NAME_FIELDS:
            if value := nodeData.get(field):
                return value
        return fallback

    def _formatNodeProperties(self, nodeData: Dict[str, Any]) -> List[str]:
        """Format node properties for context output."""
        return [
            f"  {key}: {value}"
            for key, value in nodeData.items()
            if key not in self._EXCLUDED_PROPERTIES
        ]

    def _formatRelationship(self, kg: KnowledgeGraph, sourceId: str, targetId: str) -> str:
        """Format a single relationship for context output."""
        edgeData = kg.graph.get_edge_data(sourceId, targetId)
        relation = edgeData.get('relation', self._DEFAULT_RELATION) if edgeData else self._DEFAULT_RELATION

        targetNode = kg.graph.nodes[targetId]
        targetType = targetNode.get('type', 'Unknown')
        targetName = self._getNodeDisplayName(targetNode, targetId)

        return f"    --[{relation}]--> {targetType}: {targetName} (ID: {targetId})"

    def _formatNodeContext(self, kg: KnowledgeGraph, nodeId: str) -> List[str]:
        """Build context lines for a single node."""
        nodeData = kg.graph.nodes[nodeId]
        nodeType = nodeData.get('type', 'Unknown')
        nodeName = self._getNodeDisplayName(nodeData, nodeId)

        lines = [f"- {nodeType}: {nodeName} (ID: {nodeId})"]
        lines.extend(self._formatNodeProperties(nodeData))

        # Add relationships
        successors = list(kg.graph.successors(nodeId))[:self._MAX_RELATIONSHIPS]
        if successors:
            lines.append("  Relationships:")
            lines.extend(
                self._formatRelationship(kg, nodeId, targetId)
                for targetId in successors
            )

        lines.append("")  # Blank line between nodes
        return lines

    def _getKnowledgeGraphContext(self, kg: KnowledgeGraph, vectorDb: VectorStore, query: str) -> str:
        """
        Retrieve relevant context from knowledge graph based on query.

        Args:
            kg: KnowledgeGraph instance
            vectorDb: VectorStore instance for semantic search
            query: User's search query

        Returns:
            Formatted context string for LLM consumption
        """
        searchResults = vectorDb.search(query, k=10)
        validNodeIds = [
            nodeId for nodeId in searchResults['ids'][0][:self._MAX_SEARCH_RESULTS]
            if nodeId in kg.graph.nodes
        ]

        contextLines = ["Knowledge Graph Information:\n"]
        for nodeId in validNodeIds:
            contextLines.extend(self._formatNodeContext(kg, nodeId))

        return "\n".join(contextLines)

    def query(self, kg: KnowledgeGraph, vectorDb: VectorStore, userQuery: str) -> str:
        """
        Query the knowledge graph using natural language.

        Args:
            kg: KnowledgeGraph instance
            vectorDb: VectorStore instance
            userQuery: Natural language question

        Returns:
            AI-generated answer based on knowledge graph data

        Examples:
            query(kg, vectorDb, "What Jira tickets are related to data quality?")
            query(kg, vectorDb, "Which pipelines process patient consent data?")
            query(kg, vectorDb, "Show me all PII columns in the database")
        """
        # Get relevant context from knowledge graph
        context = self._getKnowledgeGraphContext(kg, vectorDb, userQuery)

        # Create prompt for Azure OpenAI
        systemPrompt = """You are a helpful assistant that answers questions about a Data Platform knowledge graph containing:
        - Data Pipelines (ETL jobs from Databricks/Airflow with schedules and owners)
        - Tables (from Unity Catalog with schema, row counts, and descriptions)
        - Columns (with data types, PII flags, and nullability)
        - Confluence Pages (documentation for pipelines and data models)
        - Jira Tickets (tracking work on pipelines and data quality)
        - Alerts (monitoring pipelines and tables for failures/anomalies)
        - Data Quality Rules (validation rules for tables and columns)
        - Environments (dev, staging, production)

        Use the provided knowledge graph information to answer questions accurately.
        If the information isn't available in the context, say so clearly.
        Be concise and specific in your answers.

        When asked "Is X part of this project?" or "Does this project have X?", search for related items and give a clear YES/NO answer with evidence.

        IMPORTANT: When mentioning any entity (Jira tickets, pipelines, tables, etc.), ALWAYS include its ID in your response.
        Format: "Entity Name (ID: entity-id)"
        Example: "DATA-101 (ID: DATA-101)" or "Customer Data Ingestion (ID: pipeline_customer_ingestion)" """

        userPrompt = f"""Context from Knowledge Graph:
        {context}

        User Question: {userQuery}

        Please answer the question based on the knowledge graph information provided above."""

        # Call Azure OpenAI
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": userPrompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content

    def queryWithReasoning(self, kg: KnowledgeGraph, vectorDb: VectorStore, userQuery: str) -> Dict[str, Any]:
        """
        Query with detailed reasoning and sources.

        Returns:
            Dictionary with 'answer', 'reasoning', and 'sources'
        """
        context = self._getKnowledgeGraphContext(kg, vectorDb, userQuery)

        systemPrompt = """You are a data platform knowledge graph analyst. Answer questions and explain your reasoning.
        Provide your response in this format:

        ANSWER: [Your direct answer]

        REASONING: [Explain how you arrived at this answer based on the knowledge graph]

        SOURCES: [List the specific entities/relationships you used]

        IMPORTANT: When mentioning any entity (Jira tickets, pipelines, tables, etc.), ALWAYS include its ID.
        Format: "Entity Name (ID: entity-id)"
        Example: "DATA-101 (ID: DATA-101)" or "Customer Data Ingestion (ID: pipeline_customer_ingestion)" """

        userPrompt = f"""Context from Knowledge Graph:
        {context}

        User Question: {userQuery}"""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": userPrompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        content = response.choices[0].message.content

        # Parse response
        result = {
            'answer': '',
            'reasoning': '',
            'sources': '',
            'fullResponse': content
        }

        if 'ANSWER:' in content:
            parts = content.split('REASONING:')
            result['answer'] = parts[0].replace('ANSWER:', '').strip()

            if len(parts) > 1:
                reasoningParts = parts[1].split('SOURCES:')
                result['reasoning'] = reasoningParts[0].strip()

                if len(reasoningParts) > 1:
                    result['sources'] = reasoningParts[1].strip()
        else:
            result['answer'] = content

        return result


def askQuestion(kg: KnowledgeGraph, vectorDb: VectorStore, question: str) -> str:
    """
    Convenience function to ask a natural language question.

    Args:
        kg: KnowledgeGraph instance
        vectorDb: VectorStore instance
        question: Your question in plain English

    Returns:
        AI-generated answer

    Examples:
        askQuestion(kg, vectorDb, "What pipelines are running daily?")
        askQuestion(kg, vectorDb, "Show me critical data quality rules")
        askQuestion(kg, vectorDb, "Which tables contain PII data?")
    """
    queryEngine = NaturalLanguageQueryEngine()
    return queryEngine.query(kg, vectorDb, question)
