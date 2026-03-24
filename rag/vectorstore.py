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
    collection = client.get_or_create_collection("data_dictionary")

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
    collection = client.get_or_create_collection("ontology")

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
    collection = client.get_or_create_collection("lineage")

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


def reset_collections(client):
    """Delete and recreate all collections to remove stale data."""
    for name in ["data_dictionary", "ontology", "lineage"]:
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

    print(f"[VectorStore] All data ingested into ChromaDB at {CHROMA_DIR}")
    return client


if __name__ == "__main__":
    build_vectorstore()
