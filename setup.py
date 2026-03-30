"""
Setup script for the SDLC Knowledge Graph package.

Installs the top-level packages: graph/, rag/, pipeline/, dictionary/,
profiling/, utils/, dps/, and scripts/.

Version history:
    1.0.0 — original src/ layout
    2.0.0 — restructured to medallion-architecture layout (pipeline/graph/rag/dps)
"""

from setuptools import setup, find_packages

setup(
    name="kg_local",
    version="2.0.0",
    description="Knowledge Graph for SDLC data management — Reckitt Nutrition Data Platform",

    # Discover all packages with __init__.py; exclude the old src/ and examples/
    # directories (now deleted) and the virtual environment
    packages=find_packages(exclude=["src", "src.*", "examples", "venv", "venv.*"]),

    # Core runtime dependencies — required for the KG + RAG pipeline
    install_requires=[
        "openai>=1.0.0",                   # OpenRouter API client (OpenAI-compatible)
        "rich>=13.0.0",                    # Color-coded CLI output (console, markup)
        "python-dotenv>=1.0.0",            # .env file loading for API keys
        "chromadb>=0.4.0",                 # Vector store for semantic search
        "sentence-transformers>=2.2.0",    # all-MiniLM-L6-v2 embedding model
        "networkx>=3.0",                   # Knowledge graph (DiGraph)
        "pymupdf>=1.23.0",                 # PDF text extraction for DPS evaluator
    ],

    # Optional dependency group — only needed for image-based (scanned) PDFs
    extras_require={
        "ocr": [
            "pytesseract>=0.3.10",   # Tesseract OCR Python bindings
            "Pillow>=10.0.0",        # Image processing (required by pytesseract)
        ],
    },

    python_requires=">=3.8",
)
