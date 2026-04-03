"""
Query module for Data Platform Knowledge Graph.

Two query categories:
    1. GRAPH TRAVERSAL  — pure NetworkX; no LLM, no vector search
    2. SEMANTIC SEARCH  — VectorStore + Retriever for broad discovery

All display functions use rich markup via utils.formatting.console for
color-coded terminal output.
"""

from typing import List, Dict, Any, Tuple
from graph.knowledge_graph import KnowledgeGraph
from rag.vectorstore import VectorStore
from utils.formatting import (
    console, printHeader, printSubHeader, printSeparator,
    formatNodeInfo, formatRelationship,
    colorScore, colorStatus, colorStatusIcon, colorSeverity,
    colorLayer, colorEntityType, colorPriority, colorPii, scoreBar
)


# ============================================================================
# GRAPH TRAVERSAL QUERIES
# ============================================================================

def queryPipelineRelationships(kg: KnowledgeGraph, limit: int = 10) -> None:
    """Display relationships for all pipelines in the graph."""
    printHeader("QUERY: Pipeline Relationships")

    pipelineEdges = [
        (u, v, d) for u, v, d in kg.queryEdges()
        if kg.graph.nodes[u].get('type') == 'Pipeline'
    ]

    if not pipelineEdges:
        console.print("\n  No pipeline relationships found.", style="dim")
        return

    for source, target, relation in pipelineEdges[:limit]:
        sourceName = kg.graph.nodes[source].get('name', source)
        targetName = kg.graph.nodes[target].get('name') or kg.graph.nodes[target].get('title', target)
        targetType = kg.graph.nodes[target].get('type', 'Unknown')
        console.print(
            f"  [bold]{sourceName}[/bold] "
            f"[blue]--[[/blue][bold]{relation}[/bold][blue]]-->[/blue] "
            f"{colorEntityType(targetType)} {targetName}"
        )


def queryPipelineStatus(kg: KnowledgeGraph) -> None:
    """Display pipeline status grouped by operational state."""
    printHeader("QUERY: Data Pipeline Status")

    pipelines = [
        (pid, data) for pid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    if not pipelines:
        console.print("\n  No data pipelines found.", style="dim")
        return

    byStatus = {}
    for pid, data in pipelines:
        byStatus.setdefault(data.get('status', 'unknown'), []).append(data)

    for status in ['active', 'paused', 'failed']:
        if status not in byStatus:
            continue
        icon = colorStatusIcon(status)
        console.print(f"\n  {colorStatus(status.upper())} [{icon}]:")
        for pipeline in byStatus[status]:
            console.print(f"    [bold]- {pipeline.get('name')}[/bold]")
            console.print(
                f"      [dim]Schedule:[/dim] {pipeline.get('schedule')}  "
                f"[dim]Owner:[/dim] {pipeline.get('owner')}"
            )


def queryTablesByPipeline(kg: KnowledgeGraph) -> None:
    """Display tables grouped by their source pipeline."""
    printHeader("QUERY: Tables by Pipeline")

    pipelines = [
        (pid, data) for pid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    if not pipelines:
        console.print("\n  No pipelines found.", style="dim")
        return

    for pid, pipelineData in pipelines:
        tables = [
            kg.graph.nodes[t] for t in kg.graph.successors(pid)
            if kg.graph.nodes[t].get('type') == 'Table'
        ]
        if tables:
            console.print(f"\n  [bold cyan]{pipelineData.get('name')}[/bold cyan]:")
            for table in tables:
                layer      = table.get('layer', table.get('schema', ''))
                rowCount   = table.get('rowCount', 0)
                rowStr     = f"{rowCount:,}" if rowCount else "N/A"
                layerLabel = colorLayer(layer) if layer else ""
                console.print(
                    f"    {layerLabel} [bold]{table.get('schema')}.{table.get('name')}[/bold] "
                    f"[dim]({rowStr} rows)[/dim]"
                )


def queryPiiColumns(kg: KnowledgeGraph) -> None:
    """Find and display all columns marked as PII."""
    printHeader("QUERY: PII Columns")

    piiColumns = [
        (cid, data) for cid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Column' and data.get('isPii')
    ]

    if not piiColumns:
        console.print("\n  No PII columns found.", style="dim")
        return

    console.print(f"\n  Found [bold red]{len(piiColumns)}[/bold red] PII columns:")
    for cid, colData in piiColumns:
        tableId = next(
            (p for p in kg.graph.predecessors(cid)
             if kg.graph.nodes[p].get('type') == 'Table'),
            None
        )
        tableName = kg.graph.nodes[tableId].get('name') if tableId else 'Unknown'
        console.print(
            f"\n    [bold]{tableName}.{colData.get('name')}[/bold]"
            f"[bold red] [PII][/bold red]"
        )
        console.print(
            f"      [dim]Type:[/dim] {colData.get('dataType')}  "
            f"[dim]Nullable:[/dim] {colData.get('isNullable')}"
        )
        console.print(f"      [dim]{colData.get('description')}[/dim]")


def queryJiraByPipeline(kg: KnowledgeGraph) -> None:
    """Display Jira tickets grouped by the pipeline they track."""
    printHeader("QUERY: Jira Tickets by Pipeline")

    pipelines = [
        (pid, data) for pid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    for pid, pipelineData in pipelines:
        jiraTickets = [
            kg.graph.nodes[src] for src in kg.graph.predecessors(pid)
            if kg.graph.nodes[src].get('type') == 'JiraTicket'
        ]
        if jiraTickets:
            console.print(f"\n  [bold cyan]{pipelineData.get('name')}[/bold cyan]:")
            for ticket in jiraTickets:
                status = ticket.get('status', 'N/A')
                icon   = colorStatusIcon(status)
                console.print(
                    f"    [{icon}] [bold]{ticket.get('summary')}[/bold] "
                    f"[dim]({colorStatus(status)})[/dim]"
                )
                console.print(
                    f"        [dim]Priority:[/dim] {colorPriority(ticket.get('priority', ''))}  "
                    f"[dim]Assignee:[/dim] {ticket.get('assignee')}"
                )


def queryConfluenceByPipeline(kg: KnowledgeGraph) -> None:
    """Display Confluence documentation for each pipeline."""
    printHeader("QUERY: Documentation by Pipeline")

    pipelines = [
        (pid, data) for pid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Pipeline'
    ]

    for pid, pipelineData in pipelines:
        docs = [
            kg.graph.nodes[t] for t in kg.graph.successors(pid)
            if kg.graph.nodes[t].get('type') == 'ConfluencePage'
        ]
        if docs:
            console.print(f"\n  [bold cyan]{pipelineData.get('name')}[/bold cyan]:")
            for doc in docs:
                console.print(
                    f"    [blue][[/blue]{doc.get('space')}[blue]][/blue] "
                    f"[bold]{doc.get('title')}[/bold]  "
                    f"[dim]Author: {doc.get('author')}[/dim]"
                )


def queryAlertsByPipeline(kg: KnowledgeGraph) -> None:
    """Display alerts configured for each pipeline."""
    printHeader("QUERY: Alerts by Pipeline")

    alerts = [
        (aid, data) for aid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'Alert'
    ]

    if not alerts:
        console.print("\n  No alerts found.", style="dim")
        return

    byPipeline = {}
    for aid, alertData in alerts:
        for t in kg.graph.successors(aid):
            tNode = kg.graph.nodes[t]
            if tNode.get('type') == 'Pipeline':
                byPipeline.setdefault(tNode.get('name', t), []).append(alertData)

    for pipelineName, pipelineAlerts in byPipeline.items():
        console.print(f"\n  [bold cyan]{pipelineName}[/bold cyan]:")
        for alert in pipelineAlerts:
            sev     = alert.get('severity', '')
            enabled = alert.get('enabled')
            enabledStr = "[green]ON[/green]" if enabled else "[dim]OFF[/dim]"
            console.print(
                f"    {colorSeverity(sev)}  {enabledStr}  "
                f"[bold]{alert.get('name')}[/bold] "
                f"[dim]({alert.get('alertType')})[/dim]"
            )
            if alert.get('threshold'):
                console.print(f"        [dim]Threshold: {alert.get('threshold')}[/dim]")


def queryDataQualityRules(kg: KnowledgeGraph) -> None:
    """Display data quality rules grouped by table."""
    printHeader("QUERY: Data Quality Rules")

    rules = [
        (rid, data) for rid, data in kg.graph.nodes(data=True)
        if data.get('type') == 'DataQualityRule'
    ]

    if not rules:
        console.print("\n  No data quality rules found.", style="dim")
        return

    byTable = {}
    for rid, ruleData in rules:
        for t in kg.graph.successors(rid):
            tNode = kg.graph.nodes[t]
            if tNode.get('type') == 'Table':
                byTable.setdefault(tNode.get('name', t), []).append(ruleData)

    for tableName, tableRules in byTable.items():
        console.print(f"\n  [bold]{tableName}[/bold]:")
        for rule in tableRules:
            sev     = rule.get('severity', '')
            enabled = rule.get('enabled')
            enabledStr = "[green]ON[/green]" if enabled else "[dim]OFF[/dim]"
            console.print(
                f"    {colorSeverity(sev)}  {enabledStr}  "
                f"[bold]{rule.get('name')}[/bold]"
            )
            console.print(
                f"        [dim]Type: {rule.get('ruleType')} | "
                f"{rule.get('description')}[/dim]"
            )


def queryJiraWorkByStatus(jiraTickets: List[Dict[str, Any]]) -> None:
    """Display Jira tickets grouped by status."""
    printHeader("QUERY: Jira Tickets by Status")

    jiraByStatus: Dict[str, list] = {}
    for ticket in jiraTickets:
        jiraByStatus.setdefault(ticket['status'], []).append(ticket)

    for status in ['To Do', 'In Progress', 'Done']:
        if status not in jiraByStatus:
            continue
        tickets     = jiraByStatus[status]
        totalPoints = sum(t.get('storyPoints', 0) or 0 for t in tickets)
        console.print(
            f"\n  {colorStatus(status)}: "
            f"[bold]{len(tickets)}[/bold] tickets  "
            f"[dim]({totalPoints} story points)[/dim]"
        )
        for ticket in tickets[:5]:
            icon = colorStatusIcon(status)
            console.print(
                f"    [{icon}] [dim]{ticket['id']}[/dim]  "
                f"[bold]{ticket['summary']}[/bold]  "
                f"{colorPriority(ticket.get('priority', 'N/A'))}"
            )


def queryCriticalAlerts(alerts: List[Dict[str, Any]]) -> None:
    """Display critical alert configurations."""
    printHeader("QUERY: Critical Alerts")

    criticalAlerts = [a for a in alerts if a['severity'] == 'critical' and a['enabled']]

    console.print(
        f"\n  [bold red]{len(criticalAlerts)}[/bold red] critical alerts enabled:"
    )
    for alert in criticalAlerts:
        console.print(
            f"\n    [bold red]{alert['name']}[/bold red] "
            f"[dim]({alert['alertType']})[/dim]"
        )
        console.print(f"      [dim]Channels:[/dim] {', '.join(alert['notificationChannels'])}")
        if alert.get('threshold'):
            console.print(f"      [dim]Threshold:[/dim] {alert['threshold']}")


def queryNodeProperty(kg: KnowledgeGraph, entityQuery: str, prop: str) -> None:
    """
    Graph traversal: look up a specific property on any node by name or ID.
    Used for factual lookups like tags, status, owner, description.
    """
    # Find the best matching node
    match = None
    for nId, data in kg.graph.nodes(data=True):
        name = data.get('name') or data.get('title', '')
        if entityQuery.lower() in nId.lower() or entityQuery.lower() in name.lower():
            match = (nId, data)
            break

    if not match:
        console.print(f"\n  [yellow]Entity '{entityQuery}' not found in graph.[/yellow]")
        return

    nId, data = match
    entityType = data.get('type', 'Unknown')
    entityName = data.get('name') or data.get('title', nId)

    printHeader(f"{prop.upper()}: {entityName}")
    console.print(f"\n  [dim]ID:[/dim] {nId}  {colorEntityType(entityType)}\n")

    value = data.get(prop)
    if value is None:
        console.print(f"  [yellow]No '{prop}' property found on this entity.[/yellow]")
        return

    if isinstance(value, list):
        if not value:
            console.print(f"  [yellow]No {prop} defined.[/yellow]")
        else:
            console.print(f"  [bold]{len(value)} {prop}(s):[/bold]\n")
            for i, item in enumerate(value, 1):
                console.print(f"  [bold cyan]{i}.[/bold cyan] {item}")
    else:
        console.print(f"  [bold]{prop}:[/bold] {value}")
    console.print()


def queryKPIsByDashboard(kg: KnowledgeGraph, dashboardQuery: str) -> None:
    """
    Graph traversal: find all KPIs contained in a dashboard.
    Matches by dashboard ID or partial name — follows CONTAINS edges directly.
    """
    # Find matching dashboard node by ID or name
    dashboardId = None
    for nId, data in kg.graph.nodes(data=True):
        if data.get('type') != 'PowerBIDashboard':
            continue
        if (dashboardQuery.lower() in nId.lower() or
                dashboardQuery.lower() in data.get('name', '').lower()):
            dashboardId = nId
            break

    if not dashboardId:
        console.print(f"\n  [yellow]Dashboard '{dashboardQuery}' not found.[/yellow]")
        return

    dashData = kg.graph.nodes[dashboardId]
    printHeader(f"KPIs: {dashData.get('name', dashboardId)}")
    console.print(f"\n  [dim]ID:[/dim] {dashboardId}")
    console.print(f"  [dim]Workspace:[/dim] {dashData.get('workspace', 'N/A')}")
    console.print(f"  [dim]Status:[/dim] {colorStatus(dashData.get('status', 'N/A'))}\n")

    # Follow CONTAINS edges from dashboard → KPI nodes
    kpis = [
        tId for tId in kg.graph.successors(dashboardId)
        if kg.graph.nodes[tId].get('type') == 'PowerBIKPI'
        and kg.graph.get_edge_data(dashboardId, tId, {}).get('relation') == 'CONTAINS'
    ]

    if not kpis:
        console.print("  [yellow]No KPIs found for this dashboard.[/yellow]")
        return

    console.print(f"  [bold]{len(kpis)} KPI(s) found:[/bold]\n")
    for i, kpiId in enumerate(kpis, 1):
        kData = kg.graph.nodes[kpiId]
        console.print(f"  [bold cyan]{i}.[/bold cyan] [bold]{kData.get('name', kpiId)}[/bold]  [dim]({kpiId})[/dim]")
        console.print(f"     [dim]Description:[/dim] {kData.get('description', 'N/A')}")
        console.print(f"     [dim]Unit:[/dim] {kData.get('unit', 'N/A')}")
        console.print()


def queryGraphStatistics(kg: KnowledgeGraph) -> None:
    """Display overall graph statistics."""
    printHeader("QUERY: Graph Statistics")

    totalNodes = kg.graph.number_of_nodes()
    totalEdges = kg.graph.number_of_edges()

    nodeTypes: Dict[str, int] = {}
    for _, data in kg.graph.nodes(data=True):
        t = data.get('type', 'Unknown')
        nodeTypes[t] = nodeTypes.get(t, 0) + 1

    console.print(f"\n  [bold]Total Nodes:[/bold] [cyan]{totalNodes}[/cyan]")
    console.print(f"  [bold]Total Edges:[/bold] [cyan]{totalEdges}[/cyan]")
    console.print(f"\n  [bold]Node Types:[/bold]")
    for ntype, count in sorted(nodeTypes.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * count
        console.print(f"    {colorEntityType(ntype):<35} [cyan]{count:>3}[/cyan]  [dim]{bar}[/dim]")


# ============================================================================
# FEATURE LOOKUP FUNCTIONS
# ============================================================================

def isFeatureInProject(kg: KnowledgeGraph, vectorDb: VectorStore,
                       featureName: str, threshold: float = 1.5) -> Dict[str, Any]:
    """Check if a feature / component exists in the project."""
    results = vectorDb.search(featureName, k=10)

    matches = []
    for i, docId in enumerate(results['ids'][0]):
        distance = results['distances'][0][i]
        if distance <= threshold and docId in kg.graph.nodes:
            nodeData = kg.graph.nodes[docId]
            nodeName = nodeData.get('name') or nodeData.get('title') or nodeData.get('summary') or docId
            matches.append({
                'id':       docId,
                'name':     nodeName,
                'type':     nodeData.get('type', 'Unknown'),
                'distance': distance,
                'data':     dict(nodeData)
            })

    return {'found': len(matches) > 0, 'featureName': featureName,
            'matchCount': len(matches), 'matches': matches}


def findFeature(kg: KnowledgeGraph, vectorDb: VectorStore, featureName: str) -> None:
    """Interactive function to check if a feature exists and display results."""
    printHeader(f"FEATURE SEARCH: '{featureName}'")

    result = isFeatureInProject(kg, vectorDb, featureName)

    if result['found']:
        console.print(
            f"\n  [green]YES[/green] — [bold]'{featureName}'[/bold] found in project! "
            f"[dim]({result['matchCount']} matches)[/dim]"
        )
        console.print("\n  Related items:")
        for match in result['matches'][:5]:
            sim = (1 - match['distance'] / 2) * 100
            console.print(
                f"\n    {colorEntityType(match['type'])} [bold]{match['name']}[/bold]  "
                f"{colorScore(sim)}"
            )
            console.print(f"      [dim]ID: {match['id']}[/dim]")
            data = match['data']
            if match['type'] == 'Pipeline':
                console.print(f"      [dim]Schedule: {data.get('schedule')} | Owner: {data.get('owner')}[/dim]")
            elif match['type'] == 'Table':
                console.print(f"      [dim]Schema: {data.get('schema')} | Rows: {data.get('rowCount', 0):,}[/dim]")
            elif match['type'] == 'Column':
                console.print(f"      [dim]Type: {data.get('dataType')}[/dim]{colorPii(data.get('isPii', False))}")
            elif match['type'] == 'JiraTicket':
                console.print(f"      [dim]Status:[/dim] {colorStatus(data.get('status', ''))}  [dim]Priority:[/dim] {colorPriority(data.get('priority', ''))}")
            elif match['type'] == 'Alert':
                console.print(f"      [dim]Type: {data.get('alertType')} |[/dim] {colorSeverity(data.get('severity', ''))}")
    else:
        console.print(f"\n  [red]NO[/red] — [bold]'{featureName}'[/bold] not found in project.")
        console.print("  [dim]Try searching for related terms or check spelling.[/dim]")


def getFeatureStatus(kg: KnowledgeGraph, vectorDb: VectorStore,
                     featureName: str) -> Dict[str, Any]:
    """Get comprehensive status of a feature across the data platform."""
    result = isFeatureInProject(kg, vectorDb, featureName, threshold=1.8)

    status = {
        'feature': featureName, 'found': result['found'],
        'pipelines': [], 'tables': [], 'columns': [],
        'jiraTickets': [], 'documentation': [], 'alerts': [], 'dataQualityRules': []
    }

    if not result['found']:
        return status

    for match in result['matches']:
        nodeType = match['type']
        if nodeType == 'Pipeline':
            status['pipelines'].append({
                'id': match['id'], 'name': match['data'].get('name'),
                'status': match['data'].get('status'),
                'schedule': match['data'].get('schedule'), 'owner': match['data'].get('owner')
            })
        elif nodeType == 'Table':
            status['tables'].append({
                'id': match['id'], 'name': match['data'].get('name'),
                'schema': match['data'].get('schema'), 'rowCount': match['data'].get('rowCount')
            })
        elif nodeType == 'Column':
            status['columns'].append({
                'id': match['id'], 'name': match['data'].get('name'),
                'dataType': match['data'].get('dataType'), 'isPii': match['data'].get('isPii')
            })
        elif nodeType == 'JiraTicket':
            status['jiraTickets'].append({
                'id': match['id'], 'summary': match['data'].get('summary'),
                'status': match['data'].get('status'), 'priority': match['data'].get('priority')
            })
        elif nodeType == 'ConfluencePage':
            status['documentation'].append({
                'id': match['id'], 'title': match['data'].get('title'),
                'space': match['data'].get('space')
            })
        elif nodeType == 'Alert':
            status['alerts'].append({
                'id': match['id'], 'name': match['data'].get('name'),
                'alertType': match['data'].get('alertType'), 'severity': match['data'].get('severity')
            })
        elif nodeType == 'DataQualityRule':
            status['dataQualityRules'].append({
                'id': match['id'], 'name': match['data'].get('name'),
                'ruleType': match['data'].get('ruleType'), 'severity': match['data'].get('severity')
            })

    return status


def showFeatureStatus(kg: KnowledgeGraph, vectorDb: VectorStore, featureName: str) -> None:
    """Display comprehensive feature status across the data platform."""
    printHeader(f"FEATURE STATUS: '{featureName}'")

    status = getFeatureStatus(kg, vectorDb, featureName)

    if not status['found']:
        console.print(f"\n  [red]Feature '{featureName}' not found in project.[/red]")
        return

    console.print(f"\n  [bold]Feature '[cyan]{featureName}[/cyan]' — Data Platform Status[/bold]\n")

    if status['pipelines']:
        console.print("  [bold]PIPELINES[/bold]")
        for p in status['pipelines']:
            console.print(f"    [{colorStatusIcon(p['status'])}] [bold]{p['name']}[/bold]")
            console.print(f"        [dim]Schedule: {p['schedule']} | Owner: {p['owner']}[/dim]")

    if status['tables']:
        console.print("\n  [bold]TABLES[/bold]")
        for t in status['tables']:
            console.print(f"    [bold]{t['schema']}.{t['name']}[/bold] [dim]({(t['rowCount'] or 0):,} rows)[/dim]")

    if status['columns']:
        console.print("\n  [bold]COLUMNS[/bold]")
        for c in status['columns']:
            console.print(f"    [bold]{c['name']}[/bold] [dim]({c['dataType']})[/dim]{colorPii(c['isPii'])}")

    if status['jiraTickets']:
        console.print("\n  [bold]JIRA TICKETS[/bold]")
        for t in status['jiraTickets']:
            icon = colorStatusIcon(t['status'])
            console.print(f"    [{icon}] [dim]{t['id']}:[/dim] [bold]{t['summary']}[/bold] {colorStatus(t['status'])}")

    if status['documentation']:
        console.print("\n  [bold]DOCUMENTATION[/bold]")
        for d in status['documentation']:
            console.print(f"    [blue][[/blue]{d['space']}[blue]][/blue] {d['title']}")

    if status['alerts']:
        console.print("\n  [bold]ALERTS[/bold]")
        for a in status['alerts']:
            console.print(f"    {colorSeverity(a['severity'])}  [bold]{a['name']}[/bold] [dim]({a['alertType']})[/dim]")

    if status['dataQualityRules']:
        console.print("\n  [bold]DATA QUALITY RULES[/bold]")
        for r in status['dataQualityRules']:
            console.print(f"    [bold]{r['name']}[/bold] [dim]({r['ruleType']})[/dim]")


def listAllFeatures(kg: KnowledgeGraph) -> Dict[str, List[str]]:
    """List all features / components in the project grouped by entity type."""
    features: Dict[str, List[str]] = {}
    for nodeId, data in kg.graph.nodes(data=True):
        nodeType = data.get('type', 'Unknown')
        nodeName = data.get('name') or data.get('title') or data.get('summary') or nodeId
        features.setdefault(nodeType, []).append(nodeName)
    return features


def showAllFeatures(kg: KnowledgeGraph) -> None:
    """Display all features / components in the project."""
    printHeader("ALL PROJECT COMPONENTS")

    features = listAllFeatures(kg)
    for nodeType, names in sorted(features.items()):
        console.print(f"\n  {colorEntityType(nodeType)} [dim]({len(names)})[/dim]:")
        for name in names[:10]:
            console.print(f"    [dim]-[/dim] {name}")
        if len(names) > 10:
            console.print(f"    [dim]... and {len(names) - 10} more[/dim]")


# ============================================================================
# SEMANTIC SEARCH FUNCTIONS
# ============================================================================

def searchEntities(vectorDb: VectorStore, query: str,
                   entityType: str = None, k: int = 5) -> List[Dict[str, Any]]:
    """
    Flexible entity search using the full RAG retrieval pipeline.
    Returns rich result dicts: {id, text, metadata, vectorScore, keywordScore, combinedScore}
    """
    from rag.retriever import Retriever
    return Retriever(vectorDb, topN=k).retrieve(query, entityType=entityType)


def queryRelationshipsBySearch(kg: KnowledgeGraph, vectorDb: VectorStore,
                                query: str, entityType: str = None, k: int = 5) -> None:
    """Search for entities by semantic query and display their graph relationships."""
    typeFilter = f" [dim](type: {entityType})[/dim]" if entityType else ""
    console.print(f"\n  [bold]Search:[/bold] '[cyan]{query}[/cyan]'{typeFilter}")

    results = searchEntities(vectorDb, query, entityType, k)

    if not results:
        console.print("    [dim]No results found[/dim]")
        return

    for i, result in enumerate(results, 1):
        docId         = result["id"]
        vectorScore   = result["vectorScore"]
        combinedScore = result["combinedScore"]

        if docId not in kg.graph.nodes:
            console.print(f"    {i}. [dim]{docId}[/dim] {colorScore(combinedScore)} [dim]— not in graph[/dim]")
            continue

        nodeData = kg.graph.nodes[docId]
        nodeName = nodeData.get('name') or nodeData.get('summary') or nodeData.get('title') or docId
        nodeType = nodeData.get('type', 'Unknown')

        console.print(
            f"\n    [bold]{i}.[/bold] {colorEntityType(nodeType)} [bold]{nodeName}[/bold]  "
            f"{colorScore(combinedScore)} [dim]| semantic: {vectorScore:.0f}%[/dim]"
        )

        outgoing = list(kg.graph.successors(docId))
        if outgoing:
            console.print("       [dim]Relationships:[/dim]")
            for target in outgoing[:3]:
                edgeData   = kg.graph.get_edge_data(docId, target)
                relation   = edgeData.get('relation', 'RELATED_TO') if edgeData else 'RELATED_TO'
                targetData = kg.graph.nodes[target]
                targetName = targetData.get('name') or targetData.get('summary') or target
                targetType = targetData.get('type', 'Unknown')
                console.print(
                    f"         [blue]--[[/blue]{relation}[blue]]-->[/blue] "
                    f"{colorEntityType(targetType)} {targetName}"
                )

        incoming = list(kg.graph.predecessors(docId))
        for source in incoming[:2]:
            edgeData   = kg.graph.get_edge_data(source, docId)
            relation   = edgeData.get('relation', 'RELATED_TO') if edgeData else 'RELATED_TO'
            sourceData = kg.graph.nodes[source]
            sourceName = sourceData.get('name') or sourceData.get('summary') or source
            sourceType = sourceData.get('type', 'Unknown')
            console.print(
                f"         [blue]<--[[/blue]{relation}[blue]]--[/blue] "
                f"{colorEntityType(sourceType)} {sourceName}"
            )


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
        typeFilter = f" [dim](type: {entityType})[/dim]" if entityType else ""
        console.print(f"\n  [bold]Search:[/bold] '[cyan]{query}[/cyan]'{typeFilter}")
        results = searchEntities(vectorDb, query, entityType, k=3)
        for i, result in enumerate(results, 1):
            console.print(
                f"    {i}. [dim]{result['id']}[/dim]  {colorScore(result['combinedScore'])}"
            )


# ============================================================================
# ORCHESTRATION
# ============================================================================

def runAllQueries(kg: KnowledgeGraph, vectorDb: VectorStore,
                  data: Dict[str, Any]) -> None:
    """Execute all predefined queries on the knowledge graph."""
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
