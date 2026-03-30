"""
Bronze Layer — Raw / Landing Zone

Contains raw pipelines and tables ingested directly from source systems
(SAP S/4HANA, SAP MDM, Nielsen IQ, Salesforce CRM) with no transformations.
Reckitt Nutrition Bronze data + generic platform pipelines/tables.
"""

# =============================================================================
# BRONZE PIPELINES
# =============================================================================

bronze_pipelines = [
    # -------------------------------------------------------------------------
    # Generic Platform Pipelines (no explicit layer — landing raw data)
    # -------------------------------------------------------------------------
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
    },

    # -------------------------------------------------------------------------
    # Reckitt Nutrition — Bronze Layer (Raw Ingestion from Source Systems)
    # -------------------------------------------------------------------------
    {
        "id": "pipeline_rn_bronze_sales",
        "name": "RN Bronze: SAP Sales Raw Ingestion",
        "description": "Ingests raw sales transaction data from SAP S/4HANA into Databricks Bronze layer for Reckitt Nutrition. Covers all markets: APAC, EMEA, Americas.",
        "owner": "reckitt-data-engineering",
        "schedule": "daily",
        "status": "active",
        "layer": "bronze",
        "sourceSystem": "SAP S/4HANA",
        "tags": ["reckitt", "nutrition", "bronze", "sap", "sales", "ingestion", "raw"]
    },
    {
        "id": "pipeline_rn_bronze_product",
        "name": "RN Bronze: Product Catalog Raw Ingestion",
        "description": "Ingests raw product master data (SKUs, brands, categories, nutritional info) from SAP MDM into Bronze layer for Reckitt Nutrition portfolio.",
        "owner": "reckitt-data-engineering",
        "schedule": "daily",
        "status": "active",
        "layer": "bronze",
        "sourceSystem": "SAP MDM",
        "tags": ["reckitt", "nutrition", "bronze", "product", "sku", "mdm", "catalog"]
    },
    {
        "id": "pipeline_rn_bronze_market",
        "name": "RN Bronze: Nielsen Market Data Ingestion",
        "description": "Ingests raw Nielsen retail audit and consumer panel data into Bronze layer. Covers market share, distribution, and consumer penetration metrics for baby nutrition and adult nutrition segments.",
        "owner": "reckitt-market-intelligence",
        "schedule": "weekly",
        "status": "active",
        "layer": "bronze",
        "sourceSystem": "Nielsen IQ",
        "tags": ["reckitt", "nutrition", "bronze", "nielsen", "market", "consumer-panel", "market-share"]
    },
    {
        "id": "pipeline_rn_bronze_consumer",
        "name": "RN Bronze: Consumer Insights Raw Ingestion",
        "description": "Ingests raw consumer survey data, loyalty program data, and CRM interactions for Reckitt Nutrition consumers (Enfamil, Nutramigen, Enfalac brands).",
        "owner": "reckitt-consumer-analytics",
        "schedule": "daily",
        "status": "active",
        "layer": "bronze",
        "sourceSystem": "Salesforce CRM",
        "tags": ["reckitt", "nutrition", "bronze", "consumer", "crm", "loyalty", "enfamil"]
    },
]

# =============================================================================
# BRONZE TABLES
# =============================================================================

bronze_tables = [
    # Generic platform tables (no explicit layer field — treated as raw/bronze)
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
    },

    # -------------------------------------------------------------------------
    # Reckitt Nutrition — Bronze Tables (Raw / Landing Zone)
    # -------------------------------------------------------------------------
    {
        "id": "table_rn_bronze_sales_raw",
        "name": "rn_sales_raw",
        "pipelineId": "pipeline_rn_bronze_sales",
        "schema": "bronze",
        "layer": "bronze",
        "database": "reckitt_nutrition",
        "description": "Raw SAP sales transaction records for Reckitt Nutrition. Contains unvalidated invoice lines, billing documents, and returns across all markets.",
        "rowCount": 45000000,
        "tags": ["reckitt", "nutrition", "bronze", "sap", "sales", "raw", "landing"]
    },
    {
        "id": "table_rn_bronze_product_raw",
        "name": "rn_product_raw",
        "pipelineId": "pipeline_rn_bronze_product",
        "schema": "bronze",
        "layer": "bronze",
        "database": "reckitt_nutrition",
        "description": "Raw product master data from SAP MDM for all Reckitt Nutrition SKUs (Enfamil, Nutramigen, Enfalac, Mead Johnson, Durex Naturals nutrition lines).",
        "rowCount": 18500,
        "tags": ["reckitt", "nutrition", "bronze", "product", "sku", "mdm", "raw"]
    },
    {
        "id": "table_rn_bronze_market_raw",
        "name": "rn_market_raw",
        "pipelineId": "pipeline_rn_bronze_market",
        "schema": "bronze",
        "layer": "bronze",
        "database": "reckitt_nutrition",
        "description": "Raw Nielsen IQ retail audit and panel data. Contains market share, distribution metrics, and consumer penetration data for baby and adult nutrition categories.",
        "rowCount": 8200000,
        "tags": ["reckitt", "nutrition", "bronze", "nielsen", "market", "raw", "panel"]
    },
    {
        "id": "table_rn_bronze_consumer_raw",
        "name": "rn_consumer_raw",
        "pipelineId": "pipeline_rn_bronze_consumer",
        "schema": "bronze",
        "layer": "bronze",
        "database": "reckitt_nutrition",
        "description": "Raw Salesforce CRM consumer data: HCP interactions, loyalty members, sample requests, and digital engagement for Enfamil brand consumers.",
        "rowCount": 3100000,
        "tags": ["reckitt", "nutrition", "bronze", "consumer", "crm", "raw", "pii"]
    },
]

# =============================================================================
# BRONZE COLUMNS
# =============================================================================

bronze_columns = [
    # customers table
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

    # orders table
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

    # inventory table
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

    # fraud_scores table
    {"id": "col_fraud_txn", "name": "transaction_id", "tableId": "table_fraud_scores",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Transaction identifier"},
    {"id": "col_fraud_score", "name": "risk_score", "tableId": "table_fraud_scores",
     "dataType": "FLOAT", "isPii": False, "isNullable": False,
     "description": "ML fraud risk score (0-1)"},
    {"id": "col_fraud_flag", "name": "is_fraudulent", "tableId": "table_fraud_scores",
     "dataType": "BOOLEAN", "isPii": False, "isNullable": False,
     "description": "Fraud classification flag"},

    # payments table
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

    # payment_providers table
    {"id": "col_provider_id", "name": "provider_id", "tableId": "table_payment_providers",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Unique provider identifier"},
    {"id": "col_provider_name", "name": "provider_name", "tableId": "table_payment_providers",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Provider display name (Stripe, PayPal, Square)"},
    {"id": "col_provider_enabled", "name": "is_enabled", "tableId": "table_payment_providers",
     "dataType": "BOOLEAN", "isPii": False, "isNullable": False,
     "description": "Whether provider is active in the pluggable framework"},

    # -------------------------------------------------------------------------
    # Reckitt Nutrition — Bronze Sales Raw Columns
    # -------------------------------------------------------------------------
    {"id": "col_rn_br_sales_invoice_id", "name": "invoice_id", "tableId": "table_rn_bronze_sales_raw",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "SAP billing document number (raw, may contain duplicates in Bronze)"},
    {"id": "col_rn_br_sales_sku", "name": "material_number", "tableId": "table_rn_bronze_sales_raw",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "SAP material number (maps to Reckitt Nutrition SKU in Silver)"},
    {"id": "col_rn_br_sales_revenue", "name": "net_sales_value_lc", "tableId": "table_rn_bronze_sales_raw",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "Net sales value in local currency (before currency normalization in Silver)"},
    {"id": "col_rn_br_sales_market", "name": "sales_org_code", "tableId": "table_rn_bronze_sales_raw",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "SAP sales organisation code (raw market identifier, conformed in Silver)"},
    {"id": "col_rn_br_sales_volume", "name": "quantity_in_base_uom", "tableId": "table_rn_bronze_sales_raw",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Sales volume in SAP base unit of measure (cases, eaches)"},
]
