"""
Data ingestion module for Data Platform Knowledge Graph.
Handles adding entities to both the knowledge graph and vector store.

Relationships:
    Pipeline --CONTAINS--> Table
    Table --CONTAINS--> Column
    Pipeline --DOCUMENTED_IN--> ConfluencePage
    JiraTicket --TRACKS--> Pipeline
    JiraTicket --REFERENCES--> ConfluencePage
    Alert --MONITORS--> Pipeline/Table
    DataQualityRule --VALIDATES--> Table/Column
"""

from typing import List, Dict, Any
from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore


def ingestPipelines(kg: KnowledgeGraph, vectorDb: VectorStore, pipelines: List[Dict[str, Any]]) -> None:
    """Add data pipeline nodes to the knowledge graph and vector store."""
    print("Adding Data Pipelines...")
    for pipeline in pipelines:
        kg.add_node(
            pipeline["id"],
            "Pipeline",
            name=pipeline["name"],
            description=pipeline["description"],
            owner=pipeline["owner"],
            schedule=pipeline["schedule"],
            status=pipeline["status"]
        )

        vectorDb.add(
            pipeline["id"],
            f"{pipeline['name']} - {pipeline['description']}",
            {"type": "Pipeline", "tags": ",".join(pipeline["tags"]), "owner": pipeline["owner"], "schedule": pipeline["schedule"]}
        )


def ingestTables(kg: KnowledgeGraph, vectorDb: VectorStore, tables: List[Dict[str, Any]]) -> None:
    """Add table nodes and their relationships to pipelines."""
    print("Adding Tables...")
    for table in tables:
        kg.add_node(
            table["id"],
            "Table",
            name=table["name"],
            schema=table["schema"],
            description=table["description"],
            rowCount=table["rowCount"]
        )

        # Link table to its pipeline
        if table.get("pipelineId"):
            kg.add_edge(table["pipelineId"], "CONTAINS", table["id"])

        vectorDb.add(
            table["id"],
            f"{table['schema']}.{table['name']} - {table['description']}",
            {"type": "Table", "tags": ",".join(table["tags"]), "schema": table["schema"]}
        )


def ingestColumns(kg: KnowledgeGraph, vectorDb: VectorStore, columns: List[Dict[str, Any]]) -> None:
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

        # Link column to its table
        if col.get("tableId"):
            kg.add_edge(col["tableId"], "CONTAINS", col["id"])

        piiTag = "pii" if col["isPii"] else ""
        vectorDb.add(
            col["id"],
            f"{col['name']} ({col['dataType']}) - {col['description']}",
            {"type": "Column", "dataType": col["dataType"], "isPii": str(col["isPii"]), "tags": piiTag}
        )


def ingestConfluencePages(kg: KnowledgeGraph, vectorDb: VectorStore,
                          confluencePages: List[Dict[str, Any]]) -> None:
    """Add Confluence documentation pages and their relationships to pipelines."""
    print("Adding Confluence Pages...")
    for doc in confluencePages:
        kg.add_node(
            doc["id"],
            "ConfluencePage",
            title=doc["title"],
            space=doc["space"],
            author=doc["author"]
        )

        # Link pipelines to their documentation
        for pipelineId in doc.get("relatedPipelines", []):
            kg.add_edge(pipelineId, "DOCUMENTED_IN", doc["id"])

        vectorDb.add(
            doc["id"],
            f"{doc['title']} - {doc['contentPreview']}",
            {"type": "Confluence", "tags": ",".join(doc["tags"]), "space": doc["space"]}
        )


def ingestJiraTickets(kg: KnowledgeGraph, vectorDb: VectorStore,
                      jiraTickets: List[Dict[str, Any]]) -> None:
    """Add Jira tickets and their relationships to pipelines and confluence."""
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
            storyPoints=j.get("storyPoints")
        )

        # Link Jira to pipelines it tracks
        for pipelineId in j.get("linkedPipelines", []):
            kg.add_edge(j["id"], "TRACKS", pipelineId)

        # Link Jira to referenced Confluence pages
        for confId in j.get("linkedConfluence", []):
            kg.add_edge(j["id"], "REFERENCES", confId)

        vectorDb.add(
            j["id"],
            f"{j['summary']} - {j.get('description', '')}",
            {"type": "Jira", "tags": ",".join(j["tags"]), "status": j["status"], "priority": j["priority"]}
        )


def ingestAlerts(kg: KnowledgeGraph, vectorDb: VectorStore, alerts: List[Dict[str, Any]]) -> None:
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

        # Link alerts to what they monitor
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

        # Link rule to table it validates
        if rule.get("tableId"):
            kg.add_edge(rule["id"], "VALIDATES", rule["tableId"])

        # Link rule to specific column if applicable
        if rule.get("columnId"):
            kg.add_edge(rule["id"], "VALIDATES", rule["columnId"])

        vectorDb.add(
            rule["id"],
            f"{rule['name']} - {rule['description']}",
            {"type": "DataQualityRule", "ruleType": rule["ruleType"], "severity": rule["severity"]}
        )


def ingestEnvironments(kg: KnowledgeGraph, vectorDb: VectorStore, environments: List[Dict[str, Any]]) -> None:
    """Add environment nodes."""
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


def ingestAllData(kg: KnowledgeGraph, vectorDb: VectorStore, data: Dict[str, Any]) -> None:
    """
    Ingest all data platform entities into the knowledge graph and vector store.

    Args:
        kg: KnowledgeGraph instance
        vectorDb: VectorStore instance
        data: Dictionary containing all data lists
    """
    ingestPipelines(kg, vectorDb, data['pipelines'])
    ingestTables(kg, vectorDb, data['tables'])
    ingestColumns(kg, vectorDb, data['columns'])
    ingestConfluencePages(kg, vectorDb, data['confluencePages'])
    ingestJiraTickets(kg, vectorDb, data['jiraTickets'])
    ingestAlerts(kg, vectorDb, data['alerts'])
    ingestDataQualityRules(kg, vectorDb, data['dataQualityRules'])
    ingestEnvironments(kg, vectorDb, data['environments'])
