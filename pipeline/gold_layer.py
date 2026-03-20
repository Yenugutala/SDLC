"""Gold Layer: Create views on silver tables with different obfuscated names."""

import json
import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
MAPPINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mappings")

# Gold column mappings: silver_col -> gold_col
PATIENTS_GOLD_MAP = {
    "col_x1a": "attr_m1",
    "fld_7b2": "attr_m2",
    "fld_9c3": "attr_m3",
    "attr_d4e": "attr_m4",
    "flg_5f1": "attr_m5",
    "cod_8g2": "attr_m6",
    "val_2h7": "attr_m7",
    "txt_3j9": "attr_m8",
    "ref_6k4": "attr_m9",
}

VISITS_GOLD_MAP = {
    "col_y2b": "dim_n1",
    "col_x1a": "dim_n2",
    "dt_4m8": "dim_n3",
    "cat_1n5": "dim_n4",
    "txt_7p3": "dim_n5",
    "ref_2q6": "dim_n6",
    "txt_9r1": "dim_n7",
    "num_3s7": "msr_n8",
    "flg_8t2": "dim_n9",
}

GOLD_PATIENTS_VIEW = "gold_vw_p99"
GOLD_VISITS_VIEW = "gold_vw_q88"


def create_gold_views(db_path=None):
    """Create gold views on silver tables with renamed columns."""
    db_path = db_path or DB_PATH
    os.makedirs(MAPPINGS_DIR, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build patients view
    patient_cols = ", ".join(
        f"{silver} AS {gold}" for silver, gold in PATIENTS_GOLD_MAP.items()
    )
    cursor.execute(f"DROP VIEW IF EXISTS {GOLD_PATIENTS_VIEW}")
    cursor.execute(
        f"CREATE VIEW {GOLD_PATIENTS_VIEW} AS SELECT {patient_cols} FROM silver_tbl_a1"
    )

    # Build visits view
    visit_cols = ", ".join(
        f"{silver} AS {gold}" for silver, gold in VISITS_GOLD_MAP.items()
    )
    cursor.execute(f"DROP VIEW IF EXISTS {GOLD_VISITS_VIEW}")
    cursor.execute(
        f"CREATE VIEW {GOLD_VISITS_VIEW} AS SELECT {visit_cols} FROM silver_tbl_b2"
    )

    conn.commit()
    conn.close()

    # Save mappings for lineage tracking
    mappings = {
        "silver_tbl_a1_to_gold_vw_p99": PATIENTS_GOLD_MAP,
        "silver_tbl_b2_to_gold_vw_q88": VISITS_GOLD_MAP,
    }
    mapping_path = os.path.join(MAPPINGS_DIR, "silver_to_gold.json")
    with open(mapping_path, "w") as f:
        json.dump(mappings, f, indent=2)

    print(f"[Gold] Created views {GOLD_PATIENTS_VIEW} and {GOLD_VISITS_VIEW}")
    print(f"[Gold] Column mappings saved to {mapping_path}")
    return mappings


if __name__ == "__main__":
    create_gold_views()
