"""
SMART INTAKE - Demo / Smoke Test
==================================
Run this to verify the DE backend works end-to-end WITHOUT a live API server.
Tests: question bank, conditional engine, auto-fill, validation, progress calc.

Usage:
  python -m smart_intake.demo
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from smart_intake.questions import ALL_QUESTIONS, INITIAL_VISIBLE, QUESTION_MAP
from smart_intake.conditional_engine import (
    detect_compliance_flags, get_visible_questions,
    auto_fill_values, validate_all
)


def separator(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print('═'*60)


def demo_question_catalog():
    separator("QUESTION CATALOG SUMMARY")
    from collections import Counter
    phase_counts = Counter(q.phase.value for q in ALL_QUESTIONS)
    for phase, count in sorted(phase_counts.items()):
        print(f"  {phase}: {count} questions")
    print(f"\n  Total questions : {len(ALL_QUESTIONS)}")
    print(f"  Initially shown : {len(INITIAL_VISIBLE)} (Q1–Q8)")
    print(f"  Conditional     : {sum(1 for q in ALL_QUESTIONS if q.conditional)}")
    print(f"  Auto-calculated : {sum(1 for q in ALL_QUESTIONS if q.auto_fill)}")
    print(f"  LLM triggers    : {sum(1 for q in ALL_QUESTIONS if q.is_llm_followup_trigger)}")


def demo_compliance_detection():
    separator("COMPLIANCE FLAG DETECTION")

    scenarios = [
        {"name": "EU Healthcare", "Q3": ["EU"], "Q4": "Healthcare / Clinical"},
        {"name": "US Finance",    "Q3": ["North America"], "Q4": "Finance / Accounting"},
        {"name": "UK Life Sci",   "Q3": ["UK"], "Q4": "Life Sciences / Pharma"},
        {"name": "APAC Only",     "Q3": ["APAC"], "Q4": "Operations / Manufacturing"},
        {"name": "Global Finance","Q3": ["EU","North America","APAC"], "Q4": "Finance / Accounting"},
    ]

    for s in scenarios:
        answers = {"Q3": s["Q3"], "Q4": s["Q4"]}
        flags = detect_compliance_flags(answers)
        flag_names = [f.value for f in flags] if flags else ["None"]
        print(f"  {s['name']:<22} → {', '.join(flag_names)}")


def demo_visibility_engine():
    separator("CONDITIONAL VISIBILITY")

    base_answers = {}
    visible_base = get_visible_questions(base_answers)
    print(f"  No answers yet → {len(visible_base)} questions visible")

    eu_healthcare = {
        "Q3": ["EU"],
        "Q4": "Healthcare / Clinical",
        "Q12a": "Yes"
    }
    visible_eu = get_visible_questions(eu_healthcare)
    print(f"  EU + Healthcare + PHI=Yes → {len(visible_eu)} questions visible")
    new_qs = [qid for qid in visible_eu if qid not in visible_base]
    print(f"  Newly unlocked: {new_qs}")

    finance_answers = {"Q3": ["North America"], "Q4": "Finance / Accounting", "Q13a": "Yes"}
    visible_fin = get_visible_questions(finance_answers)
    fin_new = [qid for qid in visible_fin if qid not in visible_base]
    print(f"\n  Finance + SOX=Yes → new questions: {fin_new}")


def demo_autofill():
    separator("AUTO-FILL CALCULATIONS")

    answers = {
        "Q3": ["EU"],
        "Q4": "Healthcare / Clinical",
        "Q7": "10–100 GB / day",
        "Q9": 15,
        "Q10": ["Missing / null values", "Duplicate records"],
        "Q12a": "Yes",
        "Q21": "Azure Databricks",
        "Q25": 5,
        "Q26": 85,
        "Q27": 20,
        "Q28": 70,
        "Q30": 50000,
        "Q31": 60,
        "Q33": 25000,
        "Q36": 125,
        "Q37": 30000,
        "Q38": 18
    }

    fills = auto_fill_values(answers)

    labels = {
        "Q34": "Monthly infrastructure cost",
        "Q35": "Dev effort (weeks)",
        "Q39": "Total implementation cost",
        "Q40": "3-year TCO",
        "Q41": "Net 3-year ROI %"
    }

    for qid, label in labels.items():
        val = fills.get(qid, "N/A")
        unit = "%" if qid == "Q41" else ("wks" if qid == "Q35" else "$")
        print(f"  {label:<35} {unit}{val:,.0f}" if isinstance(val, float) else f"  {label:<35} {val}")


def demo_validation():
    separator("VALIDATION ENGINE")

    bad_answers = {
        "Q1": "",                # required, too short
        "Q7": "10–100 GB / day",
        "Q25": -5,               # below min
        "Q26": 1000,             # above max
        "Q28": 110,              # % > 100
    }
    errors = validate_all(bad_answers)
    print(f"  Errors found: {len(errors)}")
    for qid, msg in errors.items():
        print(f"    {qid}: {msg}")

    good_answers = {
        "Q1": "Patient 360 Analytics",
        "Q2": "Dr. Jane Smith",
        "Q3": ["EU"],
        "Q4": "Healthcare / Clinical",
        "Q5": "2025-09-01",
        "Q6": ["Epic EHR"],
        "Q7": "10–100 GB / day",
        "Q8": "Daily (batch)",
        "Q9": 12,
        "Q10": ["Missing / null values"],
        "Q16": "Restricted / Highly Sensitive",
        "Q17": ["Power BI"],
        "Q21": "Azure Databricks",
        "Q22": "GitHub (Cloud)",
        "Q24": "Currently 3 analysts manually pull Epic reports every Monday, "
               "spending 15 hours each to build a weekly patient census dashboard.",
        "Q25": 3,
        "Q26": 85,
        "Q27": 15,
        "Q28": 75,
        "Q29": "No",
        "Q30": 0,
        "Q32": "No",
        "Q36": 125,
        "Q38": 18
    }
    good_errors = validate_all(good_answers)
    print(f"\n  Well-formed answers → errors: {len(good_errors)}")
    if good_errors:
        for qid, msg in good_errors.items():
            print(f"    {qid}: {msg}")
    else:
        print("  All valid!")


def demo_phase_summary():
    separator("PHASE NAVIGATION SUMMARY (for UI progress bar)")

    phases_info = [
        ("phase_1", "Project Context",         "Q1–Q5",   "Always shown"),
        ("phase_2", "Data Requirements",        "Q6–Q11",  "Always shown"),
        ("phase_3", "Security & Compliance",    "Q12–Q16", "Conditional (GDPR/SOX/GxP/HIPAA)"),
        ("phase_4", "Visualization & Technical","Q17–Q23", "Always shown"),
        ("phase_5", "ROI Assessment",           "Q24–Q33", "Always shown"),
        ("phase_6", "ROM Estimation",           "Q34–Q41", "Auto-calculated + manual inputs"),
    ]

    print(f"\n  {'Phase':<10} {'Name':<30} {'Qs':<12} {'Notes'}")
    print(f"  {'-'*9} {'-'*29} {'-'*11} {'-'*35}")
    for pid, name, qs, notes in phases_info:
        print(f"  {pid:<10} {name:<30} {qs:<12} {notes}")


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("  SMART INTAKE — DE Backend Demo")
    print("█"*60)

    demo_question_catalog()
    demo_compliance_detection()
    demo_visibility_engine()
    demo_autofill()
    demo_validation()
    demo_phase_summary()

    print("\n" + "✓"*60)
    print("  All demos completed successfully.")
    print("✓"*60 + "\n")
