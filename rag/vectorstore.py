"""Vector Store: Ingest data dictionary, ontology, lineage, and code into ChromaDB."""

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
    """Ingest data dictionary into ChromaDB."""
    collection = client.get_or_create_collection("data_dictionary")

    dict_path = os.path.join(OUTPUT_DIR, "data_dictionary.json")
    with open(dict_path) as f:
        data_dict = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for layer, tables in data_dict.items():
        for table_name, table_info in tables.items():
            for col in table_info.get("columns", []):
                doc = (
                    f"Layer: {layer} | Table: {table_name} | "
                    f"Column: {col['column_name']} | "
                    f"Original Name: {col['original_name']} | "
                    f"Type: {col['data_type']} | "
                    f"Description: {col['description']} | "
                    f"Null%: {col['null_pct']} | "
                    f"Unique Count: {col['unique_count']} | "
                    f"Samples: {col['sample_values']}"
                )
                documents.append(doc)
                metadatas.append({
                    "layer": layer,
                    "table": table_name,
                    "column": col["column_name"],
                    "original_name": col["original_name"],
                    "type": "data_dictionary",
                })
                ids.append(f"dict_{layer}_{table_name}_{col['column_name']}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[VectorStore] Ingested {len(documents)} data dictionary entries")


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
            f"Bronze Table: {entity_info['layers']['bronze'].get('table', 'N/A')} | "
            f"Silver Table: {entity_info['layers']['silver'].get('table', 'N/A')} | "
            f"Gold View: {entity_info['layers']['gold'].get('view', 'N/A')}"
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
            f"Bronze Join: {rel['join_keys']['bronze']['from_table']}.{rel['join_keys']['bronze']['from_column']} = "
            f"{rel['join_keys']['bronze']['to_table']}.{rel['join_keys']['bronze']['to_column']} | "
            f"Silver Join: {rel['join_keys']['silver']['from_table']}.{rel['join_keys']['silver']['from_column']} = "
            f"{rel['join_keys']['silver']['to_table']}.{rel['join_keys']['silver']['to_column']} | "
            f"Gold Join: {rel['join_keys']['gold']['from_table']}.{rel['join_keys']['gold']['from_column']} = "
            f"{rel['join_keys']['gold']['to_table']}.{rel['join_keys']['gold']['to_column']}"
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
        for entry in entries:
            doc = (
                f"Column Lineage: {entry['source_column']} | "
                f"Source: {entry['source_file']}.{entry['source_column']} -> "
                f"Bronze: {entry['bronze_table']}.{entry['bronze_column']} -> "
                f"Silver: {entry['silver_table']}.{entry['silver_column']} -> "
                f"Gold: {entry['gold_view']}.{entry['gold_column']}"
            )
            documents.append(doc)
            metadatas.append({
                "source_column": entry["source_column"],
                "type": "lineage",
                "entity": lineage_type.replace("_lineage", ""),
            })
            ids.append(f"lineage_{lineage_type}_{entry['source_column']}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[VectorStore] Ingested {len(documents)} lineage entries")


def ingest_code(client):
    """Ingest Python source code files into ChromaDB."""
    collection = client.get_or_create_collection("code")

    documents = []
    metadatas = []
    ids = []

    for root, dirs, files in os.walk(PROJECT_DIR):
        # Skip chroma_db and __pycache__ directories
        dirs[:] = [d for d in dirs if d not in ("chroma_db", "__pycache__", ".git")]
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, PROJECT_DIR)
                with open(filepath) as f:
                    code = f.read()

                # Chunk code into ~500 char segments for better retrieval
                chunk_size = 500
                for i in range(0, len(code), chunk_size):
                    chunk = code[i : i + chunk_size]
                    doc = f"File: {rel_path} | Code:\n{chunk}"
                    documents.append(doc)
                    metadatas.append({
                        "file": rel_path,
                        "type": "code",
                        "chunk_index": i // chunk_size,
                    })
                    ids.append(f"code_{rel_path}_{i // chunk_size}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[VectorStore] Ingested {len(documents)} code chunks")


def reset_collections(client):
    """Delete and recreate all collections to remove stale data."""
    for name in ["data_dictionary", "ontology", "lineage", "code"]:
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
    ingest_code(client)

    print(f"[VectorStore] All data ingested into ChromaDB at {CHROMA_DIR}")
    return client


if __name__ == "__main__":
    build_vectorstore()
