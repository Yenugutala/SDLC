"""
SMART INTAKE - LLM Follow-up Question Generator
=================================================
When should LLM be called?
  ✅ Q3  → Region answer → check if new compliance considerations apply
  ✅ Q11 → KPI description → generate metric-specific sub-questions
  ✅ Q24 → Manual process description → generate ROI sub-questions
  ✅ After Phase 3 → generate domain-specific data governance questions

When NOT to use LLM:
  ❌ Static conditional logic (GDPR/SOX/GxP) — use conditional_engine.py
  ❌ Auto-fill calculations — use conditional_engine.auto_fill_values()
  ❌ Validation — deterministic rules only

LLM is called ONLY for open-ended, context-aware clarification.
This keeps cost low and response times fast.

Flow:
  UI answer submitted → DE API → trigger check → LLM call (if triggered)
  → returns list[DynamicQuestion] → UI appends below parent question
"""

import json
from typing import Any, Dict, List, Optional
from smart_intake.models import QuestionType


# ─────────────────────────────────────────────
# DYNAMIC QUESTION (returned by LLM)
# ─────────────────────────────────────────────

class DynamicQuestion:
    """A question generated at runtime by the LLM."""

    def __init__(
        self,
        id: str,
        parent_id: str,
        text: str,
        help_text: str,
        q_type: str,
        options: Optional[List[str]] = None,
        required: bool = False
    ):
        self.id = id
        self.parent_id = parent_id
        self.text = text
        self.help_text = help_text
        self.type = q_type
        self.options = options or []
        self.required = required
        self.is_dynamic = True

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "text": self.text,
            "help_text": self.help_text,
            "type": self.type,
            "options": self.options,
            "required": self.required,
            "is_dynamic": True
        }


# ─────────────────────────────────────────────
# PROMPT TEMPLATES (DE-owned, versioned)
# ─────────────────────────────────────────────

PROMPT_TEMPLATES: Dict[str, str] = {

    "Q11_kpi_followup": """
You are a data engineering intake specialist.
A business user described their required KPIs as:
"{kpi_description}"

Their domain is: {domain}
Their data sources are: {sources}

Generate 3-5 targeted follow-up questions that clarify:
1. Calculation logic for each KPI (numerator, denominator, filters)
2. Required grain (daily/weekly/monthly? by department/region?)
3. Historical lookback period needed
4. Benchmark targets or SLA thresholds

Return a JSON array of questions with fields:
  id, text, help_text, type (text|number|single_select|multi_select), options (if applicable), required (bool)

Use IDs: Q11_f1, Q11_f2, Q11_f3, etc.
""",

    "Q24_roi_followup": """
You are a business analyst specializing in ROI assessment.
A stakeholder described their manual process as:
"{manual_process}"

Their domain is: {domain}
Their primary data sources: {sources}

Generate 4-6 targeted follow-up questions that help quantify ROI:
1. Specific bottleneck steps that take the most time
2. Frequency of errors and their downstream impact
3. Downstream systems or teams that depend on this process
4. Seasonal or cyclical patterns in workload
5. Any existing partial automation

Return JSON array with fields:
  id, text, help_text, type, options (if applicable), required (bool)

Use IDs: Q24_f1, Q24_f2, Q24_f3, etc.
""",

    "Q3_region_followup": """
You are a data governance specialist.
The user selected these operating regions: {regions}

Based on the selected regions beyond standard GDPR/SOX/GxP,
generate 2-3 region-specific compliance questions if relevant:
- PDPA (Thailand/Singapore)
- LGPD (Brazil)
- PIPEDA (Canada)
- CCPA (California)
- Data localization requirements (China, Russia)

Only generate questions if the selected regions actually require them.
Return JSON array with fields: id, text, help_text, type, options, required
Use IDs: Q3_f1, Q3_f2, etc. Return empty array [] if no additional questions needed.
""",

    "post_phase3_governance": """
You are a data governance architect reviewing intake answers.

Project answers so far:
- Domain: {domain}
- Regions: {regions}
- Compliance flags: {compliance_flags}
- Data volume: {volume}
- Data sources: {sources}

Generate 2-4 domain-specific data governance questions not already covered.
Focus on: data ownership, retention policy, access control model,
masking/tokenization requirements.

Return JSON array with: id, text, help_text, type, options, required
Use IDs: DG_f1, DG_f2, etc.
"""
}


# ─────────────────────────────────────────────
# LLM CALL (Anthropic Claude API)
# ─────────────────────────────────────────────

def _call_claude(prompt: str, model: str = "claude-sonnet-4-6") -> str:
    """
    Calls Claude API and returns raw text response.
    Requires ANTHROPIC_API_KEY in environment.
    """
    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")


def _parse_llm_questions(
    raw_text: str,
    parent_id: str
) -> List[DynamicQuestion]:
    """Extracts JSON array from LLM response and builds DynamicQuestion list."""
    # Strip markdown code fences if present
    text = raw_text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        data = json.loads(text.strip())
    except json.JSONDecodeError:
        # Try to extract JSON array with simple heuristic
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            return []

    questions = []
    for item in data:
        questions.append(DynamicQuestion(
            id=item.get("id", f"{parent_id}_fx"),
            parent_id=parent_id,
            text=item.get("text", ""),
            help_text=item.get("help_text", ""),
            q_type=item.get("type", "text"),
            options=item.get("options"),
            required=item.get("required", False)
        ))
    return questions


# ─────────────────────────────────────────────
# PUBLIC API — called by intake_engine.py
# ─────────────────────────────────────────────

def generate_kpi_followups(
    kpi_description: str,
    answers: Dict[str, Any]
) -> List[DynamicQuestion]:
    """Generates follow-up questions after Q11 (KPI description)."""
    prompt = PROMPT_TEMPLATES["Q11_kpi_followup"].format(
        kpi_description=kpi_description,
        domain=answers.get("Q4", "Unknown"),
        sources=", ".join(answers.get("Q6", []) or [])
    )
    raw = _call_claude(prompt)
    return _parse_llm_questions(raw, parent_id="Q11")


def generate_roi_followups(
    manual_process: str,
    answers: Dict[str, Any]
) -> List[DynamicQuestion]:
    """Generates follow-up questions after Q24 (manual process description)."""
    prompt = PROMPT_TEMPLATES["Q24_roi_followup"].format(
        manual_process=manual_process,
        domain=answers.get("Q4", "Unknown"),
        sources=", ".join(answers.get("Q6", []) or [])
    )
    raw = _call_claude(prompt)
    return _parse_llm_questions(raw, parent_id="Q24")


def generate_region_followups(
    regions: List[str],
    answers: Dict[str, Any]
) -> List[DynamicQuestion]:
    """Generates region-specific compliance follow-ups beyond GDPR."""
    non_standard = [r for r in regions if r not in ("EU", "UK", "North America")]
    if not non_standard:
        return []
    prompt = PROMPT_TEMPLATES["Q3_region_followup"].format(
        regions=", ".join(regions)
    )
    raw = _call_claude(prompt)
    return _parse_llm_questions(raw, parent_id="Q3")


def generate_governance_questions(answers: Dict[str, Any]) -> List[DynamicQuestion]:
    """Generates data governance questions after Phase 3 is complete."""
    from smart_intake.conditional_engine import detect_compliance_flags
    flags = detect_compliance_flags(answers)
    prompt = PROMPT_TEMPLATES["post_phase3_governance"].format(
        domain=answers.get("Q4", "Unknown"),
        regions=", ".join(answers.get("Q3", []) or []),
        compliance_flags=", ".join(f.value for f in flags),
        volume=answers.get("Q7", "Unknown"),
        sources=", ".join(answers.get("Q6", []) or [])
    )
    raw = _call_claude(prompt)
    return _parse_llm_questions(raw, parent_id="phase_3_end")


# ─────────────────────────────────────────────
# TRIGGER MAP (used by intake_engine)
# question_id → generator function
# ─────────────────────────────────────────────

FOLLOWUP_TRIGGERS: Dict[str, callable] = {
    "Q3":  lambda val, answers: generate_region_followups(
        val if isinstance(val, list) else [val], answers
    ),
    "Q11": lambda val, answers: generate_kpi_followups(val, answers),
    "Q24": lambda val, answers: generate_roi_followups(val, answers),
}
