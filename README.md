# Knowledge Graph - SDLC Data Management System

A Python-based Knowledge Graph system for managing and querying Software Development Lifecycle (SDLC) data, including pipelines, datasets, data quality rules, Jira tickets, and Confluence documentation.

## Features

- **Graph-based Data Model**: Uses NetworkX for representing entities and relationships
- **Semantic Search**: Vector-based search using ChromaDB and sentence transformers
- **Natural Language Queries**: Query the knowledge graph using plain English with Azure OpenAI
- **Rich Entity Types**: Support for pipelines, datasets, tables, columns, data quality rules, transformations, Jira tickets, Confluence pages, and alerts
- **Flexible Query Engine**: Multiple query methods for different use cases

## Project Structure

```
kg_local/
├── src/
│   ├── core/               # Core components
│   │   ├── kg.py          # Knowledge Graph implementation
│   │   └── vectorStore.py # Vector database for semantic search
│   ├── data/              # Data management
│   │   ├── dataIngestion.py  # Data ingestion functions
│   │   └── mockData.py       # Sample data
│   └── queries/           # Query engines
│       ├── queryEngine.py         # Graph query functions
│       └── naturalLanguageQuery.py # AI-powered queries
├── examples/              # Example scripts
│   ├── queryExamples.py      # Natural language query examples
│   ├── searchExamples.py     # Vector search examples
│   ├── testQuery.py          # Quick test script
│   └── interactiveQuery.py   # Interactive query interface
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
├── setup.py             # Package setup
└── .env                 # Environment variables (Azure OpenAI config)
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/as-mac-1024/Desktop/kg_local
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

5. **Configure Azure OpenAI (for natural language queries):**

   Edit the `.env` file with your Azure OpenAI credentials:
   ```bash
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_DEPLOYMENT=gpt-4.1
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   ```

## Usage

### Running the Main Application

The main application creates a knowledge graph, ingests data, and runs various queries:

```bash
source venv/bin/activate
python main.py
```

This will:
- Initialize the knowledge graph and vector store
- Ingest all sample data
- Run predefined queries showing:
  - Pipeline relationships
  - PII columns
  - Data quality rules by severity
  - Tables by quality score
  - Jira work status
  - Critical alerts
  - Vector search results
  - Graph statistics

### Example Scripts

#### 1. Natural Language Queries

```bash
python examples/queryExamples.py
```

Ask questions in plain English:
- "What Jira tickets are related to data quality?"
- "Which pipelines process patient consent data?"
- "Show me all columns that contain PII data"

#### 2. Vector Search Examples

```bash
python examples/searchExamples.py
```

Demonstrates semantic search capabilities:
- Find Jira tickets by topic
- Find pipelines by functionality
- Find datasets by content
- Search across all entities

#### 3. Quick Test

```bash
python examples/testQuery.py
```

Quick test of natural language queries with ID tracking.

#### 4. Interactive Query Interface

```bash
python examples/interactiveQuery.py
```

Interactive command-line interface for querying the knowledge graph.

## Programming with the Knowledge Graph

### Basic Usage

```python
from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore
from src.data.dataIngestion import ingestAllData
from src.data.mockData import *

# Initialize
kg = KnowledgeGraph()
vectorDb = VectorStore()

# Prepare data
data = {
    'pipelines': pipelines,
    'datasets': datasets,
    'tables': tables,
    'columns': columns,
    'dataQualityRules': dataQualityRules,
    'transformations': transformations,
    'confluencePages': confluencePages,
    'jiraTickets': jiraTickets,
    'alerts': alerts
}

# Ingest data
ingestAllData(kg, vectorDb, data)
```

### Natural Language Queries

```python
from src.queries.naturalLanguageQuery import askQuestion

# Ask questions in plain English
answer = askQuestion(kg, vectorDb, "What are the critical data quality rules?")
print(answer)
```

### Vector Search

```python
from src.queries.queryEngine import searchEntities

# Search for entities by semantic similarity
results = searchEntities(vectorDb, "patient consent GDPR", entityType="Pipeline", k=5)

for docId, distance in results:
    print(f"Found: {docId} (similarity: {1-distance:.2f})")
```

### Graph Queries

```python
from src.queries.queryEngine import (
    queryPipelineRelationships,
    queryPiiColumns,
    queryDataQualityRulesBySeverity
)

# Query pipeline relationships
queryPipelineRelationships(kg)

# Find PII columns
queryPiiColumns(kg)

# Get data quality rules by severity
queryDataQualityRulesBySeverity(kg)
```

### Adding Custom Data

```python
# Add a new pipeline
kg.addNode(
    "pipeline_new",
    "Pipeline",
    name="New Data Pipeline",
    owner="data_team",
    schedule="hourly"
)

# Add to vector store for search
vectorDb.add(
    "pipeline_new",
    "New Data Pipeline - Processes real-time sensor data",
    {"type": "Pipeline", "tags": "real-time,iot", "owner": "data_team"}
)

# Create relationships
kg.addEdge("pipeline_new", "PRODUCES", "dataset_sensors")
```

## API Reference

### KnowledgeGraph Class

```python
class KnowledgeGraph:
    def addNode(nodeId, nodeType, **attrs)  # Add a node to the graph
    def addEdge(fromNode, relation, toNode)  # Add a directed edge
    def queryEdges()  # Get all edges with relationships
    def neighbors(nodeId)  # Get successor nodes
```

### VectorStore Class

```python
class VectorStore:
    def add(docId, text, metadata)  # Add document to vector store
    def search(query, k=5)  # Semantic search for similar documents
```

### Query Functions

```python
# Natural language queries
askQuestion(kg, vectorDb, question)  # Simple Q&A
queryEngine.query(kg, vectorDb, question)  # Detailed query
queryEngine.queryWithReasoning(kg, vectorDb, question)  # With reasoning

# Vector search
searchEntities(vectorDb, query, entityType=None, k=5)
queryRelationshipsBySearch(kg, vectorDb, query, entityType=None, k=5)

# Graph queries
queryPipelineRelationships(kg, limit=10)
queryPiiColumns(kg)
queryDataQualityRulesBySeverity(kg)
queryTablesByQualityScore(kg, topN=5)
queryGraphStatistics(kg)
```

## Supported Entity Types

- **Pipeline**: Data processing pipelines
- **Dataset**: Collections of tables
- **Table**: Database tables
- **Column**: Table columns
- **DataQualityRule**: Data validation rules
- **Transformation**: Data transformations
- **ConfluencePage**: Documentation pages
- **JiraTicket**: Issue tracking tickets
- **Alert**: Monitoring alerts

## Naming Conventions

The project uses **camelCase** naming convention throughout:
- Variables: `vectorDb`, `nodeId`, `dataQualityRules`
- Functions: `addNode()`, `queryEdges()`, `searchEntities()`
- Classes: `KnowledgeGraph`, `VectorStore`, `NaturalLanguageQueryEngine`

Legacy snake_case methods are maintained for backward compatibility.

## Dependencies

- `networkx>=3.0` - Graph structure
- `chromadb>=0.4.0` - Vector database
- `sentence-transformers>=2.2.0` - Text embeddings
- `openai>=1.0.0` - Azure OpenAI integration
- `python-dotenv>=1.0.0` - Environment configuration

## Troubleshooting

### Import Errors

If you encounter `ModuleNotFoundError: No module named 'src'`, make sure you've installed the package:

```bash
pip install -e .
```

### Azure OpenAI Errors

If natural language queries fail, verify your `.env` file has the correct Azure OpenAI credentials.

### Virtual Environment

Always activate the virtual environment before running scripts:

```bash
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

## Contributing

When adding new features:

1. Follow the camelCase naming convention
2. Add docstrings to all functions and classes
3. Update the relevant `__init__.py` files
4. Add examples to the `examples/` directory
5. Update this README

## License

This project is for educational and demonstration purposes.

## Contact

For questions or issues, please refer to the project documentation or create an issue in the repository.
