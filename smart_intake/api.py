"""
SMART INTAKE - REST API (FastAPI)
===================================
This is the CONTRACT between DE backend and UI team.

All endpoints return JSON. UI team calls these from React/Angular frontend.

Endpoints:
  GET  /api/questions                     → full question catalog (all phases)
  GET  /api/questions/{phase}             → questions for a specific phase
  POST /api/evaluate                      → get visible questions + compliance flags
  POST /api/autosave                      → save answers to Cosmos DB
  POST /api/validate                      → validate all answers
  GET  /api/sessions/{user_id}/drafts     → list draft sessions
  POST /api/sessions                      → create new session
  GET  /api/sessions/{session_id}         → resume a session
  POST /api/sessions/{session_id}/submit  → submit final intake
  POST /api/followup/{question_id}        → generate LLM follow-up questions
  GET  /api/progress/{session_id}         → progress indicator data

Run:
  uvicorn smart_intake.api:app --reload --port 8000
"""

import dataclasses
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Provide stubs so the module can be imported without FastAPI for testing
    class FastAPI:
        def get(self, *a, **kw): return lambda f: f
        def post(self, *a, **kw): return lambda f: f
    class BaseModel: pass
    HTTPException = Exception
    BackgroundTasks = object
    CORSMiddleware = object

from smart_intake.questions import ALL_QUESTIONS, QUESTION_MAP, INITIAL_VISIBLE
from smart_intake.conditional_engine import (
    get_visible_questions, detect_compliance_flags,
    auto_fill_values, validate_all
)
from smart_intake.models import Phase


app = FastAPI(
    title="SMART INTAKE API",
    description="DE backend for the Smart Intake form system",
    version="1.0.0"
)

if FASTAPI_AVAILABLE:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten for production
        allow_methods=["*"],
        allow_headers=["*"]
    )


def _q_to_dict(q) -> Dict:
    """Converts Question dataclass to JSON-serializable dict."""
    d = dataclasses.asdict(q)
    d["phase"] = q.phase.value
    d["type"] = q.type.value
    return d


# ═══════════════════════════════════════════════════════════════
# PYDANTIC REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class EvaluateRequest(BaseModel):
    answers: Dict[str, Any]
    session_id: Optional[str] = None


class AutoSaveRequest(BaseModel):
    session_id: str
    user_id: str
    answers: Dict[str, Any]
    current_phase: str
    project_name: Optional[str] = None


class ValidateRequest(BaseModel):
    answers: Dict[str, Any]


class CreateSessionRequest(BaseModel):
    user_id: str
    project_name: str


class SubmitRequest(BaseModel):
    user_id: str


class FollowUpRequest(BaseModel):
    question_id: str
    answer_value: Any
    all_answers: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/questions")
def get_all_questions():
    """
    Returns full question catalog.
    UI uses this to pre-load all questions and manage show/hide locally.
    """
    return {
        "total": len(ALL_QUESTIONS),
        "initial_visible": INITIAL_VISIBLE,
        "questions": [_q_to_dict(q) for q in ALL_QUESTIONS]
    }


@app.get("/api/questions/{phase}")
def get_phase_questions(phase: str):
    """
    Returns questions for a specific phase.
    phase values: phase_1, phase_2, phase_3, phase_4, phase_5, phase_6
    """
    try:
        p = Phase(phase)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}. "
                            f"Valid: {[ph.value for ph in Phase]}")

    qs = [q for q in ALL_QUESTIONS if q.phase == p]
    return {
        "phase": phase,
        "count": len(qs),
        "questions": [_q_to_dict(q) for q in qs]
    }


@app.post("/api/evaluate")
def evaluate_conditions(req: EvaluateRequest):
    """
    KEY ENDPOINT — called by UI after every answer change.

    Returns:
      - visible_question_ids: which questions to show
      - compliance_flags: GDPR, SOX, GxP, HIPAA triggered
      - auto_fill: fields the UI should pre-populate
      - progress: per-phase completion percentage
    """
    answers = req.answers
    visible = get_visible_questions(answers)
    flags = detect_compliance_flags(answers)
    fills = auto_fill_values(answers)
    progress = _calc_progress(answers, visible)

    return {
        "visible_question_ids": visible,
        "compliance_flags": [f.value for f in flags],
        "auto_fill": fills,
        "progress": progress
    }


@app.post("/api/validate")
def validate_answers(req: ValidateRequest):
    """
    Returns all validation errors for current answers.
    UI calls this before allowing phase navigation.
    """
    errors = validate_all(req.answers)
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_count": len(errors)
    }


@app.post("/api/autosave")
def autosave(req: AutoSaveRequest, background_tasks: BackgroundTasks):
    """
    Auto-save endpoint — UI calls every 30 seconds.
    Returns updated_at timestamp.
    """
    from smart_intake import cosmos_store
    from smart_intake.models import Phase as PhaseEnum, ComplianceFlag

    session = cosmos_store.get_session(req.session_id, req.user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.answers = req.answers
    try:
        session.current_phase = PhaseEnum(req.current_phase)
    except ValueError:
        pass

    flags = detect_compliance_flags(req.answers)
    session.compliance_flags = flags

    if req.project_name:
        session.project_name = req.project_name

    saved = cosmos_store.save_session(session)
    return {
        "session_id": saved.session_id,
        "updated_at": saved.updated_at,
        "status": "saved"
    }


@app.post("/api/sessions")
def create_session(req: CreateSessionRequest):
    """Creates a new intake session. Returns session_id."""
    from smart_intake import cosmos_store
    session = cosmos_store.create_session(req.user_id, req.project_name)
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "status": session.status.value
    }


@app.get("/api/sessions/{user_id}/drafts")
def list_drafts(user_id: str):
    """Returns all draft sessions for a user (for the 'Resume Intake' screen)."""
    from smart_intake import cosmos_store
    drafts = cosmos_store.list_drafts(user_id)
    return {"user_id": user_id, "drafts": drafts, "count": len(drafts)}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str, user_id: str):
    """Loads a full session (for resume). user_id required as query param."""
    from smart_intake import cosmos_store
    session = cosmos_store.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    visible = get_visible_questions(session.answers)
    fills = auto_fill_values(session.answers)

    return {
        "session_id": session.session_id,
        "project_name": session.project_name,
        "status": session.status.value,
        "current_phase": session.current_phase.value,
        "answers": session.answers,
        "compliance_flags": [f.value for f in session.compliance_flags],
        "visible_question_ids": visible,
        "auto_fill": fills,
        "updated_at": session.updated_at
    }


@app.post("/api/sessions/{session_id}/submit")
def submit_session(session_id: str, req: SubmitRequest):
    """
    Submits the intake. Runs final validation first.
    Returns ROI and ROM summaries.
    """
    from smart_intake import cosmos_store
    session = cosmos_store.get_session(session_id, req.user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    errors = validate_all(session.answers)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Validation failed", "errors": errors}
        )

    fills = auto_fill_values(session.answers)
    session.roi_summary = {
        "annual_labor_savings": _calc_labor_savings(session.answers),
        "error_reduction_savings": float(session.answers.get("Q30", 0))
                                   * float(session.answers.get("Q31", 0) or 0) / 100,
        "license_savings": float(session.answers.get("Q33", 0)),
        "revenue_uplift": float(session.answers.get("Q29b", 0)),
    }
    session.roi_summary["total_annual_benefit"] = sum(session.roi_summary.values())

    session.rom_summary = {
        "total_implementation_cost": fills.get("Q39", 0),
        "tco_3yr": fills.get("Q40", 0),
        "net_roi_pct": fills.get("Q41", 0),
        "dev_weeks": fills.get("Q35", 0),
        "monthly_infra": fills.get("Q34", 0),
    }

    submitted = cosmos_store.submit_session(session_id, req.user_id)
    return {
        "session_id": submitted.session_id,
        "status": submitted.status.value,
        "roi_summary": submitted.roi_summary,
        "rom_summary": submitted.rom_summary
    }


@app.post("/api/followup/{question_id}")
def get_followup_questions(question_id: str, req: FollowUpRequest):
    """
    Calls LLM to generate context-aware follow-up questions.
    UI calls this after user answers a 'trigger' question.

    Trigger questions: Q3, Q11, Q24
    """
    from smart_intake.llm_followup import FOLLOWUP_TRIGGERS

    if question_id not in FOLLOWUP_TRIGGERS:
        return {"question_id": question_id, "followups": [], "message": "No follow-ups for this question"}

    try:
        generator = FOLLOWUP_TRIGGERS[question_id]
        followups = generator(req.answer_value, req.all_answers)
        return {
            "question_id": question_id,
            "followups": [fq.to_dict() for fq in followups],
            "count": len(followups)
        }
    except RuntimeError as e:
        # LLM unavailable — return empty (non-blocking)
        return {
            "question_id": question_id,
            "followups": [],
            "error": str(e)
        }


@app.get("/api/progress/{session_id}")
def get_progress(session_id: str, user_id: str):
    """Returns per-phase progress for the progress bar UI component."""
    from smart_intake import cosmos_store
    session = cosmos_store.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    visible = get_visible_questions(session.answers)
    return _calc_progress(session.answers, visible)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _calc_progress(answers: Dict, visible_ids: List[str]) -> Dict:
    """Calculates per-phase completion %."""
    phase_stats = {}
    for phase in Phase:
        phase_qs = [q for q in ALL_QUESTIONS if q.phase == phase and q.id in visible_ids]
        answered = [q for q in phase_qs if q.id in answers and answers[q.id] not in (None, "", [])]
        pct = round(len(answered) / len(phase_qs) * 100) if phase_qs else 0
        phase_stats[phase.value] = {
            "total": len(phase_qs),
            "answered": len(answered),
            "pct": pct
        }
    total_visible = len(visible_ids)
    total_answered = sum(1 for qid in visible_ids if qid in answers and answers[qid] not in (None, "", []))
    phase_stats["overall"] = {
        "total": total_visible,
        "answered": total_answered,
        "pct": round(total_answered / total_visible * 100) if total_visible else 0
    }
    return phase_stats


def _calc_labor_savings(answers: Dict) -> float:
    return (
        float(answers.get("Q25", 0)) *
        float(answers.get("Q26", 75)) *
        float(answers.get("Q27", 0)) *
        52 *
        float(answers.get("Q28", 0)) / 100
    )


# ─────────────────────────────────────────────
# DEV SERVER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("smart_intake.api:app", host="0.0.0.0", port=8000, reload=True)
