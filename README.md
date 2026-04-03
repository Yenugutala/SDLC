# SDLC Knowledge Graph 

A Python-based Knowledge Graph for **SDLC automation** — connecting data pipelines, tables, columns, Power BI dashboards, Jira tickets, Confluence docs, and a Data Dictionary into a single queryable graph. Built around **Reckitt Nutrition** as the primary domain.

The core purpose is to answer SDLC impact questions like:
- *Which dashboards break if a column is renamed?*
- *Which KPIs depend on a pipeline?*
- *Which Jira ticket modified a dataset?*

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Data Model](#3-data-model)
4. [Query System — Two Tracks](#4-query-system--two-tracks)
5. [Reckitt Nutrition Domain](#5-reckitt-nutrition-domain)
6. [Setup & Running](#6-setup--running)
7. [Scripts Reference](#7-scripts-reference)
8. [Key Files Reference](#8-key-files-reference)
9. [Environment Variables](#9-environment-variables)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mock Data Layer                          │
│   src/data/mockData.py  (pipelines, tables, columns, KPIs ...)  │
└───────────────────────────────┬─────────────────────────────────┘
                                │  ingestAllData()
                    ┌───────────┴───────────┐
                    ▼                       ▼
        ┌───────────────────┐   ┌───────────────────────┐
        │   NetworkX Graph  │   │   ChromaDB + Embeddings│
        │  (KnowledgeGraph) │   │     (VectorStore)      │
        │                   │   │                        │
        │  Nodes + Edges    │   │  text → all-MiniLM-L6  │
        │  (relationships)  │   │  → 384-dim vectors     │
        └─────────┬─────────┘   └───────────┬────────────┘
                  │                         │
        ┌─────────▼─────────┐   ┌───────────▼────────────┐
        │  TRACK 1          │   │  TRACK 2               │
        │  Graph Traversal  │   │  RAG + LLM             │
        │  (SDLC commands)  │   │  (free-text questions) │
        │  No LLM. Fast.    │   │  OpenRouter API        │
        └───────────────────┘   └────────────────────────┘
```

**Two data stores run in parallel:**

| Store | Library | Purpose | Persistence |
|---|---|---|---|
| Knowledge Graph | NetworkX `DiGraph` | Nodes + directed edges (relationships) | In-memory |
| Vector Store | ChromaDB | Text embeddings for semantic search | In-memory |

Both are populated together during ingestion — every entity gets a node in NetworkX AND an embedding in ChromaDB.

---

## 2. Project Structure

```
sdlc_KG/
├── main.py                        # Entry point — builds KG and runs all queries
├── setup.py                       # Makes `from src.xxx import` work project-wide
├── requirements.txt               # Python dependencies
├── .env                           # API keys (OpenRouter)
│
├── src/
│   ├── core/
│   │   ├── kg.py                  # KnowledgeGraph class (NetworkX wrapper)
│   │   └── vectorStore.py         # VectorStore class (ChromaDB wrapper)
│   │
│   ├── data/
│   │   ├── mockData.py            # All mock data (pipelines, tables, KPIs, etc.)
│   │   └── dataIngestion.py       # Ingests mock data → NetworkX + ChromaDB
│   │
│   ├── queries/
│   │   ├── queryEngine.py         # Graph query functions (no LLM)
│   │   └── naturalLanguageQuery.py # RAG + LLM via OpenRouter
│   │
│   └── utils/
│       └── formatting.py          # Print helpers (headers, separators)
│
└── examples/
    ├── interactiveQuery.py        # ★ Main interactive CLI (use this)
    ├── inspectVectorDB.py         # Inspect ChromaDB embeddings at runtime
    ├── queryExamples.py           # Batch LLM query examples
    └── searchExamples.py          # Vector search examples
```

---

## 3. Data Model

### Entity Types (Graph Nodes)

| Entity | ID Prefix | Description |
|---|---|---|
| `Pipeline` | `pipeline_` | Databricks ETL job (has `layer`: bronze/silver/gold) |
| `Table` | `table_` | Databricks Unity Catalog table (has `layer`, `database`) |
| `Column` | `col_` | Table column (has `dataType`, `isPii`) |
| `ConfluencePage` | `conf_` | Documentation page |
| `JiraTicket` | `DATA-`, `RN-` | Work item |
| `Alert` | `alert_` | Monitoring alert config |
| `DataQualityRule` | `dq_` | Validation rule on a table/column |
| `Environment` | `env_` | Dev / Staging / Production |
| `PowerBIDashboard` | `pbi_` | Power BI report |
| `PowerBIKPI` | `kpi_` | KPI tile within a dashboard |
| `DataDictionaryEntry` | `dict_` | Business term linking all sources |

### Relationships (Graph Edges)

```
Pipeline ──[CONTAINS]──────────► Table
Pipeline ──[PRODUCES]──────────► Table          (output of this pipeline)
Pipeline ──[DOCUMENTED_IN]─────► ConfluencePage

Table ────[CONTAINS]───────────► Column

JiraTicket ──[TRACKS]──────────► Pipeline
JiraTicket ──[REFERENCES]──────► ConfluencePage
JiraTicket ──[MODIFIED]────────► Table          ← audit trail for schema changes

Alert ────[MONITORS]───────────► Pipeline / Table

DataQualityRule ──[VALIDATES]──► Table / Column

PowerBIDashboard ──[CONTAINS]──► PowerBIKPI
PowerBIDashboard ──[READS_FROM]► Table

PowerBIKPI ──[READS_FROM]──────► Table          ← pipeline dependency analysis
PowerBIKPI ──[READS_FROM]──────► Column         ← column impact analysis

DataDictionaryEntry ──[DEFINES]────────► Column
DataDictionaryEntry ──[MAPS_TO]────────► Column  (Silver/Bronze counterpart)
DataDictionaryEntry ──[REFERENCED_IN]──► ConfluencePage
DataDictionaryEntry ──[TRACKED_BY]─────► JiraTicket
DataDictionaryEntry ──[MEASURED_BY]────► PowerBIKPI
```

---

## 4. Query System — Two Tracks

### Track 1 — Graph Traversal (slash commands, no LLM)

Pure Python functions that walk the NetworkX graph following specific edge types. Deterministic, fast, always correct. Used by the SDLC impact commands.

**SDLC Query 1: Column impact analysis**
```
"Which dashboards break if column X changes?"

Column  ←─[READS_FROM]─── PowerBIKPI  ←─[CONTAINS]─── PowerBIDashboard
```

**SDLC Query 2: Pipeline dependency analysis**
```
"Which KPIs depend on pipeline X?"

Pipeline ──[PRODUCES]──► Table  ←─[READS_FROM]─── KPI  ←─[CONTAINS]─── Dashboard
```

**SDLC Query 3: Audit trail**
```
"Which Jira ticket modified table X?"

JiraTicket ──[MODIFIED]──► Table   (look backwards from table)
```

### Track 2 — RAG + LLM (free-text questions)

The LLM never queries the graph directly. It reads a pre-fetched text context.

```
User question
    │
    ├─ Step 1: ChromaDB semantic search
    │   Question → sentence-transformer → 384-dim vector
    │   Compare against all stored node embeddings
    │   Return top 8 most similar node IDs
    │
    ├─ Step 2: Context building (NetworkX)
    │   For each matched node:
    │     - Fetch all node properties
    │     - Fetch outgoing edges (what this node points to)
    │     - Fetch incoming edges (what depends on this node)
    │   Format as plain text
    │
    └─ Step 3: OpenRouter (gpt-4o-mini)
        [system prompt with schema description]
        + [context text from Step 2]
        + [user question]
        → Natural language answer
```

---

## 5. Reckitt Nutrition Domain

The Reckitt Nutrition data follows a standard **Medallion Architecture** (Bronze → Silver → Gold):

```
SAP S/4HANA          Bronze Layer           Silver Layer          Gold Layer
Nielsen IQ      ──►  (raw landing)   ──►   (cleansed)     ──►   (KPI-ready)
Salesforce CRM       Databricks             Databricks            Databricks
SAP MDM                                                               │
                                                                      ▼
                                                              Power BI Dashboards
                                                              (Executive, Sales,
                                                               Market Intelligence,
                                                               Data Quality)
```

**Brands covered:** Enfamil, Nutramigen, Enfalac, Mead Johnson

**Pipelines per layer:**

| Layer | Pipelines |
|---|---|
| Bronze | `pipeline_rn_bronze_sales`, `_product`, `_market`, `_consumer` |
| Silver | `pipeline_rn_silver_sales`, `_product`, `_market` |
| Gold | `pipeline_rn_gold_sales_summary`, `_market_share`, `_kpi_metrics` |

**Power BI Dashboards:**

| Dashboard ID | Description |
|---|---|
| `pbi_rn_executive` | C-suite KPIs: Revenue, Market Share, Volume Growth |
| `pbi_rn_sales_performance` | Revenue by Brand, NRM waterfall, promotional tracking |
| `pbi_rn_market_intelligence` | Nielsen market share, distribution, consumer penetration |
| `pbi_rn_data_quality` | Pipeline SLA, data quality scores |

**Key Jira tickets:**

| Ticket | Description |
|---|---|
| `RN-204` | Column rename in Silver → breaks Gold + Power BI (in progress) |
| `RN-206` | Power BI Executive Dashboard broken due to pipeline failure (critical bug) |
| `RN-203` | Gold KPI metrics table built for Power BI |

---

## 6. Setup & Running

### First-time setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install package (enables `from src.xxx import` in main.py)
pip install -e .

# 4. Set your OpenRouter API key in .env
#    OPENROUTER_API_KEY=sk-or-...
```

### Running

```bash
# Main pipeline — builds graph, runs all pre-defined queries
python main.py

# Interactive CLI — recommended for exploration
python examples/interactiveQuery.py

# Inspect vector DB embeddings
python examples/inspectVectorDB.py

# Batch LLM query examples
python examples/queryExamples.py
```

---

## 7. Scripts Reference

### `examples/interactiveQuery.py` — Interactive CLI

The main interface for exploring the knowledge graph.

**SDLC Impact commands (Track 1 — pure graph, no LLM):**

| Command | What it answers |
|---|---|
| `/sdlc` | Runs all 3 SDLC demo queries |
| `/impact <column_id>` | Which dashboards/KPIs break if this column changes? |
| `/depends <pipeline_id>` | Which KPIs depend on this pipeline? |
| `/whochanged <table_id>` | Which Jira tickets modified this table? |

**Feature search (vector search):**

| Command | What it does |
|---|---|
| `/find <feature>` | Semantic search for a feature |
| `/status <feature>` | Full status across pipelines, tables, tickets |
| `/list` | All nodes grouped by type |
| `/stats` | Node and edge counts |

**Free-text questions (Track 2 — LLM):**
Just type any question in plain English.

```
Your question: Which dashboards read from the Gold market share table?
Your question: What is the lineage of net revenue from Bronze to Power BI?
Your question: /impact col_rn_kpi_value
Your question: /whochanged rn_silver_sales
```

Partial names work for SDLC commands — `/impact kpi_value` finds `col_rn_kpi_value`.

---

### `examples/inspectVectorDB.py` — Vector DB Inspector

Lets you see the raw ChromaDB contents after ingestion.

Shows:
- Total documents and breakdown by entity type
- Each document's stored text and first 8 embedding dimensions
- Filtered view by entity type (e.g. only `PowerBIKPI`)
- Similarity search with cosine distance scores
- Full 384-dimensional embedding vector for any document

---

## 8. Key Files Reference

### `src/data/mockData.py`
All mock data as Python lists of dicts. Sections:
- `pipelines` — includes Reckitt Nutrition Bronze/Silver/Gold pipelines
- `tables` — includes `layer` and `database` fields for Reckitt tables
- `columns` — includes column-level lineage descriptions
- `confluencePages`, `jiraTickets` — includes `modifiedTables` field on Jira tickets
- `powerBIDashboards`, `powerBIKPIs` — Reckitt Nutrition Power BI
- `dataDictionary` — ontology entries linking all sources

### `src/data/dataIngestion.py`
One `ingest*` function per entity type. Each function:
1. Calls `kg.add_node()` to add to NetworkX
2. Calls `vectorDb.add()` to create and store the embedding
3. Calls `kg.add_edge()` to create relationships

`ingestAllData()` calls all functions in sequence.

### `src/core/kg.py`
Thin wrapper around `networkx.DiGraph`. Key methods:
- `addNode(id, type, **attrs)` — add a node
- `addEdge(from, relation, to)` — add a directed edge
- `queryEdges()` — get all `(source, target, relation)` tuples
- `neighbors(id)` — get successor node IDs

### `src/core/vectorStore.py`
Wrapper around ChromaDB. Key methods:
- `add(docId, text, metadata)` — embed text and store
- `search(query, k=5)` — semantic similarity search, returns node IDs + distances

Embedding model: `all-MiniLM-L6-v2` (384 dimensions, runs locally).
Storage: **in-memory** — rebuilt on every run.

### `src/queries/naturalLanguageQuery.py`
`NaturalLanguageQueryEngine` class connecting to OpenRouter.
- `query(kg, vectorDb, question)` — returns a plain English answer
- `queryWithReasoning(kg, vectorDb, question)` — returns `answer`, `reasoning`, `sources`
- `askQuestion(kg, vectorDb, question)` — convenience wrapper

Context builder fetches both **outgoing and incoming** graph edges for each matched node, giving the LLM full relationship context.

### `src/queries/queryEngine.py`
Pure graph query functions (no LLM). Key functions:
- `queryPipelineRelationships(kg)` — all pipeline edges
- `queryPiiColumns(kg)` — columns with `isPii=True`
- `queryJiraByPipeline(kg)` — Jira tickets grouped by pipeline
- `searchEntities(vectorDb, query, entityType, k)` — filtered semantic search
- `findFeature(kg, vectorDb, name)` — check if feature exists
- `runAllQueries(kg, vectorDb, data)` — runs everything (used by `main.py`)

---

## 9. Environment Variables

File: `.env` in project root.

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes (for LLM queries) | OpenRouter API key — get from openrouter.ai |
| `OPENROUTER_MODEL` | No | LLM model to use (default: `openai/gpt-4o-mini`) |

LLM queries (Track 2 and `queryExamples.py`) will fail without the API key. All graph traversal queries (Track 1, `/sdlc`, `/impact`, `/depends`, `/whochanged`) work without it.
