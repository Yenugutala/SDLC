"""Data profiling using Great Expectations for each layer."""

import json
import os
import sqlite3
import pandas as pd
import great_expectations as gx

from pipeline.schema_utils import get_tables_by_prefix


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def profile_dataframe(df, table_name):
    """Profile a dataframe and return stats dict."""
    profile = {"table_name": table_name, "row_count": len(df), "columns": {}}

    for col in df.columns:
        col_stats = {
            "data_type": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(float(df[col].isnull().mean() * 100), 2),
            "unique_count": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(3).tolist(),
        }

        # Add min/max for numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            col_stats["min"] = float(df[col].min()) if not df[col].isnull().all() else None
            col_stats["max"] = float(df[col].max()) if not df[col].isnull().all() else None
            col_stats["mean"] = round(float(df[col].mean()), 2) if not df[col].isnull().all() else None
        else:
            col_stats["min_length"] = int(df[col].astype(str).str.len().min())
            col_stats["max_length"] = int(df[col].astype(str).str.len().max())

        profile["columns"][col] = col_stats

    return profile


def run_profiling(db_path=None):
    """Profile all layers: bronze, silver, gold."""
    db_path = db_path or DB_PATH
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = sqlite3.connect(db_path)

    tables = {
        "bronze": get_tables_by_prefix(db_path, "bronze_"),
        "silver": get_tables_by_prefix(db_path, "silver_"),
        "gold": get_tables_by_prefix(db_path, "gold_"),
    }

    all_profiles = {}

    for layer, table_list in tables.items():
        layer_profiles = {}
        for table_name in table_list:
            try:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                profile = profile_dataframe(df, table_name)
                layer_profiles[table_name] = profile
                print(f"[Profiling] {layer}/{table_name}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"[Profiling] Error profiling {table_name}: {e}")
                layer_profiles[table_name] = {"error": str(e)}

        all_profiles[layer] = layer_profiles

        # Save per-layer profile
        output_path = os.path.join(OUTPUT_DIR, f"{layer}_profile.json")
        with open(output_path, "w") as f:
            json.dump(layer_profiles, f, indent=2, default=str)

    conn.close()

    print(f"[Profiling] Results saved to {OUTPUT_DIR}")
    return all_profiles


if __name__ == "__main__":
    run_profiling()
