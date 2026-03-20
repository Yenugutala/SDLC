"""Silver Layer: Transform bronze tables with obfuscated column names."""

import json
import os
import sqlite3
import pandas as pd


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
MAPPINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mappings")

# Obfuscated column mappings: original -> silver
PATIENTS_COLUMN_MAP = {
    "patient_id": "col_x1a",
    "first_name": "fld_7b2",
    "last_name": "fld_9c3",
    "dob": "attr_d4e",
    "gender": "flg_5f1",
    "blood_type": "cod_8g2",
    "phone": "val_2h7",
    "address": "txt_3j9",
    "insurance_provider": "ref_6k4",
}

VISITS_COLUMN_MAP = {
    "visit_id": "col_y2b",
    "patient_id": "col_x1a",
    "visit_date": "dt_4m8",
    "department": "cat_1n5",
    "diagnosis": "txt_7p3",
    "doctor_name": "ref_2q6",
    "treatment": "txt_9r1",
    "bill_amount": "num_3s7",
    "status": "flg_8t2",
}

SILVER_PATIENTS_TABLE = "silver_tbl_a1"
SILVER_VISITS_TABLE = "silver_tbl_b2"


def transform_silver(db_path=None):
    """Read bronze tables, rename columns, write as silver tables."""
    db_path = db_path or DB_PATH
    os.makedirs(MAPPINGS_DIR, exist_ok=True)

    conn = sqlite3.connect(db_path)

    # Transform patients
    patients_df = pd.read_sql("SELECT * FROM bronze_patients", conn)
    patients_silver = patients_df.rename(columns=PATIENTS_COLUMN_MAP)
    patients_silver.to_sql(SILVER_PATIENTS_TABLE, conn, if_exists="replace", index=False)

    # Transform visits
    visits_df = pd.read_sql("SELECT * FROM bronze_visits", conn)
    visits_silver = visits_df.rename(columns=VISITS_COLUMN_MAP)
    visits_silver.to_sql(SILVER_VISITS_TABLE, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

    # Save mappings for lineage tracking
    mappings = {
        "bronze_patients_to_silver_tbl_a1": PATIENTS_COLUMN_MAP,
        "bronze_visits_to_silver_tbl_b2": VISITS_COLUMN_MAP,
    }
    mapping_path = os.path.join(MAPPINGS_DIR, "bronze_to_silver.json")
    with open(mapping_path, "w") as f:
        json.dump(mappings, f, indent=2)

    print(f"[Silver] Created {SILVER_PATIENTS_TABLE} and {SILVER_VISITS_TABLE}")
    print(f"[Silver] Column mappings saved to {mapping_path}")
    return mappings


if __name__ == "__main__":
    transform_silver()
