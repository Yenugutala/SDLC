"""Ontology: Programmatically discover entities and relationships using LLM — no hardcoded patterns."""

import json
import os
import re
import anthropic
from dotenv import load_dotenv

from pipeline.schema_utils import get_all_bronze_schemas, get_entity_name_from_bronze

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def detect_primary_key(entity_name, columns, profile_stats):
    """Detect the primary key column using uniqueness stats and naming conventions."""
    entity_singular = entity_name.rstrip("s")

    # Strategy 1: column named {entity}_id or id with unique count == row count
    if profile_stats:
        row_count = profile_stats.get("row_count", 0)
        for col_name, col_stats in profile_stats.get("columns", {}).items():
            if col_stats.get("unique_count") == row_count and col_name.endswith("_id"):
                return col_name

    # Strategy 2: naming convention ({entity_singular}_id)
    for col in columns:
        if col == f"{entity_singular}_id" or col == "id":
            return col

    # Strategy 3: any column ending in _id with unique values
    if profile_stats:
        row_count = profile_stats.get("row_count", 0)
        for col_name, col_stats in profile_stats.get("columns", {}).items():
            if col_name.endswith("_id") and col_stats.get("unique_count") == row_count:
                return col_name

    # Strategy 4: first column
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


def generate_ontology_descriptions(entities_info, relationships_info):
    """Use LLM to generate entity and relationship descriptions in one call."""
    client = anthropic.Anthropic()

    entities_ctx = []
    for name, info in entities_info.items():
        attrs = ", ".join(info["attributes"][:10])
        entities_ctx.append(
            f"- {name}: PK={info['pk']}, columns=[{attrs}]"
        )

    rels_ctx = []
    for rel in relationships_info:
        key = f"{rel['from']}__{rel['to']}"
        rels_ctx.append(
            f"- {key}: {rel['from']} -> {rel['to']} linked by column '{rel['join_col']}'"
        )

    prompt = (
        f"Based on these database entities and their relationships, generate descriptions.\n\n"
        f"Entities:\n{chr(10).join(entities_ctx)}\n\n"
        f"Relationships:\n{chr(10).join(rels_ctx) if rels_ctx else 'None detected'}\n\n"
        f"Return ONLY a valid JSON object:\n"
        f'{{"entities": {{"EntityName": "description", ...}}, '
        f'"relationships": {{"From__To": {{"description": "...", "type": "one_to_many or one_to_one or many_to_many"}}, ...}}}}\n'
        f"No markdown, no explanation, just the JSON."
    )

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        try:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        print(f"[Ontology] Warning: LLM call failed: {e}")
        return {"entities": {}, "relationships": {}}


def build_entity(entity_name, bronze_table, columns, pk, lineage_data, description):
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

    return entity_key, {
        "description": description,
        "source_file": f"{entity_name}.csv",
        "primary_key": pk,
        "attributes": attributes,
        "layers": layers,
    }


def generate_ontology(db_path=None):
    """Programmatically generate ontology from database metadata and LLM descriptions."""
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

    # Detect PKs and relationships programmatically
    entity_info_for_llm = {}
    entity_pks = {}
    for bronze_table, columns in bronze_schemas.items():
        entity_name = get_entity_name_from_bronze(bronze_table)
        entity_key = entity_name.title().rstrip("s")
        profile = bronze_profile.get(bronze_table, {})
        pk = detect_primary_key(entity_name, columns, profile)
        entity_pks[entity_key] = pk
        entity_info_for_llm[entity_key] = {
            "pk": pk,
            "attributes": [c for c in columns if c != pk],
        }

    raw_relationships = detect_relationships(bronze_schemas, bronze_profile)

    rels_for_llm = []
    for rel in raw_relationships:
        from_key = rel["from_entity_name"].title().rstrip("s")
        to_key = rel["to_entity_name"].title().rstrip("s")
        rels_for_llm.append({
            "from": from_key,
            "to": to_key,
            "join_col": rel["join_column"],
        })

    # Generate descriptions via LLM (one call for all entities + relationships)
    print("[Ontology] Generating entity and relationship descriptions via LLM...")
    llm_descriptions = generate_ontology_descriptions(entity_info_for_llm, rels_for_llm)

    # Build entities with LLM descriptions
    entities = {}
    for bronze_table, columns in bronze_schemas.items():
        entity_name = get_entity_name_from_bronze(bronze_table)
        entity_key = entity_name.title().rstrip("s")
        profile = bronze_profile.get(bronze_table, {})
        pk = detect_primary_key(entity_name, columns, profile)

        description = llm_descriptions.get("entities", {}).get(
            entity_key,
            f"Entity representing {entity_name} data",
        )

        ek, entity_def = build_entity(
            entity_name, bronze_table, columns, pk, lineage_data, description
        )
        entities[ek] = entity_def

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

        # Use LLM description and relationship type
        rel_key = f"{from_entity_key}__{to_entity_key}"
        llm_rel = llm_descriptions.get("relationships", {}).get(rel_key, {})
        rel_description = llm_rel.get(
            "description",
            f"{from_entity_key} is linked to {to_entity_key} via {join_col}",
        )
        rel_type = llm_rel.get("type", "one_to_many")

        relationships.append({
            "name": f"{from_entity_key} has {to_entity_name.title()}",
            "type": rel_type,
            "from_entity": from_entity_key,
            "to_entity": to_entity_key,
            "join_description": rel_description,
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
