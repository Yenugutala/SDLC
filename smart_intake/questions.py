"""
SMART INTAKE - Static Question Bank (Q1–Q41)
=============================================
Complete question catalog for all 6 phases.
This is the SINGLE SOURCE OF TRUTH consumed by:
  - UI team (via /api/questions endpoint)
  - DE conditional logic engine
  - LLM follow-up generator
  - Cosmos DB schema validator

Phases:
  Phase 1  : Project Context         Q1–Q5
  Phase 2  : Data Requirements       Q6–Q11
  Phase 3  : Security & Compliance   Q12–Q16
  Phase 4  : Visualization/Technical Q17–Q23
  Phase 5  : ROI                     Q24–Q33
  Phase 6  : ROM (Rough Order of Magnitude) Q34–Q41

Conditional Triggers:
  Q3  (Region)  → EU/UK triggers GDPR block (Q12a-Q12c)
  Q4  (Domain)  → Finance triggers SOX (Q13a-Q13b)
                  Life Science triggers GxP (Q14a-Q14c)
                  Healthcare triggers HIPAA (Q15a)
  Q6  (Source)  → auto-fills source catalog metadata in Q7-Q8
  Q24 (Manual)  → LLM generates context-aware sub-questions
"""

from smart_intake.models import (
    Question, QuestionType, Phase,
    ValidationRule, ConditionalLogic, AutoFill
)

# ═══════════════════════════════════════════════════════════════
# PHASE 1 — Project Context  (Q1–Q5)
# ═══════════════════════════════════════════════════════════════

PHASE_1_QUESTIONS: list[Question] = [

    Question(
        id="Q1",
        phase=Phase.P1_PROJECT_CONTEXT,
        category="Project Context",
        order=1,
        text="What is the name of the project or initiative?",
        help_text="Use a short, memorable name. This will be used across all artifacts.",
        type=QuestionType.TEXT,
        validation=ValidationRule(required=True, min_length=3, max_length=100),
        tags=["project_name", "identifier"]
    ),

    Question(
        id="Q2",
        phase=Phase.P1_PROJECT_CONTEXT,
        category="Project Context",
        order=2,
        text="Who is the primary business owner / sponsor of this project?",
        help_text="The person accountable for scope, budget, and sign-off.",
        type=QuestionType.TEXT,
        validation=ValidationRule(required=True),
        tags=["stakeholder", "owner"]
    ),

    Question(
        id="Q3",
        phase=Phase.P1_PROJECT_CONTEXT,
        category="Project Context",
        order=3,
        text="In which geographic region(s) will this solution operate?",
        help_text="Select all regions where data will be processed or stored. This drives compliance requirements.",
        type=QuestionType.MULTI,
        options=["North America", "EU", "UK", "APAC", "LATAM", "Middle East", "Global"],
        validation=ValidationRule(required=True),
        tags=["region", "compliance", "gdpr_trigger"],
        is_llm_followup_trigger=True
    ),

    Question(
        id="Q4",
        phase=Phase.P1_PROJECT_CONTEXT,
        category="Project Context",
        order=4,
        text="What is the primary business domain of this project?",
        help_text="This determines which compliance frameworks (SOX, GxP, HIPAA) are auto-applied.",
        type=QuestionType.SINGLE,
        options=[
            "Healthcare / Clinical",
            "Life Sciences / Pharma",
            "Finance / Accounting",
            "HR / People Analytics",
            "Supply Chain / Logistics",
            "Marketing / CRM",
            "Operations / Manufacturing",
            "IT / Infrastructure",
            "Other"
        ],
        validation=ValidationRule(required=True),
        tags=["domain", "sox_trigger", "gxp_trigger", "hipaa_trigger"]
    ),

    Question(
        id="Q5",
        phase=Phase.P1_PROJECT_CONTEXT,
        category="Project Context",
        order=5,
        text="What is the target go-live date for the first deliverable?",
        help_text="Used to back-calculate ROM sprint planning.",
        type=QuestionType.DATE,
        validation=ValidationRule(required=True),
        tags=["timeline", "schedule"]
    ),
]


# ═══════════════════════════════════════════════════════════════
# PHASE 2 — Data Requirements  (Q6–Q11)
# ═══════════════════════════════════════════════════════════════

PHASE_2_QUESTIONS: list[Question] = [

    Question(
        id="Q6",
        phase=Phase.P2_DATA_REQUIREMENTS,
        category="Data Requirements",
        order=6,
        text="What are the primary data source systems?",
        help_text="Select all sources. Your selection auto-fills known schema metadata in Q7 and Q8.",
        type=QuestionType.MULTI,
        options=[
            "Epic EHR", "Cerner", "Salesforce", "SAP", "Workday",
            "Oracle EBS", "Snowflake", "Azure SQL", "AWS S3",
            "REST API", "Flat Files (CSV/Excel)", "Kafka / Streaming",
            "On-Premise DB (SQL Server / Oracle)", "Other"
        ],
        validation=ValidationRule(required=True),
        auto_fill=AutoFill(source_type="catalog", source_ref="source_catalog_metadata"),
        tags=["source_system", "catalog_trigger"]
    ),

    Question(
        id="Q7",
        phase=Phase.P2_DATA_REQUIREMENTS,
        category="Data Requirements",
        order=7,
        text="What is the approximate total data volume?",
        help_text="Estimated rows per day or GB — used for infrastructure sizing (ROM Q34).",
        type=QuestionType.SINGLE,
        options=[
            "< 1 GB / day",
            "1–10 GB / day",
            "10–100 GB / day",
            "100 GB – 1 TB / day",
            "> 1 TB / day",
            "Unknown"
        ],
        validation=ValidationRule(required=True),
        tags=["volume", "infrastructure_sizing"]
    ),

    Question(
        id="Q8",
        phase=Phase.P2_DATA_REQUIREMENTS,
        category="Data Requirements",
        order=8,
        text="What is the required data refresh frequency?",
        help_text="Determines pipeline scheduling and near-real-time architecture needs.",
        type=QuestionType.SINGLE,
        options=[
            "Real-time (< 1 min)",
            "Near real-time (1–15 min)",
            "Hourly",
            "Daily (batch)",
            "Weekly",
            "On-demand / ad hoc"
        ],
        validation=ValidationRule(required=True),
        tags=["latency", "pipeline_schedule"]
    ),

    Question(
        id="Q9",
        phase=Phase.P2_DATA_REQUIREMENTS,
        category="Data Requirements",
        order=9,
        text="How many distinct data entities / tables are in scope?",
        help_text="A rough count. Example: patients, visits, orders, products = 4 entities.",
        type=QuestionType.NUMBER,
        validation=ValidationRule(required=True, min_value=1, max_value=10000),
        tags=["scope", "complexity"]
    ),

    Question(
        id="Q10",
        phase=Phase.P2_DATA_REQUIREMENTS,
        category="Data Requirements",
        order=10,
        text="Are there existing data quality issues that must be addressed?",
        help_text="Check all that apply. This shapes the Silver layer transformation logic.",
        type=QuestionType.MULTI,
        options=[
            "Duplicate records",
            "Missing / null values",
            "Inconsistent formats (dates, codes)",
            "Referential integrity violations",
            "Stale / outdated records",
            "No known issues",
            "Unknown"
        ],
        validation=ValidationRule(required=True),
        tags=["data_quality", "silver_layer"]
    ),

    Question(
        id="Q11",
        phase=Phase.P2_DATA_REQUIREMENTS,
        category="Data Requirements",
        order=11,
        text="Are there specific KPIs or metrics the Gold layer must produce?",
        help_text="List the top 3–5 business metrics. Example: readmission rate, claim denial rate.",
        type=QuestionType.TEXTAREA,
        validation=ValidationRule(required=False, max_length=1000),
        tags=["kpi", "gold_layer", "business_metric"],
        is_llm_followup_trigger=True
    ),
]


# ═══════════════════════════════════════════════════════════════
# PHASE 3 — Security & Compliance  (Q12–Q16)
# Base questions always shown; sub-questions shown conditionally
# ═══════════════════════════════════════════════════════════════

PHASE_3_QUESTIONS: list[Question] = [

    # ── GDPR block (shown when Q3 includes EU or UK) ──────────
    Question(
        id="Q12a",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="GDPR Compliance",
        order=12,
        text="Does this project process Personal Identifiable Information (PII) of EU/UK residents?",
        help_text="Includes names, emails, IP addresses, health data, financial data.",
        type=QuestionType.SINGLE,
        options=["Yes", "No", "Unsure"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q3",
            trigger_values=["EU", "UK"],
            action="show"
        ),
        tags=["gdpr", "pii"]
    ),

    Question(
        id="Q12b",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="GDPR Compliance",
        order=13,
        text="Is a Data Processing Agreement (DPA) in place with all data processors?",
        type=QuestionType.SINGLE,
        options=["Yes", "No – needs to be established", "In progress"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q3",
            trigger_values=["EU", "UK"],
            action="show"
        ),
        tags=["gdpr", "dpa"]
    ),

    Question(
        id="Q12c",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="GDPR Compliance",
        order=14,
        text="What is the lawful basis for data processing under GDPR?",
        type=QuestionType.SINGLE,
        options=[
            "Consent",
            "Contractual necessity",
            "Legal obligation",
            "Vital interests",
            "Public task",
            "Legitimate interests",
            "Not yet determined"
        ],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q12a",
            trigger_values=["Yes"],
            action="show"
        ),
        tags=["gdpr", "lawful_basis"]
    ),

    # ── SOX block (shown when Q4 = Finance / Accounting) ──────
    Question(
        id="Q13a",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="SOX Compliance",
        order=15,
        text="Will this system be part of financial reporting or general ledger processes?",
        type=QuestionType.SINGLE,
        options=["Yes", "No", "Partially"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q4",
            trigger_values=["Finance / Accounting"],
            action="show"
        ),
        tags=["sox", "financial_reporting"]
    ),

    Question(
        id="Q13b",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="SOX Compliance",
        order=16,
        text="Are audit trails and change history required for all financial data modifications?",
        type=QuestionType.SINGLE,
        options=["Yes – full audit trail", "Yes – key fields only", "No", "TBD"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q13a",
            trigger_values=["Yes", "Partially"],
            action="show"
        ),
        tags=["sox", "audit_trail"]
    ),

    # ── GxP block (shown when Q4 = Life Sciences / Pharma) ────
    Question(
        id="Q14a",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="GxP Compliance",
        order=17,
        text="Does this project involve GxP-regulated data (clinical trials, manufacturing, lab)?",
        type=QuestionType.SINGLE,
        options=["Yes", "No", "Unsure"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q4",
            trigger_values=["Life Sciences / Pharma"],
            action="show"
        ),
        tags=["gxp", "21cfr_part11"]
    ),

    Question(
        id="Q14b",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="GxP Compliance",
        order=18,
        text="Will electronic signatures (21 CFR Part 11) be required?",
        type=QuestionType.SINGLE,
        options=["Yes", "No", "TBD"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q14a",
            trigger_values=["Yes"],
            action="show"
        ),
        tags=["gxp", "esignature"]
    ),

    Question(
        id="Q14c",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="GxP Compliance",
        order=19,
        text="Is a Computer System Validation (CSV) plan required for this system?",
        type=QuestionType.SINGLE,
        options=["Yes – full IQ/OQ/PQ", "Yes – risk-based approach", "No", "TBD"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q14a",
            trigger_values=["Yes"],
            action="show"
        ),
        tags=["gxp", "csv", "validation_plan"]
    ),

    # ── HIPAA block (shown when Q4 = Healthcare / Clinical) ───
    Question(
        id="Q15a",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="HIPAA Compliance",
        order=20,
        text="Does this project process Protected Health Information (PHI)?",
        type=QuestionType.SINGLE,
        options=["Yes", "No", "De-identified data only"],
        validation=ValidationRule(required=True),
        conditional=ConditionalLogic(
            trigger_question_id="Q4",
            trigger_values=["Healthcare / Clinical"],
            action="show"
        ),
        tags=["hipaa", "phi"]
    ),

    # ── Universal Security ─────────────────────────────────────
    Question(
        id="Q16",
        phase=Phase.P3_SECURITY_COMPLIANCE,
        category="Data Security",
        order=21,
        text="What is the data classification level of the primary dataset?",
        help_text="This drives encryption, access control, and network segmentation requirements.",
        type=QuestionType.SINGLE,
        options=[
            "Public",
            "Internal / Non-sensitive",
            "Confidential",
            "Restricted / Highly Sensitive"
        ],
        validation=ValidationRule(required=True),
        tags=["security", "data_classification"]
    ),
]


# ═══════════════════════════════════════════════════════════════
# PHASE 4 — Visualization & Technical  (Q17–Q23)
# ═══════════════════════════════════════════════════════════════

PHASE_4_QUESTIONS: list[Question] = [

    Question(
        id="Q17",
        phase=Phase.P4_VISUALIZATION,
        category="Visualization Platform",
        order=22,
        text="Which BI / visualization platform will be used?",
        help_text="This determines the Gold layer output format and connector requirements.",
        type=QuestionType.MULTI,
        options=[
            "Power BI", "Tableau", "Looker", "Databricks SQL",
            "Azure Synapse Analytics", "AWS QuickSight",
            "Custom React / D3.js", "No visualization needed", "TBD"
        ],
        validation=ValidationRule(required=True),
        tags=["bi_platform", "visualization"]
    ),

    Question(
        id="Q18",
        phase=Phase.P4_VISUALIZATION,
        category="Visualization Platform",
        order=23,
        text="List the top 5 filters / slicers required on dashboards.",
        help_text="Example: date range, department, region, product category, status.",
        type=QuestionType.TEXTAREA,
        validation=ValidationRule(required=False, max_length=500),
        tags=["filters", "dashboard_spec"]
    ),

    Question(
        id="Q19",
        phase=Phase.P4_VISUALIZATION,
        category="Layout & UX",
        order=24,
        text="What chart types are required?",
        type=QuestionType.MULTI,
        options=[
            "KPI Scorecard / Summary Cards",
            "Line / Trend Chart",
            "Bar / Column Chart",
            "Pie / Donut Chart",
            "Heatmap",
            "Scatter Plot",
            "Geospatial / Map",
            "Funnel Chart",
            "Table / Grid",
            "Gantt / Timeline"
        ],
        validation=ValidationRule(required=False),
        tags=["chart_types", "visualization"]
    ),

    Question(
        id="Q20",
        phase=Phase.P4_VISUALIZATION,
        category="Layout & UX",
        order=25,
        text="Do you have an existing wireframe, mockup, or design reference?",
        help_text="Upload PNG, PDF, Figma export, or paste a URL.",
        type=QuestionType.FILE_UPLOAD,
        validation=ValidationRule(required=False),
        tags=["wireframe", "design_reference"]
    ),

    Question(
        id="Q21",
        phase=Phase.P4_VISUALIZATION,
        category="Technical Architecture",
        order=26,
        text="Which compute platform will run the data pipeline?",
        type=QuestionType.SINGLE,
        options=[
            "Azure Databricks",
            "Azure Data Factory + Synapse",
            "AWS Glue + EMR",
            "Google Dataflow",
            "Snowflake Tasks",
            "dbt Core / Cloud",
            "Apache Spark (on-prem)",
            "TBD"
        ],
        validation=ValidationRule(required=True),
        tags=["compute_platform", "adb_trigger"]
    ),

    Question(
        id="Q22",
        phase=Phase.P4_VISUALIZATION,
        category="Technical Architecture",
        order=27,
        text="Where will the pipeline code be stored and managed?",
        type=QuestionType.SINGLE,
        options=[
            "GitHub (Cloud)",
            "Azure DevOps Repos",
            "GitLab",
            "Bitbucket",
            "Databricks Repos",
            "No version control currently"
        ],
        validation=ValidationRule(required=True),
        tags=["source_control", "github_trigger"]
    ),

    Question(
        id="Q23",
        phase=Phase.P4_VISUALIZATION,
        category="Technical Architecture",
        order=28,
        text="Upload any additional supporting documents (architecture diagrams, data samples, etc.)",
        help_text="Accepts PDF, Excel, CSV, PNG, DOCX. Max 10 files, 50MB each.",
        type=QuestionType.FILE_UPLOAD,
        validation=ValidationRule(required=False),
        tags=["attachments", "multi_file_upload"]
    ),
]


# ═══════════════════════════════════════════════════════════════
# PHASE 5 — ROI Questions  (Q24–Q33)
# ═══════════════════════════════════════════════════════════════

PHASE_5_QUESTIONS: list[Question] = [

    Question(
        id="Q24",
        phase=Phase.P5_ROI,
        category="Manual Process Assessment",
        order=29,
        text="Describe the manual / current-state process this solution will replace or improve.",
        help_text="The more detail you provide, the more accurate the ROI calculation.",
        type=QuestionType.TEXTAREA,
        validation=ValidationRule(required=True, min_length=50, max_length=2000),
        tags=["manual_process", "roi_context"],
        is_llm_followup_trigger=True
    ),

    Question(
        id="Q25",
        phase=Phase.P5_ROI,
        category="Labor Savings",
        order=30,
        text="How many FTEs (full-time equivalents) are currently involved in this process?",
        type=QuestionType.NUMBER,
        validation=ValidationRule(required=True, min_value=0.5, max_value=10000),
        tags=["fte", "labor_cost"]
    ),

    Question(
        id="Q26",
        phase=Phase.P5_ROI,
        category="Labor Savings",
        order=31,
        text="What is the average fully-loaded hourly cost per FTE (salary + benefits)?",
        help_text="Use your organization's blended rate. Default: $75/hr if unknown.",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=True, min_value=10, max_value=500),
        tags=["hourly_rate", "labor_cost"]
    ),

    Question(
        id="Q27",
        phase=Phase.P5_ROI,
        category="Labor Savings",
        order=32,
        text="How many hours per week does each FTE spend on this manual process?",
        type=QuestionType.NUMBER,
        validation=ValidationRule(required=True, min_value=0.5, max_value=60),
        tags=["hours_per_week", "labor_savings"]
    ),

    Question(
        id="Q28",
        phase=Phase.P5_ROI,
        category="Labor Savings",
        order=33,
        text="What percentage of that effort will be eliminated by this solution?",
        help_text="Be conservative. Full automation rarely exceeds 80–85%.",
        type=QuestionType.PERCENTAGE,
        validation=ValidationRule(required=True, min_value=5, max_value=100),
        tags=["automation_pct", "labor_savings"]
    ),

    Question(
        id="Q29",
        phase=Phase.P5_ROI,
        category="Revenue Impact",
        order=34,
        text="Is there a direct revenue opportunity enabled by this solution?",
        help_text="Example: faster time-to-market, new product upsell, reduced churn.",
        type=QuestionType.SINGLE,
        options=["Yes – quantifiable", "Yes – difficult to quantify", "No"],
        validation=ValidationRule(required=True),
        tags=["revenue_impact", "roi"]
    ),

    Question(
        id="Q29b",
        phase=Phase.P5_ROI,
        category="Revenue Impact",
        order=35,
        text="Estimated annual revenue uplift (USD)?",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=True, min_value=0),
        conditional=ConditionalLogic(
            trigger_question_id="Q29",
            trigger_values=["Yes – quantifiable"],
            action="show"
        ),
        tags=["revenue_uplift", "roi"]
    ),

    Question(
        id="Q30",
        phase=Phase.P5_ROI,
        category="Error & Rework Reduction",
        order=36,
        text="What is the estimated annual cost of errors, rework, or compliance issues in the current process?",
        help_text="Include fines, rework hours, customer refunds, audit costs.",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=False, min_value=0),
        tags=["error_cost", "roi"]
    ),

    Question(
        id="Q31",
        phase=Phase.P5_ROI,
        category="Error & Rework Reduction",
        order=37,
        text="What percentage of those errors will this solution prevent?",
        type=QuestionType.PERCENTAGE,
        validation=ValidationRule(required=False, min_value=0, max_value=100),
        conditional=ConditionalLogic(
            trigger_question_id="Q30",
            trigger_values=["*"],  # any non-zero value
            action="show"
        ),
        tags=["error_reduction_pct", "roi"]
    ),

    Question(
        id="Q32",
        phase=Phase.P5_ROI,
        category="License Consolidation",
        order=38,
        text="Are there existing tools or licenses that will be decommissioned?",
        help_text="Example: legacy BI tool, ETL platform, manual reporting tool.",
        type=QuestionType.SINGLE,
        options=["Yes", "No", "Unsure"],
        validation=ValidationRule(required=True),
        tags=["license_savings", "roi"]
    ),

    Question(
        id="Q33",
        phase=Phase.P5_ROI,
        category="License Consolidation",
        order=39,
        text="Estimated annual license savings from decommissioning (USD)?",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=True, min_value=0),
        conditional=ConditionalLogic(
            trigger_question_id="Q32",
            trigger_values=["Yes"],
            action="show"
        ),
        tags=["license_savings", "roi"]
    ),
]


# ═══════════════════════════════════════════════════════════════
# PHASE 6 — ROM (Rough Order of Magnitude)  (Q34–Q41)
# Many are auto-calculated from earlier phases
# ═══════════════════════════════════════════════════════════════

PHASE_6_QUESTIONS: list[Question] = [

    Question(
        id="Q34",
        phase=Phase.P6_ROM,
        category="Infrastructure Cost",
        order=40,
        text="Estimated monthly cloud infrastructure cost (auto-calculated from Q7, Q21)?",
        help_text="Auto-filled based on data volume (Q7) and compute platform (Q21). Override if known.",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=True, min_value=0),
        auto_fill=AutoFill(
            source_type="calculation",
            source_ref="calc_infra_cost(Q7, Q21)"
        ),
        tags=["infrastructure", "rom", "auto_calc"]
    ),

    Question(
        id="Q35",
        phase=Phase.P6_ROM,
        category="Development Effort",
        order=41,
        text="Estimated development effort (auto-calculated from Q9, Q10, Q12–Q15)?",
        help_text="Auto-filled in weeks based on entities (Q9), data quality issues (Q10), and compliance requirements.",
        type=QuestionType.NUMBER,
        validation=ValidationRule(required=True, min_value=1, max_value=200),
        auto_fill=AutoFill(
            source_type="calculation",
            source_ref="calc_dev_weeks(Q9, Q10, Q12a, Q13a, Q14a, Q15a)"
        ),
        tags=["development_effort", "rom", "auto_calc"]
    ),

    Question(
        id="Q36",
        phase=Phase.P6_ROM,
        category="Development Effort",
        order=42,
        text="Average blended rate for development team (USD/hr)?",
        help_text="Used to convert dev-weeks into dollar cost.",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=True, min_value=50, max_value=500),
        tags=["dev_rate", "rom"]
    ),

    Question(
        id="Q37",
        phase=Phase.P6_ROM,
        category="Licensing",
        order=43,
        text="Estimated new tool / platform license cost (annual, USD)?",
        help_text="Include Databricks DBUs, Power BI Premium, Snowflake credits, etc.",
        type=QuestionType.CURRENCY,
        validation=ValidationRule(required=False, min_value=0),
        tags=["licensing_cost", "rom"]
    ),

    Question(
        id="Q38",
        phase=Phase.P6_ROM,
        category="Ongoing Support",
        order=44,
        text="Estimated annual support / maintenance effort (% of development cost)?",
        help_text="Industry standard: 15–20% of build cost per year.",
        type=QuestionType.PERCENTAGE,
        validation=ValidationRule(required=True, min_value=5, max_value=50),
        tags=["support_cost", "rom"]
    ),

    Question(
        id="Q39",
        phase=Phase.P6_ROM,
        category="ROM Summary",
        order=45,
        text="Total Implementation Cost (auto-calculated from Q34–Q38)?",
        help_text="= Infrastructure + (Dev Weeks × Rate × 40hrs) + Licensing.",
        type=QuestionType.CALCULATED,
        auto_fill=AutoFill(
            source_type="calculation",
            source_ref="calc_total_impl_cost(Q34, Q35, Q36, Q37)"
        ),
        validation=ValidationRule(required=False),
        tags=["total_cost", "rom", "auto_calc"]
    ),

    Question(
        id="Q40",
        phase=Phase.P6_ROM,
        category="ROM Summary",
        order=46,
        text="3-Year Total Cost of Ownership (TCO) — auto-calculated?",
        help_text="= Impl Cost + (Annual Infra + Support) × 3 years.",
        type=QuestionType.CALCULATED,
        auto_fill=AutoFill(
            source_type="calculation",
            source_ref="calc_3yr_tco(Q34, Q38, Q39)"
        ),
        validation=ValidationRule(required=False),
        tags=["tco", "rom", "auto_calc"]
    ),

    Question(
        id="Q41",
        phase=Phase.P6_ROM,
        category="ROM Summary",
        order=47,
        text="Net 3-Year ROI % — auto-calculated?",
        help_text="= ((3-yr Benefits – TCO) / TCO) × 100. Benefits from Phase 5.",
        type=QuestionType.CALCULATED,
        auto_fill=AutoFill(
            source_type="calculation",
            source_ref="calc_net_roi(Q25..Q33, Q40)"
        ),
        validation=ValidationRule(required=False),
        tags=["net_roi", "rom", "auto_calc"]
    ),
]


# ═══════════════════════════════════════════════════════════════
# MASTER CATALOG — all questions in order
# ═══════════════════════════════════════════════════════════════

ALL_QUESTIONS: list[Question] = (
    PHASE_1_QUESTIONS +
    PHASE_2_QUESTIONS +
    PHASE_3_QUESTIONS +
    PHASE_4_QUESTIONS +
    PHASE_5_QUESTIONS +
    PHASE_6_QUESTIONS
)

QUESTION_MAP: dict[str, Question] = {q.id: q for q in ALL_QUESTIONS}

# First 8 questions shown by default (Progressive Disclosure)
INITIAL_VISIBLE = [q.id for q in ALL_QUESTIONS[:8]]
