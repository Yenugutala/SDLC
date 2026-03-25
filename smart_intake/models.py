"""
SMART INTAKE - Data Models & Schemas
=====================================
Defines all data structures shared between DE backend and UI team.
These schemas are the CONTRACT between DE and UI.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class QuestionType(str, Enum):
    TEXT        = "text"
    TEXTAREA    = "textarea"
    SINGLE      = "single_select"
    MULTI       = "multi_select"
    NUMBER      = "number"
    CURRENCY    = "currency"
    PERCENTAGE  = "percentage"
    DATE        = "date"
    FILE_UPLOAD = "file_upload"
    CALCULATED  = "calculated"      # auto-computed, read-only


class Phase(str, Enum):
    P1_PROJECT_CONTEXT  = "phase_1"   # Q1–Q5
    P2_DATA_REQUIREMENTS = "phase_2"  # Q6–Q11
    P3_SECURITY_COMPLIANCE = "phase_3" # Q12–Q16
    P4_VISUALIZATION    = "phase_4"   # Q17–Q23
    P5_ROI              = "phase_5"   # Q24–Q33
    P6_ROM              = "phase_6"   # Q34–Q41


class ComplianceFlag(str, Enum):
    GDPR  = "GDPR"
    SOX   = "SOX"
    GXP   = "GxP"
    HIPAA = "HIPAA"
    NONE  = "None"


class IntakeStatus(str, Enum):
    DRAFT     = "draft"
    SUBMITTED = "submitted"
    APPROVED  = "approved"
    REJECTED  = "rejected"


# ─────────────────────────────────────────────
# QUESTION SCHEMA  (DE → UI contract)
# ─────────────────────────────────────────────

@dataclass
class ValidationRule:
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None          # regex
    allowed_values: Optional[List[str]] = None


@dataclass
class ConditionalLogic:
    """Show this question only when the condition is met."""
    trigger_question_id: str               # e.g. "Q3"
    trigger_values: List[str]              # e.g. ["EU", "UK"]
    action: str = "show"                   # show | hide | require | auto_fill


@dataclass
class AutoFill:
    """Auto-populate this question from a source."""
    source_type: str                       # catalog | calculation | llm
    source_ref: str                        # catalog field name, formula, or LLM prompt key


@dataclass
class Question:
    id: str                                # e.g. "Q1", "Q14b"
    phase: Phase
    category: str                          # "Project Context", "ROI", etc.
    order: int                             # display order within phase
    text: str                              # question label shown to user
    type: QuestionType
    help_text: Optional[str] = None
    options: Optional[List[str]] = None    # for select types
    validation: ValidationRule = field(default_factory=ValidationRule)
    conditional: Optional[ConditionalLogic] = None
    auto_fill: Optional[AutoFill] = None
    tags: List[str] = field(default_factory=list)  # for LLM context
    is_llm_followup_trigger: bool = False   # triggers LLM follow-up generation
    followup_ids: List[str] = field(default_factory=list)  # child question IDs


# ─────────────────────────────────────────────
# INTAKE SESSION  (stored in Cosmos DB)
# ─────────────────────────────────────────────

@dataclass
class IntakeSession:
    session_id: str
    user_id: str
    project_name: str
    status: IntakeStatus
    current_phase: Phase
    answers: Dict[str, Any]                # {question_id: answer_value}
    compliance_flags: List[ComplianceFlag]
    roi_summary: Optional[Dict] = None
    rom_summary: Optional[Dict] = None
    llm_followups_generated: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    cosmos_etag: Optional[str] = None


# ─────────────────────────────────────────────
# API RESPONSE SCHEMAS  (DE → UI)
# ─────────────────────────────────────────────

@dataclass
class PhaseQuestionsResponse:
    phase: str
    total_questions: int
    visible_questions: List[Dict]          # serialized Question objects
    progress_pct: float
    compliance_flags_triggered: List[str]


@dataclass
class ROISummary:
    annual_hours_saved: float
    hourly_rate: float
    annual_labor_savings: float
    error_reduction_savings: float
    license_consolidation_savings: float
    total_annual_benefit: float
    payback_months: float


@dataclass
class ROMSummary:
    development_weeks: float
    infrastructure_cost: float
    licensing_cost: float
    support_cost_annual: float
    total_implementation_cost: float
    total_3yr_tco: float
    net_3yr_roi_pct: float
