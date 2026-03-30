"""
Ontology — Entity Types & Relationship Definitions

Defines the canonical entity types, relationship types, and cross-system
mapping rules for the Data Platform Knowledge Graph.
This ontology governs how entities from Databricks, Confluence, Power BI,
Jira, and the Data Dictionary interrelate.
"""

from typing import Dict, List

# =============================================================================
# ENTITY TYPES
# =============================================================================

ENTITY_TYPES: List[str] = [
    "Pipeline",            # Databricks / Airflow pipeline
    "Table",               # Databricks Unity Catalog table (Bronze/Silver/Gold)
    "Column",              # Column within a table
    "ConfluencePage",      # Confluence documentation page
    "JiraTicket",          # Jira issue (Story, Bug, Epic, Task)
    "Alert",               # Monitoring alert (pipeline failure, SLA breach)
    "DataQualityRule",     # Great Expectations / DQ rule on a table/column
    "Environment",         # Databricks workspace environment (Dev/Staging/Prod)
    "PowerBIDashboard",    # Power BI dashboard / report
    "PowerBIKPI",          # KPI tile within a Power BI dashboard
    "DataDictionaryEntry", # Business term / ontology entry
]

# =============================================================================
# RELATIONSHIP TYPES
# =============================================================================

RELATIONSHIP_TYPES: Dict[str, str] = {
    # Pipeline → Table
    "CONTAINS":       "Pipeline contains / owns a table",
    "PRODUCES":       "Pipeline writes / produces a table",
    "CONSUMES":       "Pipeline reads / consumes a table from a prior layer",

    # Table → Column
    # (CONTAINS reused: Table --CONTAINS--> Column)

    # Pipeline → ConfluencePage
    "DOCUMENTED_IN":  "Pipeline is documented in a Confluence page",

    # JiraTicket → Pipeline / Table / ConfluencePage
    "TRACKS":         "Jira ticket tracks work on a pipeline",
    "REFERENCES":     "Jira ticket references a Confluence page",
    "MODIFIED":       "Jira ticket modified a table (schema change, column rename, etc.)",

    # Alert → Pipeline / Table
    "MONITORS":       "Alert monitors a pipeline or table for failures/breaches",

    # DataQualityRule → Table / Column
    "VALIDATES":      "Data quality rule validates a table or column",

    # PowerBIDashboard → PowerBIKPI
    # (CONTAINS reused: Dashboard --CONTAINS--> KPI)

    # PowerBIKPI → Table / Column
    "READS_FROM":     "Power BI KPI reads data from a table or column",

    # DataDictionaryEntry → Column / ConfluencePage / JiraTicket / PowerBIKPI
    "DEFINES":        "Dictionary entry is the business definition of a column (Gold layer)",
    "MAPS_TO":        "Dictionary entry maps to a column in a different layer (Silver/Bronze lineage)",
    "REFERENCED_IN":  "Dictionary entry is documented in a Confluence page",
    "TRACKED_BY":     "Dictionary entry is related to a Jira ticket",
    "MEASURED_BY":    "Dictionary entry is measured / computed as a Power BI KPI",
}

# =============================================================================
# LAYER DEFINITIONS (Medallion Architecture)
# =============================================================================

LAYERS: Dict[str, Dict] = {
    "bronze": {
        "label": "Bronze",
        "description": "Raw landing zone — data ingested as-is from source systems (SAP, Nielsen IQ, Salesforce CRM). No transformations. May contain duplicates, raw currency codes, unnormalised values.",
        "storage": "Databricks Unity Catalog — bronze schema",
        "ingestionMethod": ["Auto Loader", "JDBC", "API pull", "file drop"],
    },
    "silver": {
        "label": "Silver",
        "description": "Cleansed and conformed layer — deduplication, currency normalisation, code mapping, schema standardisation. Business-consumable but not yet aggregated.",
        "storage": "Databricks Unity Catalog — silver schema",
        "transformations": ["deduplication", "currency_normalisation", "code_mapping", "brand_hierarchy_enrichment"],
    },
    "gold": {
        "label": "Gold",
        "description": "Business-ready aggregation layer — KPIs, summaries, and metrics consumed directly by Power BI dashboards. Single source of truth for reporting.",
        "storage": "Databricks Unity Catalog — gold schema",
        "consumers": ["Power BI", "Tableau", "Ad-hoc SQL", "Data Science"],
    },
}

# =============================================================================
# SOURCE SYSTEM REGISTRY
# =============================================================================

SOURCE_SYSTEMS: List[Dict] = [
    {
        "id": "sap_s4hana",
        "name": "SAP S/4HANA",
        "type": "ERP",
        "description": "Core enterprise resource planning system. Source for sales transactions, billing documents, and financial data.",
        "extractionMethod": "JDBC / SAP RFC",
        "layer": "bronze",
    },
    {
        "id": "sap_mdm",
        "name": "SAP MDM",
        "type": "Master Data Management",
        "description": "Product master data management system. Source for SKU definitions, brand hierarchy, nutritional classifications.",
        "extractionMethod": "JDBC",
        "layer": "bronze",
    },
    {
        "id": "nielsen_iq",
        "name": "Nielsen IQ",
        "type": "Market Data Provider",
        "description": "Third-party retail audit and consumer panel data provider. Source for market share, distribution coverage, and consumer penetration metrics.",
        "extractionMethod": "File drop (SFTP)",
        "layer": "bronze",
    },
    {
        "id": "salesforce_crm",
        "name": "Salesforce CRM",
        "type": "CRM",
        "description": "Customer relationship management system. Source for consumer interactions, HCP engagements, and loyalty program data.",
        "extractionMethod": "Salesforce REST API",
        "layer": "bronze",
    },
]

# =============================================================================
# ID PREFIX CONVENTIONS
# =============================================================================

ID_PREFIXES: Dict[str, str] = {
    "pipeline_": "Pipeline",
    "table_":    "Table",
    "col_":      "Column",
    "conf_":     "ConfluencePage",
    "DATA-":     "JiraTicket",
    "RN-":       "JiraTicket",
    "alert_":    "Alert",
    "dq_":       "DataQualityRule",
    "env_":      "Environment",
    "pbi_":      "PowerBIDashboard",
    "kpi_":      "PowerBIKPI",
    "dict_":     "DataDictionaryEntry",
}


def resolveEntityType(entityId: str) -> str:
    """Infer entity type from its ID prefix."""
    for prefix, entityType in ID_PREFIXES.items():
        if entityId.startswith(prefix):
            return entityType
    return "Unknown"
