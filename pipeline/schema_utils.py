"""Schema utilities: Discover tables and columns from the SQLite database."""

import sqlite3


def get_tables_by_prefix(db_path, prefix):
    """Return all table/view names matching a given prefix."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name LIKE ?",
        (f"{prefix}%",),
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(tables)


def get_column_names(db_path, table_name):
    """Return ordered list of column names for a table or view."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns


def get_all_bronze_schemas(db_path):
    """Discover all bronze tables and their column schemas.

    Returns: {"bronze_patients": ["patient_id", "first_name", ...], ...}
    """
    tables = get_tables_by_prefix(db_path, "bronze_")
    schemas = {}
    for table in tables:
        schemas[table] = get_column_names(db_path, table)
    return schemas


def get_entity_name_from_bronze(bronze_table_name):
    """Extract entity name from bronze table name.

    'bronze_patients' -> 'patients'
    """
    return bronze_table_name.replace("bronze_", "", 1)
