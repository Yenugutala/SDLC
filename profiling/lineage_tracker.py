"""
Lineage Tracker — Bronze → Silver → Gold column-level lineage.

Builds and serialises a column lineage map that traces how each Gold column
was derived from Silver, and Silver from Bronze. Used for impact analysis
(e.g. "if Bronze column X changes, which Gold KPIs are affected?").

Why column-level lineage matters:
    A schema change (rename, type change, removal) in a Bronze column can silently
    break a Gold KPI and the Power BI dashboard that reads it. This tracker
    makes that impact chain explicit so engineers can assess blast radius before
    making changes.

Data model:
    COLUMN_LINEAGE maps Gold column ID → lineage record containing:
        - Column IDs and names at each layer (Bronze, Silver, Gold)
        - Table IDs at each layer
        - Transform notes (business logic applied at each hop)
        - Downstream KPIs and dashboards that depend on this Gold column
"""

import json
from typing import Dict, List, Any, Optional


# =============================================================================
# LINEAGE MAP
# Keyed by Gold column ID. Each record traces back to Silver and Bronze.
# Silver/Bronze fields are None for computed columns that have no direct lineage.
# =============================================================================

COLUMN_LINEAGE: Dict[str, Dict[str, Any]] = {

    # ─────────────────────────────────────────────────────────────────────────
    # Revenue: Bronze net_sales_value_lc → Silver net_revenue_usd → Gold total_net_revenue_usd
    # Transforms: currency conversion (LC → USD) + trade spend deduction + aggregation
    # ─────────────────────────────────────────────────────────────────────────
    "col_rn_gd_revenue": {
        "goldColumn":    "col_rn_gd_revenue",
        "goldName":      "total_net_revenue_usd",
        "goldTable":     "table_rn_gold_sales_summary",

        "silverColumn":  "col_rn_sv_sales_revenue_usd",
        "silverName":    "net_revenue_usd",
        "silverTable":   "table_rn_silver_sales",

        "bronzeColumn":  "col_rn_br_sales_revenue",
        "bronzeName":    "net_sales_value_lc",
        "bronzeTable":   "table_rn_bronze_sales_raw",

        "transformNotes": (
            "Bronze: raw local-currency value from SAP → "
            "Silver: currency converted to USD, trade spend deducted → "
            "Gold: aggregated SUM by brand/market/period"
        ),
        # Any change to this column propagates to these downstream consumers
        "downstreamKPIs":        ["kpi_rn_revenue_by_brand", "kpi_rn_nrm"],
        "downstreamDashboards":  ["pbi_rn_executive", "pbi_rn_sales_performance"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # Market share: Bronze value_share_pct (raw Nielsen) → Silver (normalised) → Gold value_share_pct
    # Note: Silver/Bronze column IDs are None — the columns exist but are not
    # tracked at the column level (only table-level lineage is available here).
    # ─────────────────────────────────────────────────────────────────────────
    "col_rn_ms_value_share": {
        "goldColumn":    "col_rn_ms_value_share",
        "goldName":      "value_share_pct",
        "goldTable":     "table_rn_gold_market_share",

        "silverColumn":  None,   # column not individually tracked — table-level only
        "silverName":    None,
        "silverTable":   "table_rn_silver_market",

        "bronzeColumn":  None,
        "bronzeName":    None,
        "bronzeTable":   "table_rn_bronze_market_raw",

        "transformNotes": (
            "Bronze: raw Nielsen retail audit value share by product code → "
            "Silver: product codes aligned to internal SKU hierarchy, geography standardised → "
            "Gold: aggregated by Reckitt brand and market code"
        ),
        "downstreamKPIs":       ["kpi_rn_market_share"],
        "downstreamDashboards": ["pbi_rn_executive", "pbi_rn_market_intelligence"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # KPI value: computed column — no direct Bronze/Silver lineage.
    # Derived in the Gold KPI pipeline by aggregating Gold sales and market share.
    # ─────────────────────────────────────────────────────────────────────────
    "col_rn_kpi_value": {
        "goldColumn":    "col_rn_kpi_value",
        "goldName":      "kpi_value",
        "goldTable":     "table_rn_gold_kpi_metrics",

        # All None — this column is computed entirely within the Gold layer
        "silverColumn":  None,
        "silverName":    None,
        "silverTable":   None,

        "bronzeColumn":  None,
        "bronzeName":    None,
        "bronzeTable":   None,

        "transformNotes": (
            "Computed in Gold KPI pipeline by aggregating Gold sales summary and "
            "Gold market share tables. No direct Bronze/Silver column — derived metric."
        ),
        # This column feeds ALL KPIs — the most impactful column in the graph
        "downstreamKPIs": [
            "kpi_rn_revenue_by_brand", "kpi_rn_market_share", "kpi_rn_volume_growth",
            "kpi_rn_distribution_coverage", "kpi_rn_consumer_penetration",
            "kpi_rn_pipeline_sla", "kpi_rn_dq_score"
        ],
        "downstreamDashboards": [
            "pbi_rn_executive", "pbi_rn_sales_performance",
            "pbi_rn_market_intelligence", "pbi_rn_data_quality"
        ],
    },
}


# =============================================================================
# PUBLIC API
# =============================================================================

def getColumnLineage(goldColumnId: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the full lineage record for a Gold column.

    Args:
        goldColumnId: ID of the Gold column (e.g. 'col_rn_gd_revenue')

    Returns:
        Lineage dict or None if this column is not tracked.
    """
    return COLUMN_LINEAGE.get(goldColumnId)


def getImpactedDownstream(bronzeOrSilverColumnId: str) -> List[str]:
    """
    Given a Bronze or Silver column ID, return all Gold column IDs that depend on it.

    Used for impact analysis: "if I rename/remove this Bronze column,
    which Gold columns (and therefore which KPIs and dashboards) are affected?"

    Args:
        bronzeOrSilverColumnId: Bronze or Silver column ID

    Returns:
        List of Gold column IDs impacted by a change to the given column.
        Empty list if the column is not a tracked upstream dependency.
    """
    impacted = []
    for goldColId, lineage in COLUMN_LINEAGE.items():
        # Check both Bronze and Silver slots — the given column may be at either layer
        if bronzeOrSilverColumnId in (lineage.get("bronzeColumn"), lineage.get("silverColumn")):
            impacted.append(goldColId)
    return impacted


def buildFullLineageGraph() -> Dict[str, Any]:
    """
    Build a complete lineage graph as a serialisable dict.

    Suitable for export to JSON or loading into a visualisation tool (e.g. Mermaid,
    Apache Atlas, or a custom D3 diagram).

    Returns:
        Dict with:
            nodes — sorted list of all column IDs (Bronze, Silver, Gold)
            edges — list of {from, to, relation, layer} dicts
    """
    nodes: set = set()
    edges: list = []

    for goldColId, lineage in COLUMN_LINEAGE.items():
        # Every entry contributes its Gold column as a node
        nodes.add(goldColId)

        if lineage.get("silverColumn"):
            nodes.add(lineage["silverColumn"])
            edges.append({
                "from":     lineage["silverColumn"],
                "to":       goldColId,
                "relation": "FLOWS_TO",
                "layer":    "silver_to_gold",
            })

        if lineage.get("bronzeColumn"):
            nodes.add(lineage["bronzeColumn"])
            edges.append({
                "from":     lineage["bronzeColumn"],
                # Bronze flows to Silver if Silver exists, otherwise directly to Gold
                "to":       lineage.get("silverColumn") or goldColId,
                "relation": "FLOWS_TO",
                "layer":    "bronze_to_silver",
            })

    return {"nodes": sorted(nodes), "edges": edges}


def exportLineageJson(path: str = "lineage.json") -> None:
    """
    Serialise the full lineage graph to a JSON file.

    Args:
        path: Output file path (default: lineage.json in working directory)
    """
    graph = buildFullLineageGraph()
    with open(path, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"Lineage graph exported to {path}  "
          f"({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")


def printImpactReport(columnId: str) -> None:
    """
    Print an impact analysis report for a given column.

    Handles two cases:
        1. Gold column ID — shows its full Bronze→Silver→Gold lineage chain
           plus all downstream KPIs and dashboards.
        2. Bronze or Silver column ID — shows which Gold columns (and therefore
           which KPIs and dashboards) would be broken by a change to it.
        3. Unknown column — reports that no lineage record was found.

    Args:
        columnId: Any tracked column ID (Bronze, Silver, or Gold)
    """
    # Case 1: this is a Gold column with a direct lineage record
    lineage = getColumnLineage(columnId)

    if lineage:
        print(f"\n  Gold column: {lineage['goldName']} ({columnId})")
        print(f"  Table: {lineage['goldTable']}")

        print(f"\n  Lineage:")
        # Only print layers that have tracked columns
        if lineage.get("bronzeName"):
            print(f"    Bronze: {lineage['bronzeName']} ({lineage['bronzeTable']})")
        if lineage.get("silverName"):
            print(f"    Silver: {lineage['silverName']} ({lineage['silverTable']})")
        print(f"    Gold:   {lineage['goldName']} ({lineage['goldTable']})")

        print(f"\n  Transform: {lineage['transformNotes']}")
        print(f"\n  Downstream KPIs: {', '.join(lineage.get('downstreamKPIs', []))}")
        print(f"  Downstream Dashboards: {', '.join(lineage.get('downstreamDashboards', []))}")

    else:
        # Case 2: this is an upstream (Bronze/Silver) column — find what depends on it
        impacted = getImpactedDownstream(columnId)
        if impacted:
            print(f"\n  Column {columnId} is upstream of Gold columns:")
            for goldColId in impacted:
                goldLineage = COLUMN_LINEAGE[goldColId]
                print(f"    → {goldLineage['goldName']} ({goldColId}) in {goldLineage['goldTable']}")
                print(f"      Downstream KPIs: {', '.join(goldLineage.get('downstreamKPIs', []))}")
        else:
            # Case 3: column not tracked at all
            print(f"\n  Column {columnId}: no lineage record found.")
