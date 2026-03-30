"""
DPS (Design/Project Specification) Template Definition.

Defines all required sections of a DPS document, their sub-sections,
and per-persona evaluation criteria (PM, BA, Tech Lead).

Based on: RITM2195089-DPS-Unified Customer Master NA (BD/Becton Dickinson)
This template is generic enough to apply to any enterprise data project DPS.

Section status types:
    PRESENT   - Section found with meaningful content
    EMPTY     - Section heading found, but body is blank/table is unfilled
    MISSING   - Section heading not found at all in the document
"""

from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# REQUIRED SECTION DEFINITIONS
# Each entry defines:
#   id          : internal key used throughout the engine
#   label       : human-readable name for display/reports
#   patterns    : regex patterns to detect this section heading in extracted text
#   subsections : child sections that must also be checked
#   required    : True = must be present; False = recommended but optional
#   guidance    : what to fill in if this section is empty/missing
# ─────────────────────────────────────────────────────────────────────────────

DPS_SECTIONS: List[Dict] = [
    {
        "id": "purpose",
        "label": "1.0 Purpose",
        "patterns": [r"1[.\d\s]+purpose", r"^\s*purpose\s*$"],
        "subsections": [],
        "required": True,
        "guidance": "State the business objective, who requested it, and the expected outcome."
    },
    {
        "id": "scope",
        "label": "2.0 Scope",
        "patterns": [r"2[.\d\s]+scope", r"^\s*scope\s*$"],
        "subsections": [
            {
                "id": "scope_in",
                "label": "In Scope",
                "patterns": [r"in[\s\-]+scope", r"in scope"],
                "guidance": "List all source systems, datasets, regions, and brands in scope."
            },
            {
                "id": "scope_out",
                "label": "Out of Scope",
                "patterns": [r"out[\s\-]+of[\s\-]+scope", r"not in scope"],
                "guidance": "Explicitly list what is excluded (systems, regions, use cases)."
            }
        ],
        "required": True,
        "guidance": "Define In Scope and Out of Scope boundaries for data sources, regions, and use cases."
    },
    {
        "id": "definitions",
        "label": "3.0 Definitions / Acronyms",
        "patterns": [r"3[.\d\s]+def", r"definitions?\s*/\s*acronyms?", r"glossary"],
        "subsections": [],
        "required": True,
        "guidance": "Define all acronyms and business terms used in this document (e.g. ETL, KPI, MDM, NRM)."
    },
    {
        "id": "references",
        "label": "4.0 References",
        "patterns": [r"4[.\d\s]+ref", r"^\s*references?\s*$"],
        "subsections": [],
        "required": True,
        "guidance": "List referenced docs: Confluence pages, architecture diagrams, source system specs, prior DPS versions."
    },
    {
        "id": "roles",
        "label": "5.0 Roles and Responsibilities",
        "patterns": [r"5[.\d\s]+roles?", r"roles?\s+and\s+responsibilities", r"raci"],
        "subsections": [],
        "required": True,
        "guidance": "List each role (Product Owner, BA, Tech Lead, Data Engineer, QA, AMO) with named owners."
    },
    {
        "id": "assumptions",
        "label": "6.0 Assumptions, Dependencies & Constraints",
        "patterns": [
            r"6[.\d\s]+assum", r"assumptions?,?\s+dependencies", r"assumptions?\s+and\s+constraints?"
        ],
        "subsections": [],
        "required": True,
        "guidance": "Document assumptions about source data, external dependencies (teams/approvals), and constraints (timeline, tech)."
    },
    {
        "id": "user_requirements",
        "label": "7.0 User Requirements",
        "patterns": [r"7[.\d\s]+user", r"user\s+requirements?"],
        "subsections": [
            {
                "id": "data_product_requirements",
                "label": "7.1 Data Product Requirements",
                "patterns": [r"7[\.\s]*1", r"data\s+product\s+req"],
                "guidance": "List all required fields with: name, data type, source system, transformation rule, business definition."
            },
            {
                "id": "source_system",
                "label": "7.2 Source System",
                "patterns": [r"7[\.\s]*2", r"source\s+system"],
                "guidance": "Identify source systems with: name, type (ERP/CRM/MDM), connection method, format, refresh frequency."
            },
            {
                "id": "security_groups",
                "label": "7.3 Security Groups",
                "patterns": [r"7[\.\s]*3", r"security\s+groups?", r"access\s+groups?"],
                "guidance": "List AD/AAD security groups with access level (read/write) and business justification. Required for InfoSec sign-off."
            },
            {
                "id": "visualization_layer",
                "label": "7.4 Visualization Layer",
                "patterns": [r"7[\.\s]*4", r"visuali[sz]ation\s+layer", r"reporting\s+layer"],
                "guidance": "Specify Power BI workspace, dashboard name, required KPIs, audience, and refresh schedule."
            }
        ],
        "required": True,
        "guidance": "Cover: required data fields, source systems, access groups, and visualization layer details."
    },
    {
        "id": "functional_design",
        "label": "8.0 Functional Design",
        "patterns": [r"8[.\d\s]+func", r"functional\s+design"],
        "subsections": [
            {
                "id": "transformation_logic",
                "label": "8.1 Transformation & Business Logic",
                "patterns": [r"8[\.\s]*1", r"transform", r"business\s+logic", r"calculation"],
                "guidance": "Document joins, filters, aggregations, and calculated field logic. Use a Source → Rule → Target mapping table."
            },
            {
                "id": "data_latency",
                "label": "8.2 Data Latency",
                "patterns": [r"8[\.\s]*2", r"data\s+latency", r"freshness", r"sla"],
                "guidance": "Specify refresh frequency (real-time/daily/weekly), acceptable lag SLA, and failure handling."
            },
            {
                "id": "data_ingestion",
                "label": "8.3 Data Ingestion",
                "patterns": [r"8[\.\s]*3", r"data\s+ingestion", r"ingestion\s+method"],
                "guidance": "Specify: full load vs incremental, extraction method (JDBC/API/file), Bronze layer path, partitioning key."
            },
            {
                "id": "security_design",
                "label": "8.4 Security",
                "patterns": [r"8[\.\s]*4", r"security(?!\s+group)"],
                "guidance": "Cover data classification, PII field masking, encryption standards, and Unity Catalog permissions."
            },
            {
                "id": "regulatory",
                "label": "8.5 Regulatory",
                "patterns": [r"8[\.\s]*5", r"regulat", r"compliance", r"gdpr", r"ccpa", r"hipaa"],
                "guidance": "List applicable regulations (GDPR/CCPA/HIPAA/SOX), data residency rules, retention policy, and audit logging."
            }
        ],
        "required": True,
        "guidance": "Detail transformation logic, data latency SLA, ingestion approach, security, and regulatory requirements."
    },
    {
        "id": "architecture",
        "label": "9.0 Architecture",
        "patterns": [r"9[.\d\s]+arch", r"architecture\s+committee", r"infrastructure"],
        "subsections": [
            {
                "id": "infrastructure",
                "label": "9.1 Infrastructure",
                "patterns": [r"9[\.\s]*1", r"infrastructure", r"compute", r"cluster"],
                "guidance": "Specify Databricks cluster config, Unity Catalog paths, storage accounts, and Dev/Stage/Prod environment setup."
            }
        ],
        "required": True,
        "guidance": "Document compute/storage architecture, data flow diagram, and Architecture Committee approval."
    },
    {
        "id": "amo_support",
        "label": "10.0 AMO Support",
        "patterns": [r"10[.\d\s]+amo", r"amo\s+support", r"application\s+management"],
        "subsections": [],
        "required": True,
        "guidance": "Define monitoring alerts, on-call runbook, SLA breach escalation, and AMO team access."
    },
    {
        "id": "mapping_specs",
        "label": "11.0 Mapping Specifications",
        "patterns": [r"11[.\d\s]+map", r"mapping\s+spec", r"column\s+mapping"],
        "subsections": [],
        "required": True,
        "guidance": "Attach the column-level mapping Excel: Source System | Source Column | Transformation Rule | Target Column | PII Flag."
    },
    {
        "id": "appendix",
        "label": "12.0 Appendix",
        "patterns": [r"12[.\d\s]+app", r"^\s*appendix\s*$"],
        "subsections": [],
        "required": False,
        "guidance": (
            "Optional: attach diagrams, ERDs, sample data, sign-off emails, "
            "Architecture Committee approval screenshots."
        )
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# PER-PERSONA EVALUATION CRITERIA
# For each section, defines what each persona (PM / BA / Tech Lead) looks for.
# Used by the LLM to generate persona-specific quality scores and feedback.
# ─────────────────────────────────────────────────────────────────────────────

PERSONA_CRITERIA: Dict[str, Dict[str, str]] = {

    "purpose": {
        "PM": "Is the business objective clearly stated? Is there a named stakeholder/sponsor? Is the value delivery outcome measurable?",
        "BA": "Does the purpose tie to specific user stories or business capabilities? Are success metrics implied?",
        "Tech Lead": "Is the scope of the technical deliverable inferable from the purpose? Are there hints about data complexity?"
    },

    "scope": {
        "PM": "Are in-scope and out-of-scope clearly separated? Is there a risk of scope creep without these boundaries?",
        "BA": "Are all affected business domains listed? Is the scope consistent with the user requirements section?",
        "Tech Lead": "Can the pipeline scope (which systems, tables, layers) be derived? Are integration points bounded?"
    },

    "definitions": {
        "PM": "Are business terms defined so non-technical stakeholders can read the document without ambiguity?",
        "BA": "Are all abbreviations from User Requirements and Functional Design sections defined here?",
        "Tech Lead": "Are technical acronyms (ETL, Unity Catalog, Bronze/Silver/Gold) included?"
    },

    "references": {
        "PM": "Are previous project references (prior DPS, related Jira epics) listed to avoid rework?",
        "BA": "Are business requirement documents and stakeholder sign-off referenced?",
        "Tech Lead": "Are architecture diagrams, data dictionaries, and source system specs referenced?"
    },

    "roles": {
        "PM": "Is there a clear Product Owner? Are responsibilities assigned to named individuals, not just roles?",
        "BA": "Is the BA role defined? Are business SMEs (subject matter experts) listed for each domain?",
        "Tech Lead": "Are the Data Engineer, Architect, and QA roles explicitly assigned? Is there a DRI (Directly Responsible Individual)?"
    },

    "assumptions": {
        "PM": "Are timeline assumptions explicit? Are external blockers (approvals, licenses) listed?",
        "BA": "Are data quality assumptions documented? What happens if source data doesn't match assumptions?",
        "Tech Lead": "Are technical assumptions (schema stability, API availability, volume estimates) documented? Are fallback strategies mentioned?"
    },

    "user_requirements": {
        "PM": "Are all requirements traceable to a business need? Are priorities (must-have vs nice-to-have) indicated?",
        "BA": "Are security groups defined with named AD groups? Is the visualization layer specified with Power BI workspace and dashboard names?",
        "Tech Lead": "Are all source systems identified with connection details? Is the data product field list complete with data types?"
    },

    "data_product_requirements": {
        "PM": "Is the list of required fields approved by the business? Are there acceptance criteria?",
        "BA": "Does each field have a business definition? Are calculated fields explained in business terms?",
        "Tech Lead": "Do fields include data types, nullable flags, and source system mapping?"
    },

    "source_system": {
        "PM": "Are source system owners identified? Are there data sharing agreements in place?",
        "BA": "Is the data extraction frequency aligned with the business SLA expectations?",
        "Tech Lead": "Are connection methods, authentication, and extraction patterns (full/incremental) specified?"
    },

    "security_groups": {
        "PM": "Is executive/leadership access provisioned appropriately? Is there a data steward named?",
        "BA": "Are functional groups (Finance, Sales, HR) mapped to the correct access levels?",
        "Tech Lead": "Are AD/AAD group names provided? Is row-level security (RLS) needed? Are Unity Catalog permissions specified?"
    },

    "visualization_layer": {
        "PM": "Is the Power BI workspace and dashboard name agreed with the business? Who signs off on the report design?",
        "BA": "Are all KPIs and visuals listed with their business definitions and calculation logic?",
        "Tech Lead": "Is the Gold layer table feeding Power BI identified? Are DirectQuery vs Import mode and refresh schedules specified?"
    },

    "functional_design": {
        "PM": "Is the functional design approved by the business? Are edge cases handled?",
        "BA": "Are transformation rules traceable to business requirements? Is there a mapping spec attached?",
        "Tech Lead": "Is transformation logic precise enough to implement without asking further questions? Are all edge cases and null handling covered?"
    },

    "transformation_logic": {
        "PM": "Does the transformation logic produce the KPIs the business expects?",
        "BA": "Are business rules (e.g., revenue = net_sales - returns - discounts) explicitly stated?",
        "Tech Lead": "Are join keys, aggregation grain, filter conditions, and NULL handling all specified?"
    },

    "data_latency": {
        "PM": "Is the data freshness SLA agreed with stakeholders? What is the business impact of delays?",
        "BA": "Is the SLA consistent with what the business stated in user requirements?",
        "Tech Lead": "Is the pipeline schedule (cron), retry policy, and alerting threshold documented?"
    },

    "data_ingestion": {
        "PM": "Is the ingestion approach approved? Any licensing or cost implications?",
        "BA": "Is the ingestion frequency consistent with the data latency SLA?",
        "Tech Lead": "Are Bronze layer paths, file formats, incremental keys, and watermark strategies specified?"
    },

    "security_design": {
        "PM": "Is InfoSec team involved? Are there data classification approvals required?",
        "BA": "Are PII fields identified and masking requirements specified in business terms?",
        "Tech Lead": "Are column-level masking, encryption standards, and Unity Catalog row filters documented?"
    },

    "regulatory": {
        "PM": "Has Legal/Compliance reviewed this section? Are there approval gating requirements?",
        "BA": "Are data retention policies specified in the requirements?",
        "Tech Lead": "Is audit logging implemented? Are GDPR delete/anonymisation workflows designed?"
    },

    "architecture": {
        "PM": "Has the Architecture Committee approved this design? Are there cost implications?",
        "BA": "Is the architecture understandable to a non-technical stakeholder?",
        "Tech Lead": "Is the full tech stack (cluster type, catalog paths, storage, networking) documented? Are Dev/Stage/Prod environments specified?"
    },

    "amo_support": {
        "PM": "Is there a clear handoff plan to AMO? Is the go-live date agreed?",
        "BA": "Are runbooks and support escalation paths documented in plain language?",
        "Tech Lead": "Are monitoring alerts, SLA breach conditions, and on-call procedures defined? Is there a rollback plan?"
    },

    "mapping_specs": {
        "PM": "Has the mapping spec been reviewed and approved by the business?",
        "BA": "Does every target field have a source mapping? Are business definitions included?",
        "Tech Lead": "Is the mapping spreadsheet attached? Does it cover all Bronze → Silver → Gold transformations with data types?"
    },

    "appendix": {
        "PM": "Are Architecture Committee approvals and stakeholder sign-offs attached?",
        "BA": "Are sample data snapshots or test cases included?",
        "Tech Lead": "Are ERDs, data flow diagrams, and environment topology diagrams attached?"
    }
}


# Build a quick lookup dict for section by id
SECTION_BY_ID: Dict[str, Dict] = {s["id"]: s for s in DPS_SECTIONS}

# All required section IDs (flat, including sub-sections)
def getAllSectionIds() -> List[str]:
    """Return flat list of all section IDs (top-level + sub-sections)."""
    ids = []
    for section in DPS_SECTIONS:
        ids.append(section["id"])
        for sub in section.get("subsections", []):
            ids.append(sub["id"])
    return ids
