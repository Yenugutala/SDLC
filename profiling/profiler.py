"""
Data Profiler — Column-level quality statistics.

Computes null rates, uniqueness, data type distributions, and value ranges
for Bronze, Silver, and Gold tables. Results feed the Data Quality Dashboard
and the DataQualityRule validation framework.

Usage:
    profile = profileTable("table_rn_silver_sales", silver_columns, sampleData)
    printProfileReport(profile)

    # Or profile all tables at once:
    allProfiles = profileAllTables(bronze_columns + silver_columns + gold_columns)
"""

from typing import Dict, List, Any, Optional


def profileTable(tableId: str, columns: List[Dict[str, Any]],
                 sampleData: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Profile a table's columns and return quality metrics.

    When sampleData is provided, computes value-level metrics (null rate,
    uniqueness). Without sampleData, returns structural metadata only
    (column count, PII flags, nullability) — useful for schema-level reporting
    without needing to load actual data.

    Args:
        tableId:    ID of the table being profiled (e.g. 'table_rn_silver_sales')
        columns:    List of column definitions from bronze/silver/gold_layer.py
        sampleData: Optional list of row dicts for value-level analysis.
                    Each dict should map column name → value.

    Returns:
        Profile report dict with per-column metrics and table-level summary.

    Example output::

        {
          "tableId": "table_rn_silver_sales",
          "columnCount": 5,
          "piiColumnCount": 0,
          "columns": {
            "net_revenue_usd": {
              "dataType": "DECIMAL",
              "isPii": false,
              "isNullable": false,
              "nullRate": 0.0,
              "uniquenessRate": 0.98,
              "issues": []
            },
            ...
          },
          "issues": []
        }
    """
    # Filter the global column list down to columns belonging to this table
    tableCols = [c for c in columns if c.get("tableId") == tableId]

    # Table-level summary — issues list collects all column-level problems
    report: Dict[str, Any] = {
        "tableId":        tableId,
        "columnCount":    len(tableCols),
        # PII count drives masking requirements and compliance reporting
        "piiColumnCount": sum(1 for c in tableCols if c.get("isPii")),
        "columns":        {},
        "issues":         [],  # aggregated list of all issues across all columns
    }

    for col in tableCols:
        # Start with structural metadata — always available
        colProfile: Dict[str, Any] = {
            "dataType":       col.get("dataType", "UNKNOWN"),
            "isPii":          col.get("isPii", False),
            "isNullable":     col.get("isNullable", True),
            # None = not computed (no sample data); 0.0 = computed and clean
            "nullRate":       None,
            "uniquenessRate": None,
            "issues":         [],
        }

        if sampleData:
            # Extract this column's values from every row in the sample
            values    = [row.get(col["name"]) for row in sampleData]
            total     = len(values)
            # Count null/empty as missing — empty string is semantically null here
            nullCount = sum(1 for v in values if v is None or v == "")
            # Unique count excludes nulls — uniqueness measures distinct non-null values
            uniqueCount = len(set(str(v) for v in values if v is not None))

            colProfile["nullRate"]       = round(nullCount / total, 4) if total else 0.0
            # Denominator is non-null count — avoids division by zero for all-null columns
            colProfile["uniquenessRate"] = round(uniqueCount / (total - nullCount), 4) \
                                           if (total - nullCount) > 0 else 0.0

            # Flag constraint violations — non-nullable columns with actual null values
            if not col.get("isNullable") and nullCount > 0:
                issue = (f"Non-nullable column '{col['name']}' has {nullCount} null values "
                         f"({colProfile['nullRate']*100:.1f}%)")
                colProfile["issues"].append(issue)
                # Also bubble the issue up to the table-level issues list
                report["issues"].append(issue)

        report["columns"][col["name"]] = colProfile

    return report


def profileAllTables(allColumns: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Profile all tables that appear in a column list.

    Discovers table IDs by scanning the 'tableId' field on columns — no need
    to pass a separate table list.

    Args:
        allColumns: Combined column list from bronze/silver/gold_layer.py

    Returns:
        Dict mapping tableId → profile report (see profileTable).
    """
    # Deduplicate table IDs using a set comprehension
    tableIds = list({c["tableId"] for c in allColumns if c.get("tableId")})
    # Profile each table — no sample data available at this call site
    return {tid: profileTable(tid, allColumns) for tid in tableIds}


def printProfileReport(profile: Dict[str, Any]) -> None:
    """Print a concise single-table profile report to stdout."""
    print(f"\n  Table: {profile['tableId']}")
    print(f"  Columns: {profile['columnCount']}  |  PII columns: {profile['piiColumnCount']}")

    for colName, colData in profile["columns"].items():
        piiFlag  = " [PII]" if colData["isPii"] else ""
        # Only show null rate if it was computed (sample data was provided)
        nullInfo = f"  null={colData['nullRate']*100:.1f}%" if colData["nullRate"] is not None else ""
        print(f"    {colName} ({colData['dataType']}){piiFlag}{nullInfo}")

    if profile["issues"]:
        print(f"\n  Issues ({len(profile['issues'])}):")
        for issue in profile["issues"]:
            print(f"    ! {issue}")
    else:
        print("  No issues detected.")
