"""
SMART INTAKE - Interactive CLI Session
========================================
Run this to walk through the Smart Intake questionnaire interactively.

  python3 -m smart_intake.intake_session

Features:
  - Progressive disclosure (starts with 8 Qs, unlocks more as you answer)
  - Conditional questions appear automatically (GDPR, SOX, GxP, HIPAA)
  - Multi-select with numbered menu
  - Auto-fill calculated fields shown inline
  - LLM follow-up questions (requires ANTHROPIC_API_KEY env var)
  - Skip optional questions with Enter
  - Type 'back' to re-answer previous question
  - Type 'status' to see progress + compliance flags
  - Type 'summary' to see ROI/ROM at any point
  - Type 'quit' to save and exit
"""

import os
import sys
import textwrap
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from smart_intake.questions import ALL_QUESTIONS, QUESTION_MAP
from smart_intake.models import QuestionType, Phase
from smart_intake.conditional_engine import (
    get_visible_questions,
    detect_compliance_flags,
    auto_fill_values,
    validate_answer,
)

# ─────────────────────────────────────────────
# TERMINAL COLOURS
# ─────────────────────────────────────────────

def _c(text: str, code: str) -> str:
    """Wrap text in ANSI colour code."""
    codes = {
        "cyan":    "\033[96m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "red":     "\033[91m",
        "bold":    "\033[1m",
        "dim":     "\033[2m",
        "blue":    "\033[94m",
        "magenta": "\033[95m",
        "reset":   "\033[0m",
    }
    return f"{codes.get(code,'')}{text}{codes['reset']}"


def _banner(title: str, colour: str = "cyan"):
    width = 62
    print()
    print(_c("═" * width, colour))
    print(_c(f"  {title}", colour))
    print(_c("═" * width, colour))


def _wrap(text: str, indent: int = 4) -> str:
    return textwrap.fill(text, width=76, initial_indent=" " * indent,
                         subsequent_indent=" " * indent)


# ─────────────────────────────────────────────
# PHASE METADATA
# ─────────────────────────────────────────────

PHASE_LABELS = {
    Phase.P1_PROJECT_CONTEXT:     ("1", "Project Context",          "cyan"),
    Phase.P2_DATA_REQUIREMENTS:   ("2", "Data Requirements",         "blue"),
    Phase.P3_SECURITY_COMPLIANCE: ("3", "Security & Compliance",     "yellow"),
    Phase.P4_VISUALIZATION:       ("4", "Visualization & Technical", "magenta"),
    Phase.P5_ROI:                 ("5", "ROI Assessment",            "green"),
    Phase.P6_ROM:                 ("6", "ROM Estimation",            "dim"),
}


# ─────────────────────────────────────────────
# INPUT HELPERS
# ─────────────────────────────────────────────

def _input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "quit"


def _ask_text(q) -> Optional[str]:
    val = _input(_c("  > ", "green"))
    if val.lower() in ("quit", "back", "status", "summary", "skip"):
        return val.lower()
    if val == "" and not q.validation.required:
        return None
    return val


def _ask_single(q) -> Optional[Any]:
    """Numbered single-select menu."""
    opts = q.options or []
    for i, opt in enumerate(opts, 1):
        print(f"    {_c(str(i), 'yellow')}.  {opt}")
    while True:
        raw = _input(_c(f"  Enter number (1–{len(opts)}): ", "green"))
        if raw.lower() in ("quit", "back", "status", "summary", "skip"):
            return raw.lower()
        if raw == "" and not q.validation.required:
            return None
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(opts):
                return opts[idx]
        except ValueError:
            pass
        print(_c(f"    Please enter a number between 1 and {len(opts)}.", "red"))


def _ask_multi(q) -> Optional[Any]:
    """Numbered multi-select menu."""
    opts = q.options or []
    for i, opt in enumerate(opts, 1):
        print(f"    {_c(str(i), 'yellow')}.  {opt}")
    print(_c("    Enter numbers separated by commas (e.g. 1,3,5):", "dim"))
    while True:
        raw = _input(_c("  > ", "green"))
        if raw.lower() in ("quit", "back", "status", "summary", "skip"):
            return raw.lower()
        if raw == "" and not q.validation.required:
            return None
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            selected = [opts[i] for i in indices if 0 <= i < len(opts)]
            if selected:
                return selected
        except (ValueError, IndexError):
            pass
        print(_c(f"    Invalid selection. Use numbers 1–{len(opts)} separated by commas.", "red"))


def _ask_number(q) -> Optional[Any]:
    rule = q.validation
    hint = ""
    if rule.min_value is not None and rule.max_value is not None:
        hint = f" ({rule.min_value}–{rule.max_value})"
    elif rule.min_value is not None:
        hint = f" (min {rule.min_value})"
    while True:
        raw = _input(_c(f"  Enter number{hint}: ", "green"))
        if raw.lower() in ("quit", "back", "status", "summary", "skip"):
            return raw.lower()
        if raw == "" and not rule.required:
            return None
        try:
            val = float(raw)
            err = validate_answer(q.id, val)
            if err:
                print(_c(f"    {err}", "red"))
            else:
                return val
        except ValueError:
            print(_c("    Please enter a valid number.", "red"))


def _ask_currency(q) -> Optional[Any]:
    rule = q.validation
    while True:
        raw = _input(_c("  $ ", "green"))
        if raw.lower() in ("quit", "back", "status", "summary", "skip"):
            return raw.lower()
        raw = raw.replace(",", "").replace("$", "")
        if raw == "" and not rule.required:
            return None
        try:
            val = float(raw)
            err = validate_answer(q.id, val)
            if err:
                print(_c(f"    {err}", "red"))
            else:
                return val
        except ValueError:
            print(_c("    Please enter a valid dollar amount.", "red"))


def _ask_percentage(q) -> Optional[Any]:
    rule = q.validation
    while True:
        raw = _input(_c("  % ", "green"))
        if raw.lower() in ("quit", "back", "status", "summary", "skip"):
            return raw.lower()
        raw = raw.replace("%", "")
        if raw == "" and not rule.required:
            return None
        try:
            val = float(raw)
            err = validate_answer(q.id, val)
            if err:
                print(_c(f"    {err}", "red"))
            else:
                return val
        except ValueError:
            print(_c("    Please enter a percentage (0–100).", "red"))


def _ask_textarea(q) -> Optional[str]:
    print(_c("  (Press Enter twice to finish)", "dim"))
    lines = []
    while True:
        try:
            line = input("  | ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.lower() in ("quit", "back", "status", "summary"):
            return line.lower()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if not text and not q.validation.required:
        return None
    return text or None


# ─────────────────────────────────────────────
# QUESTION RENDERER
# ─────────────────────────────────────────────

def _render_question(q, index: int, total: int, answers: Dict, dynamic_qs: List):
    """Prints the full question block."""
    num, label, colour = PHASE_LABELS.get(q.phase, ("?", "Unknown", "dim"))

    # Phase badge + progress
    phase_tag = _c(f" Phase {num}: {label} ", colour)
    progress = _c(f"[{index}/{total}]", "dim")
    print()
    print(f"  {phase_tag}  {progress}")

    # Compliance badge if this question is compliance-related
    compliance_tags = [t for t in q.tags if t in ("gdpr", "sox", "gxp", "hipaa")]
    if compliance_tags:
        badges = " ".join(_c(f"[{t.upper()}]", "yellow") for t in compliance_tags)
        print(f"  {badges}")

    # Required marker
    req_marker = _c(" *required", "red") if q.validation.required else _c(" optional", "dim")

    # Question text
    print()
    print(_wrap(_c(f"{q.id}. {q.text}", "bold"), indent=2))
    print(req_marker)

    # Help text
    if q.help_text:
        print(_wrap(q.help_text, indent=4))

    # Auto-fill hint
    if q.auto_fill:
        fills = auto_fill_values(answers)
        if q.id in fills:
            val = fills[q.id]
            if isinstance(val, float):
                formatted = f"{val:,.1f}" if q.type == QuestionType.PERCENTAGE else f"${val:,.0f}"
            else:
                formatted = str(val)
            print(_c(f"    Auto-calculated: {formatted}  (press Enter to accept)", "green"))

    print()


# ─────────────────────────────────────────────
# LLM FOLLOW-UP GENERATOR
# ─────────────────────────────────────────────

def _try_llm_followup(q_id: str, answer: Any, answers: Dict) -> List:
    """Attempts LLM follow-up generation. Returns [] silently if unavailable."""
    try:
        from smart_intake.llm_followup import FOLLOWUP_TRIGGERS
        if q_id not in FOLLOWUP_TRIGGERS:
            return []
        print(_c("\n  Generating follow-up questions...", "dim"))
        trigger = FOLLOWUP_TRIGGERS[q_id]
        followups = trigger(answer, answers)
        return followups
    except RuntimeError as e:
        if "ANTHROPIC_API_KEY" in str(e) or "not installed" in str(e):
            return []
        print(_c(f"  [LLM unavailable: {e}]", "dim"))
        return []
    except Exception:
        return []


def _ask_dynamic_question(dq) -> Optional[Any]:
    """Asks a dynamically generated LLM question."""
    print()
    print(_c(f"  {dq.id} (follow-up). {dq.text}", "bold"))
    if dq.help_text:
        print(_wrap(dq.help_text, indent=4))
    req = _c(" *required", "red") if dq.required else _c(" optional", "dim")
    print(req)
    print()

    if dq.options:
        for i, opt in enumerate(dq.options, 1):
            print(f"    {_c(str(i), 'yellow')}.  {opt}")

        if dq.type in ("single_select", "multi_select"):
            is_multi = dq.type == "multi_select"
            prompt = f"  Enter number(s): " if is_multi else f"  Enter number: "
            while True:
                raw = _input(_c(prompt, "green"))
                if raw.lower() in ("quit", "back", "status", "summary", "skip"):
                    return None
                if raw == "":
                    return None
                try:
                    if is_multi:
                        indices = [int(x.strip()) - 1 for x in raw.split(",")]
                        return [dq.options[i] for i in indices if 0 <= i < len(dq.options)]
                    else:
                        idx = int(raw) - 1
                        if 0 <= idx < len(dq.options):
                            return dq.options[idx]
                except (ValueError, IndexError):
                    pass
                print(_c("    Invalid selection.", "red"))

    raw = _input(_c("  > ", "green"))
    if raw.lower() in ("quit", "back", "status", "summary", "skip", ""):
        return None
    return raw


# ─────────────────────────────────────────────
# STATUS / SUMMARY DISPLAY
# ─────────────────────────────────────────────

def _show_status(answers: Dict):
    _banner("CURRENT STATUS", "cyan")
    flags = detect_compliance_flags(answers)
    answered = [k for k, v in answers.items() if v not in (None, "", [])]
    visible = get_visible_questions(answers)

    print(f"  Questions answered : {_c(str(len(answered)), 'green')}")
    print(f"  Questions visible  : {_c(str(len(visible)), 'cyan')}")

    if flags:
        flag_str = "  ".join(_c(f.value, "yellow") for f in flags)
        print(f"  Compliance flags   : {flag_str}")
    else:
        print(f"  Compliance flags   : {_c('None triggered yet', 'dim')}")

    # Per-phase progress
    print()
    print("  Phase Progress:")
    for phase, (num, label, colour) in PHASE_LABELS.items():
        phase_qs = [q for q in ALL_QUESTIONS if q.phase == phase and q.id in visible]
        done = [q for q in phase_qs if answers.get(q.id) not in (None, "", [])]
        bar_len = 20
        filled = int(bar_len * len(done) / len(phase_qs)) if phase_qs else 0
        bar = _c("█" * filled, colour) + _c("░" * (bar_len - filled), "dim")
        pct = f"{round(len(done)/len(phase_qs)*100)}%" if phase_qs else "0%"
        print(f"    Phase {num}  {bar}  {pct:>4}  {label}")


def _show_summary(answers: Dict):
    _banner("ROI & ROM SUMMARY", "green")
    fills = auto_fill_values(answers)

    # ROI
    fte = float(answers.get("Q25", 0))
    rate = float(answers.get("Q26", 0))
    hrs = float(answers.get("Q27", 0))
    pct = float(answers.get("Q28", 0)) / 100
    labor = fte * rate * hrs * 52 * pct
    errors = float(answers.get("Q30", 0)) * (float(answers.get("Q31", 0) or 0) / 100)
    licenses = float(answers.get("Q33", 0))
    revenue = float(answers.get("Q29b", 0))
    total_benefit = labor + errors + licenses + revenue

    print(_c("  ROI INPUTS", "green"))
    print(f"    FTEs affected        : {fte}")
    print(f"    Hourly rate          : ${rate:,.0f}")
    print(f"    Hours/week saved     : {hrs * pct:.1f} hrs")
    print(f"    Annual labor savings : {_c(f'${labor:,.0f}', 'green')}")
    if errors:
        print(f"    Error cost savings   : {_c(f'${errors:,.0f}', 'green')}")
    if licenses:
        print(f"    License savings      : {_c(f'${licenses:,.0f}', 'green')}")
    if revenue:
        print(f"    Revenue uplift       : {_c(f'${revenue:,.0f}', 'green')}")
    print(f"    Total annual benefit : {_c(f'${total_benefit:,.0f}', 'bold')}")

    # ROM
    print()
    print(_c("  ROM ESTIMATES (auto-calculated)", "cyan"))
    infra = fills.get("Q34", answers.get("Q34", 0))
    dev_wks = fills.get("Q35", answers.get("Q35", 0))
    impl = fills.get("Q39", 0)
    tco = fills.get("Q40", 0)
    roi_pct = fills.get("Q41", 0)

    if infra:
        print(f"    Monthly infra cost   : ${float(infra):,.0f}")
    if dev_wks:
        print(f"    Dev effort           : {dev_wks:.0f} weeks")
    if impl:
        print(f"    Implementation cost  : {_c(f'${impl:,.0f}', 'cyan')}")
    if tco:
        print(f"    3-year TCO           : {_c(f'${tco:,.0f}', 'cyan')}")
    if roi_pct:
        colour = "green" if roi_pct > 0 else "red"
        print(f"    Net 3-yr ROI         : {_c(f'{roi_pct:.1f}%', colour)}")


# ─────────────────────────────────────────────
# SAVE SESSION (to SQLite)
# ─────────────────────────────────────────────

def _save_session(session_id: str, user_id: str, project_name: str,
                  answers: Dict, current_phase: Phase):
    try:
        from smart_intake import cosmos_store
        session = cosmos_store.get_session(session_id, user_id)
        if session is None:
            session = cosmos_store.create_session(user_id, project_name)
            session.session_id = session_id
        session.answers = answers
        session.current_phase = current_phase
        session.compliance_flags = detect_compliance_flags(answers)
        if project_name:
            session.project_name = project_name
        cosmos_store.save_session(session)
        print(_c(f"\n  Session saved (ID: {session_id[:8]}...)", "dim"))
    except Exception as e:
        print(_c(f"\n  Auto-save skipped: {e}", "dim"))


# ─────────────────────────────────────────────
# MAIN INTAKE LOOP
# ─────────────────────────────────────────────

def run_intake():
    """Interactive intake session loop."""

    # ── Welcome banner ──
    os.system("clear" if os.name == "posix" else "cls")
    print()
    print(_c("╔══════════════════════════════════════════════════════════╗", "cyan"))
    print(_c("║       SMART INTAKE — Data Engineering Questionnaire      ║", "cyan"))
    print(_c("║  Answer questions to generate your ROI/ROM estimate       ║", "dim"))
    print(_c("╚══════════════════════════════════════════════════════════╝", "cyan"))
    print()
    print(_c("  Commands you can type at any time:", "dim"))
    print(_c("    'skip'    → skip optional question", "dim"))
    print(_c("    'back'    → re-answer previous question", "dim"))
    print(_c("    'status'  → show progress + compliance flags", "dim"))
    print(_c("    'summary' → show ROI/ROM summary so far", "dim"))
    print(_c("    'quit'    → save and exit", "dim"))
    print()

    # ── Session setup ──
    session_id = str(uuid.uuid4())
    user_id = _input(_c("  Your name / email: ", "cyan")) or "user"
    project_name = _input(_c("  Project name (optional): ", "cyan")) or "Untitled"

    answers: Dict[str, Any] = {}
    dynamic_answers: Dict[str, Any] = {}  # LLM-generated Q answers stored separately
    answered_order: List[str] = []        # for 'back' navigation
    current_phase = Phase.P1_PROJECT_CONTEXT
    auto_saved_at = datetime.now()

    print()
    print(_c(f"  Starting intake for: {project_name}", "green"))
    print(_c("  (8 questions shown first — more unlock as you answer)", "dim"))

    # ── Question loop ──
    idx = 0
    while True:
        # Recompute visible questions each iteration (answers change visibility)
        visible_ids = get_visible_questions(answers)

        # Auto-fill calculated fields silently
        fills = auto_fill_values(answers)
        for fid, fval in fills.items():
            q = QUESTION_MAP.get(fid)
            if q and q.type == QuestionType.CALCULATED:
                answers[fid] = fval

        if idx >= len(visible_ids):
            break  # all visible questions answered

        q_id = visible_ids[idx]
        q = QUESTION_MAP.get(q_id)
        if not q:
            idx += 1
            continue

        # Skip already-answered calculated questions
        if q.type == QuestionType.CALCULATED:
            idx += 1
            continue

        # Track current phase for save
        current_phase = q.phase

        # Auto-save every 60 seconds
        if (datetime.now() - auto_saved_at).seconds >= 60:
            _save_session(session_id, user_id, project_name, answers, current_phase)
            auto_saved_at = datetime.now()

        # Render question
        _render_question(q, idx + 1, len(visible_ids), answers, [])

        # Get existing answer for re-display
        existing = answers.get(q_id)
        if existing not in (None, "", []):
            print(_c(f"    Current answer: {existing}  (Enter to keep)", "dim"))

        # ── Type-specific input ──
        if q.type == QuestionType.FILE_UPLOAD:
            print(_c("    [File upload — enter filename or path, or skip]", "dim"))
            val = _input(_c("  > ", "green"))
            if val.lower() in ("quit", "back", "status", "summary", "skip"):
                pass
            elif val:
                answers[q_id] = val
                answered_order.append(q_id)
                idx += 1
            else:
                idx += 1
            continue

        if q.type == QuestionType.SINGLE:
            val = _ask_single(q)
        elif q.type == QuestionType.MULTI:
            val = _ask_multi(q)
        elif q.type == QuestionType.NUMBER:
            val = _ask_number(q)
        elif q.type == QuestionType.CURRENCY:
            val = _ask_currency(q)
        elif q.type == QuestionType.PERCENTAGE:
            val = _ask_percentage(q)
        elif q.type == QuestionType.TEXTAREA:
            val = _ask_textarea(q)
        else:
            val = _ask_text(q)

        # ── Handle control commands ──
        if val == "quit":
            _save_session(session_id, user_id, project_name, answers, current_phase)
            _show_summary(answers)
            print(_c("\n  Session saved. Goodbye!\n", "cyan"))
            return

        if val == "back":
            if answered_order:
                prev_id = answered_order.pop()
                # Remove answer to force re-ask
                answers.pop(prev_id, None)
                idx = visible_ids.index(prev_id) if prev_id in visible_ids else max(0, idx - 1)
            else:
                print(_c("  Already at the first question.", "dim"))
            continue

        if val == "status":
            _show_status(answers)
            continue

        if val == "summary":
            _show_summary(answers)
            continue

        if val == "skip":
            if q.validation.required:
                print(_c("  This question is required and cannot be skipped.", "red"))
                continue
            idx += 1
            continue

        # ── Validate & store ──
        if val is None and existing not in (None, "", []):
            # User pressed Enter with existing answer — keep it
            idx += 1
            continue

        if val is None and q.validation.required:
            print(_c("  This question is required.", "red"))
            continue

        # Accept auto-fill if user pressed Enter on a pre-filled field
        if val is None and q.id in fills:
            answers[q_id] = fills[q_id]
            answered_order.append(q_id)
            idx += 1
            continue

        error = validate_answer(q_id, val)
        if error and val is not None:
            print(_c(f"  {error}", "red"))
            continue

        # ── Save answer ──
        answers[q_id] = val
        answered_order.append(q_id)

        # ── Compliance flag notification ──
        flags = detect_compliance_flags(answers)
        if flags:
            flag_names = [f.value for f in flags]
            new_flags = [f for f in flag_names
                         if f not in [fl.value for fl in detect_compliance_flags(
                             {k: v for k, v in answers.items() if k != q_id}
                         )]]
            if new_flags:
                print()
                for f in new_flags:
                    msg = {
                        "GDPR":  "GDPR compliance questions will be added.",
                        "SOX":   "SOX audit trail questions will be added.",
                        "GxP":   "GxP / 21 CFR Part 11 questions will be added.",
                        "HIPAA": "HIPAA / PHI questions will be added.",
                    }.get(f, f"{f} questions will be added.")
                    print(_c(f"  [{f}] {msg}", "yellow"))

        # ── LLM Follow-up trigger ──
        if q.is_llm_followup_trigger and val:
            followups = _try_llm_followup(q_id, val, answers)
            if followups:
                print()
                print(_c(f"  {len(followups)} follow-up question(s) generated:", "magenta"))
                for fq in followups:
                    fval = _ask_dynamic_question(fq)
                    if fval not in (None, ""):
                        dynamic_answers[fq.id] = fval

        idx += 1

    # ── Completion ──
    _banner("INTAKE COMPLETE", "green")
    _save_session(session_id, user_id, project_name, answers, current_phase)

    filled_answers = {k: v for k, v in answers.items() if v not in (None, "", [])}
    total_visible = len(get_visible_questions(answers))
    print(f"\n  Answered  : {_c(str(len(filled_answers)), 'green')} / {total_visible} questions")
    print(f"  Session ID: {_c(session_id[:16] + '...', 'dim')}")

    _show_status(answers)
    print()
    _show_summary(answers)

    # ── Export summary ──
    print()
    export = _input(_c("  Export answers to JSON? (y/n): ", "cyan"))
    if export.lower() == "y":
        import json
        out = {
            "session_id": session_id,
            "user_id": user_id,
            "project_name": project_name,
            "answers": {**answers, **dynamic_answers},
            "compliance_flags": [f.value for f in detect_compliance_flags(answers)],
            "roi_rom": auto_fill_values(answers),
            "exported_at": datetime.now().isoformat()
        }
        fname = f"intake_{session_id[:8]}.json"
        with open(fname, "w") as f:
            json.dump(out, f, indent=2)
        print(_c(f"  Saved to {fname}", "green"))

    print()
    print(_c("  Thank you! Your intake is complete.", "cyan"))
    print()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    run_intake()
