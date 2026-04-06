"""Vector Store: Ingest data dictionary, ontology, and lineage into ChromaDB.

Embedding strategy:
  - Description-first document text for better semantic matching
  - Stats (null_pct, unique_count, sample_values) in metadata only — not embedded
  - Cross-layer concept documents group the same business column across layers
"""

import json
import os
import chromadb


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "profiling_output")
CHROMA_DIR = os.path.join(PROJECT_DIR, "chroma_db")


def get_chroma_client():
    """Get or create a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=CHROMA_DIR)


def ingest_data_dictionary(client):
    """Ingest data dictionary into ChromaDB with description-first document text.

    Document text is optimized for embedding quality:
      - Description and original name lead (semantic signal)
      - Obfuscated column name and table follow (lookup keys)
      - Stats stored in metadata only (not embedded)

    Also generates cross-layer concept documents that group the same
    business column (by original_name) across bronze/silver/gold layers.
    """
    collection = client.get_or_create_collection("data_dictionary", metadata={"hnsw:space": "cosine"})

    dict_path = os.path.join(OUTPUT_DIR, "data_dictionary.json")
    with open(dict_path) as f:
        data_dict = json.load(f)

    documents = []
    metadatas = []
    ids = []

    # Track columns by original_name for concept document generation
    concept_groups = {}

    for layer, tables in data_dict.items():
        for table_name, table_info in tables.items():
            for col in table_info.get("columns", []):
                # Description-first document text for better embeddings
                doc = (
                    f"Description: {col['description']} | "
                    f"Original Name: {col['original_name']} | "
                    f"Column: {col['column_name']} | "
                    f"Table: {table_name} | "
                    f"Layer: {layer} | "
                    f"Type: {col['data_type']}"
                )
                documents.append(doc)
                # Stats in metadata only — not embedded
                metadatas.append({
                    "layer": layer,
                    "table": table_name,
                    "column": col["column_name"],
                    "original_name": col["original_name"],
                    "type": "data_dictionary",
                    "null_pct": float(col.get("null_pct", 0)),
                    "unique_count": int(col.get("unique_count", 0)),
                    "sample_values": str(col.get("sample_values", [])),
                })
                ids.append(f"dict_{layer}_{table_name}_{col['column_name']}")

                # Group for concept docs
                orig = col["original_name"]
                if orig not in concept_groups:
                    concept_groups[orig] = []
                concept_groups[orig].append({
                    "layer": layer,
                    "table": table_name,
                    "column": col["column_name"],
                    "description": col["description"],
                    "data_type": col["data_type"],
                })

    # Generate cross-layer concept documents
    for original_name, appearances in concept_groups.items():
        layers_text = " -> ".join(
            f"{a['layer']}.{a['table']}.{a['column']}"
            for a in sorted(appearances, key=lambda x: {"bronze": 0, "silver": 1, "gold": 2}.get(x["layer"], 3))
        )
        description = appearances[0]["description"]
        doc = (
            f"Concept: {original_name} | "
            f"Description: {description} | "
            f"Appears across layers: {layers_text}"
        )
        documents.append(doc)
        metadatas.append({
            "original_name": original_name,
            "type": "concept",
            "layer_count": len(set(a["layer"] for a in appearances)),
        })
        ids.append(f"concept_{original_name}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    col_count = len(documents) - len(concept_groups)
    print(f"[VectorStore] Ingested {col_count} data dictionary entries + {len(concept_groups)} concept documents")


def ingest_ontology(client):
    """Ingest ontology into ChromaDB."""
    collection = client.get_or_create_collection("ontology", metadata={"hnsw:space": "cosine"})

    ont_path = os.path.join(OUTPUT_DIR, "ontology.json")
    with open(ont_path) as f:
        ontology = json.load(f)

    documents = []
    metadatas = []
    ids = []

    # Entities
    for entity_name, entity_info in ontology["entities"].items():
        doc = (
            f"Entity: {entity_name} | "
            f"Description: {entity_info['description']} | "
            f"Source: {entity_info['source_file']} | "
            f"Primary Key: {entity_info['primary_key']} | "
            f"Attributes: {', '.join(entity_info['attributes'])} | "
            f"Bronze Table: {entity_info['layers'].get('bronze', {}).get('table', 'N/A')} | "
            f"Silver Table: {entity_info['layers'].get('silver', {}).get('table', 'N/A')} | "
            f"Gold View: {entity_info['layers'].get('gold', {}).get('view', 'N/A')}"
        )
        documents.append(doc)
        metadatas.append({"entity": entity_name, "type": "entity"})
        ids.append(f"entity_{entity_name}")

    # Relationships
    for rel in ontology["relationships"]:
        doc = (
            f"Relationship: {rel['name']} | "
            f"Type: {rel['type']} | "
            f"From: {rel['from_entity']} -> To: {rel['to_entity']} | "
            f"Description: {rel['join_description']} | "
            f"Bronze Join: {rel['join_keys'].get('bronze', {}).get('from_table', 'N/A')}.{rel['join_keys'].get('bronze', {}).get('from_column', 'N/A')} = "
            f"{rel['join_keys'].get('bronze', {}).get('to_table', 'N/A')}.{rel['join_keys'].get('bronze', {}).get('to_column', 'N/A')} | "
            f"Silver Join: {rel['join_keys'].get('silver', {}).get('from_table', 'N/A')}.{rel['join_keys'].get('silver', {}).get('from_column', 'N/A')} = "
            f"{rel['join_keys'].get('silver', {}).get('to_table', 'N/A')}.{rel['join_keys'].get('silver', {}).get('to_column', 'N/A')} | "
            f"Gold Join: {rel['join_keys'].get('gold', {}).get('from_table', 'N/A')}.{rel['join_keys'].get('gold', {}).get('from_column', 'N/A')} = "
            f"{rel['join_keys'].get('gold', {}).get('to_table', 'N/A')}.{rel['join_keys'].get('gold', {}).get('to_column', 'N/A')}"
        )
        documents.append(doc)
        metadatas.append({"relationship": rel["name"], "type": "relationship"})
        ids.append(f"rel_{rel['name'].replace(' ', '_')}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[VectorStore] Ingested {len(documents)} ontology entries")


def ingest_lineage(client):
    """Ingest lineage data into ChromaDB."""
    collection = client.get_or_create_collection("lineage", metadata={"hnsw:space": "cosine"})

    lineage_path = os.path.join(OUTPUT_DIR, "lineage.json")
    with open(lineage_path) as f:
        lineage = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for lineage_type, entries in lineage.items():
        for i, entry in enumerate(entries):
            doc = (
                f"Column Lineage: {entry['source_column']} | "
                f"Source: {entry.get('source_table', entry['bronze_table'])}.{entry['source_column']} -> "
                f"Bronze: {entry['bronze_table']}.{entry['bronze_column']} -> "
                f"Silver: {entry['silver_table']}.{entry['silver_column']} -> "
                f"Gold: {entry['gold_view']}.{entry['gold_column']} | "
                f"Transformation: {entry.get('transformation_type', 'rename')} | "
                f"Expression: {entry.get('expression', 'N/A')}"
            )
            documents.append(doc)
            metadatas.append({
                "source_column": entry["source_column"],
                "source_table": entry.get("source_table", entry.get("bronze_table", "")),
                "type": "lineage",
                "transformation_type": entry.get("transformation_type", "rename"),
                "silver_table": lineage_type.replace("_lineage", ""),
                "silver_column": entry.get("silver_column", ""),
                "gold_column": entry.get("gold_column", ""),
            })
            ids.append(f"lineage_{lineage_type}_{i}_{entry['source_column']}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[VectorStore] Ingested {len(documents)} lineage entries")


def ingest_pbi_lineage(client):
    """Ingest PBI lineage into a separate 'pbi_lineage' ChromaDB collection.

    Document types:
      - pbi_column_lineage: PBI column -> Gold column mapping
      - pbi_end_to_end: Full chain PBI -> Gold -> Silver -> Bronze -> CSV
    """
    collection = client.get_or_create_collection("pbi_lineage", metadata={"hnsw:space": "cosine"})

    documents = []
    metadatas = []
    ids = []

    # Type 1: PBI column lineage (from pbi_lineage.json column_mappings)
    pbi_lineage_path = os.path.join(OUTPUT_DIR, "pbi_lineage.json")
    with open(pbi_lineage_path) as f:
        pbi_lineage = json.load(f)

    for cm in pbi_lineage.get("column_mappings", []):
        doc = (
            f"PBI Column Lineage: {cm['pbi_column']} | "
            f"PBI: {cm['pbi_table']}.{cm['pbi_column']} "
            f"({cm['pbi_dataset']}) -> "
            f"Gold: {cm['gold_view']}.{cm['gold_column']} | "
            f"DataType: {cm['pbi_data_type']}"
        )
        documents.append(doc)
        metadatas.append({
            "type": "pbi_column_lineage",
            "pbi_column": cm["pbi_column"],
            "pbi_table": cm["pbi_table"],
            "pbi_dataset": cm["pbi_dataset"],
            "gold_view": cm["gold_view"],
            "gold_column": cm["gold_column"],
            "pbi_data_type": cm["pbi_data_type"],
        })
        ids.append(f"pbi_lineage_{cm['pbi_table']}_{cm['pbi_column']}")

    col_lineage_count = len(documents)

    # Type 2: End-to-end lineage (from pbi_end_to_end_lineage.json)
    e2e_path = os.path.join(OUTPUT_DIR, "pbi_end_to_end_lineage.json")
    if os.path.exists(e2e_path):
        with open(e2e_path) as f:
            e2e_data = json.load(f)

        for entry in e2e_data:
            doc = (
                f"End-to-End Lineage: {entry['pbi_column']} | "
                f"PBI: {entry['pbi_table']}.{entry['pbi_column']} -> "
                f"Gold: {entry['gold_view']}.{entry['gold_column']} -> "
                f"Silver: {entry['silver_table']}.{entry['silver_column']} -> "
                f"Bronze: {entry['bronze_table']}.{entry['bronze_column']} -> "
                f"Source: {entry['source_file']}.{entry['source_column']} | "
                f"Transformation: {entry['transformation_type']}"
            )
            documents.append(doc)
            metadatas.append({
                "type": "pbi_end_to_end",
                "pbi_column": entry["pbi_column"],
                "pbi_table": entry["pbi_table"],
                "gold_column": entry["gold_column"],
                "silver_column": entry["silver_column"],
                "bronze_column": entry["bronze_column"],
                "source_file": entry["source_file"],
                "source_column": entry.get("source_column", ""),
                "transformation_type": entry["transformation_type"],
            })
            ids.append(f"pbi_e2e_{entry['pbi_table']}_{entry['pbi_column']}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    e2e_count = len(documents) - col_lineage_count
    print(f"[VectorStore] Ingested {col_lineage_count} PBI column lineage + {e2e_count} end-to-end lineage into pbi_lineage")


def ingest_pbi_catalog(client):
    """Ingest PBI catalog metadata into a separate 'pbi_catalog' ChromaDB collection.

    Document types:
      - pbi_column: PBI column definitions
      - pbi_measure: KPIs with DAX expressions
      - pbi_report: Report metadata
      - pbi_dashboard: Dashboard metadata with tile listings
      - pbi_artifact_relationship: Dashboard -> Report -> Dataset hierarchy
    """
    collection = client.get_or_create_collection("pbi_catalog", metadata={"hnsw:space": "cosine"})

    documents = []
    metadatas = []
    ids = []

    pbi_lineage_path = os.path.join(OUTPUT_DIR, "pbi_lineage.json")
    with open(pbi_lineage_path) as f:
        pbi_lineage = json.load(f)

    # Type 3: PBI Measures/KPIs
    for m in pbi_lineage.get("measures", []):
        dep_cols = ", ".join(m.get("dependent_pbi_columns", []))
        doc = (
            f"PBI Measure: {m['measure_name']} | "
            f"Table: {m['pbi_table']} | "
            f"Dataset: {m['pbi_dataset']} | "
            f"DAX: {m['dax_expression']} | "
            f"Depends on columns: {dep_cols} | "
            f"Source Gold View: {m['gold_view']}"
        )
        documents.append(doc)
        metadatas.append({
            "type": "pbi_measure",
            "measure_name": m["measure_name"],
            "pbi_table": m["pbi_table"],
            "pbi_dataset": m["pbi_dataset"],
            "dax_expression": m["dax_expression"],
            "gold_view": m["gold_view"],
        })
        ids.append(f"pbi_measure_{m['pbi_table']}_{m['measure_name'].replace(' ', '_')}")

    measure_count = len(documents)

    # Type 4: PBI Columns
    for cm in pbi_lineage.get("column_mappings", []):
        doc = (
            f"PBI Column: {cm['pbi_column']} | "
            f"Table: {cm['pbi_table']} | "
            f"Dataset: {cm['pbi_dataset']} | "
            f"Type: {cm['pbi_data_type']} | "
            f"Maps to Gold column: {cm['gold_column']} in {cm['gold_view']}"
        )
        documents.append(doc)
        metadatas.append({
            "type": "pbi_column",
            "pbi_column": cm["pbi_column"],
            "pbi_table": cm["pbi_table"],
            "pbi_dataset": cm["pbi_dataset"],
            "pbi_data_type": cm["pbi_data_type"],
            "gold_view": cm["gold_view"],
            "gold_column": cm["gold_column"],
        })
        ids.append(f"pbi_col_{cm['pbi_table']}_{cm['pbi_column']}")

    col_count = len(documents) - measure_count

    # Type 5: PBI Reports
    # Build report info from dashboard lineage (reports referenced by tiles)
    seen_reports = set()
    for db_entry in pbi_lineage.get("dashboards", []):
        for tile in db_entry.get("tiles", []):
            report_name = tile.get("report", "Unknown")
            dataset_name = tile.get("dataset", "Unknown")
            report_id = tile.get("report_id", "")
            if report_name not in seen_reports:
                seen_reports.add(report_name)
                doc = (
                    f"PBI Report: {report_name} | "
                    f"Dataset: {dataset_name} | "
                    f"Report ID: {report_id}"
                )
                documents.append(doc)
                metadatas.append({
                    "type": "pbi_report",
                    "report_name": report_name,
                    "dataset_name": dataset_name,
                })
                ids.append(f"pbi_report_{report_name.replace(' ', '_')}")

    report_count = len(seen_reports)

    # Type 6: PBI Dashboards
    for db_entry in pbi_lineage.get("dashboards", []):
        db_name = db_entry["dashboard"]
        tiles = db_entry.get("tiles", [])
        tile_names = ", ".join(t.get("tile", "") for t in tiles)
        report_names = ", ".join(sorted(set(t.get("report", "") for t in tiles)))

        doc = (
            f"PBI Dashboard: {db_name} | "
            f"Tiles: {tile_names} | "
            f"Reports: {report_names}"
        )
        documents.append(doc)
        metadatas.append({
            "type": "pbi_dashboard",
            "dashboard_name": db_name,
            "tile_count": len(tiles),
        })
        ids.append(f"pbi_dashboard_{db_name.replace(' ', '_')}")

    dashboard_count = len(pbi_lineage.get("dashboards", []))

    # Type 7: PBI Artifact Relationships
    for db_entry in pbi_lineage.get("dashboards", []):
        db_name = db_entry["dashboard"]
        tiles = db_entry.get("tiles", [])
        reports = sorted(set(t.get("report", "") for t in tiles))
        datasets = sorted(set(t.get("dataset", "") for t in tiles))
        gold_views = sorted(set(t.get("gold_view", "") for t in tiles))

        doc = (
            f"PBI Artifact Hierarchy: Dashboard '{db_name}' -> "
            f"contains Tiles -> linked to Reports: {', '.join(reports)} -> "
            f"Reports use Datasets: {', '.join(datasets)} -> "
            f"Datasets sourced from Gold Views: {', '.join(gold_views)}"
        )
        documents.append(doc)
        metadatas.append({
            "type": "pbi_artifact_relationship",
            "dashboard_name": db_name,
        })
        ids.append(f"pbi_rel_{db_name.replace(' ', '_')}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    total = len(documents)
    print(f"[VectorStore] Ingested {total} PBI catalog entries into pbi_catalog "
          f"({measure_count} measures, {col_count} columns, "
          f"{report_count} reports, {dashboard_count} dashboards, "
          f"{dashboard_count} relationships)")


def ingest_catalog_summary(client):
    """Generate a dynamic catalog summary from profiling outputs and ingest into data_dictionary.

    Reads the actual JSON files to compute counts, so the summary auto-updates
    whenever the pipeline runs — no hardcoded numbers.
    """
    parts = []

    # --- Data Dictionary ---
    dict_path = os.path.join(OUTPUT_DIR, "data_dictionary.json")
    if os.path.exists(dict_path):
        with open(dict_path) as f:
            data_dict = json.load(f)
        layer_details = []
        total_tables = 0
        total_cols = 0
        for layer, tables in data_dict.items():
            table_names = list(tables.keys())
            col_count = sum(len(t.get("columns", [])) for t in tables.values())
            total_tables += len(table_names)
            total_cols += col_count
            layer_details.append(
                f"{layer.title()} ({len(table_names)} tables: {', '.join(table_names)})"
            )
        parts.append(
            f"Data Dictionary: {total_tables} tables with {total_cols} columns across "
            f"{' | '.join(layer_details)}. "
            f"Includes column descriptions, data types, sample values, and statistics."
        )

    # --- Ontology ---
    ont_path = os.path.join(OUTPUT_DIR, "ontology.json")
    if os.path.exists(ont_path):
        with open(ont_path) as f:
            ontology = json.load(f)
        entities = list(ontology.get("entities", {}).keys())
        rel_count = len(ontology.get("relationships", []))
        parts.append(
            f"Ontology: {len(entities)} entities ({', '.join(entities)}) "
            f"and {rel_count} relationships."
        )

    # --- Lineage ---
    lin_path = os.path.join(OUTPUT_DIR, "lineage.json")
    if os.path.exists(lin_path):
        with open(lin_path) as f:
            lineage = json.load(f)
        lineage_count = sum(len(entries) for entries in lineage.values())
        parts.append(
            f"Lineage: {lineage_count} column-level lineage entries tracking "
            f"data flow from source CSV files through Bronze -> Silver -> Gold layers."
        )

    # --- Power BI ---
    pbi_path = os.path.join(OUTPUT_DIR, "pbi_lineage.json")
    if os.path.exists(pbi_path):
        with open(pbi_path) as f:
            pbi = json.load(f)
        dashboards = pbi.get("dashboards", [])
        dashboard_count = len(dashboards)
        tile_count = sum(len(d.get("tiles", [])) for d in dashboards)
        measure_count = len(pbi.get("measures", []))
        col_map_count = len(pbi.get("column_mappings", []))

        # Count unique reports and datasets from tiles
        reports = set()
        datasets = set()
        for d in dashboards:
            for t in d.get("tiles", []):
                if t.get("report"):
                    reports.add(t["report"])
                if t.get("dataset"):
                    datasets.add(t["dataset"])

        measure_names = [m["measure_name"] for m in pbi.get("measures", [])]

        pbi_parts = [
            f"Power BI: {dashboard_count} dashboards with {tile_count} tiles",
            f"{len(reports)} reports" if reports else None,
            f"{len(datasets)} datasets mapped to Gold views" if datasets else None,
            f"{measure_count} DAX measures ({', '.join(measure_names)})" if measure_names else None,
            f"{col_map_count} column mappings from PBI to Gold layer",
        ]
        parts.append(". ".join(p for p in pbi_parts if p) + ".")

        # End-to-end lineage
        e2e_path = os.path.join(OUTPUT_DIR, "pbi_end_to_end_lineage.json")
        if os.path.exists(e2e_path):
            with open(e2e_path) as f:
                e2e = json.load(f)
            parts.append(
                f"End-to-End Lineage: {len(e2e)} column chains tracing data from "
                f"PBI dashboard columns back through Gold -> Silver -> Bronze -> source CSV files."
            )

    summary_doc = "CATALOG SUMMARY | " + " | ".join(parts)

    collection = client.get_collection("data_dictionary")
    collection.upsert(
        documents=[summary_doc],
        metadatas=[{"type": "catalog_summary"}],
        ids=["catalog_summary"],
    )
    print(f"[VectorStore] Ingested dynamic catalog summary (1 document)")


def reset_collections(client):
    """Delete and recreate all collections to remove stale data."""
    for name in ["data_dictionary", "ontology", "lineage", "pbi_lineage", "pbi_catalog"]:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    print("[VectorStore] Cleared all existing collections")


def build_vectorstore():
    """Run full ingestion into ChromaDB."""
    client = get_chroma_client()

    # Always reset collections to remove stale data from previous runs
    reset_collections(client)

    ingest_data_dictionary(client)
    ingest_ontology(client)
    ingest_lineage(client)

    # PBI collections (only if PBI lineage has been built)
    pbi_lineage_path = os.path.join(OUTPUT_DIR, "pbi_lineage.json")
    if os.path.exists(pbi_lineage_path):
        ingest_pbi_lineage(client)
        ingest_pbi_catalog(client)
    else:
        print("[VectorStore] No pbi_lineage.json found, skipping PBI ingestion")

    # Dynamic catalog summary (after all other ingestions so counts are complete)
    ingest_catalog_summary(client)

    print(f"[VectorStore] All data ingested into ChromaDB at {CHROMA_DIR}")
    return client


if __name__ == "__main__":
    build_vectorstore()
