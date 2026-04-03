"""
Data ingestion module for Data Platform Knowledge Graph.

Responsible for populating both the KnowledgeGraph (NetworkX) and the
VectorStore (ChromaDB) from the structured data in pipeline/ and dictionary/.

Each ingest function does two things for every entity:
    1. kg.add_node() — registers the entity in the graph with its attributes
    2. vectorDb.add() / addChunked() — embeds a text description for semantic search

Relationship wiring:
    Pipeline --CONTAINS-->    Table
    Pipeline --PRODUCES-->    Table        (output table of this pipeline)
    Pipeline --CONSUMES-->    Table        (input from a prior layer)
    Table    --CONTAINS-->    Column
    Pipeline --DOCUMENTED_IN--> ConfluencePage
    JiraTicket --TRACKS-->    Pipeline
    JiraTicket --REFERENCES-> ConfluencePage
    JiraTicket --MODIFIED-->  Table
    Alert    --MONITORS-->    Pipeline / Table
    DataQualityRule --VALIDATES--> Table / Column
    PowerBIDashboard --CONTAINS--> PowerBIKPI
    PowerBIKPI --READS_FROM-->     Table / Column
    DataDictionaryEntry --DEFINES-->       Column
    DataDictionaryEntry --MAPS_TO-->       Column  (Silver/Bronze lineage)
    DataDictionaryEntry --REFERENCED_IN--> ConfluencePage
    DataDictionaryEntry --TRACKED_BY-->    JiraTicket
    DataDictionaryEntry --MEASURED_BY-->   PowerBIKPI
"""

from typing import List, Dict, Any
from graph.knowledge_graph import KnowledgeGraph
from rag.vectorstore import VectorStore


def ingestPipelines(kg: KnowledgeGraph, vectorDb: VectorStore,
                    pipelines: List[Dict[str, Any]]) -> None:
    """Add data pipeline nodes to the knowledge graph and vector store."""
    print("Adding Data Pipelines...")
    for pipeline in pipelines:
        # Store all pipeline attributes on the KG node for graph traversal queries
        kg.add_node(
            pipeline["id"],
            "Pipeline",
            name=pipeline["name"],
            description=pipeline["description"],
            owner=pipeline["owner"],
            schedule=pipeline["schedule"],
            status=pipeline["status"],
            layer=pipeline.get("layer", ""),
            sourceSystem=pipeline.get("sourceSystem", ""),
            sourceLayer=pipeline.get("sourceLayer", "")
        )

        # Include layer tag in the embedded text so queries like
        # "Bronze ingestion pipelines" surface the right results
        layerInfo = f" [Layer: {pipeline['layer']}]" if pipeline.get("layer") else ""
        vectorDb.add(
            pipeline["id"],
            f"{pipeline['name']}{layerInfo} - {pipeline['description']}",
            {"type": "Pipeline", "tags": ",".join(pipeline["tags"]),
             "owner": pipeline["owner"], "schedule": pipeline["schedule"],
             "layer": pipeline.get("layer", "")}
        )


def ingestTables(kg: KnowledgeGraph, vectorDb: VectorStore,
                 tables: List[Dict[str, Any]]) -> None:
    """Add table nodes and their relationships to pipelines."""
    print("Adding Tables...")
    for table in tables:
        # Normalise layer: some tables use "schema" as the layer indicator
        layer = table.get("layer", table["schema"])

        kg.add_node(
            table["id"],
            "Table",
            name=table["name"],
            schema=table["schema"],
            layer=layer,
            database=table.get("database", ""),
            description=table["description"],
            rowCount=table["rowCount"]
        )

        # Wire table to its source pipeline (bidirectional semantics):
        # CONTAINS = pipeline owns the table, PRODUCES = pipeline writes to it
        if table.get("pipelineId"):
            kg.add_edge(table["pipelineId"], "CONTAINS", table["id"])
            kg.add_edge(table["pipelineId"], "PRODUCES", table["id"])

        # Prefix schema with layer label so "BRONZE sales_raw" is more findable
        vectorDb.add(
            table["id"],
            f"[{layer.upper()}] {table['schema']}.{table['name']} - {table['description']}",
            {"type": "Table", "tags": ",".join(table["tags"]),
             "schema": table["schema"], "layer": layer,
             "database": table.get("database", "")}
        )


def ingestColumns(kg: KnowledgeGraph, vectorDb: VectorStore,
                  columns: List[Dict[str, Any]]) -> None:
    """Add column nodes and their relationships to tables."""
    print("Adding Columns...")
    for col in columns:
        kg.add_node(
            col["id"],
            "Column",
            name=col["name"],
            dataType=col["dataType"],
            isPii=col["isPii"],
            isNullable=col["isNullable"],
            description=col["description"]
        )

        # Every column belongs to exactly one table
        if col.get("tableId"):
            kg.add_edge(col["tableId"], "CONTAINS", col["id"])

        # Include "pii" in the metadata tag for filtered PII-focused queries
        piiTag = "pii" if col["isPii"] else ""
        vectorDb.add(
            col["id"],
            f"{col['name']} ({col['dataType']}) - {col['description']}",
            {"type": "Column", "dataType": col["dataType"],
             "isPii": str(col["isPii"]), "tags": piiTag}
        )


def ingestConfluencePages(kg: KnowledgeGraph, vectorDb: VectorStore,
                          confluencePages: List[Dict[str, Any]]) -> None:
    """Add Confluence documentation pages and their relationships to pipelines."""
    print("Adding Confluence Pages...")
    for doc in confluencePages:
        # Only store structural metadata on the KG node — full content goes to the vector store
        kg.add_node(
            doc["id"],
            "ConfluencePage",
            title=doc["title"],
            space=doc["space"],
            author=doc["author"],
            tags=doc.get("tags", [])
        )

        # A Confluence page can document multiple pipelines
        for pipelineId in doc.get("relatedPipelines", []):
            kg.add_edge(pipelineId, "DOCUMENTED_IN", doc["id"])

        # Use addChunked — Confluence pages can have long content.
        # For short contentPreview values this is a no-op (single chunk).
        # Include tags in the embedded text so queries about tags return this page
        tagsText = f" Tags: {', '.join(doc['tags'])}." if doc.get('tags') else ""
        vectorDb.addChunked(
            doc["id"],
            f"{doc['title']} - {doc['contentPreview']}{tagsText}",
            {"type": "Confluence", "tags": ",".join(doc["tags"]), "space": doc["space"]}
        )


def ingestJiraTickets(kg: KnowledgeGraph, vectorDb: VectorStore,
                      jiraTickets: List[Dict[str, Any]]) -> None:
    """Add Jira tickets and their relationships to pipelines, Confluence, and tables."""
    print("Adding Jira Tickets...")
    for j in jiraTickets:
        kg.add_node(
            j["id"],
            "JiraTicket",
            summary=j["summary"],
            issueType=j["issueType"],
            status=j["status"],
            priority=j["priority"],
            assignee=j["assignee"],
            storyPoints=j.get("storyPoints"),
            linkedPipelines=j.get("linkedPipelines", []),
            linkedConfluence=j.get("linkedConfluence", []),
            tags=j.get("tags", [])
        )

        # TRACKS: ticket owns work on a pipeline (e.g. a feature or bug fix)
        for pipelineId in j.get("linkedPipelines", []):
            kg.add_edge(j["id"], "TRACKS", pipelineId)

        # REFERENCES: ticket links to supporting documentation
        for confId in j.get("linkedConfluence", []):
            kg.add_edge(j["id"], "REFERENCES", confId)

        # MODIFIED: ticket caused a schema change on a table — key for impact analysis
        for tableId in j.get("modifiedTables", []):
            kg.add_edge(j["id"], "MODIFIED", tableId)

        # Use addChunked — Jira descriptions can be long (acceptance criteria, etc.)
        vectorDb.addChunked(
            j["id"],
            f"{j['summary']} - {j.get('description', '')}",
            {"type": "Jira", "tags": ",".join(j["tags"]),
             "status": j["status"], "priority": j["priority"]}
        )


def ingestAlerts(kg: KnowledgeGraph, vectorDb: VectorStore,
                 alerts: List[Dict[str, Any]]) -> None:
    """Add alert configurations and their monitoring relationships."""
    print("Adding Alerts...")
    for alert in alerts:
        kg.add_node(
            alert["id"],
            "Alert",
            name=alert["name"],
            alertType=alert["alertType"],
            severity=alert["severity"],
            enabled=alert["enabled"],
            threshold=alert.get("threshold", "")
        )

        # An alert monitors either a pipeline (SLA / failure) or a table (row count / freshness)
        if alert.get("pipelineId"):
            kg.add_edge(alert["id"], "MONITORS", alert["pipelineId"])
        if alert.get("tableId"):
            kg.add_edge(alert["id"], "MONITORS", alert["tableId"])

        vectorDb.add(
            alert["id"],
            f"{alert['name']} - {alert['alertType']} ({alert['severity']})",
            {"type": "Alert", "alertType": alert["alertType"], "severity": alert["severity"]}
        )


def ingestDataQualityRules(kg: KnowledgeGraph, vectorDb: VectorStore,
                           dataQualityRules: List[Dict[str, Any]]) -> None:
    """Add data quality rules and their validation relationships."""
    print("Adding Data Quality Rules...")
    for rule in dataQualityRules:
        kg.add_node(
            rule["id"],
            "DataQualityRule",
            name=rule["name"],
            ruleType=rule["ruleType"],
            severity=rule["severity"],
            description=rule["description"],
            enabled=rule["enabled"]
        )

        # A rule can validate at table level (row count, freshness) OR column level (nulls, format)
        if rule.get("tableId"):
            kg.add_edge(rule["id"], "VALIDATES", rule["tableId"])
        if rule.get("columnId"):
            kg.add_edge(rule["id"], "VALIDATES", rule["columnId"])

        vectorDb.add(
            rule["id"],
            f"{rule['name']} - {rule['description']}",
            {"type": "DataQualityRule", "ruleType": rule["ruleType"], "severity": rule["severity"]}
        )


def ingestEnvironments(kg: KnowledgeGraph, vectorDb: VectorStore,
                       environments: List[Dict[str, Any]]) -> None:
    """Add environment nodes (Dev, Staging, Prod)."""
    print("Adding Environments...")
    for env in environments:
        kg.add_node(
            env["id"],
            "Environment",
            name=env["name"],
            envType=env["type"],
            url=env["url"],
            status=env["status"]
        )

        vectorDb.add(
            env["id"],
            f"{env['name']} environment - {env['url']}",
            {"type": "Environment", "envType": env["type"], "status": env["status"]}
        )


def ingestPowerBIDashboards(kg: KnowledgeGraph, vectorDb: VectorStore,
                             dashboards: List[Dict[str, Any]]) -> None:
    """Add Power BI dashboard nodes and their relationships to source tables."""
    print("Adding Power BI Dashboards...")
    for dash in dashboards:
        kg.add_node(
            dash["id"],
            "PowerBIDashboard",
            name=dash["name"],
            description=dash["description"],
            workspace=dash["workspace"],
            owner=dash["owner"],
            refreshSchedule=dash["refreshSchedule"],
            status=dash["status"]
        )

        # Direct table reads — used for impact analysis:
        # "If table X changes, which dashboards need to be checked?"
        for tableId in dash.get("readsFromTables", []):
            kg.add_edge(dash["id"], "READS_FROM", tableId)

        # Include KPI IDs in the dashboard text so the LLM can see all KPIs
        # directly from the dashboard record — not just from individual KPI retrieval
        kpiList = dash.get("containsKPIs", [])
        kpiText = f" Contains KPIs: {', '.join(kpiList)}." if kpiList else ""
        vectorDb.add(
            dash["id"],
            f"Power BI Dashboard: {dash['name']} - {dash['description']}{kpiText}",
            {"type": "PowerBIDashboard", "tags": ",".join(dash["tags"]),
             "workspace": dash["workspace"], "owner": dash["owner"]}
        )


def ingestPowerBIKPIs(kg: KnowledgeGraph, vectorDb: VectorStore,
                       kpis: List[Dict[str, Any]]) -> None:
    """Add Power BI KPI nodes and their relationships to dashboards, tables, and columns."""
    print("Adding Power BI KPIs...")
    for kpi in kpis:
        kg.add_node(
            kpi["id"],
            "PowerBIKPI",
            name=kpi["name"],
            description=kpi["description"],
            calculation=kpi["calculation"],
            unit=kpi["unit"],
            target=kpi["target"]
        )

        # Primary dashboard membership
        if kpi.get("dashboardId"):
            kg.add_edge(kpi["dashboardId"], "CONTAINS", kpi["id"])

        # A KPI can appear in multiple dashboards (e.g. Revenue shown on both
        # Executive and Sales Performance dashboards)
        for dashId in kpi.get("usedInDashboards", []):
            if dashId != kpi.get("dashboardId"):    # avoid duplicate edge
                kg.add_edge(dashId, "CONTAINS", kpi["id"])

        # KPI → Table and KPI → Column edges enable column-level impact analysis:
        # "If col_rn_gd_revenue is renamed, which KPIs break?"
        for tableId in kpi.get("readsFromTables", []):
            kg.add_edge(kpi["id"], "READS_FROM", tableId)
        for colId in kpi.get("readsFromColumns", []):
            kg.add_edge(kpi["id"], "READS_FROM", colId)

        # Include all dashboards this KPI appears in so it surfaces for any
        # of its associated dashboards during retrieval — not just the primary one
        allDashboards = list({kpi.get("dashboardId", "")} | set(kpi.get("usedInDashboards", [])))
        allDashboards = [d for d in allDashboards if d]
        dashboardText = f" Used in dashboards: {', '.join(allDashboards)}." if allDashboards else ""
        vectorDb.add(
            kpi["id"],
            f"Power BI KPI: {kpi['name']} - {kpi['description']} Calculation: {kpi['calculation']}.{dashboardText}",
            {"type": "PowerBIKPI", "tags": ",".join(kpi["tags"]), "unit": kpi["unit"]}
        )


def ingestDataDictionary(kg: KnowledgeGraph, vectorDb: VectorStore,
                          dictionary: List[Dict[str, Any]]) -> None:
    """
    Add Data Dictionary / Ontology entries linking all entity types.

    Dictionary entries are the "hub" nodes that connect business terminology
    to technical artefacts — they bridge Databricks columns, Confluence docs,
    Power BI KPIs, and Jira tickets under a single business concept.
    """
    print("Adding Data Dictionary entries...")
    for entry in dictionary:
        kg.add_node(
            entry["id"],
            "DataDictionaryEntry",
            term=entry["term"],
            definition=entry["definition"],
            domain=entry["domain"],
            owner=entry["owner"]
        )

        # DEFINES: this term is the authoritative definition of a Gold column
        if entry.get("sourceColumn"):
            kg.add_edge(entry["id"], "DEFINES", entry["sourceColumn"])

        # MAPS_TO: links the same concept across layers (Silver/Bronze columns)
        if entry.get("silverColumn"):
            kg.add_edge(entry["id"], "MAPS_TO", entry["silverColumn"])
        if entry.get("bronzeColumn"):
            kg.add_edge(entry["id"], "MAPS_TO", entry["bronzeColumn"])

        # Cross-system linkage — a single term can span multiple Confluence pages,
        # Jira tickets (e.g. DQ incidents), and Power BI KPIs
        for confId in entry.get("relatedConfluence", []):
            kg.add_edge(entry["id"], "REFERENCED_IN", confId)
        for jiraId in entry.get("relatedJiraTickets", []):
            kg.add_edge(entry["id"], "TRACKED_BY", jiraId)
        for kpiId in entry.get("relatedKPIs", []):
            kg.add_edge(entry["id"], "MEASURED_BY", kpiId)

        vectorDb.add(
            entry["id"],
            f"Data Dictionary: {entry['term']} - {entry['definition']}",
            {"type": "DataDictionaryEntry", "tags": ",".join(entry["tags"]),
             "domain": entry["domain"], "term": entry["term"]}
        )


def ingestAllData(kg: KnowledgeGraph, vectorDb: VectorStore,
                  data: Dict[str, Any]) -> None:
    """
    Ingest all data platform entities into the knowledge graph and vector store.

    Ingestion order matters for relationship wiring:
        Pipelines must exist before tables (CONTAINS edges point from pipeline → table).
        Tables must exist before columns (CONTAINS edges point from table → column).
        All other entities (Jira, Confluence, Alerts, etc.) can be ingested in any order
        because their edges point to already-registered pipeline/table nodes.

    Args:
        kg:      KnowledgeGraph instance (empty at start of session)
        vectorDb: VectorStore instance (empty at start of session)
        data:    Dict with keys matching the ingest function parameters below
    """
    # Foundation: pipelines → tables → columns (strict order for edge wiring)
    ingestPipelines(kg, vectorDb, data['pipelines'])
    ingestTables(kg, vectorDb, data['tables'])
    ingestColumns(kg, vectorDb, data['columns'])

    # Cross-system entities (order-independent after pipeline/table/column are loaded)
    ingestConfluencePages(kg, vectorDb, data['confluencePages'])
    ingestJiraTickets(kg, vectorDb, data['jiraTickets'])
    ingestAlerts(kg, vectorDb, data['alerts'])
    ingestDataQualityRules(kg, vectorDb, data['dataQualityRules'])
    ingestEnvironments(kg, vectorDb, data['environments'])

    # Power BI layer — depends on tables/columns being in the graph for READS_FROM edges
    ingestPowerBIDashboards(kg, vectorDb, data.get('powerBIDashboards', []))
    ingestPowerBIKPIs(kg, vectorDb, data.get('powerBIKPIs', []))

    # Data dictionary — depends on all other nodes existing for DEFINES/MEASURED_BY/etc.
    ingestDataDictionary(kg, vectorDb, data.get('dataDictionary', []))
