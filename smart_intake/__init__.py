"""
SMART INTAKE Package
====================
Entry point for the Smart Intake system.

Modules:
  models            → Data classes & enums (DE↔UI contract)
  questions         → Static Q1-Q41 question bank
  conditional_engine → Visibility rules, compliance detection, auto-fill, validation
  llm_followup      → LLM-powered follow-up question generation
  cosmos_store      → Cosmos DB / SQLite persistence
  api               → FastAPI REST endpoints (consumed by UI team)
"""

__version__ = "1.0.0"
