"""Bronze Layer: Ingest all raw CSV files into SQLite database."""

import glob
import os
import sqlite3
import pandas as pd


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")


def ingest_bronze(db_path=None):
    """Read all CSVs from data/ and load them into SQLite as bronze tables."""
    db_path = db_path or DB_PATH

    conn = sqlite3.connect(db_path)
    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))

    total_rows = 0
    for csv_path in csv_files:
        filename = os.path.splitext(os.path.basename(csv_path))[0]
        table_name = f"bronze_{filename}"
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        total_rows += len(df)
        print(f"[Bronze] Ingested {len(df)} rows into {table_name}")

    conn.commit()
    conn.close()

    print(f"[Bronze] Total: {len(csv_files)} files, {total_rows} rows into {db_path}")
    return db_path


if __name__ == "__main__":
    ingest_bronze()
