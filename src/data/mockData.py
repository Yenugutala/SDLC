"""
Data Platform Knowledge Graph - Mock Data

Represents data lineage and metadata from:
- Databricks (pipelines, tables, columns)
- Confluence (documentation)
- Jira (tickets)
- Vector DB (semantic search)

Relationships:
    Pipeline --contains--> Table
    Table --contains--> Column
    Column --has_type--> DataType
    Pipeline --documented_in--> ConfluencePage
    JiraTicket --tracks--> Pipeline
    Alert --monitors--> Pipeline/Table
"""

# =============================================================================
# DATA PIPELINES (from Databricks/Airflow)
# =============================================================================

pipelines = [
    {
        "id": "pipeline_customer_ingestion",
        "name": "Customer Data Ingestion",
        "description": "Ingests customer data from CRM systems into the data lake",
        "owner": "data-engineering",
        "schedule": "daily",
        "status": "active",
        "tags": ["customer", "ingestion", "crm", "pii"]
    },
    {
        "id": "pipeline_order_processing",
        "name": "Order Processing Pipeline",
        "description": "Processes e-commerce orders and calculates metrics",
        "owner": "data-engineering",
        "schedule": "hourly",
        "status": "active",
        "tags": ["orders", "ecommerce", "metrics", "revenue"]
    },
    {
        "id": "pipeline_inventory_sync",
        "name": "Inventory Sync Pipeline",
        "description": "Synchronizes inventory levels across warehouses",
        "owner": "supply-chain-analytics",
        "schedule": "every_15_min",
        "status": "active",
        "tags": ["inventory", "warehouse", "sync", "realtime"]
    },
    {
        "id": "pipeline_user_analytics",
        "name": "User Analytics Pipeline",
        "description": "Aggregates user behavior data for analytics dashboards",
        "owner": "analytics-team",
        "schedule": "daily",
        "status": "active",
        "tags": ["analytics", "user-behavior", "dashboards", "reporting"]
    },
    {
        "id": "pipeline_fraud_detection",
        "name": "Fraud Detection Pipeline",
        "description": "Real-time fraud detection using ML models",
        "owner": "security-analytics",
        "schedule": "streaming",
        "status": "active",
        "tags": ["fraud", "ml", "security", "streaming", "realtime"]
    },
    {
        "id": "pipeline_payment_processing",
        "name": "Payment Processing Pipeline",
        "description": "Pluggable payment framework for processing transactions via multiple payment providers (Stripe, PayPal, Square)",
        "owner": "payments-team",
        "schedule": "streaming",
        "status": "active",
        "tags": ["payment", "pluggable", "framework", "transactions", "stripe", "paypal", "gateway"]
    }
]

# =============================================================================
# TABLES (from Databricks Unity Catalog)
# =============================================================================

tables = [
    # Customer Ingestion Pipeline Tables
    {
        "id": "table_customers",
        "name": "customers",
        "pipelineId": "pipeline_customer_ingestion",
        "schema": "gold",
        "description": "Master customer dimension table",
        "rowCount": 2500000,
        "tags": ["customer", "dimension", "pii"]
    },
    {
        "id": "table_customer_addresses",
        "name": "customer_addresses",
        "pipelineId": "pipeline_customer_ingestion",
        "schema": "gold",
        "description": "Customer shipping and billing addresses",
        "rowCount": 4200000,
        "tags": ["customer", "addresses", "pii"]
    },
    # Order Processing Pipeline Tables
    {
        "id": "table_orders",
        "name": "orders",
        "pipelineId": "pipeline_order_processing",
        "schema": "gold",
        "description": "Order transactions fact table",
        "rowCount": 15000000,
        "tags": ["orders", "fact", "transactions"]
    },
    {
        "id": "table_order_items",
        "name": "order_items",
        "pipelineId": "pipeline_order_processing",
        "schema": "gold",
        "description": "Line items for each order",
        "rowCount": 45000000,
        "tags": ["orders", "items", "fact"]
    },
    # Inventory Sync Pipeline Tables
    {
        "id": "table_inventory",
        "name": "inventory",
        "pipelineId": "pipeline_inventory_sync",
        "schema": "gold",
        "description": "Current inventory levels by warehouse",
        "rowCount": 850000,
        "tags": ["inventory", "warehouse", "snapshot"]
    },
    {
        "id": "table_inventory_movements",
        "name": "inventory_movements",
        "pipelineId": "pipeline_inventory_sync",
        "schema": "gold",
        "description": "Inventory movement transactions",
        "rowCount": 12000000,
        "tags": ["inventory", "movements", "fact"]
    },
    # User Analytics Pipeline Tables
    {
        "id": "table_user_sessions",
        "name": "user_sessions",
        "pipelineId": "pipeline_user_analytics",
        "schema": "gold",
        "description": "User session data for analytics",
        "rowCount": 100000000,
        "tags": ["analytics", "sessions", "user"]
    },
    {
        "id": "table_page_views",
        "name": "page_views",
        "pipelineId": "pipeline_user_analytics",
        "schema": "gold",
        "description": "Page view events",
        "rowCount": 500000000,
        "tags": ["analytics", "pageviews", "events"]
    },
    # Fraud Detection Pipeline Tables
    {
        "id": "table_fraud_scores",
        "name": "fraud_scores",
        "pipelineId": "pipeline_fraud_detection",
        "schema": "gold",
        "description": "ML-generated fraud risk scores",
        "rowCount": 15000000,
        "tags": ["fraud", "ml", "scores"]
    },
    {
        "id": "table_fraud_alerts",
        "name": "fraud_alerts",
        "pipelineId": "pipeline_fraud_detection",
        "schema": "gold",
        "description": "Triggered fraud alerts for review",
        "rowCount": 250000,
        "tags": ["fraud", "alerts", "security"]
    },
    # Payment Processing Pipeline Tables
    {
        "id": "table_payments",
        "name": "payments",
        "pipelineId": "pipeline_payment_processing",
        "schema": "gold",
        "description": "Payment transactions from all payment providers",
        "rowCount": 28000000,
        "tags": ["payment", "transactions", "fact"]
    },
    {
        "id": "table_payment_providers",
        "name": "payment_providers",
        "pipelineId": "pipeline_payment_processing",
        "schema": "gold",
        "description": "Configured payment providers and gateway settings",
        "rowCount": 15,
        "tags": ["payment", "providers", "dimension", "pluggable"]
    },
    {
        "id": "table_payment_methods",
        "name": "payment_methods",
        "pipelineId": "pipeline_payment_processing",
        "schema": "gold",
        "description": "Customer payment methods (cards, wallets, bank accounts)",
        "rowCount": 5200000,
        "tags": ["payment", "methods", "pii"]
    }
]

# =============================================================================
# COLUMNS (from Databricks Unity Catalog)
# =============================================================================

columns = [
    # customers table columns
    {"id": "col_cust_id", "name": "customer_id", "tableId": "table_customers",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Unique customer identifier"},
    {"id": "col_cust_email", "name": "email", "tableId": "table_customers",
     "dataType": "STRING", "isPii": True, "isNullable": False,
     "description": "Customer email address"},
    {"id": "col_cust_name", "name": "full_name", "tableId": "table_customers",
     "dataType": "STRING", "isPii": True, "isNullable": False,
     "description": "Customer full name"},
    {"id": "col_cust_phone", "name": "phone", "tableId": "table_customers",
     "dataType": "STRING", "isPii": True, "isNullable": True,
     "description": "Customer phone number"},
    {"id": "col_cust_created", "name": "created_at", "tableId": "table_customers",
     "dataType": "TIMESTAMP", "isPii": False, "isNullable": False,
     "description": "Account creation timestamp"},

    # orders table columns
    {"id": "col_order_id", "name": "order_id", "tableId": "table_orders",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Unique order identifier"},
    {"id": "col_order_cust", "name": "customer_id", "tableId": "table_orders",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Foreign key to customers"},
    {"id": "col_order_total", "name": "total_amount", "tableId": "table_orders",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Order total in USD"},
    {"id": "col_order_status", "name": "status", "tableId": "table_orders",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Order status (pending, shipped, delivered, cancelled)"},
    {"id": "col_order_date", "name": "order_date", "tableId": "table_orders",
     "dataType": "DATE", "isPii": False, "isNullable": False,
     "description": "Date order was placed"},

    # inventory table columns
    {"id": "col_inv_sku", "name": "sku", "tableId": "table_inventory",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Product SKU"},
    {"id": "col_inv_warehouse", "name": "warehouse_id", "tableId": "table_inventory",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Warehouse identifier"},
    {"id": "col_inv_quantity", "name": "quantity", "tableId": "table_inventory",
     "dataType": "INTEGER", "isPii": False, "isNullable": False,
     "description": "Current stock quantity"},
    {"id": "col_inv_updated", "name": "last_updated", "tableId": "table_inventory",
     "dataType": "TIMESTAMP", "isPii": False, "isNullable": False,
     "description": "Last sync timestamp"},

    # fraud_scores table columns
    {"id": "col_fraud_txn", "name": "transaction_id", "tableId": "table_fraud_scores",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Transaction identifier"},
    {"id": "col_fraud_score", "name": "risk_score", "tableId": "table_fraud_scores",
     "dataType": "FLOAT", "isPii": False, "isNullable": False,
     "description": "ML fraud risk score (0-1)"},
    {"id": "col_fraud_flag", "name": "is_fraudulent", "tableId": "table_fraud_scores",
     "dataType": "BOOLEAN", "isPii": False, "isNullable": False,
     "description": "Fraud classification flag"},

    # payments table columns
    {"id": "col_payment_id", "name": "payment_id", "tableId": "table_payments",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Unique payment transaction identifier"},
    {"id": "col_payment_provider", "name": "provider_id", "tableId": "table_payments",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Payment provider (stripe, paypal, square)"},
    {"id": "col_payment_amount", "name": "amount", "tableId": "table_payments",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Payment amount in cents"},
    {"id": "col_payment_currency", "name": "currency", "tableId": "table_payments",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "ISO 4217 currency code"},
    {"id": "col_payment_status", "name": "status", "tableId": "table_payments",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Payment status (pending, completed, failed, refunded)"},

    # payment_providers table columns
    {"id": "col_provider_id", "name": "provider_id", "tableId": "table_payment_providers",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Unique provider identifier"},
    {"id": "col_provider_name", "name": "provider_name", "tableId": "table_payment_providers",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Provider display name (Stripe, PayPal, Square)"},
    {"id": "col_provider_enabled", "name": "is_enabled", "tableId": "table_payment_providers",
     "dataType": "BOOLEAN", "isPii": False, "isNullable": False,
     "description": "Whether provider is active in the pluggable framework"}
]

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
    }
]

# =============================================================================
# ALERTS (Monitoring)
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
