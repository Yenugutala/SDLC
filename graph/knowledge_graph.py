"""
Knowledge Graph core module using NetworkX.

The knowledge graph is a directed graph (DiGraph) where:
    - Nodes represent entities: pipelines, tables, columns, Jira tickets,
      Confluence pages, alerts, Power BI dashboards/KPIs, data dictionary entries.
    - Edges represent typed relationships: PRODUCES, CONTAINS, TRACKS, READS_FROM, etc.

Why NetworkX DiGraph?
    - In-memory, no setup required
    - First-class support for directed edges with typed attributes
    - Rich traversal API (successors, predecessors, shortest_path, etc.)
    - Sufficient for the ~100–300 node scale of this KG

All nodes store their entity type in the "type" attribute so queries can
filter by type without inspecting the ID prefix.
"""

import networkx as nx


class KnowledgeGraph:
    """Directed knowledge graph wrapping a NetworkX DiGraph."""

    def __init__(self):
        # DiGraph (directed) rather than Graph (undirected) — relationships
        # like PRODUCES and CONSUMES have direction that matters for traversal.
        self.graph = nx.DiGraph()

    def addNode(self, nodeId: str, nodeType: str, **attrs) -> None:
        """
        Add a node to the knowledge graph.

        The 'type' attribute is always set — it is the primary filter used by
        query functions (e.g. "give me all Pipeline nodes").

        Args:
            nodeId:   Unique identifier (e.g. "pipeline_rn_bronze_sales")
            nodeType: Entity type string (e.g. "Pipeline", "Table", "Column")
            **attrs:  Domain-specific attributes stored on the node
                      (name, description, owner, schedule, isPii, etc.)
        """
        self.graph.add_node(nodeId, type=nodeType, **attrs)

    def addEdge(self, fromNode: str, relation: str, toNode: str) -> None:
        """
        Add a directed edge between two nodes.

        Edges carry a 'relation' attribute — the relationship type label
        (e.g. "PRODUCES", "CONTAINS", "READS_FROM"). This is used when
        formatting context for the LLM and when printing traversal results.

        Args:
            fromNode: Source node ID (the subject)
            relation: Relationship type label (the verb)
            toNode:   Target node ID (the object)
        """
        self.graph.add_edge(fromNode, toNode, relation=relation)

    def queryEdges(self):
        """
        Get all edges in the graph with their relationship labels.

        Returns:
            List of (source_id, target_id, relation_label) tuples
        """
        return [
            (u, v, d["relation"])
            for u, v, d in self.graph.edges(data=True)
        ]

    def neighbors(self, nodeId: str):
        """
        Get all successor nodes (nodes this node points to).

        Note: returns successors only (outgoing edges). For predecessors
        (incoming edges) use kg.graph.predecessors(nodeId) directly.

        Args:
            nodeId: Node ID to get neighbours for

        Returns:
            List of successor node IDs
        """
        return list(self.graph.successors(nodeId))

    # Aliases for backwards compatibility with snake_case callers
    add_node    = addNode
    add_edge    = addEdge
    query_edges = queryEdges
