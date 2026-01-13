"""
Query module for Data Platform Knowledge Graph.
Contains flexible search and query functions for analyzing pipelines, tables, and data lineage.
"""

from typing import List, Dict, Any, Tuple
from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore
from src.utils.formatting import (
    printHeader, printSubHeader, printSeparator,
    formatNodeInfo, formatRelationship
)


def queryPipelineRelationships(kg: KnowledgeGraph, limit: int = 10) -> None:
    """Display relationships for all pipelines in the graph."""
    printHeader("QUERY: Pipeline Relationships")

    pipelineEdges = [
        (u, v, d) for u, v, d in kg.queryEdges()
        if kg.graph.nodes[u].get('type') == 'Pipeline'
    ]

    if not pipelineEdges:
        print("\n  No pipeline relationships found.")
        return

    for source, target, relation in pipelineEdges[:limit]:
        sourceName = kg.graph.nodes[source].get('name', source)
        targetName = kg.graph.nodes[target].get('name') or kg.graph.nodes[target].get('title', target)
        targetType = kg.graph.nodes[target].get('type', 'Unknown')
        print(f"  {sourceName} --[{relation}]--> [{targetType}] {targetName}")


def queryPipelineStatus(kg: KnowledgeGraph) -> None:
    """Display pipeline status grouped by schedule."""
    printHeader("QUERY: Data Pipeline Status")

    pipelines = [
        (pipelineId, data) for pipelineId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    if not pipelines:
        print("\n  No data pipelines found.")
        return

    # Group by status
    byStatus = {}
    for pipelineId, data in pipelines:
        status = data.get('status', 'unknown')
        byStatus.setdefault(status, []).append(data)

    for status in ['active', 'paused', 'failed']:
        if status in byStatus:
            statusIcon = "+" if status == 'active' else ("~" if status == 'paused' else "X")
            print(f"\n  {status.upper()} [{statusIcon}]:")
            for pipeline in byStatus[status]:
                print(f"    - {pipeline.get('name')}")
                print(f"      Schedule: {pipeline.get('schedule')} | Owner: {pipeline.get('owner')}")


def queryTablesByPipeline(kg: KnowledgeGraph) -> None:
    """Display tables grouped by their source pipeline."""
    printHeader("QUERY: Tables by Pipeline")

    pipelines = [
        (pipelineId, data) for pipelineId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    if not pipelines:
        print("\n  No pipelines found.")
        return

    for pipelineId, pipelineData in pipelines:
        tables = [
            kg.graph.nodes[target]
            for target in kg.graph.successors(pipelineId)
            if kg.graph.nodes[target].get('type') == 'Table'
        ]

        if tables:
            print(f"\n  {pipelineData.get('name')}:")
            for table in tables:
                rowCount = table.get('rowCount', 0)
                rowCountStr = f"{rowCount:,}" if rowCount else "N/A"
                print(f"    - {table.get('schema')}.{table.get('name')} ({rowCountStr} rows)")


def queryPiiColumns(kg: KnowledgeGraph) -> None:
    """Find and display all columns marked as PII."""
    printHeader("QUERY: PII Columns")

    piiColumns = [
        (colId, data) for colId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Column' and data.get('isPii')
    ]

    if not piiColumns:
        print("\n  No PII columns found.")
        return

    print(f"\n  Found {len(piiColumns)} PII columns:")
    for colId, colData in piiColumns:
        # Find parent table
        tableId = next(
            (pred for pred in kg.graph.predecessors(colId)
             if kg.graph.nodes[pred].get('type') == 'Table'),
            None
        )
        tableName = kg.graph.nodes[tableId].get('name') if tableId else 'Unknown'

        print(f"\n    {tableName}.{colData.get('name')}")
        print(f"      Type: {colData.get('dataType')} | Nullable: {colData.get('isNullable')}")
        print(f"      Description: {colData.get('description')}")


def queryJiraByPipeline(kg: KnowledgeGraph) -> None:
    """Display Jira tickets grouped by the pipeline they track."""
    printHeader("QUERY: Jira Tickets by Pipeline")

    pipelines = [
        (pipelineId, data) for pipelineId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    for pipelineId, pipelineData in pipelines:
        # Find Jira tickets that track this pipeline
        jiraTickets = [
            kg.graph.nodes[source]
            for source in kg.graph.predecessors(pipelineId)
            if kg.graph.nodes[source].get('type') == 'JiraTicket'
        ]

        if jiraTickets:
            print(f"\n  {pipelineData.get('name')}:")
            for ticket in jiraTickets:
                status = ticket.get('status', 'N/A')
                statusIcon = "+" if status == 'Done' else ("~" if status == 'In Progress' else "-")
                ticketId = ticket.get('summary', '').split()[0] if ticket.get('summary') else 'Unknown'
                print(f"    [{statusIcon}] {ticket.get('summary')} ({status})")
                print(f"        Priority: {ticket.get('priority')} | Assignee: {ticket.get('assignee')}")


def queryConfluenceByPipeline(kg: KnowledgeGraph) -> None:
    """Display Confluence documentation for each pipeline."""
    printHeader("QUERY: Documentation by Pipeline")

    pipelines = [
        (pipelineId, data) for pipelineId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    for pipelineId, pipelineData in pipelines:
        # Find Confluence pages for this pipeline
        docs = [
            kg.graph.nodes[target]
            for target in kg.graph.successors(pipelineId)
            if kg.graph.nodes[target].get('type') == 'ConfluencePage'
        ]

        if docs:
            print(f"\n  {pipelineData.get('name')}:")
            for doc in docs:
                print(f"    [{doc.get('space')}] {doc.get('title')}")
                print(f"        Author: {doc.get('author')}")


def queryAlertsByPipeline(kg: KnowledgeGraph) -> None:
    """Display alerts configured for each pipeline."""
    printHeader("QUERY: Alerts by Pipeline")

    alerts = [
        (alertId, data) for alertId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Alert'
    ]

    if not alerts:
        print("\n  No alerts found.")
        return

    # Group alerts by what they monitor
    byPipeline = {}
    for alertId, alertData in alerts:
        # Find what this alert monitors
        for target in kg.graph.successors(alertId):
            targetNode = kg.graph.nodes[target]
            if targetNode.get('type') == 'Pipeline':
                pipelineName = targetNode.get('name', target)
                byPipeline.setdefault(pipelineName, []).append(alertData)

    for pipelineName, pipelineAlerts in byPipeline.items():
        print(f"\n  {pipelineName}:")
        for alert in pipelineAlerts:
            severityIcon = "!!" if alert.get('severity') == 'critical' else "!"
            enabledIcon = "+" if alert.get('enabled') else "-"
            print(f"    [{severityIcon}][{enabledIcon}] {alert.get('name')} ({alert.get('alertType')})")
            if alert.get('threshold'):
                print(f"        Threshold: {alert.get('threshold')}")


def queryDataQualityRules(kg: KnowledgeGraph) -> None:
    """Display data quality rules grouped by table."""
    printHeader("QUERY: Data Quality Rules")

    rules = [
        (ruleId, data) for ruleId, data in kg.graph.nodes(data=True)
        if data.get('type') == 'DataQualityRule'
    ]

    if not rules:
        print("\n  No data quality rules found.")
        return

    # Group by table
    byTable = {}
    for ruleId, ruleData in rules:
        for target in kg.graph.successors(ruleId):
            targetNode = kg.graph.nodes[target]
            if targetNode.get('type') == 'Table':
                tableName = targetNode.get('name', target)
                byTable.setdefault(tableName, []).append(ruleData)

    for tableName, tableRules in byTable.items():
        print(f"\n  {tableName}:")
        for rule in tableRules:
            severityIcon = "!!" if rule.get('severity') == 'critical' else "!"
            enabledIcon = "+" if rule.get('enabled') else "-"
            print(f"    [{severityIcon}][{enabledIcon}] {rule.get('name')}")
            print(f"        Type: {rule.get('ruleType')} | {rule.get('description')}")


def queryJiraWorkByStatus(jiraTickets: List[Dict[str, Any]]) -> None:
    """Display Jira tickets grouped by status."""
    printHeader("QUERY: Jira Tickets by Status")

    jiraByStatus = {}
    for ticket in jiraTickets:
        jiraByStatus.setdefault(ticket['status'], []).append(ticket)

    for status in ['To Do', 'In Progress', 'Done']:
        if status in jiraByStatus:
            tickets = jiraByStatus[status]
            totalPoints = sum(t.get('storyPoints', 0) or 0 for t in tickets)
            print(f"\n  {status}: {len(tickets)} tickets ({totalPoints} story points)")

            for ticket in tickets[:5]:
                priority = ticket.get('priority', 'N/A')
                issueType = ticket.get('issueType', 'Task')
                print(f"    [{ticket['id']}] [{issueType}] {ticket['summary']} ({priority})")


def queryCriticalAlerts(alerts: List[Dict[str, Any]]) -> None:
    """Display critical alert configurations."""
    printHeader("QUERY: Critical Alerts")

    criticalAlerts = [
        alert for alert in alerts
        if alert['severity'] == 'critical' and alert['enabled']
    ]

    print(f"\n  {len(criticalAlerts)} critical alerts enabled:")
    for alert in criticalAlerts:
        print(f"\n    {alert['name']} ({alert['alertType']})")
        print(f"      Channels: {', '.join(alert['notificationChannels'])}")
        if alert.get('threshold'):
            print(f"      Threshold: {alert['threshold']}")


def queryGraphStatistics(kg: KnowledgeGraph) -> None:
    """Display overall graph statistics."""
    printHeader("QUERY: Graph Statistics")

    totalNodes = kg.graph.number_of_nodes()
    totalEdges = kg.graph.number_of_edges()

    nodeTypes = {}
    for node, data in kg.graph.nodes(data=True):
        nodeType = data.get('type', 'Unknown')
        nodeTypes[nodeType] = nodeTypes.get(nodeType, 0) + 1

    print(f"\n  Total Nodes: {totalNodes}")
    print(f"  Total Edges: {totalEdges}")
    print(f"\n  Node Types:")
    for ntype, count in sorted(nodeTypes.items(), key=lambda x: x[1], reverse=True):
        print(f"    {ntype}: {count}")


# ============================================================================
# FEATURE LOOKUP FUNCTIONS
# ============================================================================

def isFeatureInProject(kg: KnowledgeGraph, vectorDb: VectorStore, featureName: str, threshold: float = 1.5) -> Dict[str, Any]:
    """
    Check if a feature/component exists in the project.

    Args:
        kg: KnowledgeGraph instance
        vectorDb: VectorStore instance
        featureName: Name of the feature to search for (e.g., "customer", "fraud", "inventory")
        threshold: Distance threshold for considering a match (lower = stricter)

    Returns:
        Dictionary with 'found', 'matches', and 'details'

    Examples:
        isFeatureInProject(kg, vectorDb, "customer data")
        isFeatureInProject(kg, vectorDb, "fraud detection")
        isFeatureInProject(kg, vectorDb, "inventory")
    """
    results = vectorDb.search(featureName, k=10)

    matches = []
    for i, docId in enumerate(results['ids'][0]):
        distance = results['distances'][0][i]
        if distance <= threshold and docId in kg.graph.nodes:
            nodeData = kg.graph.nodes[docId]
            nodeName = nodeData.get('name') or nodeData.get('title') or nodeData.get('summary') or docId
            nodeType = nodeData.get('type', 'Unknown')
            matches.append({
                'id': docId,
                'name': nodeName,
                'type': nodeType,
                'distance': distance,
                'data': dict(nodeData)
            })

    return {
        'found': len(matches) > 0,
        'featureName': featureName,
        'matchCount': len(matches),
        'matches': matches
    }


def findFeature(kg: KnowledgeGraph, vectorDb: VectorStore, featureName: str) -> None:
    """
    Interactive function to check if a feature exists and display results.

    Args:
        kg: KnowledgeGraph instance
        vectorDb: VectorStore instance
        featureName: Name of the feature to search for
    """
    printHeader(f"FEATURE SEARCH: '{featureName}'")

    result = isFeatureInProject(kg, vectorDb, featureName)

    if result['found']:
        print(f"\n  YES - '{featureName}' found in project! ({result['matchCount']} matches)")
        print("\n  Related items:")
        for match in result['matches'][:5]:
            print(f"\n    [{match['type']}] {match['name']}")
            print(f"      ID: {match['id']}")
            print(f"      Relevance: {(1 - match['distance']/2) * 100:.1f}%")

            # Show key attributes based on type
            data = match['data']
            if match['type'] == 'Pipeline':
                print(f"      Schedule: {data.get('schedule')} | Owner: {data.get('owner')}")
            elif match['type'] == 'Table':
                print(f"      Schema: {data.get('schema')} | Rows: {data.get('rowCount', 0):,}")
            elif match['type'] == 'Column':
                print(f"      Type: {data.get('dataType')} | PII: {data.get('isPii')}")
            elif match['type'] == 'JiraTicket':
                print(f"      Status: {data.get('status')} | Priority: {data.get('priority')}")
            elif match['type'] == 'ConfluencePage':
                print(f"      Space: {data.get('space')} | Author: {data.get('author')}")
            elif match['type'] == 'Alert':
                print(f"      Type: {data.get('alertType')} | Severity: {data.get('severity')}")
            elif match['type'] == 'DataQualityRule':
                print(f"      Rule Type: {data.get('ruleType')} | Severity: {data.get('severity')}")
    else:
        print(f"\n  NO - '{featureName}' not found in project.")
        print("\n  Try searching for related terms or check spelling.")


def getFeatureStatus(kg: KnowledgeGraph, vectorDb: VectorStore, featureName: str) -> Dict[str, Any]:
    """
    Get comprehensive status of a feature including related pipelines, tables, tickets, and alerts.

    Args:
        kg: KnowledgeGraph instance
        vectorDb: VectorStore instance
        featureName: Name of the feature to analyze

    Returns:
        Dictionary with feature status across data platform components
    """
    result = isFeatureInProject(kg, vectorDb, featureName, threshold=1.8)

    status = {
        'feature': featureName,
        'found': result['found'],
        'pipelines': [],
        'tables': [],
        'columns': [],
        'jiraTickets': [],
        'documentation': [],
        'alerts': [],
        'dataQualityRules': []
    }

    if not result['found']:
        return status

    for match in result['matches']:
        nodeType = match['type']
        if nodeType == 'Pipeline':
            status['pipelines'].append({
                'id': match['id'],
                'name': match['data'].get('name'),
                'status': match['data'].get('status'),
                'schedule': match['data'].get('schedule'),
                'owner': match['data'].get('owner')
            })
        elif nodeType == 'Table':
            status['tables'].append({
                'id': match['id'],
                'name': match['data'].get('name'),
                'schema': match['data'].get('schema'),
                'rowCount': match['data'].get('rowCount')
            })
        elif nodeType == 'Column':
            status['columns'].append({
                'id': match['id'],
                'name': match['data'].get('name'),
                'dataType': match['data'].get('dataType'),
                'isPii': match['data'].get('isPii')
            })
        elif nodeType == 'JiraTicket':
            status['jiraTickets'].append({
                'id': match['id'],
                'summary': match['data'].get('summary'),
                'status': match['data'].get('status'),
                'priority': match['data'].get('priority')
            })
        elif nodeType == 'ConfluencePage':
            status['documentation'].append({
                'id': match['id'],
                'title': match['data'].get('title'),
                'space': match['data'].get('space')
            })
        elif nodeType == 'Alert':
            status['alerts'].append({
                'id': match['id'],
                'name': match['data'].get('name'),
                'alertType': match['data'].get('alertType'),
                'severity': match['data'].get('severity')
            })
        elif nodeType == 'DataQualityRule':
            status['dataQualityRules'].append({
                'id': match['id'],
                'name': match['data'].get('name'),
                'ruleType': match['data'].get('ruleType'),
                'severity': match['data'].get('severity')
            })

    return status


def showFeatureStatus(kg: KnowledgeGraph, vectorDb: VectorStore, featureName: str) -> None:
    """
    Display comprehensive feature status across the data platform.
    """
    printHeader(f"FEATURE STATUS: '{featureName}'")

    status = getFeatureStatus(kg, vectorDb, featureName)

    if not status['found']:
        print(f"\n  Feature '{featureName}' not found in project.")
        return

    print(f"\n  Feature '{featureName}' - Data Platform Status:\n")

    # Pipelines
    if status['pipelines']:
        print("  PIPELINES:")
        for pipeline in status['pipelines']:
            statusIcon = "+" if pipeline['status'] == 'active' else "~"
            print(f"    [{statusIcon}] {pipeline['name']}")
            print(f"        Schedule: {pipeline['schedule']} | Owner: {pipeline['owner']}")

    # Tables
    if status['tables']:
        print("\n  TABLES:")
        for table in status['tables']:
            rowCount = table['rowCount'] or 0
            print(f"    {table['schema']}.{table['name']} ({rowCount:,} rows)")

    # Columns
    if status['columns']:
        print("\n  COLUMNS:")
        for col in status['columns']:
            piiFlag = " [PII]" if col['isPii'] else ""
            print(f"    {col['name']} ({col['dataType']}){piiFlag}")

    # Jira Tickets
    if status['jiraTickets']:
        print("\n  JIRA TICKETS:")
        for ticket in status['jiraTickets']:
            statusIcon = "+" if ticket['status'] == 'Done' else ("~" if ticket['status'] == 'In Progress' else "-")
            print(f"    [{statusIcon}] {ticket['id']}: {ticket['summary']} ({ticket['status']})")

    # Documentation
    if status['documentation']:
        print("\n  DOCUMENTATION:")
        for doc in status['documentation']:
            print(f"    [{doc['space']}] {doc['title']}")

    # Alerts
    if status['alerts']:
        print("\n  ALERTS:")
        for alert in status['alerts']:
            severityIcon = "!!" if alert['severity'] == 'critical' else "!"
            print(f"    [{severityIcon}] {alert['name']} ({alert['alertType']})")

    # Data Quality Rules
    if status['dataQualityRules']:
        print("\n  DATA QUALITY RULES:")
        for rule in status['dataQualityRules']:
            print(f"    {rule['name']} ({rule['ruleType']})")


def listAllFeatures(kg: KnowledgeGraph) -> Dict[str, List[str]]:
    """
    List all features/components in the project grouped by type.

    Returns:
        Dictionary mapping entity types to lists of names
    """
    features = {}

    for nodeId, data in kg.graph.nodes(data=True):
        nodeType = data.get('type', 'Unknown')
        nodeName = data.get('name') or data.get('title') or data.get('summary') or nodeId

        if nodeType not in features:
            features[nodeType] = []
        features[nodeType].append(nodeName)

    return features


def showAllFeatures(kg: KnowledgeGraph) -> None:
    """Display all features/components in the project."""
    printHeader("ALL PROJECT COMPONENTS")

    features = listAllFeatures(kg)

    for nodeType, names in sorted(features.items()):
        print(f"\n  {nodeType} ({len(names)}):")
        for name in names[:10]:  # Show first 10
            print(f"    - {name}")
        if len(names) > 10:
            print(f"    ... and {len(names) - 10} more")


def searchEntities(vectorDb: VectorStore, query: str, entityType: str = None, k: int = 5) -> List[Tuple[str, float]]:
    """
    Flexible search function to find entities by semantic similarity.

    Args:
        vectorDb: VectorStore instance
        query: Natural language search query
        entityType: Optional filter for entity type
        k: Number of results to return

    Returns:
        List of tuples containing (entityId, distance)
    """
    searchK = k * 3 if entityType else k
    results = vectorDb.search(query, k=searchK)

    allResults = [
        (docId, results['distances'][0][i])
        for i, docId in enumerate(results['ids'][0])
    ]

    if not entityType:
        return allResults[:k]

    # Filter by entity type using prefix mapping
    typePrefixMap = {
        'Pipeline': 'pipeline_',
        'Table': 'table_',
        'Column': 'col_',
        'Jira': 'DATA-',
        'Confluence': 'conf_',
        'Alert': 'alert_',
        'DataQualityRule': 'dq_',
        'Environment': 'env_'
    }

    prefix = typePrefixMap.get(entityType, entityType)
    return [
        (docId, distance) for docId, distance in allResults
        if docId.startswith(prefix)
    ][:k]


def queryRelationshipsBySearch(kg: KnowledgeGraph, vectorDb: VectorStore,
                                query: str, entityType: str = None, k: int = 5) -> None:
    """
    Search for entities and display their relationships in the knowledge graph.
    """
    typeFilter = f" (type: {entityType})" if entityType else ""
    print(f"\n  Search: '{query}'{typeFilter}")

    results = searchEntities(vectorDb, query, entityType, k)

    if not results:
        print("    No results found")
        return

    for i, (docId, distance) in enumerate(results, 1):
        if docId not in kg.graph.nodes:
            print(f"    {i}. {docId} (distance: {distance:.3f}) - Not found in graph")
            continue

        nodeData = kg.graph.nodes[docId]
        nodeName = (nodeData.get('name') or nodeData.get('summary') or
                   nodeData.get('title') or docId)
        nodeType = nodeData.get('type', 'Unknown')

        print(f"\n    {i}. [{nodeType}] {nodeName} (distance: {distance:.3f})")

        # Get outgoing relationships
        outgoing = list(kg.graph.successors(docId))
        if outgoing:
            print(f"       Relationships:")
            for target in outgoing[:3]:
                edgeData = kg.graph.get_edge_data(docId, target)
                relation = edgeData.get('relation', 'RELATED_TO') if edgeData else 'RELATED_TO'
                targetData = kg.graph.nodes[target]
                targetName = (targetData.get('name') or targetData.get('summary') or target)
                targetType = targetData.get('type', 'Unknown')
                print(f"         --[{relation}]--> [{targetType}] {targetName}")

        # Get incoming relationships
        incoming = list(kg.graph.predecessors(docId))
        for source in incoming[:2]:
            edgeData = kg.graph.get_edge_data(source, docId)
            relation = edgeData.get('relation', 'RELATED_TO') if edgeData else 'RELATED_TO'
            sourceData = kg.graph.nodes[source]
            sourceName = (sourceData.get('name') or sourceData.get('summary') or source)
            sourceType = sourceData.get('type', 'Unknown')
            print(f"         <--[{relation}]-- [{sourceType}] {sourceName}")


def performVectorSearches(vectorDb: VectorStore, kg: KnowledgeGraph = None) -> None:
    """Perform predefined vector similarity searches."""
    printHeader("VECTOR SEARCH QUERIES")

    searchQueries = [
        ("customer data ingestion", None),
        ("fraud detection ML", None),
        ("inventory warehouse sync", None),
        ("data quality validation", "DataQualityRule"),
        ("pipeline documentation", "Confluence"),
    ]

    for query, entityType in searchQueries:
        if kg:
            queryRelationshipsBySearch(kg, vectorDb, query, entityType, k=3)
        else:
            typeFilter = f" (type: {entityType})" if entityType else ""
            print(f"\n  Search: '{query}'{typeFilter}")
            results = searchEntities(vectorDb, query, entityType, k=3)
            for i, (docId, distance) in enumerate(results, 1):
                print(f"    {i}. {docId} (distance: {distance:.3f})")


def runAllQueries(kg: KnowledgeGraph, vectorDb: VectorStore, data: Dict[str, Any]) -> None:
    """
    Execute all predefined queries on the knowledge graph.

    Args:
        kg: KnowledgeGraph instance
        vectorDb: VectorStore instance
        data: Dictionary containing all data lists
    """
    printHeader("DATA PLATFORM KNOWLEDGE GRAPH QUERIES")

    queryPipelineRelationships(kg)
    queryPipelineStatus(kg)
    queryTablesByPipeline(kg)
    queryPiiColumns(kg)
    queryJiraByPipeline(kg)
    queryConfluenceByPipeline(kg)
    queryAlertsByPipeline(kg)
    queryDataQualityRules(kg)
    queryJiraWorkByStatus(data['jiraTickets'])
    queryCriticalAlerts(data['alerts'])
    performVectorSearches(vectorDb, kg)
    queryGraphStatistics(kg)

    printHeader("DATA PLATFORM KNOWLEDGE GRAPH ANALYSIS COMPLETE")
