"""
SMART INTAKE - Historical RAG Engine
======================================
Retrieves similar past data engineering projects from a local SQLite store
and surfaces them as benchmark context for ROI/ROM/DPS estimation.

Flow:
  1. Seed historical project store on first run (sample completed projects)
  2. At Q6/Q11/Q24 triggers, find similar projects by domain + sources + volume
  3. Return benchmark stats (actual cost, dev weeks, ROI realised) to enrich LLM prompts
  4. Optionally query ChromaDB vectorstore for data asset similarity

Usage:
  from smart_intake.rag_engine import find_similar_projects, get_benchmark_stats
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
HISTORY_DB  = os.path.join(PROJECT_DIR, "pipeline.db")


# ─────────────────────────────────────────────
# SCHEMA + SEED DATA
# ─────────────────────────────────────────────

_SEED_PROJECTS = [
    {
        "project_id": "hist_001",
        "project_name": "Epic EHR Claims Analytics",
        "domain": "Healthcare",
        "sources": ["Epic EHR", "SQL Server"],
        "volume_band": "10–100 GB / day",
        "platform": "Azure Databricks",
        "compliance_flags": ["HIPAA"],
        "entity_count": 12,
        "dev_weeks_actual": 18,
        "infra_monthly_actual": 3800,
        "impl_cost_actual": 210000,
        "tco_3yr_actual": 510000,
        "annual_benefit_actual": 280000,
        "roi_pct_actual": 64.7,
        "fte_count": 6,
        "hourly_rate": 85,
        "hours_saved_pct": 40,
        "error_cost_saved": 45000,
        "license_saved": 18000,
        "dps_score": 74,
        "lessons_learned": "HIPAA masking added 3 weeks. Recommend starting data classification early."
    },
    {
        "project_id": "hist_002",
        "project_name": "SAP GL Finance Reporting",
        "domain": "Finance",
        "sources": ["SAP", "SQL Server"],
        "volume_band": "10–100 GB / day",
        "platform": "Snowflake Tasks",
        "compliance_flags": ["SOX"],
        "entity_count": 8,
        "dev_weeks_actual": 14,
        "infra_monthly_actual": 2600,
        "impl_cost_actual": 148000,
        "tco_3yr_actual": 390000,
        "annual_benefit_actual": 190000,
        "roi_pct_actual": 46.2,
        "fte_count": 4,
        "hourly_rate": 95,
        "hours_saved_pct": 35,
        "error_cost_saved": 32000,
        "license_saved": 24000,
        "dps_score": 68,
        "lessons_learned": "SOX audit trail required immutable log table. Add 2 weeks for audit infra."
    },
    {
        "project_id": "hist_003",
        "project_name": "Salesforce CRM 360 Dashboard",
        "domain": "Sales / CRM",
        "sources": ["Salesforce", "PostgreSQL"],
        "volume_band": "1–10 GB / day",
        "platform": "Azure Databricks",
        "compliance_flags": [],
        "entity_count": 6,
        "dev_weeks_actual": 8,
        "infra_monthly_actual": 1100,
        "impl_cost_actual": 72000,
        "tco_3yr_actual": 184000,
        "annual_benefit_actual": 130000,
        "roi_pct_actual": 111.9,
        "fte_count": 3,
        "hourly_rate": 75,
        "hours_saved_pct": 50,
        "error_cost_saved": 12000,
        "license_saved": 8000,
        "dps_score": 82,
        "lessons_learned": "Salesforce API rate limits caused initial delays. Use Bulk API from day 1."
    },
    {
        "project_id": "hist_004",
        "project_name": "Kafka IoT Streaming Pipeline",
        "domain": "Manufacturing / IoT",
        "sources": ["Kafka / Streaming", "MongoDB"],
        "volume_band": "> 1 TB / day",
        "platform": "Azure Databricks",
        "compliance_flags": [],
        "entity_count": 20,
        "dev_weeks_actual": 26,
        "infra_monthly_actual": 19500,
        "impl_cost_actual": 380000,
        "tco_3yr_actual": 1120000,
        "annual_benefit_actual": 520000,
        "roi_pct_actual": 39.3,
        "fte_count": 10,
        "hourly_rate": 90,
        "hours_saved_pct": 30,
        "error_cost_saved": 95000,
        "license_saved": 0,
        "dps_score": 61,
        "lessons_learned": "Streaming at scale needs separate infra sizing. Schema registry adds 2 weeks."
    },
    {
        "project_id": "hist_005",
        "project_name": "Pharma Clinical Trial Data Lake",
        "domain": "Life Sciences",
        "sources": ["Oracle", "Flat Files / CSV"],
        "volume_band": "1–10 GB / day",
        "platform": "Azure Databricks",
        "compliance_flags": ["GxP"],
        "entity_count": 15,
        "dev_weeks_actual": 24,
        "infra_monthly_actual": 2200,
        "impl_cost_actual": 295000,
        "tco_3yr_actual": 694000,
        "annual_benefit_actual": 310000,
        "roi_pct_actual": 34.1,
        "fte_count": 5,
        "hourly_rate": 100,
        "hours_saved_pct": 45,
        "error_cost_saved": 60000,
        "license_saved": 35000,
        "dps_score": 58,
        "lessons_learned": "21 CFR Part 11 validation docs took longer than dev. Budget validation effort separately."
    },
    {
        "project_id": "hist_006",
        "project_name": "Retail Inventory & Demand Forecasting",
        "domain": "Retail / E-Commerce",
        "sources": ["SQL Server", "Flat Files / CSV"],
        "volume_band": "1–10 GB / day",
        "platform": "Snowflake Tasks",
        "compliance_flags": [],
        "entity_count": 9,
        "dev_weeks_actual": 11,
        "infra_monthly_actual": 900,
        "impl_cost_actual": 88000,
        "tco_3yr_actual": 218000,
        "annual_benefit_actual": 175000,
        "roi_pct_actual": 140.8,
        "fte_count": 4,
        "hourly_rate": 70,
        "hours_saved_pct": 55,
        "error_cost_saved": 22000,
        "license_saved": 12000,
        "dps_score": 79,
        "lessons_learned": "Historical data backfill underestimated. Add 1–2 weeks for initial load."
    },
    {
        "project_id": "hist_007",
        "project_name": "Multi-Region GDPR Data Platform",
        "domain": "Financial Services",
        "sources": ["PostgreSQL", "REST API", "Kafka / Streaming"],
        "volume_band": "10–100 GB / day",
        "platform": "Azure Databricks",
        "compliance_flags": ["GDPR", "SOX"],
        "entity_count": 14,
        "dev_weeks_actual": 22,
        "infra_monthly_actual": 4200,
        "impl_cost_actual": 268000,
        "tco_3yr_actual": 638000,
        "annual_benefit_actual": 340000,
        "roi_pct_actual": 59.9,
        "fte_count": 7,
        "hourly_rate": 88,
        "hours_saved_pct": 38,
        "error_cost_saved": 55000,
        "license_saved": 28000,
        "dps_score": 65,
        "lessons_learned": "GDPR right-to-erasure logic required custom delete propagation across all layers."
    },
]


def _init_history_db() -> sqlite3.Connection:
    conn = sqlite3.connect(HISTORY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historical_projects (
            project_id TEXT PRIMARY KEY,
            project_name TEXT,
            domain TEXT,
            sources TEXT,
            volume_band TEXT,
            platform TEXT,
            compliance_flags TEXT,
            entity_count INTEGER,
            dev_weeks_actual REAL,
            infra_monthly_actual REAL,
            impl_cost_actual REAL,
            tco_3yr_actual REAL,
            annual_benefit_actual REAL,
            roi_pct_actual REAL,
            fte_count INTEGER,
            hourly_rate REAL,
            hours_saved_pct REAL,
            error_cost_saved REAL,
            license_saved REAL,
            dps_score REAL,
            lessons_learned TEXT
        )
    """)
    conn.commit()
    # Seed if empty
    count = conn.execute("SELECT COUNT(*) FROM historical_projects").fetchone()[0]
    if count == 0:
        for p in _SEED_PROJECTS:
            conn.execute("""
                INSERT OR IGNORE INTO historical_projects VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                p["project_id"], p["project_name"], p["domain"],
                json.dumps(p["sources"]), p["volume_band"], p["platform"],
                json.dumps(p["compliance_flags"]), p["entity_count"],
                p["dev_weeks_actual"], p["infra_monthly_actual"],
                p["impl_cost_actual"], p["tco_3yr_actual"],
                p["annual_benefit_actual"], p["roi_pct_actual"],
                p["fte_count"], p["hourly_rate"], p["hours_saved_pct"],
                p["error_cost_saved"], p["license_saved"],
                p["dps_score"], p["lessons_learned"]
            ))
        conn.commit()
    return conn


# ─────────────────────────────────────────────
# SIMILARITY SCORING
# ─────────────────────────────────────────────

def _score_similarity(project: Dict, answers: Dict) -> float:
    """
    Returns 0.0–1.0 similarity score between a historical project and current answers.
    Weighted: domain (40%) + sources overlap (30%) + volume band (20%) + compliance (10%)
    """
    score = 0.0

    # Domain match (40%)
    domain = answers.get("Q4", "")
    if domain and domain.lower() in project["domain"].lower():
        score += 0.40
    elif domain and any(w in project["domain"].lower() for w in domain.lower().split()):
        score += 0.20

    # Source overlap (30%)
    selected_sources = answers.get("Q6", [])
    if isinstance(selected_sources, str):
        selected_sources = [selected_sources]
    hist_sources = json.loads(project["sources"]) if isinstance(project["sources"], str) else project["sources"]
    if selected_sources and hist_sources:
        overlap = len(set(selected_sources) & set(hist_sources))
        score += 0.30 * min(overlap / max(len(selected_sources), 1), 1.0)

    # Volume band match (20%)
    volume = answers.get("Q7", "")
    if volume and volume == project["volume_band"]:
        score += 0.20
    elif volume:
        # Adjacent band partial credit
        bands = ["< 1 GB / day", "1–10 GB / day", "10–100 GB / day",
                 "100 GB – 1 TB / day", "> 1 TB / day"]
        try:
            vi = bands.index(volume)
            hi = bands.index(project["volume_band"])
            if abs(vi - hi) == 1:
                score += 0.10
        except ValueError:
            pass

    # Compliance overlap (10%)
    flags = [f.value if hasattr(f, 'value') else f for f in answers.get("_compliance_flags", [])]
    hist_flags = json.loads(project["compliance_flags"]) if isinstance(project["compliance_flags"], str) else project["compliance_flags"]
    if flags and hist_flags:
        overlap = len(set(flags) & set(hist_flags))
        score += 0.10 * min(overlap / max(len(flags), 1), 1.0)
    elif not flags and not hist_flags:
        score += 0.10  # both have no compliance — still a match signal

    return round(score, 3)


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def find_similar_projects(answers: Dict[str, Any], top_k: int = 3) -> List[Dict]:
    """
    Returns top_k historical projects most similar to the current intake answers.
    Each result includes all project fields + similarity_score.
    """
    try:
        conn = _init_history_db()
        rows = conn.execute("SELECT * FROM historical_projects").fetchall()
        cols = [
            "project_id", "project_name", "domain", "sources", "volume_band",
            "platform", "compliance_flags", "entity_count", "dev_weeks_actual",
            "infra_monthly_actual", "impl_cost_actual", "tco_3yr_actual",
            "annual_benefit_actual", "roi_pct_actual", "fte_count", "hourly_rate",
            "hours_saved_pct", "error_cost_saved", "license_saved", "dps_score",
            "lessons_learned"
        ]
        projects = []
        for row in rows:
            p = dict(zip(cols, row))
            p["sources"] = json.loads(p["sources"]) if isinstance(p["sources"], str) else p["sources"]
            p["compliance_flags"] = json.loads(p["compliance_flags"]) if isinstance(p["compliance_flags"], str) else p["compliance_flags"]
            p["similarity_score"] = _score_similarity(p, answers)
            projects.append(p)

        projects.sort(key=lambda x: x["similarity_score"], reverse=True)
        return [p for p in projects[:top_k] if p["similarity_score"] > 0.1]
    except Exception as e:
        return []


def get_benchmark_stats(answers: Dict[str, Any]) -> Optional[Dict]:
    """
    Returns aggregated benchmark stats from similar historical projects.
    Used to enrich auto-fill estimates and LLM prompts.

    Returns:
        {
          avg_dev_weeks, avg_infra_monthly, avg_impl_cost, avg_tco_3yr,
          avg_roi_pct, avg_dps_score, similar_count,
          lessons: [str], project_names: [str]
        }
    """
    similar = find_similar_projects(answers, top_k=3)
    if not similar:
        return None

    def _avg(field):
        vals = [p[field] for p in similar if p.get(field) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    return {
        "similar_count": len(similar),
        "project_names": [p["project_name"] for p in similar],
        "similarity_scores": [p["similarity_score"] for p in similar],
        "avg_dev_weeks":       _avg("dev_weeks_actual"),
        "avg_infra_monthly":   _avg("infra_monthly_actual"),
        "avg_impl_cost":       _avg("impl_cost_actual"),
        "avg_tco_3yr":         _avg("tco_3yr_actual"),
        "avg_annual_benefit":  _avg("annual_benefit_actual"),
        "avg_roi_pct":         _avg("roi_pct_actual"),
        "avg_dps_score":       _avg("dps_score"),
        "lessons": [p["lessons_learned"] for p in similar if p.get("lessons_learned")],
        "raw": similar,
    }


def format_benchmark_context(benchmark: Optional[Dict]) -> str:
    """
    Formats benchmark stats as a string block to inject into LLM prompts.
    Returns empty string if no benchmark available.
    """
    if not benchmark:
        return ""

    lines = [
        f"\n--- HISTORICAL BENCHMARK ({benchmark['similar_count']} similar projects) ---",
        f"Projects: {', '.join(benchmark['project_names'])}",
        f"Avg dev effort     : {benchmark['avg_dev_weeks']} weeks",
        f"Avg monthly infra  : ${benchmark['avg_infra_monthly']:,.0f}" if benchmark['avg_infra_monthly'] else "",
        f"Avg impl cost      : ${benchmark['avg_impl_cost']:,.0f}" if benchmark['avg_impl_cost'] else "",
        f"Avg 3-yr TCO       : ${benchmark['avg_tco_3yr']:,.0f}" if benchmark['avg_tco_3yr'] else "",
        f"Avg annual benefit : ${benchmark['avg_annual_benefit']:,.0f}" if benchmark['avg_annual_benefit'] else "",
        f"Avg realised ROI   : {benchmark['avg_roi_pct']}%" if benchmark['avg_roi_pct'] else "",
        f"Avg DPS score      : {benchmark['avg_dps_score']}/100" if benchmark['avg_dps_score'] else "",
    ]
    if benchmark.get("lessons"):
        lines.append("Lessons learned:")
        for lesson in benchmark["lessons"]:
            lines.append(f"  - {lesson}")
    lines.append("--- END BENCHMARK ---\n")
    return "\n".join(l for l in lines if l)
