"""
Gold Layer — Business-ready Aggregates & KPI Layer

Contains aggregation pipelines that compute KPIs, market share metrics,
and business-level summaries consumed directly by Power BI dashboards.
Reckitt Nutrition Gold pipelines, tables, and columns.
"""

# =============================================================================
# GOLD PIPELINES
# =============================================================================

gold_pipelines = [
    {
        "id": "pipeline_rn_gold_sales_summary",
        "name": "RN Gold: Sales Summary Aggregation",
        "description": "Aggregates Silver sales data into Gold business metrics: revenue by brand, volume by SKU, net revenue management adjustments, and promotional uplift calculations. This feeds Power BI dashboards directly.",
        "owner": "reckitt-analytics",
        "schedule": "daily",
        "status": "active",
        "layer": "gold",
        "sourceLayer": "silver",
        "tags": ["reckitt", "nutrition", "gold", "sales", "aggregation", "revenue", "kpi", "powerbi"]
    },
    {
        "id": "pipeline_rn_gold_market_share",
        "name": "RN Gold: Market Share Calculation",
        "description": "Calculates market share metrics from Silver market and sales data: value share, volume share, distribution coverage, and consumer penetration rate by brand and geography.",
        "owner": "reckitt-market-intelligence",
        "schedule": "weekly",
        "status": "active",
        "layer": "gold",
        "sourceLayer": "silver",
        "tags": ["reckitt", "nutrition", "gold", "market-share", "distribution", "consumer-penetration", "kpi"]
    },
    {
        "id": "pipeline_rn_gold_kpi_metrics",
        "name": "RN Gold: KPI Metrics for Power BI",
        "description": "Computes all Power BI KPI metrics from Gold sales and market share data: Revenue by Brand, Market Share %, Volume Growth YoY, Distribution Coverage, Consumer Penetration Rate, Net Revenue Management.",
        "owner": "reckitt-analytics",
        "schedule": "daily",
        "status": "active",
        "layer": "gold",
        "sourceLayer": "silver",
        "tags": ["reckitt", "nutrition", "gold", "kpi", "powerbi", "metrics", "reporting"]
    },
]

# =============================================================================
# GOLD TABLES
# =============================================================================

gold_tables = [
    {
        "id": "table_rn_gold_sales_summary",
        "name": "rn_sales_summary",
        "pipelineId": "pipeline_rn_gold_sales_summary",
        "schema": "gold",
        "layer": "gold",
        "database": "reckitt_nutrition",
        "description": "Aggregated Reckitt Nutrition sales summary by brand, SKU, market, and period. Source for Revenue by Brand KPI, Volume Growth YoY KPI, and Net Revenue Management dashboard in Power BI.",
        "rowCount": 920000,
        "tags": ["reckitt", "nutrition", "gold", "sales", "summary", "kpi", "powerbi", "revenue"]
    },
    {
        "id": "table_rn_gold_market_share",
        "name": "rn_market_share_metrics",
        "pipelineId": "pipeline_rn_gold_market_share",
        "schema": "gold",
        "layer": "gold",
        "database": "reckitt_nutrition",
        "description": "Market share metrics for Reckitt Nutrition by brand and geography: value share %, volume share %, distribution coverage %, and consumer penetration rate. Feeds Market Intelligence Power BI dashboard.",
        "rowCount": 145000,
        "tags": ["reckitt", "nutrition", "gold", "market-share", "distribution", "consumer-penetration", "kpi"]
    },
    {
        "id": "table_rn_gold_kpi_metrics",
        "name": "rn_kpi_metrics",
        "pipelineId": "pipeline_rn_gold_kpi_metrics",
        "schema": "gold",
        "layer": "gold",
        "database": "reckitt_nutrition",
        "description": "Pre-computed KPI metrics table consumed directly by all Power BI reports for Reckitt Nutrition. Contains Revenue by Brand, Market Share %, Volume Growth, Distribution Coverage, Consumer Penetration.",
        "rowCount": 38000,
        "tags": ["reckitt", "nutrition", "gold", "kpi", "powerbi", "metrics", "all-brands"]
    },
]

# =============================================================================
# GOLD COLUMNS
# =============================================================================

gold_columns = [
    # Gold Sales Summary
    {"id": "col_rn_gd_sales_brand", "name": "brand_name", "tableId": "table_rn_gold_sales_summary",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Reckitt Nutrition brand (Enfamil, Nutramigen, Enfalac, Mead Johnson). Used in Revenue by Brand KPI."},
    {"id": "col_rn_gd_revenue", "name": "total_net_revenue_usd", "tableId": "table_rn_gold_sales_summary",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Total net revenue in USD for the period. Direct source for 'Revenue by Brand' Power BI KPI. Changing this column breaks the Revenue by Brand KPI dashboard."},
    {"id": "col_rn_gd_volume", "name": "total_volume_cases", "tableId": "table_rn_gold_sales_summary",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Total volume in cases for the period. Source for Volume Growth YoY KPI."},
    {"id": "col_rn_gd_period", "name": "fiscal_period", "tableId": "table_rn_gold_sales_summary",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Reckitt fiscal period in YYYY-PP format (e.g. 2024-P03). Used in all time-series Power BI visuals."},
    {"id": "col_rn_gd_market", "name": "market_code", "tableId": "table_rn_gold_sales_summary",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "Reckitt market code. Used for geographic slicing in all Power BI dashboards."},

    # Gold Market Share
    {"id": "col_rn_ms_value_share", "name": "value_share_pct", "tableId": "table_rn_gold_market_share",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "Reckitt Nutrition value market share percentage by brand and geography. Source for Market Share % KPI in Power BI."},
    {"id": "col_rn_ms_volume_share", "name": "volume_share_pct", "tableId": "table_rn_gold_market_share",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "Reckitt Nutrition volume market share percentage."},
    {"id": "col_rn_ms_distribution", "name": "weighted_distribution_pct", "tableId": "table_rn_gold_market_share",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "Weighted distribution coverage % (% of stores carrying product, weighted by store sales). Source for Distribution Coverage KPI."},
    {"id": "col_rn_ms_penetration", "name": "consumer_penetration_pct", "tableId": "table_rn_gold_market_share",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "Consumer penetration rate: % of households buying Reckitt Nutrition products. Source for Consumer Penetration Rate KPI in Power BI."},

    # Gold KPI Metrics
    {"id": "col_rn_kpi_name", "name": "kpi_name", "tableId": "table_rn_gold_kpi_metrics",
     "dataType": "STRING", "isPii": False, "isNullable": False,
     "description": "KPI identifier (e.g. revenue_by_brand, market_share_pct, volume_growth_yoy)"},
    {"id": "col_rn_kpi_value", "name": "kpi_value", "tableId": "table_rn_gold_kpi_metrics",
     "dataType": "DECIMAL", "isPii": False, "isNullable": False,
     "description": "Computed KPI numeric value. All Power BI visuals read this column; any rename breaks all dashboards."},
    {"id": "col_rn_kpi_target", "name": "kpi_target", "tableId": "table_rn_gold_kpi_metrics",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "KPI target/budget value set by Reckitt Nutrition planning team"},
    {"id": "col_rn_kpi_vs_target", "name": "kpi_vs_target_pct", "tableId": "table_rn_gold_kpi_metrics",
     "dataType": "DECIMAL", "isPii": False, "isNullable": True,
     "description": "KPI actual vs target percentage. Used in traffic-light KPI tiles across all Power BI dashboards."},
]
