"""Ontology: Programmatically discover entities and relationships across all layers."""

import json
import os

from pipeline.schema_utils import get_all_bronze_schemas, get_entity_name_from_bronze


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def detect_primary_key(entity_name, columns, profile_stats):
    """Heuristically detect the primary key column."""
    entity_singular = entity_name.rstrip("s")

    # Strategy 1: naming convention ({entity_singular}_id)
    for col in columns:
        if col == f"{entity_singular}_id" or col == "id":
            return col

    # Strategy 2: uniqueness from profiling stats
    if profile_stats:
        row_count = profile_stats.get("row_count", 0)
        for col_name, col_stats in profile_stats.get("columns", {}).items():
            if col_stats.get("unique_count") == row_count and col_name.endswith("_id"):
                return col_name

    # Strategy 3: first column
    return columns[0] if columns else "unknown"


def detect_relationships(bronze_schemas, bronze_profiles):
    """Detect FK relationships by finding shared column names across tables."""
    # Build column-to-tables index
    col_to_tables = {}
    for table, columns in bronze_schemas.items():
        for col in columns:
            col_to_tables.setdefault(col, []).append(table)

    # Identify primary keys for each entity
    entity_pks = {}
    for table, columns in bronze_schemas.items():
        entity = get_entity_name_from_bronze(table)
        profile = bronze_profiles.get(table, {})
        pk = detect_primary_key(entity, columns, profile)
        entity_pks[table] = pk

    relationships = []

    # Find columns that appear in multiple tables
    for col, tables in col_to_tables.items():
        if len(tables) < 2:
            continue

        # The table where this column is the PK is the parent entity
        parent_table = None
        child_tables = []
        for table in tables:
            if entity_pks.get(table) == col:
                parent_table = table
            else:
                child_tables.append(table)

        if parent_table is None:
            continue

        for child_table in child_tables:
            parent_entity = get_entity_name_from_bronze(parent_table)
            child_entity = get_entity_name_from_bronze(child_table)
            relationships.append({
                "join_column": col,
                "from_entity_name": parent_entity,
                "to_entity_name": child_entity,
                "from_bronze_table": parent_table,
                "to_bronze_table": child_table,
            })

    return relationships


def build_entity(entity_name, bronze_table, columns, pk, lineage_data):
    """Build a single entity definition with cross-layer table references."""
    entity_key = entity_name.title().rstrip("s")

    attributes = [c for c in columns if c != pk]

    layers = {
        "bronze": {"table": bronze_table, "key_column": pk},
    }

    # Extract silver/gold table names from lineage
    lineage_entries = lineage_data.get(f"{entity_name}_lineage", [])
    if lineage_entries:
        first = lineage_entries[0]
        silver_table = first.get("silver_table", "N/A")
        gold_view = first.get("gold_view", "N/A")

        pk_entry = next((e for e in lineage_entries if e["source_column"] == pk), None)
        if pk_entry:
            layers["silver"] = {
                "table": silver_table,
                "key_column": pk_entry.get("silver_column", "N/A"),
            }
            layers["gold"] = {
                "view": gold_view,
                "key_column": pk_entry.get("gold_column", "N/A"),
            }

    description = f"A {entity_key.lower()} entity sourced from {entity_name}.csv"

    return entity_key, {
        "description": description,
        "source_file": f"{entity_name}.csv",
        "primary_key": pk,
        "attributes": attributes,
        "layers": layers,
    }


def generate_ontology(db_path=None):
    """Programmatically generate ontology from bronze schemas and lineage data."""
    db_path = db_path or DB_PATH

    # Discover bronze schemas
    bronze_schemas = get_all_bronze_schemas(db_path)

    # Load profiling data for PK detection
    bronze_profile = {}
    profile_path = os.path.join(OUTPUT_DIR, "bronze_profile.json")
    if os.path.exists(profile_path):
        with open(profile_path) as f:
            bronze_profile = json.load(f)

    # Load lineage for cross-layer references
    lineage_data = {}
    lineage_path = os.path.join(OUTPUT_DIR, "lineage.json")
    if os.path.exists(lineage_path):
        with open(lineage_path) as f:
            lineage_data = json.load(f)

    # Build entities
    entities = {}
    for bronze_table, columns in bronze_schemas.items():
        entity_name = get_entity_name_from_bronze(bronze_table)
        profile = bronze_profile.get(bronze_table, {})
        pk = detect_primary_key(entity_name, columns, profile)
        entity_key, entity_def = build_entity(entity_name, bronze_table, columns, pk, lineage_data)
        entities[entity_key] = entity_def

    # Detect relationships
    raw_relationships = detect_relationships(bronze_schemas, bronze_profile)

    # Enrich relationships with silver/gold join keys from lineage
    relationships = []
    for rel in raw_relationships:
        join_col = rel["join_column"]
        from_entity_name = rel["from_entity_name"]
        to_entity_name = rel["to_entity_name"]
        from_entity_key = from_entity_name.title().rstrip("s")
        to_entity_key = to_entity_name.title().rstrip("s")

        join_keys = {
            "bronze": {
                "from_table": rel["from_bronze_table"],
                "from_column": join_col,
                "to_table": rel["to_bronze_table"],
                "to_column": join_col,
            }
        }

        # Look up silver/gold column names from lineage
        from_lineage = lineage_data.get(f"{from_entity_name}_lineage", [])
        to_lineage = lineage_data.get(f"{to_entity_name}_lineage", [])

        from_entry = next((e for e in from_lineage if e["source_column"] == join_col), None)
        to_entry = next((e for e in to_lineage if e["source_column"] == join_col), None)

        if from_entry and to_entry:
            join_keys["silver"] = {
                "from_table": from_entry["silver_table"],
                "from_column": from_entry["silver_column"],
                "to_table": to_entry["silver_table"],
                "to_column": to_entry["silver_column"],
            }
            join_keys["gold"] = {
                "from_table": from_entry.get("gold_view", "N/A"),
                "from_column": from_entry.get("gold_column", "N/A"),
                "to_table": to_entry.get("gold_view", "N/A"),
                "to_column": to_entry.get("gold_column", "N/A"),
            }

        relationships.append({
            "name": f"{from_entity_key} has {to_entity_name.title()}",
            "type": "one_to_many",
            "from_entity": from_entity_key,
            "to_entity": to_entity_key,
            "join_description": (
                f"A {from_entity_key.lower()} can have multiple "
                f"{to_entity_name}. Linked by {join_col}."
            ),
            "join_keys": join_keys,
        })

    ontology = {"entities": entities, "relationships": relationships}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "ontology.json")
    with open(output_path, "w") as f:
        json.dump(ontology, f, indent=2)

    print(f"[Ontology] Generated ontology with {len(entities)} entities and {len(relationships)} relationships")
    print(f"[Ontology] Saved to {output_path}")
    return ontology


if __name__ == "__main__":
    generate_ontology()
