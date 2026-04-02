"""Data Push Simulator: Read Gold layer data and push to mock PBI via POST rows endpoint.

Simulates the real Power BI push dataset flow:
  1. Read Gold views from SQLite
  2. Map obfuscated column names to PBI business-friendly names
  3. POST rows to mock PBI server
"""

import os
import sqlite3
import httpx

from powerbi.mock_data_model import (
    WORKSPACE, DATASETS, DATASET_TABLES,
    get_gold_to_pbi_column_map, PBI_MOCK_HOST, PBI_MOCK_PORT,
)


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "pipeline.db")


def push_gold_to_pbi(api_base_url=None, db_path=None):
    """Push Gold layer data to mock PBI API via POST rows endpoint."""
    api_base_url = api_base_url or f"http://{PBI_MOCK_HOST}:{PBI_MOCK_PORT}"
    db_path = db_path or DB_PATH
    group_id = WORKSPACE["id"]

    conn = sqlite3.connect(db_path)

    for dataset in DATASETS:
        dataset_id = dataset["id"]
        gold_view = dataset["gold_view"]
        gold_to_pbi = get_gold_to_pbi_column_map(dataset_id)

        # Get table name from dataset tables
        tables = DATASET_TABLES.get(dataset_id, [])
        if not tables:
            print(f"[PBI Push] No tables defined for dataset {dataset['name']}, skipping")
            continue
        table_name = tables[0]["name"]

        # Read Gold view data
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {gold_view}")
        except sqlite3.OperationalError as e:
            print(f"[PBI Push] Could not read {gold_view}: {e}")
            continue

        col_names = [desc[0] for desc in cursor.description]
        raw_rows = cursor.fetchall()

        # Map column names: gold obfuscated -> PBI business names
        rows = []
        for raw_row in raw_rows:
            row = {}
            for col_name, value in zip(col_names, raw_row):
                pbi_name = gold_to_pbi.get(col_name, col_name)
                row[pbi_name] = value
            rows.append(row)

        # POST to mock PBI
        url = f"{api_base_url}/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/tables/{table_name}/rows"
        try:
            response = httpx.post(url, json={"rows": rows}, timeout=10.0)
            if response.status_code == 200:
                print(f"[PBI Push] Pushed {len(rows)} rows to {dataset['name']} -> {table_name}")
            else:
                print(f"[PBI Push] Failed to push to {table_name}: {response.status_code} {response.text}")
        except httpx.ConnectError:
            print(f"[PBI Push] Could not connect to mock PBI server at {api_base_url}")
            break

    conn.close()


if __name__ == "__main__":
    push_gold_to_pbi()
