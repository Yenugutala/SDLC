"""
Knowledge Graph core module using NetworkX.
Provides graph structure for storing entities and relationships.
"""

import networkx as nx


class KnowledgeGraph:
    """Knowledge Graph using directed graph structure."""

    def __init__(self):
        """Initialize empty directed graph."""
        self.graph = nx.DiGraph()

    def addNode(self, nodeId, nodeType, **attrs):
        """
        Add a node to the knowledge graph.

        Args:
            nodeId: Unique identifier for the node
            nodeType: Type of the node (e.g., 'Pipeline', 'Dataset')
            **attrs: Additional attributes for the node
        """
        self.graph.add_node(nodeId, type=nodeType, **attrs)

    def addEdge(self, fromNode, relation, toNode):
        """
        Add a directed edge between two nodes.

        Args:
            fromNode: Source node ID
            relation: Relationship type (e.g., 'PRODUCES', 'CONTAINS')
            toNode: Target node ID
        """
        self.graph.add_edge(fromNode, toNode, relation=relation)

    def queryEdges(self):
        """
        Get all edges in the graph with their relationships.

        Returns:
            List of tuples (source, target, relation)
        """
        return [
            (u, v, d["relation"])
            for u, v, d in self.graph.edges(data=True)
        ]

    def neighbors(self, nodeId):
        """
        Get all successor nodes of a given node.

        Args:
            nodeId: Node ID to get neighbors for

        Returns:
            List of successor node IDs
        """
        return list(self.graph.successors(nodeId))

    # Maintain backwards compatibility with snake_case methods
    add_node = addNode
    add_edge = addEdge
    query_edges = queryEdges
