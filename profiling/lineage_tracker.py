"""Lineage Tracker: Dynamically build column lineage across Bronze -> Silver -> Gold layers."""

import json
import os


MAPPINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mappings")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


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


def build_lineage():
    """Build end-to-end column lineage by dynamically parsing all mapping files."""

    # Load all mapping files
    b2s_path = os.path.join(MAPPINGS_DIR, "bronze_to_silver.json")
    s2g_path = os.path.join(MAPPINGS_DIR, "silver_to_gold.json")

    with open(b2s_path) as f:
        b2s_mappings = json.load(f)

    with open(s2g_path) as f:
        s2g_mappings = json.load(f)

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
