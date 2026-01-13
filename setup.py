"""
Setup script for Knowledge Graph package.
"""

from setuptools import setup, find_packages

setup(
    name="kg_local",
    version="1.0.0",
    description="Knowledge Graph for SDLC data management",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "networkx>=3.0",
    ],
    python_requires=">=3.8",
)
