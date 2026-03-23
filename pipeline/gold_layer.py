"""Gold Layer: Create views on silver tables with dynamically generated obfuscated names."""

import os
import random
import string
import sqlite3

from pipeline.schema_utils import get_tables_by_prefix, get_column_names


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")

GOLD_PREFIXES = ["attr", "dim", "msr", "fct", "key"]


def generate_gold_view_name(used_names):
    """Generate obfuscated gold view name like 'gold_vw_p99'."""
    while True:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
        name = f"gold_vw_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name


def generate_gold_column_name(used_names):
    """Generate obfuscated gold column name like 'attr_m1'."""
    while True:
        prefix = random.choice(GOLD_PREFIXES)
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=2))
        name = f"{prefix}_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name


def create_gold_views(db_path=None, seed=99):
    """Create gold views on silver tables with dynamically generated column names."""
    db_path = db_path or DB_PATH
    random.seed(seed)

    silver_tables = get_tables_by_prefix(db_path, "silver_")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    used_view_names = set()
    used_col_names = set()
    shared_gold_map = {}
    all_mappings = {}

    for silver_table in silver_tables:
        silver_columns = get_column_names(db_path, silver_table)
        gold_view = generate_gold_view_name(used_view_names)

        gold_map = {}
        for silver_col in silver_columns:
            if silver_col in shared_gold_map:
                gold_col = shared_gold_map[silver_col]
            else:
                gold_col = generate_gold_column_name(used_col_names)
                shared_gold_map[silver_col] = gold_col
            gold_map[silver_col] = gold_col

        col_aliases = ", ".join(f"{s} AS {g}" for s, g in gold_map.items())
        cursor.execute(f"DROP VIEW IF EXISTS {gold_view}")
        cursor.execute(f"CREATE VIEW {gold_view} AS SELECT {col_aliases} FROM {silver_table}")

        mapping_key = f"{silver_table}_to_{gold_view}"
        all_mappings[mapping_key] = gold_map

        print(f"[Gold] Created view {gold_view} from {silver_table} ({len(silver_columns)} columns)")

    conn.commit()
    conn.close()

    # No lineage storage needed — VIEW SQL in sqlite_master already contains
    # the full column mapping (SELECT silver_col AS gold_col FROM silver_table)
    print(f"[Gold] Lineage available via VIEW definitions in sqlite_master")
    return all_mappings


if __name__ == "__main__":
    create_gold_views()
