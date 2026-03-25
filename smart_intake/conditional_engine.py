"""
SMART INTAKE - Conditional Logic Engine
=========================================
DE-side engine that:
  1. Evaluates which questions should be visible given current answers
  2. Detects compliance flags (GDPR, SOX, GxP, HIPAA)
  3. Auto-fills questions from source catalog or calculations
  4. Validates answers against rules

This runs on the DE API server; UI calls /api/evaluate-conditions after each answer.
"""

from typing import Any, Dict, List, Optional
from smart_intake.models import Question, ComplianceFlag, ConditionalLogic
from smart_intake.questions import ALL_QUESTIONS, QUESTION_MAP, INITIAL_VISIBLE


# ─────────────────────────────────────────────
# COMPLIANCE FLAG DETECTION
# ─────────────────────────────────────────────

def detect_compliance_flags(answers: Dict[str, Any]) -> List[ComplianceFlag]:
    """
    Returns list of compliance frameworks triggered by current answers.

    Q3 (region) → EU or UK  → GDPR
    Q4 (domain) → Finance   → SOX
                  Life Sci  → GxP
                  Healthcare → HIPAA
    """
    flags = []
    regions = answers.get("Q3", [])
    if isinstance(regions, str):
        regions = [regions]
    if any(r in regions for r in ["EU", "UK"]):
        flags.append(ComplianceFlag.GDPR)

    domain = answers.get("Q4", "")
    if "Finance" in domain:
        flags.append(ComplianceFlag.SOX)
    if "Life Sciences" in domain or "Pharma" in domain:
        flags.append(ComplianceFlag.GXP)
    if "Healthcare" in domain or "Clinical" in domain:
        flags.append(ComplianceFlag.HIPAA)

    return flags


# ─────────────────────────────────────────────
# VISIBILITY EVALUATOR
# ─────────────────────────────────────────────

def _evaluate_condition(condition: ConditionalLogic, answers: Dict[str, Any]) -> bool:
    """Returns True if a question's show condition is met."""
    trigger_answer = answers.get(condition.trigger_question_id)
    if trigger_answer is None:
        return False

    # Wildcard: any non-empty/non-zero value
    if condition.trigger_values == ["*"]:
        return bool(trigger_answer)

    # List answer (multi-select): check intersection
    if isinstance(trigger_answer, list):
        return any(v in trigger_answer for v in condition.trigger_values)

    # Scalar answer
    return str(trigger_answer) in condition.trigger_values


def get_visible_questions(answers: Dict[str, Any]) -> List[str]:
    """
    Returns ordered list of question IDs visible given current answers.
    Always includes the first 8 (progressive disclosure base).
    """
    visible = []
    for q in ALL_QUESTIONS:
        if q.conditional is None:
            visible.append(q.id)
        elif q.conditional.action == "show" and _evaluate_condition(q.conditional, answers):
            visible.append(q.id)
    return visible


def get_required_questions(answers: Dict[str, Any]) -> List[str]:
    """Returns IDs of currently required questions."""
    visible = get_visible_questions(answers)
    required = []
    for qid in visible:
        q = QUESTION_MAP.get(qid)
        if q and q.validation.required:
            required.append(qid)
    return required


# ─────────────────────────────────────────────
# AUTO-FILL ENGINE
# ─────────────────────────────────────────────

# Source catalog: known metadata per source system
SOURCE_CATALOG: Dict[str, Dict] = {
    "Epic EHR": {
        "typical_entities": ["patients", "encounters", "diagnoses", "procedures", "medications"],
        "typical_volume": "100 GB – 1 TB / day",
        "typical_format": "HL7 FHIR / flat tables",
        "compliance_hint": ["HIPAA"]
    },
    "Salesforce": {
        "typical_entities": ["accounts", "contacts", "opportunities", "cases", "leads"],
        "typical_volume": "1–10 GB / day",
        "typical_format": "REST API / Bulk API",
        "compliance_hint": []
    },
    "SAP": {
        "typical_entities": ["GL entries", "cost centers", "purchase orders", "invoices"],
        "typical_volume": "10–100 GB / day",
        "typical_format": "IDOC / RFC / ODP",
        "compliance_hint": ["SOX"]
    },
    "Kafka / Streaming": {
        "typical_entities": ["events", "transactions", "clickstream"],
        "typical_volume": "> 1 TB / day",
        "typical_format": "Avro / JSON / Protobuf",
        "compliance_hint": []
    },
}

# Infrastructure cost lookup (volume × platform)
INFRA_COST_MATRIX: Dict[str, Dict[str, float]] = {
    "< 1 GB / day":           {"Azure Databricks": 500,  "Snowflake Tasks": 300,  "default": 400},
    "1–10 GB / day":          {"Azure Databricks": 1200, "Snowflake Tasks": 800,  "default": 1000},
    "10–100 GB / day":        {"Azure Databricks": 3500, "Snowflake Tasks": 2500, "default": 3000},
    "100 GB – 1 TB / day":    {"Azure Databricks": 8000, "Snowflake Tasks": 6000, "default": 7000},
    "> 1 TB / day":           {"Azure Databricks": 20000,"Snowflake Tasks": 15000,"default": 18000},
}

# Compliance complexity adds dev weeks
COMPLIANCE_DEV_OVERHEAD: Dict[str, int] = {
    "GDPR": 2, "SOX": 3, "GxP": 5, "HIPAA": 2
}


def auto_fill_values(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a dict of {question_id: auto_filled_value} based on current answers.
    UI should pre-populate these fields (user can override).
    """
    filled = {}

    # Q34: Infrastructure cost
    volume = answers.get("Q7", "")
    platform = answers.get("Q21", "default")
    if volume and volume in INFRA_COST_MATRIX:
        row = INFRA_COST_MATRIX[volume]
        filled["Q34"] = row.get(platform, row["default"])

    # Q35: Dev weeks = base(entities) + quality overhead + compliance overhead
    entities = answers.get("Q9")
    if entities:
        base_weeks = max(4, round(int(entities) * 0.5))
        dq_issues = answers.get("Q10", [])
        dq_overhead = len([x for x in dq_issues if x != "No known issues"]) * 1
        flags = detect_compliance_flags(answers)
        comp_overhead = sum(COMPLIANCE_DEV_OVERHEAD.get(f.value, 0) for f in flags)
        filled["Q35"] = base_weeks + dq_overhead + comp_overhead

    # Q39: Total impl cost
    infra_monthly = filled.get("Q34") or answers.get("Q34", 0)
    dev_weeks = filled.get("Q35") or answers.get("Q35", 0)
    dev_rate = answers.get("Q36", 125)
    licensing = answers.get("Q37", 0) or 0
    dev_cost = float(dev_weeks) * 40 * float(dev_rate)
    infra_setup = float(infra_monthly) * 3  # 3-month ramp
    filled["Q39"] = round(dev_cost + infra_setup + float(licensing), 2)

    # Q40: 3-year TCO
    impl_cost = filled.get("Q39") or answers.get("Q39", 0)
    annual_infra = float(infra_monthly) * 12 if infra_monthly else 0
    support_pct = float(answers.get("Q38", 18)) / 100
    annual_support = float(impl_cost) * support_pct
    filled["Q40"] = round(float(impl_cost) + (annual_infra + annual_support) * 3, 2)

    # Q41: Net 3yr ROI %
    tco = filled.get("Q40") or answers.get("Q40", 0)
    if tco:
        annual_labor = (
            float(answers.get("Q25", 0)) *
            float(answers.get("Q26", 75)) *
            float(answers.get("Q27", 0)) *
            52 *
            float(answers.get("Q28", 0)) / 100
        )
        error_savings = float(answers.get("Q30", 0)) * float(answers.get("Q31", 0) or 0) / 100
        license_savings = float(answers.get("Q33", 0))
        revenue_uplift = float(answers.get("Q29b", 0))
        annual_benefit = annual_labor + error_savings + license_savings + revenue_uplift
        three_yr_benefit = annual_benefit * 3
        filled["Q41"] = round(((three_yr_benefit - float(tco)) / float(tco)) * 100, 1) if tco else 0

    return filled


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def validate_answer(question_id: str, value: Any) -> Optional[str]:
    """
    Returns error message string if invalid, None if valid.
    """
    q = QUESTION_MAP.get(question_id)
    if not q:
        return f"Unknown question: {question_id}"

    rule = q.validation

    if rule.required and (value is None or value == "" or value == []):
        return f"{q.text} is required."

    if value is None or value == "":
        return None  # optional field, no further checks

    # Numeric / currency / percentage
    if q.type.value in ("number", "currency", "percentage"):
        try:
            num = float(value)
        except (TypeError, ValueError):
            return f"Must be a number."
        if rule.min_value is not None and num < rule.min_value:
            return f"Minimum value is {rule.min_value}."
        if rule.max_value is not None and num > rule.max_value:
            return f"Maximum value is {rule.max_value}."

    # Text length
    if isinstance(value, str):
        if rule.min_length and len(value) < rule.min_length:
            return f"Minimum {rule.min_length} characters required."
        if rule.max_length and len(value) > rule.max_length:
            return f"Maximum {rule.max_length} characters allowed."

    # Allowed values
    if rule.allowed_values:
        if isinstance(value, list):
            invalid = [v for v in value if v not in rule.allowed_values]
            if invalid:
                return f"Invalid option(s): {invalid}"
        elif value not in rule.allowed_values:
            return f"'{value}' is not a valid option."

    return None


def validate_all(answers: Dict[str, Any]) -> Dict[str, str]:
    """Returns {question_id: error_message} for all validation errors."""
    errors = {}
    visible = get_visible_questions(answers)
    for qid in visible:
        error = validate_answer(qid, answers.get(qid))
        if error:
            errors[qid] = error
    return errors
