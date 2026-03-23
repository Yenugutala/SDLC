"""Silver Layer: Transform bronze tables with dynamically generated obfuscated column names."""

import os
import random
import string
import sqlite3
import pandas as pd

from pipeline.schema_utils import get_all_bronze_schemas, get_entity_name_from_bronze


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")

PREFIXES = ["col", "fld", "attr", "flg", "cod", "val", "txt", "ref", "dt", "num", "cat"]


def generate_obfuscated_name(used_names):
    """Generate a unique random obfuscated column name like 'col_x1a'."""
    while True:
        prefix = random.choice(PREFIXES)
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
        name = f"{prefix}_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name


def generate_silver_table_name(entity_name, used_names):
    """Generate obfuscated silver table name like 'silver_tbl_a1'."""
    while True:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=2))
        name = f"silver_tbl_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name


def build_column_map(columns, shared_names_map, used_names):
    """Generate column mapping for one bronze table.

    Columns that already appear in shared_names_map get the same obfuscated name
    (preserving cross-table join keys like patient_id).
    """
    column_map = {}
    for col in columns:
        if col in shared_names_map:
            column_map[col] = shared_names_map[col]
        else:
            obfuscated = generate_obfuscated_name(used_names)
            column_map[col] = obfuscated
            shared_names_map[col] = obfuscated
    return column_map


def transform_silver(db_path=None, seed=42):
    """Read bronze tables, dynamically rename columns, write as silver tables."""
    db_path = db_path or DB_PATH
    random.seed(seed)

    # Discover all bronze tables and their schemas
    bronze_schemas = get_all_bronze_schemas(db_path)

    conn = sqlite3.connect(db_path)

    used_col_names = set()
    used_table_names = set()
    shared_names_map = {}
    all_mappings = {}

    for bronze_table, columns in bronze_schemas.items():
        entity = get_entity_name_from_bronze(bronze_table)
        silver_table = generate_silver_table_name(entity, used_table_names)
        column_map = build_column_map(columns, shared_names_map, used_col_names)

        df = pd.read_sql(f"SELECT * FROM {bronze_table}", conn)
        df_silver = df.rename(columns=column_map)
        df_silver.to_sql(silver_table, conn, if_exists="replace", index=False)

        mapping_key = f"{bronze_table}_to_{silver_table}"
        all_mappings[mapping_key] = column_map

        print(f"[Silver] Created {silver_table} from {bronze_table} ({len(columns)} columns)")

    # Store lineage metadata in the database (like Databricks Unity Catalog)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _column_lineage (
            source_table TEXT,
            source_column TEXT,
            target_table TEXT,
            target_column TEXT,
            transformation_type TEXT
        )
    """)
    cursor.execute("DELETE FROM _column_lineage WHERE transformation_type = 'rename'")
    for mapping_key, column_map in all_mappings.items():
        bronze_table = mapping_key.split("_to_")[0]
        silver_table = mapping_key.split("_to_")[1]
        for source_col, target_col in column_map.items():
            cursor.execute(
                "INSERT INTO _column_lineage VALUES (?, ?, ?, ?, ?)",
                (bronze_table, source_col, silver_table, target_col, "rename"),
            )

    conn.commit()
    conn.close()

    print(f"[Silver] Column lineage stored in _column_lineage table")
    return all_mappings


if __name__ == "__main__":
    transform_silver()
