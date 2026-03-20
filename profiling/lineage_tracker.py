"""Lineage Tracker: Build column lineage across Bronze -> Silver -> Gold layers."""

import json
import os


MAPPINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mappings")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def build_lineage():
    """Build end-to-end column lineage from source CSV to Gold views."""

    # Load mappings
    with open(os.path.join(MAPPINGS_DIR, "bronze_to_silver.json")) as f:
        bronze_to_silver = json.load(f)

    with open(os.path.join(MAPPINGS_DIR, "silver_to_gold.json")) as f:
        silver_to_gold = json.load(f)

    lineage = {"patients_lineage": [], "visits_lineage": []}

    # Patients lineage: source -> bronze -> silver -> gold
    patients_b2s = bronze_to_silver["bronze_patients_to_silver_tbl_a1"]
    patients_s2g = silver_to_gold["silver_tbl_a1_to_gold_vw_p99"]

    for source_col, silver_col in patients_b2s.items():
        gold_col = patients_s2g.get(silver_col, "N/A")
        lineage["patients_lineage"].append({
            "source_file": "patients.csv",
            "source_column": source_col,
            "bronze_table": "bronze_patients",
            "bronze_column": source_col,
            "silver_table": "silver_tbl_a1",
            "silver_column": silver_col,
            "gold_view": "gold_vw_p99",
            "gold_column": gold_col,
        })

    # Visits lineage
    visits_b2s = bronze_to_silver["bronze_visits_to_silver_tbl_b2"]
    visits_s2g = silver_to_gold["silver_tbl_b2_to_gold_vw_q88"]

    for source_col, silver_col in visits_b2s.items():
        gold_col = visits_s2g.get(silver_col, "N/A")
        lineage["visits_lineage"].append({
            "source_file": "visits.csv",
            "source_column": source_col,
            "bronze_table": "bronze_visits",
            "bronze_column": source_col,
            "silver_table": "silver_tbl_b2",
            "silver_column": silver_col,
            "gold_view": "gold_vw_q88",
            "gold_column": gold_col,
        })

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "lineage.json")
    with open(output_path, "w") as f:
        json.dump(lineage, f, indent=2)

    print(f"[Lineage] Tracked {len(lineage['patients_lineage'])} patient columns and {len(lineage['visits_lineage'])} visit columns")
    print(f"[Lineage] Saved to {output_path}")
    return lineage


if __name__ == "__main__":
    build_lineage()
