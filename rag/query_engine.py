"""
Natural Language Query Engine using OpenRouter API.

Allows querying the Data Platform knowledge graph using plain English questions.
OpenRouter provides access to multiple LLMs via an OpenAI-compatible API.

RAG pipeline (Retrieval-Augmented Generation):
    1. Cache check     — return immediately if this query was answered before
    2. Retriever       — vector search → cosine score filter → keyword rerank
    3. KG expansion    — for each retrieved node, expand 1-hop relationships
                         from the NetworkX graph (predecessors + successors)
    4. Context assembly — format nodes + relationships into a structured prompt
    5. LLM generation  — send context + question to OpenRouter (gpt-4o-mini)
    6. Cache store     — persist answer for the session lifetime

Why RAG instead of fine-tuning?
    The KG data changes frequently (new pipelines, tickets, columns). RAG keeps
    the knowledge separate from the model weights — updating the KG automatically
    updates the answers without retraining.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any, List

from graph.knowledge_graph import KnowledgeGraph
from rag.vectorstore import VectorStore
from rag.retriever import Retriever
from rag.cache import QueryCache

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# gpt-4o-mini: cost-effective, fast, good at structured context reasoning.
# Override via OPENROUTER_MODEL env var to use a more capable model.
DEFAULT_MODEL       = "openai/gpt-4o-mini"


class NaturalLanguageQueryEngine:
    """
    Query the knowledge graph using natural language via OpenRouter API.

    Each instance maintains its own session cache — identical queries within
    the same session (e.g. interactive_query.py session) skip the LLM call.
    """

    # Node properties that are redundant in the prompt (already shown as the node header)
    _EXCLUDED_PROPERTIES = frozenset({'type', 'name', 'summary', 'title', 'term'})
    # Ordered preference for the node's display name
    _NAME_FIELDS         = ('name', 'summary', 'title', 'term')
    # Cap relationships per node to keep prompt size manageable
    _MAX_RELATIONSHIPS   = 5
    _DEFAULT_RELATION    = 'RELATED_TO'

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env file")

        # OpenAI-compatible client pointed at OpenRouter's gateway
        self.client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
        self.model  = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        # Session cache — keyed by normalised query string + method prefix
        self._cache = QueryCache()

    # ─────────────────────────────────────────────────────────────────────────
    # Node formatting helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _getNodeDisplayName(self, nodeData: Dict[str, Any], fallback: str) -> str:
        """Try each name field in priority order; fall back to the node ID."""
        for field in self._NAME_FIELDS:
            if value := nodeData.get(field):
                return value
        return fallback

    def _formatNodeProperties(self, nodeData: Dict[str, Any]) -> List[str]:
        """Return non-trivial properties as indented key: value lines."""
        return [
            f"  {key}: {value}"
            for key, value in nodeData.items()
            # Skip fields already shown in the header, and skip empty values
            if key not in self._EXCLUDED_PROPERTIES and value not in (None, "", [])
        ]

    def _formatRelationship(self, kg: KnowledgeGraph, sourceId: str, targetId: str) -> str:
        """Format one outgoing edge as an arrow string for the LLM context."""
        edgeData   = kg.graph.get_edge_data(sourceId, targetId)
        relation   = edgeData.get('relation', self._DEFAULT_RELATION) if edgeData else self._DEFAULT_RELATION
        targetNode = kg.graph.nodes[targetId]
        targetType = targetNode.get('type', 'Unknown')
        targetName = self._getNodeDisplayName(targetNode, targetId)
        return f"    --[{relation}]--> {targetType}: {targetName} (ID: {targetId})"

    def _formatNodeContext(self, kg: KnowledgeGraph, nodeId: str,
                           vectorScore: float, combinedScore: float) -> List[str]:
        """
        Build context lines for one node:
            - Node header with retrieval scores (helps the LLM weight evidence)
            - Key properties
            - Outgoing relationships (what this node depends on)
            - Incoming relationships (what depends on this node — critical for
              impact analysis: "which dashboards break if column X changes?")
        """
        nodeData = kg.graph.nodes[nodeId]
        nodeType = nodeData.get('type', 'Unknown')
        nodeName = self._getNodeDisplayName(nodeData, nodeId)

        # Include scores in the header so the LLM can reason about evidence quality
        lines = [f"- {nodeType}: {nodeName} (ID: {nodeId}) "
                 f"[score: {combinedScore:.0f}% | semantic: {vectorScore:.0f}%]"]
        lines.extend(self._formatNodeProperties(nodeData))

        # Outgoing: what this node produces / reads from / documents
        successors = list(kg.graph.successors(nodeId))[:self._MAX_RELATIONSHIPS]
        if successors:
            lines.append("  Outgoing relationships:")
            lines.extend(
                self._formatRelationship(kg, nodeId, t) for t in successors
            )

        # Incoming: what depends on / monitors / tracks this node.
        # This is the key for impact queries — "if column X changes, who is affected?"
        predecessors = list(kg.graph.predecessors(nodeId))[:self._MAX_RELATIONSHIPS]
        if predecessors:
            lines.append("  Incoming relationships (who depends on this):")
            for srcId in predecessors:
                edgeData  = kg.graph.get_edge_data(srcId, nodeId)
                relation  = edgeData.get('relation', self._DEFAULT_RELATION) if edgeData else self._DEFAULT_RELATION
                srcNode   = kg.graph.nodes[srcId]
                srcType   = srcNode.get('type', 'Unknown')
                srcName   = self._getNodeDisplayName(srcNode, srcId)
                lines.append(f"    <--[{relation}]-- {srcType}: {srcName} (ID: {srcId})")

        lines.append("")  # blank line between nodes for readability
        return lines

    # ─────────────────────────────────────────────────────────────────────────
    # Retrieval — the "R" in RAG
    # ─────────────────────────────────────────────────────────────────────────

    def _getKnowledgeGraphContext(self, kg: KnowledgeGraph,
                                  vectorDb: VectorStore, query: str) -> str:
        """
        Retrieve the most relevant KG nodes for a query and assemble context.

        Steps:
            1. Retriever fetches top-8 nodes (filtered + reranked)
            2. For each node, expand 1-hop KG relationships
            3. Concatenate into a single context string for the LLM prompt

        The Retriever is instantiated here (not on __init__) because vectorDb
        is passed per query — the engine is stateless w.r.t. the data.
        """
        retriever = Retriever(vectorDb)
        results   = retriever.retrieve(query)

        contextLines = ["Knowledge Graph Information:\n"]
        for result in results:
            nodeId = result["id"]
            # Skip results whose parent ID doesn't exist in the graph
            # (can happen if a chunk's parentId was set incorrectly)
            if nodeId not in kg.graph.nodes:
                continue
            contextLines.extend(
                self._formatNodeContext(
                    kg, nodeId,
                    vectorScore=result["vectorScore"],
                    combinedScore=result["combinedScore"]
                )
            )

        return "\n".join(contextLines)

    # ─────────────────────────────────────────────────────────────────────────
    # System prompt — shared between query() and queryWithReasoning()
    # ─────────────────────────────────────────────────────────────────────────

    # Defined as a class attribute so it is only allocated once, not per call
    _SYSTEM_PROMPT = """You are a helpful assistant that answers questions about a Data Platform knowledge graph for Reckitt Nutrition SDLC automation. The graph contains:

        DATA LINEAGE (Databricks):
        - Pipelines with Bronze (raw ingestion), Silver (cleansed/conformed), Gold (business-ready) layers
        - Tables at each layer with PRODUCES/CONSUMES/CONTAINS relationships
        - Columns with data types, PII flags, and lineage across layers

        POWER BI:
        - Dashboards (Executive, Sales Performance, Market Intelligence, Data Quality)
        - KPIs that READ_FROM specific Gold tables and columns
        - Relationships: Dashboard --CONTAINS--> KPI --READS_FROM--> Table/Column

        DATA DICTIONARY (Ontology):
        - Terms linking Databricks columns, Confluence docs, Power BI KPIs, and Jira tickets
        - DataDictionaryEntry --DEFINES--> Column, --MEASURED_BY--> KPI, --REFERENCED_IN--> Confluence

        DOCUMENTATION (Confluence):
        - Technical design docs, runbooks, KPI definitions, data lineage docs

        JIRA TICKETS:
        - Work tracking with TRACKS (pipeline), REFERENCES (confluence), MODIFIED (table) relationships

        KEY QUERY PATTERNS you can answer:
        1. "Which dashboards break if column X changes?" → Find KPIs that READS_FROM that column → find Dashboards that CONTAIN those KPIs
        2. "Which KPIs depend on pipeline X?" → Find tables PRODUCED by pipeline → find KPIs that READS_FROM those tables
        3. "Which Jira ticket modified dataset X?" → Find JiraTicket nodes with MODIFIED edge to that table

        Each node in the context includes a score (combined semantic + keyword relevance).
        Use the provided knowledge graph information to answer questions accurately.
        Include entity IDs in your answers: "Entity Name (ID: entity-id)"
        Be concise and specific. If information is not in the context, say so."""

    # ─────────────────────────────────────────────────────────────────────────
    # Public query methods
    # ─────────────────────────────────────────────────────────────────────────

    def query(self, kg: KnowledgeGraph, vectorDb: VectorStore, userQuery: str) -> str:
        """
        Query the knowledge graph using natural language.

        Returns a plain-text answer. Results are cached for the session —
        identical (normalised) queries skip the LLM call entirely.

        Args:
            kg:        KnowledgeGraph instance
            vectorDb:  VectorStore instance
            userQuery: Natural language question

        Returns:
            AI-generated answer based on knowledge graph context
        """
        # Cache check — return early if this exact query was already answered
        cached = self._cache.get(userQuery, prefix="query")
        if cached is not None:
            return cached

        # Build context from the KG and fire the LLM call
        context = self._getKnowledgeGraphContext(kg, vectorDb, userQuery)

        userPrompt = (
            f"Context from Knowledge Graph:\n{context}\n\n"
            f"User Question: {userQuery}\n\n"
            f"Please answer the question based on the knowledge graph information provided above."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._SYSTEM_PROMPT},
                {"role": "user",   "content": userPrompt}
            ],
            temperature=0.3,   # low temperature — factual answers, not creative
            max_tokens=1000
        )

        answer = response.choices[0].message.content
        # Store in cache so follow-up identical questions don't re-hit the LLM
        self._cache.set(userQuery, answer, prefix="query")
        return answer

    def queryWithReasoning(self, kg: KnowledgeGraph, vectorDb: VectorStore,
                           userQuery: str) -> Dict[str, Any]:
        """
        Query with detailed reasoning and source attribution.

        Useful for debugging — shows which graph relationships the LLM used
        to arrive at its answer.

        Returns:
            Dict with keys:
                answer      — direct answer to the question
                reasoning   — how the LLM traced the graph relationships
                sources     — specific entities and edges cited
                fullResponse — raw LLM output (for debugging)
        """
        # Separate cache prefix from query() so reasoning responses are cached
        # independently — they have different formats and token counts
        cached = self._cache.get(userQuery, prefix="reasoning")
        if cached is not None:
            return cached

        context = self._getKnowledgeGraphContext(kg, vectorDb, userQuery)

        # This prompt instructs the LLM to structure its output with labelled sections
        # so we can parse ANSWER / REASONING / SOURCES programmatically below
        systemPrompt = (
            "You are a data platform knowledge graph analyst for Reckitt Nutrition SDLC automation.\n"
            "Answer questions and explain your reasoning based on the graph relationships.\n"
            "Provide your response in this exact format:\n\n"
            "ANSWER: [Your direct answer]\n\n"
            "REASONING: [Explain how you traced the relationships in the knowledge graph]\n\n"
            "SOURCES: [List the specific entities and relationships you followed]\n\n"
            "Always include entity IDs. Format: \"Entity Name (ID: entity-id)\""
        )

        userPrompt = f"Context from Knowledge Graph:\n{context}\n\nUser Question: {userQuery}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": systemPrompt},
                {"role": "user",   "content": userPrompt}
            ],
            temperature=0.3,
            max_tokens=1500    # higher limit — reasoning sections need more tokens
        )

        content = response.choices[0].message.content

        # Parse structured sections from the LLM output.
        # Split on section labels rather than using regex for robustness.
        result  = {"answer": "", "reasoning": "", "sources": "", "fullResponse": content}

        if "ANSWER:" in content:
            parts              = content.split("REASONING:")
            result["answer"]   = parts[0].replace("ANSWER:", "").strip()
            if len(parts) > 1:
                reasoningParts       = parts[1].split("SOURCES:")
                result["reasoning"]  = reasoningParts[0].strip()
                if len(reasoningParts) > 1:
                    result["sources"] = reasoningParts[1].strip()
        else:
            # LLM didn't follow the format — return raw output as the answer
            result["answer"] = content

        self._cache.set(userQuery, result, prefix="reasoning")
        return result

    def clearCache(self) -> None:
        """Clear the session cache (call this after reloading the KG data)."""
        self._cache.clear()

    def cacheSize(self) -> int:
        """Return the number of cached query results in this session."""
        return self._cache.size()


def askQuestion(kg: KnowledgeGraph, vectorDb: VectorStore, question: str) -> str:
    """
    Convenience function — ask a natural language question via OpenRouter.

    Creates a fresh engine instance (and therefore a fresh cache) for each call.
    For multi-query sessions, instantiate NaturalLanguageQueryEngine directly
    to benefit from caching across calls.

    Args:
        kg:       KnowledgeGraph instance
        vectorDb: VectorStore instance
        question: Your question in plain English

    Returns:
        AI-generated answer
    """
    return NaturalLanguageQueryEngine().query(kg, vectorDb, question)
