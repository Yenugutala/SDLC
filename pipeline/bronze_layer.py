"""Bronze Layer: Ingest raw CSV files into SQLite database."""

import os
import sqlite3
import pandas as pd


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")


def ingest_bronze(db_path=None):
    """Read raw CSVs and load them into SQLite as bronze tables."""
    db_path = db_path or DB_PATH

    patients_df = pd.read_csv(os.path.join(DATA_DIR, "patients.csv"))
    visits_df = pd.read_csv(os.path.join(DATA_DIR, "visits.csv"))

    conn = sqlite3.connect(db_path)

    patients_df.to_sql("bronze_patients", conn, if_exists="replace", index=False)
    visits_df.to_sql("bronze_visits", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

    print(f"[Bronze] Ingested {len(patients_df)} patients and {len(visits_df)} visits into {db_path}")
    return db_path


if __name__ == "__main__":
    ingest_bronze()
