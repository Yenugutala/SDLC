"""Silver Layer: Build silver tables from bronze via JOINs and calculations with obfuscated names."""

import os
import random
import string
import sqlite3


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


def generate_silver_table_name(used_names):
    """Generate obfuscated silver table name like 'silver_tbl_a1'."""
    while True:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=2))
        name = f"silver_tbl_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name


def get_silver_table_specs():
    """Define silver table specifications: JOINs, calculations, and column sources.

    Each spec defines:
      - source_tables: list of bronze tables involved
      - join_sql: the FROM...JOIN clause
      - columns: list of dicts with expression, sources, and transformation_type
    """
    return [
        {
            "name": "patient_clinical_records",
            "source_tables": ["bronze_patients", "bronze_visits"],
            "join_sql": (
                "bronze_patients "
                "JOIN bronze_visits ON bronze_patients.patient_id = bronze_visits.patient_id"
            ),
            "columns": [
                {
                    "expression": "bronze_patients.patient_id",
                    "sources": [("bronze_patients", "patient_id")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_patients.first_name || ' ' || bronze_patients.last_name",
                    "sources": [("bronze_patients", "first_name"), ("bronze_patients", "last_name")],
                    "transformation_type": "concat",
                },
                {
                    "expression": "CAST((julianday('now') - julianday(bronze_patients.dob)) / 365.25 AS INTEGER)",
                    "sources": [("bronze_patients", "dob")],
                    "transformation_type": "calculation",
                },
                {
                    "expression": "bronze_patients.gender",
                    "sources": [("bronze_patients", "gender")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_patients.blood_type",
                    "sources": [("bronze_patients", "blood_type")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.visit_date",
                    "sources": [("bronze_visits", "visit_date")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.department",
                    "sources": [("bronze_visits", "department")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.diagnosis",
                    "sources": [("bronze_visits", "diagnosis")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.doctor_name",
                    "sources": [("bronze_visits", "doctor_name")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.treatment",
                    "sources": [("bronze_visits", "treatment")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.status",
                    "sources": [("bronze_visits", "status")],
                    "transformation_type": "rename",
                },
            ],
        },
        {
            "name": "financial_records",
            "source_tables": ["bronze_visits", "bronze_billing", "bronze_patients"],
            "join_sql": (
                "bronze_visits "
                "JOIN bronze_billing ON bronze_visits.visit_id = bronze_billing.visit_id "
                "JOIN bronze_patients ON bronze_visits.patient_id = bronze_patients.patient_id"
            ),
            "columns": [
                {
                    "expression": "bronze_visits.visit_id",
                    "sources": [("bronze_visits", "visit_id")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.patient_id",
                    "sources": [("bronze_visits", "patient_id")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.department",
                    "sources": [("bronze_visits", "department")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_billing.procedure_code",
                    "sources": [("bronze_billing", "procedure_code")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.bill_amount",
                    "sources": [("bronze_visits", "bill_amount")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_billing.insurance_covered",
                    "sources": [("bronze_billing", "insurance_covered")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_visits.bill_amount - bronze_billing.insurance_covered",
                    "sources": [("bronze_visits", "bill_amount"), ("bronze_billing", "insurance_covered")],
                    "transformation_type": "calculation",
                },
                {
                    "expression": "bronze_billing.copay_amount",
                    "sources": [("bronze_billing", "copay_amount")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_patients.insurance_provider",
                    "sources": [("bronze_patients", "insurance_provider")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_billing.payment_status",
                    "sources": [("bronze_billing", "payment_status")],
                    "transformation_type": "rename",
                },
                {
                    "expression": "bronze_billing.billing_date",
                    "sources": [("bronze_billing", "billing_date")],
                    "transformation_type": "rename",
                },
            ],
        },
    ]


def transform_silver(db_path=None, seed=42):
    """Build silver tables from bronze via JOINs and calculations with obfuscated names."""
    db_path = db_path or DB_PATH
    random.seed(seed)

    specs = get_silver_table_specs()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    used_col_names = set()
    used_table_names = set()
    all_lineage_rows = []

    for spec in specs:
        silver_table = generate_silver_table_name(used_table_names)

        select_parts = []
        for col_def in spec["columns"]:
            obfuscated = generate_obfuscated_name(used_col_names)
            select_parts.append(f"{col_def['expression']} AS {obfuscated}")

            # Record lineage: one row per source column
            for src_table, src_col in col_def["sources"]:
                all_lineage_rows.append({
                    "source_table": src_table,
                    "source_column": src_col,
                    "target_table": silver_table,
                    "target_column": obfuscated,
                    "transformation_type": col_def["transformation_type"],
                    "expression": col_def["expression"],
                })

        select_clause = ", ".join(select_parts)
        sql = f"CREATE TABLE {silver_table} AS SELECT {select_clause} FROM {spec['join_sql']}"

        cursor.execute(f"DROP TABLE IF EXISTS {silver_table}")
        cursor.execute(sql)

        src_tables = ", ".join(spec["source_tables"])
        print(f"[Silver] Created {silver_table} from [{src_tables}] ({len(spec['columns'])} columns)")

    # Store lineage metadata in the database (like Databricks Unity Catalog)
    cursor.execute("DROP TABLE IF EXISTS _column_lineage")
    cursor.execute("""
        CREATE TABLE _column_lineage (
            source_table TEXT,
            source_column TEXT,
            target_table TEXT,
            target_column TEXT,
            transformation_type TEXT,
            expression TEXT
        )
    """)
    for row in all_lineage_rows:
        cursor.execute(
            "INSERT INTO _column_lineage VALUES (?, ?, ?, ?, ?, ?)",
            (row["source_table"], row["source_column"], row["target_table"],
             row["target_column"], row["transformation_type"], row["expression"]),
        )

    conn.commit()
    conn.close()

    print(f"[Silver] Column lineage stored in _column_lineage ({len(all_lineage_rows)} rows)")
    return all_lineage_rows


if __name__ == "__main__":
    transform_silver()
