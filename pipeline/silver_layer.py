"""
Silver Layer — Cleansed & Conformed

Contains transformation pipelines that cleanse, deduplicate, normalise,
and conform raw Bronze data into analysis-ready Silver tables.
Reckitt Nutrition Silver pipelines, tables, and columns.
"""

# =============================================================================
# SILVER PIPELINES
# =============================================================================

silver_pipelines = [
    {
        "id": "pipeline_rn_silver_sales",
        "name": "RN Silver: Sales Data Cleansing & Conforming",
        "description": "Transforms Bronze SAP sales data into Silver layer: deduplication, currency normalization, market code mapping, brand hierarchy enrichment, and data quality validation for Reckitt Nutrition.",
        "owner": "reckitt-data-engineering",
        "schedule": "daily",
        "status": "active",
        "layer": "silver",
        "sourceLayer": "bronze",
        "tags": ["reckitt", "nutrition", "silver", "sales", "cleansing", "normalization", "etl"]
    },
    {
        "id": "pipeline_rn_silver_product",
        "name": "RN Silver: Product Master Enrichment",
        "description": "Enriches Bronze product data with brand hierarchy, nutritional classification, regulatory codes, and market availability. Joins Enfamil, Nutramigen, Enfalac, Mead Johnson product lines.",
        "owner": "reckitt-data-engineering",
        "schedule": "daily",
        "status": "active",
        "layer": "silver",
        "sourceLayer": "bronze",
        "tags": ["reckitt", "nutrition", "silver", "product", "enrichment", "brand-hierarchy", "enfamil"]
    },
    {
        "id": "pipeline_rn_silver_market",
        "name": "RN Silver: Market Data Normalization",
        "description": "Normalizes and conforms Nielsen market data: standardizes geography codes, aligns product categories with internal SKU hierarchy, calculates weighted distribution.",
        "owner": "reckitt-market-intelligence",
        "schedule": "weekly",
        "status": "active",
        "layer": "silver",
        "sourceLayer": "bronze",
        "tags": ["reckitt", "nutrition", "silver", "nielsen", "market", "normalization", "distribution"]
    },
]

# =============================================================================
# SILVER TABLES
# =============================================================================

silver_tables = [
    {
        "id": "table_rn_silver_sales",
        "name": "rn_sales_cleansed",
        "pipelineId": "pipeline_rn_silver_sales",
        "schema": "silver",
        "layer": "silver",
        "database": "reckitt_nutrition",
        "description": "Cleansed and conformed Reckitt Nutrition sales data. Deduplicated, currency-normalized (USD), brand codes mapped to internal hierarchy, market codes standardized.",
        "rowCount": 43800000,
        "tags": ["reckitt", "nutrition", "silver", "sales", "cleansed", "conformed"]
    },
    {
        "id": "table_rn_silver_product",
        "name": "rn_product_enriched",
        "pipelineId": "pipeline_rn_silver_product",
        "schema": "silver",
        "layer": "silver",
        "database": "reckitt_nutrition",
        "description": "Enriched Reckitt Nutrition product master with full brand hierarchy (Company > Division > Brand > Sub-brand > SKU), nutritional classification, and regulatory codes.",
        "rowCount": 18200,
        "tags": ["reckitt", "nutrition", "silver", "product", "enriched", "brand-hierarchy"]
    },
    {
        "id": "table_rn_silver_market",
        "name": "rn_market_normalized",
        "pipelineId": "pipeline_rn_silver_market",
        "schema": "silver",
        "layer": "silver",
        "database": "reckitt_nutrition",
        "description": "Normalized Nielsen market data aligned to Reckitt Nutrition's internal geography and category taxonomy. Ready for market share calculation.",
        "rowCount": 7950000,
        "tags": ["reckitt", "nutrition", "silver", "market", "normalized", "nielsen"]
    },
]

# =============================================================================
# SILVER COLUMNS
# =============================================================================

silver_columns = [
    {"id": "col_rn_sv_sales_brand", "name": "brand_name", "tableId": "table_rn_silver_sales",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Reckitt Nutrition brand name (Enfamil, Nutramigen, Enfalac, Mead Johnson). Mapped from SAP material number."},
    {"id": "col_rn_sv_sales_revenue_usd", "name": "net_revenue_usd", "tableId": "table_rn_silver_sales",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Net revenue in USD after currency conversion and trade spend deductions"},
    {"id": "col_rn_sv_sales_market_code", "name": "market_code", "tableId": "table_rn_silver_sales",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Standardised Reckitt market code (e.g. US, CN, UK, BR) mapped from SAP sales org"},
    {"id": "col_rn_sv_sales_volume_cases", "name": "volume_cases", "tableId": "table_rn_silver_sales",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Normalised sales volume in 9-litre equivalent cases for cross-SKU comparison"},
    {"id": "col_rn_sv_sales_sku", "name": "sku_code", "tableId": "table_rn_silver_sales",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Reckitt Nutrition internal SKU code aligned with product master"},
]
