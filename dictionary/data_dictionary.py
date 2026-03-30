"""
Data Dictionary & Supporting Metadata

Centralises Confluence documentation, Jira tickets, alerts, data quality rules,
environments, Power BI dashboards/KPIs, and the ontology dictionary that links
all entities across Databricks, Confluence, Power BI, and Jira.
"""

# =============================================================================
# CONFLUENCE PAGES (Documentation)
# =============================================================================

confluencePages = [
    {
        "id": "conf_customer_pipeline",
        "title": "Customer Data Pipeline Architecture",
        "space": "DATA_ENGINEERING",
        "author": "john.engineer",
        "tags": ["architecture", "customer", "pipeline", "design"],
        "contentPreview": "Technical design document for customer data ingestion pipeline including data flow and transformations",
        "relatedPipelines": ["pipeline_customer_ingestion"]
    },
    {
        "id": "conf_order_processing",
        "title": "Order Processing Pipeline Runbook",
        "space": "DATA_OPS",
        "author": "sarah.ops",
        "tags": ["runbook", "orders", "operations", "troubleshooting"],
        "contentPreview": "Operational runbook for order processing pipeline with failure handling procedures",
        "relatedPipelines": ["pipeline_order_processing"]
    },
    {
        "id": "conf_inventory_design",
        "title": "Inventory Sync Design Document",
        "space": "SUPPLY_CHAIN",
        "author": "mike.analyst",
        "tags": ["design", "inventory", "sync", "warehouse"],
        "contentPreview": "Design specification for real-time inventory synchronization across warehouses",
        "relatedPipelines": ["pipeline_inventory_sync"]
    },
    {
        "id": "conf_analytics_guide",
        "title": "User Analytics Data Dictionary",
        "space": "ANALYTICS",
        "author": "lisa.analytics",
        "tags": ["dictionary", "analytics", "metrics", "definitions"],
        "contentPreview": "Data dictionary and metric definitions for user analytics tables",
        "relatedPipelines": ["pipeline_user_analytics"]
    },
    {
        "id": "conf_fraud_ml",
        "title": "Fraud Detection ML Model Documentation",
        "space": "ML_PLATFORM",
        "author": "alex.ml",
        "tags": ["ml", "fraud", "model", "documentation"],
        "contentPreview": "Documentation for fraud detection ML model including features and thresholds",
        "relatedPipelines": ["pipeline_fraud_detection"]
    },
    {
        "id": "conf_data_governance",
        "title": "Data Governance Policies",
        "space": "GOVERNANCE",
        "author": "compliance.team",
        "tags": ["governance", "compliance", "pii", "policies"],
        "contentPreview": "Enterprise data governance policies for PII handling and data retention",
        "relatedPipelines": ["pipeline_customer_ingestion", "pipeline_order_processing"]
    },
    {
        "id": "conf_payment_framework",
        "title": "Payment Pluggable Framework Architecture",
        "space": "PAYMENTS",
        "author": "payment.architect",
        "tags": ["payment", "pluggable", "framework", "architecture", "gateway", "stripe", "paypal"],
        "contentPreview": "Technical architecture for the pluggable payment framework supporting multiple payment providers including Stripe, PayPal, and Square with easy provider onboarding",
        "relatedPipelines": ["pipeline_payment_processing"]
    },
    {
        "id": "conf_payment_integration",
        "title": "Payment Provider Integration Guide",
        "space": "PAYMENTS",
        "author": "payment.architect",
        "tags": ["payment", "integration", "providers", "api", "onboarding"],
        "contentPreview": "Guide for integrating new payment providers into the pluggable framework with API specifications and configuration requirements",
        "relatedPipelines": ["pipeline_payment_processing"]
    },

    # -------------------------------------------------------------------------
    # Reckitt Nutrition — Confluence Pages
    # -------------------------------------------------------------------------
    {
        "id": "conf_rn_data_lineage",
        "title": "Reckitt Nutrition Data Lineage: Bronze → Silver → Gold",
        "space": "RN_DATA_PLATFORM",
        "author": "rn.data.architect",
        "tags": ["reckitt", "nutrition", "data-lineage", "bronze", "silver", "gold", "databricks", "architecture"],
        "contentPreview": "End-to-end data lineage documentation for Reckitt Nutrition data platform. Covers SAP ingestion into Bronze, cleansing and conforming in Silver, and KPI aggregation in Gold. Includes column-level lineage mapping and transformation logic.",
        "relatedPipelines": ["pipeline_rn_bronze_sales", "pipeline_rn_silver_sales", "pipeline_rn_gold_sales_summary", "pipeline_rn_gold_kpi_metrics"]
    },
    {
        "id": "conf_rn_data_dictionary",
        "title": "Reckitt Nutrition Data Dictionary & Ontology",
        "space": "RN_DATA_PLATFORM",
        "author": "rn.data.governance",
        "tags": ["reckitt", "nutrition", "data-dictionary", "ontology", "definitions", "kpi", "governance"],
        "contentPreview": "Official data dictionary for Reckitt Nutrition data platform. Defines all business terms, KPI calculations, brand hierarchy, market codes, and ontology linking Databricks, Confluence, Power BI, and Jira. Maintained by Data Governance team.",
        "relatedPipelines": ["pipeline_rn_gold_kpi_metrics", "pipeline_rn_gold_market_share"]
    },
    {
        "id": "conf_rn_powerbi_architecture",
        "title": "Reckitt Nutrition Power BI Architecture & Report Catalog",
        "space": "RN_DATA_PLATFORM",
        "author": "rn.bi.architect",
        "tags": ["reckitt", "nutrition", "powerbi", "dashboards", "kpi", "architecture", "report-catalog"],
        "contentPreview": "Architecture and catalog of all Reckitt Nutrition Power BI dashboards. Documents which Gold tables and columns each report reads, KPI definitions, refresh schedules, and impact analysis matrix for downstream breaking changes.",
        "relatedPipelines": ["pipeline_rn_gold_kpi_metrics", "pipeline_rn_gold_sales_summary", "pipeline_rn_gold_market_share"]
    },
    {
        "id": "conf_rn_kpi_definitions",
        "title": "Reckitt Nutrition KPI Definitions & Calculation Logic",
        "space": "RN_DATA_PLATFORM",
        "author": "rn.analytics.lead",
        "tags": ["reckitt", "nutrition", "kpi", "definitions", "calculations", "revenue", "market-share"],
        "contentPreview": "Formal definitions and calculation logic for all Reckitt Nutrition KPIs: Revenue by Brand (net revenue after trade spend), Market Share % (Nielsen value share), Volume Growth YoY, Distribution Coverage (weighted), Consumer Penetration Rate.",
        "relatedPipelines": ["pipeline_rn_gold_kpi_metrics", "pipeline_rn_gold_market_share"]
    },
    {
        "id": "conf_rn_market_intelligence",
        "title": "Reckitt Nutrition Market Intelligence Platform",
        "space": "RN_MARKET_INTEL",
        "author": "rn.market.intelligence",
        "tags": ["reckitt", "nutrition", "market-intelligence", "nielsen", "market-share", "consumer-panel"],
        "contentPreview": "Market intelligence platform documentation for Reckitt Nutrition. Covers Nielsen IQ data ingestion, market share calculation methodology, consumer panel integration, and competitive benchmarking for baby nutrition and adult nutrition segments.",
        "relatedPipelines": ["pipeline_rn_bronze_market", "pipeline_rn_silver_market", "pipeline_rn_gold_market_share"]
    }
]

# =============================================================================
# JIRA TICKETS
# =============================================================================

jiraTickets = [
    {
        "id": "DATA-101",
        "summary": "Add email validation to customer pipeline",
        "description": "Implement email format validation in customer ingestion",
        "issueType": "Story",
        "status": "Done",
        "priority": "High",
        "assignee": "john.engineer",
        "tags": ["customer", "validation", "data-quality"],
        "storyPoints": 5,
        "linkedPipelines": ["pipeline_customer_ingestion"],
        "linkedConfluence": ["conf_customer_pipeline"]
    },
    {
        "id": "DATA-102",
        "summary": "Fix duplicate orders in processing pipeline",
        "description": "Investigate and fix duplicate order records appearing in gold table",
        "issueType": "Bug",
        "status": "In Progress",
        "priority": "Critical",
        "assignee": "sarah.ops",
        "tags": ["orders", "bug", "duplicates", "data-quality"],
        "storyPoints": 8,
        "linkedPipelines": ["pipeline_order_processing"],
        "linkedConfluence": ["conf_order_processing"]
    },
    {
        "id": "DATA-103",
        "summary": "Optimize inventory sync performance",
        "description": "Reduce sync latency from 15min to 5min",
        "issueType": "Task",
        "status": "To Do",
        "priority": "Medium",
        "assignee": "mike.analyst",
        "tags": ["inventory", "performance", "optimization"],
        "storyPoints": 13,
        "linkedPipelines": ["pipeline_inventory_sync"],
        "linkedConfluence": ["conf_inventory_design"]
    },
    {
        "id": "DATA-104",
        "summary": "Add new user engagement metrics",
        "description": "Add session duration and bounce rate to analytics pipeline",
        "issueType": "Story",
        "status": "Done",
        "priority": "Medium",
        "assignee": "lisa.analytics",
        "tags": ["analytics", "metrics", "engagement"],
        "storyPoints": 5,
        "linkedPipelines": ["pipeline_user_analytics"],
        "linkedConfluence": ["conf_analytics_guide"]
    },
    {
        "id": "DATA-105",
        "summary": "Update fraud model threshold",
        "description": "Adjust fraud detection threshold to reduce false positives",
        "issueType": "Task",
        "status": "In Progress",
        "priority": "High",
        "assignee": "alex.ml",
        "tags": ["fraud", "ml", "threshold", "tuning"],
        "storyPoints": 3,
        "linkedPipelines": ["pipeline_fraud_detection"],
        "linkedConfluence": ["conf_fraud_ml"]
    },
    {
        "id": "DATA-106",
        "summary": "Implement PII masking for customer data",
        "description": "Add column-level encryption for PII fields",
        "issueType": "Story",
        "status": "Done",
        "priority": "Critical",
        "assignee": "john.engineer",
        "tags": ["pii", "security", "encryption", "compliance"],
        "storyPoints": 8,
        "linkedPipelines": ["pipeline_customer_ingestion"],
        "linkedConfluence": ["conf_customer_pipeline", "conf_data_governance"]
    },
    {
        "id": "DATA-107",
        "summary": "Create order metrics dashboard",
        "description": "Build Databricks dashboard for order KPIs",
        "issueType": "Story",
        "status": "To Do",
        "priority": "Low",
        "assignee": "sarah.ops",
        "tags": ["orders", "dashboard", "reporting"],
        "storyPoints": 5,
        "linkedPipelines": ["pipeline_order_processing"],
        "linkedConfluence": []
    },
    {
        "id": "DATA-108",
        "summary": "Implement pluggable payment framework",
        "description": "Design and implement pluggable payment architecture supporting multiple providers",
        "issueType": "Epic",
        "status": "Done",
        "priority": "Critical",
        "assignee": "payment.architect",
        "tags": ["payment", "pluggable", "framework", "architecture"],
        "storyPoints": 21,
        "linkedPipelines": ["pipeline_payment_processing"],
        "linkedConfluence": ["conf_payment_framework", "conf_payment_integration"]
    },
    {
        "id": "DATA-109",
        "summary": "Add Stripe payment provider integration",
        "description": "Integrate Stripe as a payment provider in the pluggable framework",
        "issueType": "Story",
        "status": "Done",
        "priority": "High",
        "assignee": "dev.payments",
        "tags": ["payment", "stripe", "integration", "provider"],
        "storyPoints": 8,
        "linkedPipelines": ["pipeline_payment_processing"],
        "linkedConfluence": ["conf_payment_integration"]
    },
    {
        "id": "DATA-110",
        "summary": "Add PayPal payment provider integration",
        "description": "Integrate PayPal as a payment provider in the pluggable framework",
        "issueType": "Story",
        "status": "In Progress",
        "priority": "High",
        "assignee": "dev.payments",
        "tags": ["payment", "paypal", "integration", "provider"],
        "storyPoints": 8,
        "linkedPipelines": ["pipeline_payment_processing"],
        "linkedConfluence": ["conf_payment_integration"]
    },
    {
        "id": "DATA-111",
        "summary": "Payment reconciliation report",
        "description": "Create daily reconciliation report for all payment providers",
        "issueType": "Story",
        "status": "To Do",
        "priority": "Medium",
        "assignee": "dev.payments",
        "tags": ["payment", "reconciliation", "reporting"],
        "storyPoints": 5,
        "linkedPipelines": ["pipeline_payment_processing"],
        "linkedConfluence": ["conf_payment_framework"]
    },

    # -------------------------------------------------------------------------
    # Reckitt Nutrition — Jira Tickets
    # -------------------------------------------------------------------------
    {
        "id": "RN-201",
        "summary": "Build Reckitt Nutrition Bronze ingestion pipelines from SAP",
        "description": "Implement Bronze layer pipelines to ingest raw SAP S/4HANA sales data, product master, and market data into Databricks. Set up Auto Loader with schema evolution.",
        "issueType": "Epic",
        "status": "Done",
        "priority": "Critical",
        "assignee": "rn.data.engineer",
        "tags": ["reckitt", "nutrition", "bronze", "sap", "ingestion", "databricks"],
        "storyPoints": 34,
        "linkedPipelines": ["pipeline_rn_bronze_sales", "pipeline_rn_bronze_product", "pipeline_rn_bronze_market"],
        "linkedConfluence": ["conf_rn_data_lineage"],
        "modifiedTables": ["table_rn_bronze_sales_raw", "table_rn_bronze_product_raw", "table_rn_bronze_market_raw"]
    },
    {
        "id": "RN-202",
        "summary": "Implement Silver cleansing and conforming for RN sales data",
        "description": "Build Silver transformation pipeline: deduplicate SAP billing documents, normalize currency to USD, map sales org codes to Reckitt market codes, enrich with brand hierarchy from product master.",
        "issueType": "Epic",
        "status": "Done",
        "priority": "Critical",
        "assignee": "rn.data.engineer",
        "tags": ["reckitt", "nutrition", "silver", "cleansing", "normalization", "sales"],
        "storyPoints": 21,
        "linkedPipelines": ["pipeline_rn_silver_sales", "pipeline_rn_silver_product"],
        "linkedConfluence": ["conf_rn_data_lineage"],
        "modifiedTables": ["table_rn_silver_sales", "table_rn_silver_product"]
    },
    {
        "id": "RN-203",
        "summary": "Build Gold KPI metrics table for Power BI consumption",
        "description": "Create Gold layer KPI metrics table (rn_kpi_metrics) aggregating all Reckitt Nutrition KPIs. This table is the single source of truth for all Power BI dashboards. Columns: kpi_name, kpi_value, kpi_target, kpi_vs_target_pct.",
        "issueType": "Epic",
        "status": "Done",
        "priority": "Critical",
        "assignee": "rn.analytics.lead",
        "tags": ["reckitt", "nutrition", "gold", "kpi", "powerbi", "metrics"],
        "storyPoints": 13,
        "linkedPipelines": ["pipeline_rn_gold_kpi_metrics"],
        "linkedConfluence": ["conf_rn_kpi_definitions", "conf_rn_powerbi_architecture"],
        "modifiedTables": ["table_rn_gold_kpi_metrics"]
    },
    {
        "id": "RN-204",
        "summary": "Rename column net_revenue_usd to net_revenue in Silver sales table",
        "description": "Business request to rename net_revenue_usd to net_revenue in the Silver sales table to match data dictionary standard. IMPACT: This column feeds Gold sales summary which feeds Revenue by Brand KPI in Power BI. Must update Gold pipeline and Power BI dataset before renaming.",
        "issueType": "Task",
        "status": "In Progress",
        "priority": "High",
        "assignee": "rn.data.engineer",
        "tags": ["reckitt", "nutrition", "silver", "column-rename", "breaking-change", "powerbi-impact"],
        "storyPoints": 8,
        "linkedPipelines": ["pipeline_rn_silver_sales", "pipeline_rn_gold_sales_summary", "pipeline_rn_gold_kpi_metrics"],
        "linkedConfluence": ["conf_rn_data_dictionary"],
        "modifiedTables": ["table_rn_silver_sales", "table_rn_gold_sales_summary", "table_rn_gold_kpi_metrics"]
    },
    {
        "id": "RN-205",
        "summary": "Add Nielsen market share data to Reckitt Nutrition platform",
        "description": "Integrate Nielsen IQ weekly retail audit data: Bronze ingestion, Silver normalization aligned to Reckitt's category taxonomy, Gold market share calculation (value share %, volume share %, weighted distribution).",
        "issueType": "Epic",
        "status": "Done",
        "priority": "High",
        "assignee": "rn.market.intelligence",
        "tags": ["reckitt", "nutrition", "nielsen", "market-share", "market-intelligence"],
        "storyPoints": 21,
        "linkedPipelines": ["pipeline_rn_bronze_market", "pipeline_rn_silver_market", "pipeline_rn_gold_market_share"],
        "linkedConfluence": ["conf_rn_market_intelligence", "conf_rn_data_lineage"],
        "modifiedTables": ["table_rn_bronze_market_raw", "table_rn_silver_market", "table_rn_gold_market_share"]
    },
    {
        "id": "RN-206",
        "summary": "Power BI Executive Dashboard not showing correct Revenue by Brand",
        "description": "BUG: Revenue by Brand KPI tile in the Executive Dashboard shows stale data. Root cause: Gold KPI metrics pipeline (pipeline_rn_gold_kpi_metrics) failed last night due to schema change in Silver sales table. kpi_value column returned NULL for revenue metrics.",
        "issueType": "Bug",
        "status": "In Progress",
        "priority": "Critical",
        "assignee": "rn.analytics.lead",
        "tags": ["reckitt", "nutrition", "powerbi", "bug", "kpi", "revenue", "dashboard-broken"],
        "storyPoints": 5,
        "linkedPipelines": ["pipeline_rn_gold_kpi_metrics", "pipeline_rn_gold_sales_summary"],
        "linkedConfluence": ["conf_rn_powerbi_architecture"],
        "modifiedTables": ["table_rn_gold_kpi_metrics"]
    },
    {
        "id": "RN-207",
        "summary": "Create Reckitt Nutrition Data Dictionary in Confluence",
        "description": "Document all business terms, KPI definitions, brand hierarchy, and ontology mapping across Databricks (Bronze/Silver/Gold), Confluence, Power BI, and Jira. This is the master data dictionary for Reckitt Nutrition.",
        "issueType": "Story",
        "status": "Done",
        "priority": "High",
        "assignee": "rn.data.governance",
        "tags": ["reckitt", "nutrition", "data-dictionary", "ontology", "governance", "confluence"],
        "storyPoints": 8,
        "linkedPipelines": [],
        "linkedConfluence": ["conf_rn_data_dictionary", "conf_rn_kpi_definitions"],
        "modifiedTables": []
    },
    {
        "id": "RN-208",
        "summary": "Add consumer_penetration_pct column to Gold market share table",
        "description": "New column request from Market Intelligence team: add consumer_penetration_pct to rn_market_share_metrics Gold table. This will enable Consumer Penetration Rate KPI in the Market Intelligence Power BI dashboard.",
        "issueType": "Story",
        "status": "Done",
        "priority": "Medium",
        "assignee": "rn.data.engineer",
        "tags": ["reckitt", "nutrition", "gold", "consumer-penetration", "new-column", "powerbi"],
        "storyPoints": 5,
        "linkedPipelines": ["pipeline_rn_gold_market_share"],
        "linkedConfluence": ["conf_rn_kpi_definitions"],
        "modifiedTables": ["table_rn_gold_market_share"]
    }
]

# =============================================================================
# POWER BI DASHBOARDS (Reckitt Nutrition)
# =============================================================================

powerBIDashboards = [
    {
        "id": "pbi_rn_executive",
        "name": "Reckitt Nutrition Executive Dashboard",
        "description": "C-suite executive dashboard for Reckitt Nutrition showing top-line KPIs: total revenue, market share, volume growth, and distribution coverage across all brands and markets.",
        "workspace": "Reckitt Nutrition Analytics",
        "owner": "rn.bi.architect",
        "refreshSchedule": "daily",
        "status": "published",
        "tags": ["reckitt", "nutrition", "executive", "kpi", "revenue", "market-share"],
        "containsKPIs": ["kpi_rn_revenue_by_brand", "kpi_rn_market_share", "kpi_rn_volume_growth", "kpi_rn_distribution_coverage"],
        "readsFromTables": ["table_rn_gold_kpi_metrics", "table_rn_gold_sales_summary"]
    },
    {
        "id": "pbi_rn_sales_performance",
        "name": "Reckitt Nutrition Sales Performance Dashboard",
        "description": "Sales team dashboard with detailed revenue by brand, SKU-level volume analysis, net revenue management waterfall, and promotional effectiveness tracking.",
        "workspace": "Reckitt Nutrition Analytics",
        "owner": "rn.analytics.lead",
        "refreshSchedule": "daily",
        "status": "published",
        "tags": ["reckitt", "nutrition", "sales", "revenue", "sku", "nrm", "promotional"],
        "containsKPIs": ["kpi_rn_revenue_by_brand", "kpi_rn_volume_growth", "kpi_rn_nrm"],
        "readsFromTables": ["table_rn_gold_sales_summary", "table_rn_gold_kpi_metrics"]
    },
    {
        "id": "pbi_rn_market_intelligence",
        "name": "Reckitt Nutrition Market Intelligence Dashboard",
        "description": "Market intelligence report showing Reckitt Nutrition competitive position: market share by brand and geography, distribution coverage vs competition, and consumer penetration trends from Nielsen data.",
        "workspace": "Reckitt Nutrition Analytics",
        "owner": "rn.market.intelligence",
        "refreshSchedule": "weekly",
        "status": "published",
        "tags": ["reckitt", "nutrition", "market-intelligence", "nielsen", "market-share", "consumer-penetration"],
        "containsKPIs": ["kpi_rn_market_share", "kpi_rn_distribution_coverage", "kpi_rn_consumer_penetration"],
        "readsFromTables": ["table_rn_gold_market_share", "table_rn_gold_kpi_metrics"]
    },
    {
        "id": "pbi_rn_data_quality",
        "name": "Reckitt Nutrition Data Quality Dashboard",
        "description": "Data engineering monitoring dashboard: pipeline health, data quality scores, Bronze/Silver/Gold row count reconciliation, and SLA compliance for Reckitt Nutrition data platform.",
        "workspace": "Reckitt Nutrition Data Engineering",
        "owner": "rn.data.engineer",
        "refreshSchedule": "daily",
        "status": "published",
        "tags": ["reckitt", "nutrition", "data-quality", "monitoring", "pipeline-health", "sla"],
        "containsKPIs": ["kpi_rn_pipeline_sla", "kpi_rn_dq_score"],
        "readsFromTables": ["table_rn_bronze_sales_raw", "table_rn_silver_sales", "table_rn_gold_sales_summary"]
    }
]

# =============================================================================
# POWER BI KPIs (Reckitt Nutrition)
# =============================================================================

powerBIKPIs = [
    {
        "id": "kpi_rn_revenue_by_brand",
        "name": "Revenue by Brand",
        "description": "Total net revenue in USD by Reckitt Nutrition brand (Enfamil, Nutramigen, Enfalac, Mead Johnson) for the selected fiscal period. Net of trade spend deductions.",
        "dashboardId": "pbi_rn_executive",
        "calculation": "SUM(rn_gold_kpi_metrics.kpi_value) WHERE kpi_name = 'revenue_by_brand'",
        "unit": "USD",
        "target": "As per annual operating plan",
        "tags": ["revenue", "brand", "sales", "kpi", "enfamil"],
        "readsFromTables": ["table_rn_gold_kpi_metrics", "table_rn_gold_sales_summary"],
        "readsFromColumns": ["col_rn_kpi_value", "col_rn_gd_revenue", "col_rn_gd_sales_brand"],
        "usedInDashboards": ["pbi_rn_executive", "pbi_rn_sales_performance"]
    },
    {
        "id": "kpi_rn_market_share",
        "name": "Market Share %",
        "description": "Reckitt Nutrition value market share percentage in baby nutrition and adult nutrition categories, sourced from Nielsen IQ retail audit data.",
        "dashboardId": "pbi_rn_executive",
        "calculation": "AVG(rn_gold_market_share.value_share_pct) by brand and market",
        "unit": "Percentage",
        "target": "Defined per brand per market in annual plan",
        "tags": ["market-share", "nielsen", "competitive", "kpi"],
        "readsFromTables": ["table_rn_gold_market_share", "table_rn_gold_kpi_metrics"],
        "readsFromColumns": ["col_rn_ms_value_share", "col_rn_kpi_value"],
        "usedInDashboards": ["pbi_rn_executive", "pbi_rn_market_intelligence"]
    },
    {
        "id": "kpi_rn_volume_growth",
        "name": "Volume Growth YoY %",
        "description": "Year-over-year volume growth in cases for Reckitt Nutrition brands. Calculated from Gold sales summary comparing current vs prior year period.",
        "dashboardId": "pbi_rn_sales_performance",
        "calculation": "(current_period_cases - prior_year_cases) / prior_year_cases * 100",
        "unit": "Percentage",
        "target": "Positive growth vs prior year",
        "tags": ["volume", "growth", "yoy", "sales", "kpi"],
        "readsFromTables": ["table_rn_gold_sales_summary", "table_rn_gold_kpi_metrics"],
        "readsFromColumns": ["col_rn_gd_volume", "col_rn_gd_period", "col_rn_kpi_value"],
        "usedInDashboards": ["pbi_rn_executive", "pbi_rn_sales_performance"]
    },
    {
        "id": "kpi_rn_distribution_coverage",
        "name": "Distribution Coverage %",
        "description": "Weighted distribution coverage percentage: proportion of stores (weighted by their sales volume) that carry Reckitt Nutrition products. Sourced from Nielsen distribution data.",
        "dashboardId": "pbi_rn_market_intelligence",
        "calculation": "AVG(rn_gold_market_share.weighted_distribution_pct) by brand and market",
        "unit": "Percentage",
        "target": ">85% weighted distribution in key markets",
        "tags": ["distribution", "coverage", "nielsen", "kpi", "market"],
        "readsFromTables": ["table_rn_gold_market_share", "table_rn_gold_kpi_metrics"],
        "readsFromColumns": ["col_rn_ms_distribution", "col_rn_kpi_value"],
        "usedInDashboards": ["pbi_rn_executive", "pbi_rn_market_intelligence"]
    },
    {
        "id": "kpi_rn_consumer_penetration",
        "name": "Consumer Penetration Rate %",
        "description": "Percentage of households that purchased at least one Reckitt Nutrition product in the rolling 12-week period. Sourced from Nielsen consumer panel data.",
        "dashboardId": "pbi_rn_market_intelligence",
        "calculation": "AVG(rn_gold_market_share.consumer_penetration_pct) by brand",
        "unit": "Percentage",
        "target": "Growth vs prior year period",
        "tags": ["consumer", "penetration", "panel", "nielsen", "kpi", "households"],
        "readsFromTables": ["table_rn_gold_market_share", "table_rn_gold_kpi_metrics"],
        "readsFromColumns": ["col_rn_ms_penetration", "col_rn_kpi_value"],
        "usedInDashboards": ["pbi_rn_market_intelligence"]
    },
    {
        "id": "kpi_rn_nrm",
        "name": "Net Revenue Management (NRM)",
        "description": "Net revenue after all trade spend adjustments (promotional funding, listing fees, volume rebates). Key P&L metric for Reckitt Nutrition commercial team.",
        "dashboardId": "pbi_rn_sales_performance",
        "calculation": "SUM(rn_gold_sales_summary.total_net_revenue_usd) - trade_spend_deductions",
        "unit": "USD",
        "target": "Positive NRM vs gross revenue",
        "tags": ["nrm", "net-revenue", "trade-spend", "commercial", "kpi"],
        "readsFromTables": ["table_rn_gold_sales_summary", "table_rn_gold_kpi_metrics"],
        "readsFromColumns": ["col_rn_gd_revenue", "col_rn_kpi_value", "col_rn_kpi_vs_target"],
        "usedInDashboards": ["pbi_rn_sales_performance"]
    },
    {
        "id": "kpi_rn_pipeline_sla",
        "name": "Pipeline SLA Compliance %",
        "description": "Percentage of Reckitt Nutrition Databricks pipelines that completed within their SLA window. Monitored in Data Quality Dashboard.",
        "dashboardId": "pbi_rn_data_quality",
        "calculation": "COUNT(pipelines_on_time) / COUNT(total_pipelines) * 100",
        "unit": "Percentage",
        "target": ">99% pipeline SLA compliance",
        "tags": ["sla", "pipeline", "monitoring", "data-engineering", "kpi"],
        "readsFromTables": ["table_rn_gold_kpi_metrics"],
        "readsFromColumns": ["col_rn_kpi_value", "col_rn_kpi_name"],
        "usedInDashboards": ["pbi_rn_data_quality"]
    },
    {
        "id": "kpi_rn_dq_score",
        "name": "Data Quality Score",
        "description": "Composite data quality score across all Reckitt Nutrition Gold tables: null rates, referential integrity, duplicate rates, and freshness. Displayed in Data Quality Dashboard.",
        "dashboardId": "pbi_rn_data_quality",
        "calculation": "Weighted average of null_rate, duplicate_rate, freshness_score across gold tables",
        "unit": "Score (0-100)",
        "target": ">95 data quality score",
        "tags": ["data-quality", "score", "monitoring", "governance", "kpi"],
        "readsFromTables": ["table_rn_gold_kpi_metrics", "table_rn_gold_sales_summary"],
        "readsFromColumns": ["col_rn_kpi_value", "col_rn_kpi_vs_target"],
        "usedInDashboards": ["pbi_rn_data_quality"]
    }
]

# =============================================================================
# DATA DICTIONARY / ONTOLOGY (linking Databricks, Confluence, Power BI, Jira)
# =============================================================================

dataDictionary = [
    {
        "id": "dict_revenue",
        "term": "Net Revenue (USD)",
        "definition": "Net sales value in USD after trade spend deductions (promotional funding, listing fees, volume rebates). The primary top-line commercial metric for Reckitt Nutrition.",
        "domain": "Commercial",
        "owner": "rn.data.governance",
        "tags": ["revenue", "nrm", "commercial", "finance"],
        "sourceColumn": "col_rn_gd_revenue",
        "silverColumn": "col_rn_sv_sales_revenue_usd",
        "bronzeColumn": "col_rn_br_sales_revenue",
        "relatedKPIs": ["kpi_rn_revenue_by_brand", "kpi_rn_nrm"],
        "relatedDashboards": ["pbi_rn_executive", "pbi_rn_sales_performance"],
        "relatedConfluence": ["conf_rn_kpi_definitions", "conf_rn_data_dictionary"],
        "relatedJiraTickets": ["RN-203", "RN-204"]
    },
    {
        "id": "dict_market_share",
        "term": "Market Share %",
        "definition": "Reckitt Nutrition's percentage share of the total category value sales in a given market, as measured by Nielsen IQ retail audit. Calculated as Reckitt Nutrition value sales / total category value sales × 100.",
        "domain": "Market Intelligence",
        "owner": "rn.market.intelligence",
        "tags": ["market-share", "nielsen", "competitive", "category"],
        "sourceColumn": "col_rn_ms_value_share",
        "relatedKPIs": ["kpi_rn_market_share"],
        "relatedDashboards": ["pbi_rn_executive", "pbi_rn_market_intelligence"],
        "relatedConfluence": ["conf_rn_kpi_definitions", "conf_rn_market_intelligence", "conf_rn_data_dictionary"],
        "relatedJiraTickets": ["RN-205"]
    },
    {
        "id": "dict_sku",
        "term": "SKU (Stock Keeping Unit)",
        "definition": "A unique product identifier for a specific Reckitt Nutrition product in a specific pack size and format. Maps SAP material_number (Bronze) to Reckitt internal sku_code (Silver/Gold). Each SKU belongs to a Brand > Sub-brand > Pack size hierarchy.",
        "domain": "Product",
        "owner": "rn.data.governance",
        "tags": ["sku", "product", "material-number", "brand-hierarchy"],
        "sourceColumn": "col_rn_sv_sales_sku",
        "bronzeColumn": "col_rn_br_sales_sku",
        "relatedKPIs": ["kpi_rn_revenue_by_brand", "kpi_rn_volume_growth"],
        "relatedDashboards": ["pbi_rn_sales_performance"],
        "relatedConfluence": ["conf_rn_data_dictionary"],
        "relatedJiraTickets": ["RN-201", "RN-202"]
    },
    {
        "id": "dict_brand",
        "term": "Brand",
        "definition": "Reckitt Nutrition brand identifier. Current portfolio: Enfamil (infant formula USA), Nutramigen (hypoallergenic formula), Enfalac (APAC infant formula), Mead Johnson (emerging markets). Maps to brand_name column in Silver and Gold layers.",
        "domain": "Commercial",
        "owner": "rn.data.governance",
        "tags": ["brand", "enfamil", "nutramigen", "enfalac", "mead-johnson", "portfolio"],
        "sourceColumn": "col_rn_gd_sales_brand",
        "silverColumn": "col_rn_sv_sales_brand",
        "relatedKPIs": ["kpi_rn_revenue_by_brand"],
        "relatedDashboards": ["pbi_rn_executive", "pbi_rn_sales_performance"],
        "relatedConfluence": ["conf_rn_data_dictionary", "conf_rn_kpi_definitions"],
        "relatedJiraTickets": ["RN-202"]
    },
    {
        "id": "dict_fiscal_period",
        "term": "Fiscal Period",
        "definition": "Reckitt's 13-period fiscal year in YYYY-PP format (e.g. 2024-P03 = March 2024). Reckitt uses 13 four-week periods per year, not calendar months. All time-series analysis must use fiscal_period not calendar month.",
        "domain": "Finance",
        "owner": "rn.data.governance",
        "tags": ["fiscal-period", "time", "calendar", "13-period", "finance"],
        "sourceColumn": "col_rn_gd_period",
        "relatedKPIs": ["kpi_rn_revenue_by_brand", "kpi_rn_volume_growth"],
        "relatedDashboards": ["pbi_rn_executive", "pbi_rn_sales_performance", "pbi_rn_market_intelligence"],
        "relatedConfluence": ["conf_rn_data_dictionary"],
        "relatedJiraTickets": []
    },
    {
        "id": "dict_distribution_coverage",
        "term": "Weighted Distribution Coverage %",
        "definition": "The percentage of total store volume (weighted) where a Reckitt Nutrition product is available for purchase. Calculated from Nielsen distribution data. Higher than numeric distribution as large stores carry more weight.",
        "domain": "Market Intelligence",
        "owner": "rn.market.intelligence",
        "tags": ["distribution", "coverage", "weighted", "nielsen", "availability"],
        "sourceColumn": "col_rn_ms_distribution",
        "relatedKPIs": ["kpi_rn_distribution_coverage"],
        "relatedDashboards": ["pbi_rn_executive", "pbi_rn_market_intelligence"],
        "relatedConfluence": ["conf_rn_kpi_definitions", "conf_rn_market_intelligence"],
        "relatedJiraTickets": ["RN-205"]
    },
    {
        "id": "dict_consumer_penetration",
        "term": "Consumer Penetration Rate %",
        "definition": "The percentage of all households (within the defined universe) that purchased at least one unit of the specified Reckitt Nutrition brand in a rolling 12-week period. Sourced from Nielsen consumer panel. Key indicator of brand reach.",
        "domain": "Market Intelligence",
        "owner": "rn.market.intelligence",
        "tags": ["consumer", "penetration", "households", "panel", "reach", "nielsen"],
        "sourceColumn": "col_rn_ms_penetration",
        "relatedKPIs": ["kpi_rn_consumer_penetration"],
        "relatedDashboards": ["pbi_rn_market_intelligence"],
        "relatedConfluence": ["conf_rn_kpi_definitions", "conf_rn_data_dictionary"],
        "relatedJiraTickets": ["RN-208"]
    },
    {
        "id": "dict_kpi_value",
        "term": "KPI Value",
        "definition": "The computed numeric value of any Reckitt Nutrition KPI stored in the Gold rn_kpi_metrics table. The kpi_value column is read by ALL Power BI dashboards. Any rename or type change to this column will break all Power BI reports simultaneously.",
        "domain": "Data Engineering",
        "owner": "rn.data.governance",
        "tags": ["kpi", "metrics", "powerbi", "critical-column", "breaking-change"],
        "sourceColumn": "col_rn_kpi_value",
        "relatedKPIs": ["kpi_rn_revenue_by_brand", "kpi_rn_market_share", "kpi_rn_volume_growth", "kpi_rn_distribution_coverage", "kpi_rn_consumer_penetration"],
        "relatedDashboards": ["pbi_rn_executive", "pbi_rn_sales_performance", "pbi_rn_market_intelligence", "pbi_rn_data_quality"],
        "relatedConfluence": ["conf_rn_powerbi_architecture", "conf_rn_data_dictionary"],
        "relatedJiraTickets": ["RN-203", "RN-206"]
    }
]

# =============================================================================
# ALERTS
# =============================================================================

alerts = [
    {
        "id": "alert_customer_failure",
        "name": "Customer Pipeline Failure",
        "pipelineId": "pipeline_customer_ingestion",
        "alertType": "pipeline_failure",
        "severity": "critical",
        "notificationChannels": ["slack:#data-alerts", "pagerduty:oncall"],
        "enabled": True
    },
    {
        "id": "alert_order_latency",
        "name": "Order Pipeline SLA Breach",
        "pipelineId": "pipeline_order_processing",
        "alertType": "sla_breach",
        "threshold": "latency > 30 minutes",
        "severity": "high",
        "notificationChannels": ["slack:#data-alerts", "email:data-team@company.com"],
        "enabled": True
    },
    {
        "id": "alert_inventory_sync",
        "name": "Inventory Sync Delay",
        "pipelineId": "pipeline_inventory_sync",
        "alertType": "sla_breach",
        "threshold": "latency > 20 minutes",
        "severity": "high",
        "notificationChannels": ["slack:#supply-chain"],
        "enabled": True
    },
    {
        "id": "alert_fraud_spike",
        "name": "Fraud Alert Spike",
        "tableId": "table_fraud_alerts",
        "alertType": "anomaly",
        "threshold": "count > 1000 per hour",
        "severity": "critical",
        "notificationChannels": ["slack:#security", "pagerduty:security-oncall"],
        "enabled": True
    },
    {
        "id": "alert_data_quality",
        "name": "Data Quality Check Failed",
        "pipelineId": "pipeline_customer_ingestion",
        "alertType": "data_quality",
        "threshold": "null_rate > 5%",
        "severity": "high",
        "notificationChannels": ["slack:#data-quality"],
        "enabled": True
    },
    {
        "id": "alert_payment_failure",
        "name": "Payment Pipeline Failure",
        "pipelineId": "pipeline_payment_processing",
        "alertType": "pipeline_failure",
        "severity": "critical",
        "notificationChannels": ["slack:#payments-alerts", "pagerduty:payments-oncall"],
        "enabled": True
    },
    {
        "id": "alert_payment_latency",
        "name": "Payment Processing Latency",
        "pipelineId": "pipeline_payment_processing",
        "alertType": "sla_breach",
        "threshold": "p99_latency > 500ms",
        "severity": "high",
        "notificationChannels": ["slack:#payments-alerts"],
        "enabled": True
    }
]

# =============================================================================
# DATA QUALITY RULES
# =============================================================================

dataQualityRules = [
    {
        "id": "dq_cust_email_not_null",
        "name": "Customer Email Required",
        "tableId": "table_customers",
        "columnId": "col_cust_email",
        "ruleType": "not_null",
        "severity": "critical",
        "description": "Customer email must not be null",
        "enabled": True
    },
    {
        "id": "dq_cust_email_format",
        "name": "Valid Email Format",
        "tableId": "table_customers",
        "columnId": "col_cust_email",
        "ruleType": "regex",
        "severity": "high",
        "description": "Email must match valid format",
        "enabled": True
    },
    {
        "id": "dq_order_total_positive",
        "name": "Positive Order Total",
        "tableId": "table_orders",
        "columnId": "col_order_total",
        "ruleType": "range",
        "severity": "critical",
        "description": "Order total must be positive",
        "enabled": True
    },
    {
        "id": "dq_inv_quantity_nonneg",
        "name": "Non-negative Inventory",
        "tableId": "table_inventory",
        "columnId": "col_inv_quantity",
        "ruleType": "range",
        "severity": "high",
        "description": "Inventory quantity cannot be negative",
        "enabled": True
    },
    {
        "id": "dq_fraud_score_range",
        "name": "Valid Fraud Score Range",
        "tableId": "table_fraud_scores",
        "columnId": "col_fraud_score",
        "ruleType": "range",
        "severity": "critical",
        "description": "Fraud score must be between 0 and 1",
        "enabled": True
    },
    {
        "id": "dq_payment_amount_positive",
        "name": "Positive Payment Amount",
        "tableId": "table_payments",
        "columnId": "col_payment_amount",
        "ruleType": "range",
        "severity": "critical",
        "description": "Payment amount must be positive",
        "enabled": True
    },
    {
        "id": "dq_payment_provider_valid",
        "name": "Valid Payment Provider",
        "tableId": "table_payments",
        "columnId": "col_payment_provider",
        "ruleType": "referential",
        "severity": "critical",
        "description": "Payment provider must exist in payment_providers table",
        "enabled": True
    }
]

# =============================================================================
# ENVIRONMENTS
# =============================================================================

environments = [
    {
        "id": "env_dev",
        "name": "Development",
        "type": "development",
        "url": "https://dev.databricks.company.com",
        "status": "healthy"
    },
    {
        "id": "env_staging",
        "name": "Staging",
        "type": "staging",
        "url": "https://staging.databricks.company.com",
        "status": "healthy"
    },
    {
        "id": "env_prod",
        "name": "Production",
        "type": "production",
        "url": "https://prod.databricks.company.com",
        "status": "healthy"
    }
]
