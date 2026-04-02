"""Main Orchestrator: Run the full SDLC data pipeline."""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))

from pipeline.bronze_layer import ingest_bronze
from pipeline.silver_layer import transform_silver
from pipeline.gold_layer import create_gold_views
from profiling.great_expectations_profiler import run_profiling
from profiling.lineage_tracker import build_lineage
from dictionary.data_dictionary import generate_data_dictionary
from dictionary.ontology import generate_ontology
from powerbi.mock_api_server import start_mock_server
from powerbi.data_push_simulator import push_gold_to_pbi
from powerbi.pbi_lineage_builder import build_pbi_lineage
from rag.vectorstore import build_vectorstore


def run_pipeline():
    """Execute all pipeline steps in order."""
    print("=" * 60)
    print("SDLC Data Pipeline - Healthcare")
    print("=" * 60)

    # Part 1: Data Pipeline
    print("\n--- PART 1: Data Pipeline ---\n")

    print("Step 1: Bronze Layer (Raw Ingestion)")
    ingest_bronze()

    print("\nStep 2: Silver Layer (Obfuscated Columns)")
    transform_silver()

    print("\nStep 3: Gold Layer (Views)")
    create_gold_views()

    # Part 2: Data Intelligence
    print("\n--- PART 2: Data Intelligence ---\n")

    print("Step 4: Data Profiling (Great Expectations)")
    run_profiling()

    print("\nStep 5: Lineage Tracking")
    build_lineage()

    print("\nStep 6: Data Dictionary")
    generate_data_dictionary()

    print("\nStep 7: Ontology")
    generate_ontology()

    # Part 3: Power BI Integration
    print("\n--- PART 3: Power BI Integration ---\n")

    print("Step 8: Start Mock Power BI API Server")
    server_thread = threading.Thread(
        target=start_mock_server,
        kwargs={"host": "127.0.0.1", "port": 6789},
        daemon=True,
    )
    server_thread.start()
    time.sleep(1)  # Wait for server startup

    print("\nStep 9: Push Gold Data to Mock PBI")
    push_gold_to_pbi()

    print("\nStep 10: Build PBI Lineage (Dashboard -> Source)")
    build_pbi_lineage()

    # Part 4: Vector Store (after PBI so it includes PBI data)
    print("\n--- PART 4: Vector Store ---\n")

    print("Step 11: Vector Store (ChromaDB) — includes PBI metadata")
    build_vectorstore()

    print("\n" + "=" * 60)
    print("Pipeline complete! Use 'python ask.py <question>' to query.")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
