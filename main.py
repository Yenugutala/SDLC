"""Main Orchestrator: Run the full SDLC data pipeline."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from pipeline.bronze_layer import ingest_bronze
from pipeline.silver_layer import transform_silver
from pipeline.gold_layer import create_gold_views
from profiling.great_expectations_profiler import run_profiling
from profiling.lineage_tracker import build_lineage
from dictionary.data_dictionary import generate_data_dictionary
from dictionary.ontology import generate_ontology
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

    print("\nStep 8: Vector Store (ChromaDB)")
    build_vectorstore()

    print("\n" + "=" * 60)
    print("Pipeline complete! Use 'python ask.py <question>' to query.")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
