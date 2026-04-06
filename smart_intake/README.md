# SMART INTAKE — Design & Workflow

## Overview

SMART INTAKE is an intelligent, progressive-disclosure questionnaire that collects project context from business stakeholders and automatically generates:
- **ROI** (Return on Investment) estimate
- **ROM** (Rough Order of Magnitude) cost estimate
- **DPS** (Data Pipeline Score) — readiness and risk score (0–100)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SMART INTAKE SYSTEM                          │
│                                                                     │
│   ┌─────────────┐     ┌──────────────┐     ┌────────────────────┐  │
│   │   CLI / UI  │────▶│  REST API    │────▶│  Question Engine   │  │
│   │             │     │  (api.py)    │     │  (questions.py)    │  │
│   └─────────────┘     └──────┬───────┘     └────────────────────┘  │
│                              │                                      │
│              ┌───────────────┼───────────────┐                     │
│              ▼               ▼               ▼                     │
│   ┌──────────────┐  ┌───────────────┐  ┌────────────────┐         │
│   │  Conditional │  │ LLM Follow-up │  │  Historical    │         │
│   │  Engine      │  │ Generator     │  │  RAG Engine    │         │
│   │ (conditional │  │ (llm_followup │  │ (rag_engine.py)│         │
│   │  _engine.py) │  │     .py)      │  └───────┬────────┘         │
│   └──────┬───────┘  └──────┬────────┘          │                  │
│          │                 │                   │                  │
│          ▼                 ▼                   ▼                  │
│   ┌──────────────────────────────────────────────────────┐        │
│   │              ROI / ROM / DPS Calculator              │        │
│   │    (conditional_engine.auto_fill + dps_engine.py)    │        │
│   └──────────────────────────┬───────────────────────────┘        │
│                              │                                     │
│                              ▼                                     │
│                   ┌─────────────────────┐                         │
│                   │   Session Store     │                         │
│                   │  (cosmos_store.py)  │                         │
│                   │  SQLite / CosmosDB  │                         │
│                   └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Session Flow

```
User starts session
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  PHASE 1 — Project Context  (Q1–Q5)                           │
│                                                               │
│  Q1: Project name                                             │
│  Q2: Business objective                                       │
│  Q3: Operating regions ──────────────────────────────────┐   │
│  Q4: Business domain  ────────────────────────────────┐  │   │
│  Q5: Executive sponsor                                │  │   │
└───────────────────────────────────────────────────────┼──┼───┘
        │                                               │  │
        │    Compliance flags triggered automatically   │  │
        │    ┌──────────────────────────────────────────┘  │
        │    │  Q4=Healthcare  → HIPAA block unlocked       │
        │    │  Q4=Finance     → SOX block unlocked         │
        │    │  Q4=Life Sci    → GxP block unlocked         │
        │    │  Q3=EU/UK       → GDPR block unlocked ◄──────┘
        │    └──────────────────────────┐
        ▼                               ▼
┌───────────────────────┐    ┌──────────────────────────────────┐
│  PHASE 2 — Data Reqs  │    │  PHASE 3 — Security/Compliance   │
│  (Q6–Q11)             │    │  (Q12–Q16, conditional)          │
│                       │    │                                  │
│  Q6:  Source systems  │    │  Q12: PII handling               │
│  Q7:  Data volume     │    │  GDPR: consent, erasure, DPO     │
│  Q8:  Go-live target  │    │  SOX:  audit trail, controls     │
│  Q9:  Entity count    │    │  GxP:  21 CFR Part 11 validation │
│  Q10: DQ issues  ─────┼──► │  HIPAA: PHI safeguards           │
│  Q11: KPI description │    └──────────────────────────────────┘
│       (LLM trigger)   │
└───────┬───────────────┘
        │
        │  Q11 answer → LLM generates KPI sub-questions
        │  (grain, calculation logic, benchmarks, SLA)
        ▼
┌─────────────────────────────────────┐
│  PHASE 4 — Visualization/Technical  │
│  (Q17–Q23)                          │
│                                     │
│  Q17: BI tool (Power BI / Tableau)  │
│  Q18: Refresh frequency             │
│  Q19: Report types                  │
│  Q20: Audience                      │
│  Q21: Platform (Databricks / Snow)  │
│  Q22: Latency SLA                   │
│  Q23: Archival policy               │
└───────────────────────────────────┬─┘
                                    │
        ┌───────────────────────────┘
        ▼
┌───────────────────────────────────────────────────────────────┐
│  PHASE 5 — ROI Assessment  (Q24–Q33)                          │
│                                                               │
│  Q24: Manual process description ──────► LLM generates        │
│                                         ROI sub-questions:    │
│                                         - bottleneck steps    │
│  Q25: FTE count                         - error frequency     │
│  Q26: Hourly rate                       - downstream impact   │
│  Q27: Hours/week saved                  - seasonality         │
│  Q28: % time saved                                            │
│  Q29: Revenue opportunity                                     │
│  Q30: Annual error cost                                       │
│  Q31: Error reduction %                                       │
│  Q32: Compliance fine risk                                    │
│  Q33: License consolidation savings                           │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  PHASE 6 — ROM Estimation  (Q34–Q41, mostly auto-filled)      │
│                                                               │
│  Q34: Monthly infra cost  ◄── blended (formula + historical)  │
│  Q35: Dev effort (weeks)  ◄── blended (formula + historical)  │
│  Q36: Dev hourly rate                                         │
│  Q37: Licensing cost                                          │
│  Q38: Annual support %                                        │
│  Q39: Total impl cost     ◄── auto-calculated                 │
│  Q40: 3-year TCO          ◄── auto-calculated                 │
│  Q41: Net 3-yr ROI %      ◄── auto-calculated                 │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  SESSION COMPLETE — Outputs                                   │
│                                                               │
│  ┌─────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │  ROI Summary    │  │  ROM Summary   │  │  DPS Report   │  │
│  │                 │  │                │  │               │  │
│  │  Labor savings  │  │  Dev weeks     │  │  Score 0–100  │  │
│  │  Error savings  │  │  Infra cost    │  │  Risk flags   │  │
│  │  License saves  │  │  3-yr TCO      │  │  Recs list    │  │
│  │  Revenue uplift │  │  Net ROI %     │  │  vs. peers    │  │
│  └─────────────────┘  └────────────────┘  └───────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Similar Historical Projects (RAG Engine)               │  │
│  │                                                         │  │
│  │  Top 3 past projects ranked by similarity score         │  │
│  │  Shows: actual dev weeks, impl cost, realised ROI       │  │
│  │  Shows: lessons learned from each project               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  Export to JSON?  →  intake_<session_id>.json                 │
└───────────────────────────────────────────────────────────────┘
```

---

## Conditional Logic Engine

```
Answer submitted
      │
      ▼
conditional_engine.get_visible_questions(answers)
      │
      ├── Every question evaluated: condition met? → show
      │
      ├── GDPR  triggered if: Q3 contains EU or UK
      ├── SOX   triggered if: Q4 contains Finance
      ├── GxP   triggered if: Q4 contains Life Sciences / Pharma
      └── HIPAA triggered if: Q4 contains Healthcare / Clinical

      ▼
auto_fill_values(answers)
      │
      ├── Q34 infra cost:  INFRA_COST_MATRIX[volume][platform]
      │                    blended 60% formula + 40% historical avg
      │
      ├── Q35 dev weeks:   base(entities × 0.5) + DQ overhead
      │                    + compliance overhead (GDPR+2, SOX+3, GxP+5, HIPAA+2)
      │                    blended 50% formula + 50% historical avg
      │
      ├── Q39 impl cost:   (dev_weeks × 40hr × rate) + (infra × 3mo) + licensing
      │                    blended 60% formula + 40% historical avg
      │
      ├── Q40 3-yr TCO:    impl_cost + (annual_infra + annual_support) × 3
      │
      └── Q41 Net ROI %:   ((3yr_benefit − TCO) / TCO) × 100
```

---

## LLM Follow-up Trigger Points

```
Q3  → Regions answered
        └── Non-standard regions (APAC, LATAM) → Claude generates
            region-specific compliance questions (PDPA, LGPD, CCPA)

Q11 → KPI description answered
        └── Claude generates 3–5 KPI clarification questions:
            calculation logic, grain, lookback period, benchmarks

Q24 → Manual process described
        └── Claude generates 4–6 ROI quantification questions:
            bottleneck steps, error frequency, downstream impact

Phase 3 complete
        └── Claude generates domain-specific governance questions:
            data ownership, retention policy, access control, masking

All prompts enriched with: historical benchmark context from rag_engine.py
```

---

## Historical RAG Engine (rag_engine.py)

```
At Q6 / Q11 / Q24 / session end:
        │
        ▼
find_similar_projects(answers, top_k=3)
        │
        ├── Similarity scoring (0.0–1.0):
        │     Domain match          40%
        │     Source system overlap 30%
        │     Volume band match     20%
        │     Compliance overlap    10%
        │
        ▼
get_benchmark_stats(answers)
        │
        ├── avg_dev_weeks
        ├── avg_infra_monthly
        ├── avg_impl_cost
        ├── avg_tco_3yr
        ├── avg_roi_pct
        ├── avg_dps_score
        └── lessons learned (surfaced to user)

        ▼
format_benchmark_context() → injected into every Claude API prompt
```

---

## Data Pipeline Score (DPS) — dps_engine.py

```
calculate_dps(answers) → score 0–100

Dimension            Max   Signals
─────────────────────────────────────────────────────────────────
Data Readiness        25   Source types, known DQ issues, volume
Complexity            25   Entity count, # sources, streaming, SLA
Compliance Burden     20   Active flags (GxP=−7, SOX=−5, others=−4)
ROI Confidence        15   Phase 5 fields answered
Stakeholder Clarity   15   Sponsor, objective, KPIs, deadline
─────────────────────────────────────────────────────────────────
TOTAL                100

Score Bands:
  90–100  Exceptional  — proceed to architecture & build
  75–89   Good         — minor gaps, low delivery risk
  60–74   Moderate     — address flagged gaps before build
  40–59   Needs Work   — significant unknowns, scope creep risk
  0–39    High Risk    — run a discovery sprint first
```

---

## File Map

```
smart_intake/
├── models.py              Data contracts (Question, IntakeSession, ROISummary, ROMSummary)
├── questions.py           Static question bank Q1–Q41 (single source of truth)
├── conditional_engine.py  Visibility rules, compliance detection, auto-fill + benchmark blending
├── llm_followup.py        Claude API prompts + DynamicQuestion builder + benchmark injection
├── rag_engine.py          Historical project similarity search + benchmark stats
├── dps_engine.py          Data Pipeline Score (5-dimension scoring, risk flags, recs)
├── cosmos_store.py        SQLite (dev) / Azure Cosmos DB (prod) session persistence
├── api.py                 FastAPI REST endpoints (UI team contract)
├── intake_session.py      Interactive CLI session runner
└── README.md              This file
```

---

## Running the System

```bash
# Interactive CLI (primary)
python3 -m smart_intake.intake_session

# REST API server (for UI integration)
uvicorn smart_intake.api:app --reload --port 8000

# CLI commands during a session
'status'   → show phase progress + compliance flags
'summary'  → show ROI/ROM + DPS + historical matches
'back'     → re-answer previous question
'skip'     → skip optional question
'quit'     → save session and exit
```

---

## Environment Variables

| Variable           | Default            | Purpose                          |
|--------------------|--------------------|----------------------------------|
| `ANTHROPIC_API_KEY`| (none)             | Enables LLM follow-up questions  |
| `COSMOS_ENDPOINT`  | (none)             | Azure Cosmos DB URL              |
| `COSMOS_KEY`       | (none)             | Azure Cosmos DB key              |
| `COSMOS_DATABASE`  | `smart_intake_db`  | Cosmos DB database name          |
| `COSMOS_CONTAINER` | `intake_sessions`  | Cosmos DB container name         |

Without `COSMOS_ENDPOINT`, the system falls back to local SQLite (`pipeline.db`).
Without `ANTHROPIC_API_KEY`, LLM follow-ups are silently skipped.
