"""
SMART INTAKE - Data Pipeline Score (DPS) Engine
=================================================
DPS = composite readiness / complexity score (0–100) derived from intake answers.

Dimensions (weighted):
  1. Data Readiness      (25%) — source quality, known issues, format
  2. Complexity          (25%) — entity count, volume, sources count, streaming
  3. Compliance Burden   (20%) — active compliance flags
  4. ROI Confidence      (15%) — how much ROI data the user provided
  5. Stakeholder Clarity (15%) — project scope, KPIs, executive sponsor

Score interpretation:
  90–100  Exceptional — proceed to build immediately
  75–89   Good — minor gaps, low risk
  60–74   Moderate — address data quality / compliance gaps first
  40–59   Needs Work — significant unknowns, risk of scope creep
  0–39    High Risk — recommend discovery sprint before build

Output includes:
  - overall_score (0–100)
  - dimension_scores {name: score}
  - risk_flags [str]
  - recommendations [str]
  - confidence_band ("High" | "Medium" | "Low")
"""

from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
# DIMENSION SCORERS
# ─────────────────────────────────────────────

def _score_data_readiness(answers: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    Score: how well understood and clean is the source data?
    Max: 25 points
    """
    score = 25.0
    risks = []
    recs = []

    # Q10: Known data quality issues
    dq_issues = answers.get("Q10", [])
    if isinstance(dq_issues, str):
        dq_issues = [dq_issues]
    bad_issues = [i for i in dq_issues if i != "No known issues"]
    if len(bad_issues) >= 3:
        score -= 10
        risks.append("3+ data quality issues identified (nulls, duplication, schema drift)")
        recs.append("Run a data profiling sprint before pipeline build to quantify DQ issues")
    elif len(bad_issues) >= 1:
        score -= 4 * len(bad_issues)
        recs.append(f"Address {len(bad_issues)} known DQ issue(s) in Silver layer cleansing")

    # Q6: Source systems — flat files are harder
    sources = answers.get("Q6", [])
    if isinstance(sources, str):
        sources = [sources]
    if "Flat Files / CSV" in sources:
        score -= 3
        risks.append("Flat file ingestion has schema instability risk")
        recs.append("Enforce schema contracts on flat file ingestion with Great Expectations")
    if "REST API" in sources:
        score -= 2
        recs.append("REST API pagination and rate limits require retry/backoff logic")

    # Q7: Volume — higher volume = higher complexity penalty
    volume = answers.get("Q7", "")
    vol_penalty = {
        "< 1 GB / day": 0,
        "1–10 GB / day": 0,
        "10–100 GB / day": -1,
        "100 GB – 1 TB / day": -3,
        "> 1 TB / day": -5,
    }
    score += vol_penalty.get(volume, 0)
    if volume == "> 1 TB / day":
        risks.append("High volume (>1TB/day) requires partitioning and incremental load strategy")
        recs.append("Design Z-Order / partition pruning from day 1 for >1TB/day volumes")

    return max(score, 0), risks, recs


def _score_complexity(answers: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    Score: how complex is the technical build?
    Max: 25 points
    """
    score = 25.0
    risks = []
    recs = []

    # Q9: Entity count
    entities = answers.get("Q9")
    try:
        n = int(entities) if entities else 0
    except (ValueError, TypeError):
        n = 0
    if n > 20:
        score -= 8
        risks.append(f"High entity count ({n}) — risk of underestimating lineage complexity")
        recs.append("Break pipeline into domain pods (≤8 entities each) for parallel delivery")
    elif n > 10:
        score -= 4
    elif n == 0:
        score -= 3
        risks.append("Entity count not provided — scope estimate unreliable")

    # Q6: Number of source systems
    sources = answers.get("Q6", [])
    if isinstance(sources, str):
        sources = [sources]
    if len(sources) > 4:
        score -= 5
        risks.append(f"{len(sources)} source systems — integration risk high")
        recs.append("Prioritise top 3 sources for MVP; add remaining in Phase 2")
    elif len(sources) > 2:
        score -= 2

    # Streaming penalty
    if "Kafka / Streaming" in sources:
        score -= 4
        risks.append("Streaming ingestion increases operational complexity")
        recs.append("Use Structured Streaming with checkpointing for fault tolerance")

    # Q22: Real-time requirement
    latency = answers.get("Q22", "")
    if "real-time" in str(latency).lower() or "streaming" in str(latency).lower():
        score -= 3
        recs.append("Real-time latency SLA requires dedicated streaming infra and alerting")

    return max(score, 0), risks, recs


def _score_compliance_burden(answers: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    Score: compliance readiness and burden.
    Max: 20 points
    """
    from smart_intake.conditional_engine import detect_compliance_flags
    score = 20.0
    risks = []
    recs = []

    flags = detect_compliance_flags(answers)
    flag_names = [f.value for f in flags]

    penalty = {"GDPR": 4, "SOX": 5, "GxP": 7, "HIPAA": 4}
    for flag in flag_names:
        score -= penalty.get(flag, 3)

    if "GxP" in flag_names:
        risks.append("GxP / 21 CFR Part 11 validation effort often exceeds dev effort")
        recs.append("Engage QA/validation team at project kickoff, not at go-live")
    if "SOX" in flag_names:
        recs.append("SOX requires immutable audit tables — design from schema design phase")
    if "GDPR" in flag_names:
        recs.append("GDPR right-to-erasure requires delete propagation across all pipeline layers")
    if "HIPAA" in flag_names:
        recs.append("HIPAA PHI masking must be applied at Bronze ingestion, not Silver")
    if len(flag_names) >= 2:
        risks.append(f"Multiple compliance frameworks ({', '.join(flag_names)}) — risk of conflicting requirements")

    # Q12: PII handling answered?
    pii = answers.get("Q12")
    if not pii:
        score -= 3
        risks.append("PII handling approach not defined")
        recs.append("Define PII classification and masking strategy before Bronze layer design")

    return max(score, 0), risks, recs


def _score_roi_confidence(answers: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    Score: how complete is the ROI data provided?
    Max: 15 points
    """
    score = 0.0
    risks = []
    recs = []

    # Check key ROI fields answered
    roi_fields = {
        "Q25": ("FTE count", 3),
        "Q26": ("Hourly rate", 2),
        "Q27": ("Hours/week saved", 3),
        "Q28": ("% time saved", 2),
        "Q24": ("Manual process description", 3),
        "Q30": ("Annual error cost", 2),
    }
    missing = []
    for qid, (label, pts) in roi_fields.items():
        val = answers.get(qid)
        if val not in (None, "", 0, 0.0, []):
            score += pts
        else:
            missing.append(label)

    if missing:
        risks.append(f"ROI inputs missing: {', '.join(missing)}")
        recs.append("Complete ROI section (Phase 5) for a reliable business case")

    return min(score, 15), risks, recs


def _score_stakeholder_clarity(answers: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    Score: how clear is the project scope and stakeholder alignment?
    Max: 15 points
    """
    score = 0.0
    risks = []
    recs = []

    clarity_fields = {
        "Q1":  ("Project name", 2),
        "Q2":  ("Business objective", 3),
        "Q4":  ("Domain", 2),
        "Q5":  ("Executive sponsor", 2),
        "Q11": ("KPI description", 3),
        "Q8":  ("Go-live deadline", 3),
    }
    missing = []
    for qid, (label, pts) in clarity_fields.items():
        val = answers.get(qid)
        if val not in (None, "", [], 0):
            score += pts
        else:
            missing.append(label)

    if "Q5" in [q for q, (l, p) in clarity_fields.items() if answers.get(q) in (None, "")]:
        risks.append("No executive sponsor identified — project approval risk")
        recs.append("Identify an executive sponsor before project kickoff to unblock decisions")
    if "Q2" in [q for q, (l, p) in clarity_fields.items() if answers.get(q) in (None, "")]:
        risks.append("Business objective not captured — scope creep risk")
        recs.append("Document a clear problem statement and success criteria in the project charter")

    return min(score, 15), risks, recs


# ─────────────────────────────────────────────
# MAIN DPS CALCULATOR
# ─────────────────────────────────────────────

def calculate_dps(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the full Data Pipeline Score for the current intake session.

    Returns:
        {
          overall_score: int,
          confidence_band: str,
          dimension_scores: {name: score},
          risk_flags: [str],
          recommendations: [str],
          score_breakdown: str   (for display)
        }
    """
    dr_score, dr_risks, dr_recs = _score_data_readiness(answers)
    cx_score, cx_risks, cx_recs = _score_complexity(answers)
    co_score, co_risks, co_recs = _score_compliance_burden(answers)
    ri_score, ri_risks, ri_recs = _score_roi_confidence(answers)
    sk_score, sk_risks, sk_recs = _score_stakeholder_clarity(answers)

    overall = round(dr_score + cx_score + co_score + ri_score + sk_score)
    overall = max(0, min(100, overall))

    all_risks = dr_risks + cx_risks + co_risks + ri_risks + sk_risks
    all_recs  = dr_recs  + cx_recs  + co_recs  + ri_recs  + sk_recs

    if overall >= 90:
        band = "High"
        verdict = "Exceptional — proceed to architecture and build"
    elif overall >= 75:
        band = "High"
        verdict = "Good — minor gaps, low delivery risk"
    elif overall >= 60:
        band = "Medium"
        verdict = "Moderate — address flagged gaps before build kickoff"
    elif overall >= 40:
        band = "Medium"
        verdict = "Needs Work — significant unknowns, scope creep risk"
    else:
        band = "Low"
        verdict = "High Risk — recommend a discovery sprint before committing to build"

    return {
        "overall_score": overall,
        "confidence_band": band,
        "verdict": verdict,
        "dimension_scores": {
            "Data Readiness (25)":      round(dr_score, 1),
            "Complexity (25)":          round(cx_score, 1),
            "Compliance Burden (20)":   round(co_score, 1),
            "ROI Confidence (15)":      round(ri_score, 1),
            "Stakeholder Clarity (15)": round(sk_score, 1),
        },
        "risk_flags":      all_risks,
        "recommendations": all_recs,
    }


def format_dps_report(dps: Dict[str, Any], benchmark_avg: Optional[float] = None) -> str:
    """
    Formats the DPS result as a printable CLI report block.
    """
    lines = []
    score = dps["overall_score"]
    band  = dps["confidence_band"]
    verdict = dps["verdict"]

    # Score bar
    bar_len = 40
    filled  = int(bar_len * score / 100)
    colour_map = {
        (90, 101): "█" * filled,
        (75, 90):  "█" * filled,
        (60, 75):  "█" * filled,
        (0,  60):  "█" * filled,
    }
    bar = "█" * filled + "░" * (bar_len - filled)

    lines.append("")
    lines.append(f"  DPS SCORE : {score}/100  [{band} Confidence]")
    lines.append(f"  [{bar}]")
    lines.append(f"  {verdict}")

    if benchmark_avg:
        diff = score - benchmark_avg
        direction = "above" if diff >= 0 else "below"
        lines.append(f"  vs. similar projects avg: {benchmark_avg}/100  ({abs(diff):.0f} pts {direction})")

    lines.append("")
    lines.append("  DIMENSION BREAKDOWN:")
    for dim, pts in dps["dimension_scores"].items():
        max_pts = int(dim.split("(")[1].rstrip(")"))
        bar2_len = 20
        filled2 = int(bar2_len * pts / max_pts) if max_pts else 0
        bar2 = "█" * filled2 + "░" * (bar2_len - filled2)
        lines.append(f"    {dim:<30}  {pts:>4}/{max_pts}  [{bar2}]")

    if dps["risk_flags"]:
        lines.append("")
        lines.append("  RISK FLAGS:")
        for risk in dps["risk_flags"]:
            lines.append(f"    ⚠  {risk}")

    if dps["recommendations"]:
        lines.append("")
        lines.append("  RECOMMENDATIONS:")
        for i, rec in enumerate(dps["recommendations"], 1):
            lines.append(f"    {i}. {rec}")

    lines.append("")
    return "\n".join(lines)


