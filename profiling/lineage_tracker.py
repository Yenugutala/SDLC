"""Lineage Tracker: Build column lineage by querying database metadata.

Bronze -> Silver lineage: from _column_lineage table (stored during silver ingestion)
Silver -> Gold lineage: from VIEW SQL in sqlite_master (natively available)
"""

import json
import os
import re
import sqlite3


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def query_bronze_to_silver_lineage(conn):
    """Query _column_lineage table for Bronze -> Silver mappings.

    Returns: {"bronze_X_to_silver_Y": {"bronze_col": "silver_col", ...}, ...}
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT source_table, source_column, target_table, target_column "
        "FROM _column_lineage"
    )
    rows = cursor.fetchall()

    mappings = {}
    for source_table, source_col, target_table, target_col in rows:
        key = f"{source_table}_to_{target_table}"
        if key not in mappings:
            mappings[key] = {}
        mappings[key][source_col] = target_col

    return mappings


def parse_gold_view_lineage(conn):
    """Parse VIEW SQL from sqlite_master for Silver -> Gold mappings.

    VIEW SQL looks like: CREATE VIEW gold_vw_ah9 AS SELECT cod_ifd AS fct_tz, ... FROM silver_tbl_xa
    Returns: {"silver_X_to_gold_Y": {"silver_col": "gold_col", ...}, ...}
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='view' AND name LIKE 'gold_%'"
    )
    views = cursor.fetchall()

    mappings = {}
    for view_name, sql in views:
        if not sql:
            continue

        # Extract source table from "FROM <table>"
        from_match = re.search(r'\bFROM\s+(\w+)', sql, re.IGNORECASE)
        source_table = from_match.group(1) if from_match else None

        # Extract column aliases: "source_col AS alias_col"
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        col_map = {}
        if select_match:
            columns_str = select_match.group(1)
            for pair in columns_str.split(","):
                pair = pair.strip()
                alias_match = re.match(r'(\w+)\s+AS\s+(\w+)', pair, re.IGNORECASE)
                if alias_match:
                    col_map[alias_match.group(1)] = alias_match.group(2)

        if source_table and col_map:
            key = f"{source_table}_to_{view_name}"
            mappings[key] = col_map

    return mappings


def parse_mapping_key(key):
    """Parse a mapping key like 'bronze_patients_to_silver_tbl_a1'.

    Returns: (source_table, target_table)
    """
    parts = key.split("_to_", 1)
    return parts[0], parts[1]


def infer_source_file(bronze_table):
    """Infer CSV source file from bronze table name.

    'bronze_patients' -> 'patients.csv'
    """
    entity = bronze_table.replace("bronze_", "", 1)
    return f"{entity}.csv"


def build_lineage(db_path=None):
    """Build end-to-end column lineage by querying database metadata."""
    db_path = db_path or DB_PATH

    conn = sqlite3.connect(db_path)

    # Bronze -> Silver: from _column_lineage table
    b2s_mappings = query_bronze_to_silver_lineage(conn)

    # Silver -> Gold: from VIEW SQL in sqlite_master
    s2g_mappings = parse_gold_view_lineage(conn)

    conn.close()

    # Build reverse index: silver_table -> (gold_view, column_map)
    silver_to_gold_lookup = {}
    for key, col_map in s2g_mappings.items():
        silver_table, gold_view = parse_mapping_key(key)
        silver_to_gold_lookup[silver_table] = (gold_view, col_map)

    # Build lineage by iterating all bronze-to-silver mappings
    lineage = {}

    for b2s_key, b2s_col_map in b2s_mappings.items():
        bronze_table, silver_table = parse_mapping_key(b2s_key)
        entity = bronze_table.replace("bronze_", "", 1)
        source_file = infer_source_file(bronze_table)

        lineage_key = f"{entity}_lineage"
        lineage[lineage_key] = []

        # Look up the corresponding silver-to-gold mapping
        gold_view, s2g_col_map = silver_to_gold_lookup.get(silver_table, (None, {}))

        for source_col, silver_col in b2s_col_map.items():
            gold_col = s2g_col_map.get(silver_col, "N/A")
            lineage[lineage_key].append({
                "source_file": source_file,
                "source_column": source_col,
                "bronze_table": bronze_table,
                "bronze_column": source_col,
                "silver_table": silver_table,
                "silver_column": silver_col,
                "gold_view": gold_view or "N/A",
                "gold_column": gold_col,
            })

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "lineage.json")
    with open(output_path, "w") as f:
        json.dump(lineage, f, indent=2)

    total_cols = sum(len(entries) for entries in lineage.values())
    print(f"[Lineage] Tracked {total_cols} columns across {len(lineage)} entities")
    print(f"[Lineage] Saved to {output_path}")
    return lineage


if __name__ == "__main__":
    build_lineage()
