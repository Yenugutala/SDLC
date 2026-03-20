# SDLC Data Project - Healthcare Pipeline

End-to-end data pipeline with Bronze/Silver/Gold layers, data profiling, lineage tracking, and a RAG-based query interface.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
```

## Run Pipeline

```bash
python main.py
```

This runs all steps: CSV ingestion -> Bronze -> Silver -> Gold -> Profiling -> Lineage -> Dictionary -> Ontology -> ChromaDB ingestion.

## Query the Data Catalog

```bash
python ask.py "What does col_x1a mean in silver_tbl_a1?"
python ask.py "Show me the lineage of patient_id"
python ask.py "What tables exist in the gold layer?"
python ask.py "How are patients and visits related?"
```

## Architecture

| Layer | Description |
|-------|-------------|
| **Bronze** | Raw CSV ingestion into SQLite (original column names) |
| **Silver** | Obfuscated column names (e.g., `patient_id` -> `col_x1a`) |
| **Gold** | SQL Views with different obfuscated names (e.g., `col_x1a` -> `attr_m1`) |

## Data Intelligence

- **Great Expectations**: Profiling stats for each layer
- **Lineage Tracker**: Source -> Bronze -> Silver -> Gold column mapping
- **Data Dictionary**: Column descriptions, types, stats per layer
- **Ontology**: Entity relationships (Patient 1:N Visit)
- **ChromaDB + Claude**: RAG-based Q&A over the full data catalog
