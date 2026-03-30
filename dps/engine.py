"""
DPS (Design/Project Specification) Evaluation Engine.

Flow:
    1. PDF TEXT EXTRACTION  — PyMuPDF for text-based PDFs; parallel OCR for image-based PDFs
    2. SECTION PARSING      — Regex detects which sections/sub-sections are present
    3. COMPLETENESS CHECK   — Flags each section as PRESENT / EMPTY / MISSING
    4. REPORT               — Concise output: status table + fill guidance for gaps only

Why completeness-only (no LLM scoring):
    LLM scoring was removed for speed and cost. A DPS completeness check — "is this
    section present and non-empty?" — is deterministic and doesn't require an LLM.
    Per-persona quality scoring can be layered on top using PERSONA_CRITERIA in template.py
    if needed in the future.
"""

import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any

# A section body with fewer than this many characters is treated as empty.
# 40 chars is roughly one short sentence — anything shorter is likely a placeholder.
MIN_CONTENT_LENGTH = 40

# Common template placeholder strings that indicate an unfilled section.
# Checked case-insensitively against section body text.
EMPTY_TABLE_MARKERS = [
    "click here to enter text",
    "enter text here",
    "<enter",
    "tbd",
    "to be determined",
    "to be added",
    "please fill",
]

# Status constants used throughout the module
STATUS_PRESENT = "PRESENT"
STATUS_EMPTY   = "EMPTY"
STATUS_MISSING = "MISSING"


# =============================================================================
# PDF EXTRACTION
# =============================================================================

def _ocrPage(args) -> tuple:
    """
    OCR a single PDF page (called in parallel by ThreadPoolExecutor).

    Args:
        args: (pageNum, pngBytes) tuple — page index and its PNG byte data

    Returns:
        (pageNum, text) tuple — page index and extracted text string
    """
    pageNum, pngBytes = args
    try:
        import pytesseract
        from PIL import Image
        import io
        img  = Image.open(io.BytesIO(pngBytes))
        # --psm 6: treat the image as a single uniform block of text
        text = pytesseract.image_to_string(img, config="--psm 6 -l eng")
        return (pageNum, text)
    except Exception:
        # Return empty string rather than raising — partial OCR is better than a crash
        return (pageNum, "")


def extractTextFromPdf(pdfPath: str) -> str:
    """
    Extract full text from a PDF.

    Two-stage approach:
        Stage 1: PyMuPDF direct text extraction — instant for text-based PDFs (selectable text).
        Stage 2: Parallel OCR — only if Stage 1 returns < 100 chars (image-based / scanned PDF).

    The 100-character threshold is conservative — even a single-sentence title page
    should exceed it. Below 100 chars strongly suggests the PDF is image-based.

    Args:
        pdfPath: Absolute or relative path to the PDF file

    Returns:
        Full text content of the PDF as a single string (pages joined by double newline)

    Raises:
        ImportError:    If PyMuPDF (fitz) is not installed
        FileNotFoundError: If the PDF path does not exist
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("Run: pip install pymupdf")

    if not os.path.exists(pdfPath):
        raise FileNotFoundError(f"PDF not found: {pdfPath}")

    doc = fitz.open(pdfPath)

    # Stage 1: direct text extraction (fast — no rendering required)
    pages    = [doc[i].get_text() for i in range(len(doc))]
    fullText = "\n\n".join(pages)

    # If meaningful text was found, return immediately
    if len(fullText.strip()) >= 100:
        doc.close()
        return fullText

    # Stage 2: image-based PDF detected — fall back to parallel OCR
    print("  Image-based PDF detected. Running OCR (parallel)...")
    try:
        import pytesseract  # noqa — validate presence before rendering all pages
        from PIL import Image  # noqa
        import io  # noqa
    except ImportError:
        doc.close()
        raise ImportError(
            "OCR required but not installed.\n"
            "Run: pip install pytesseract Pillow && brew install tesseract"
        )

    # Render all pages to PNG bytes at 150 DPI before threading
    # 150 DPI is a good balance: readable for OCR, not so large it's slow
    mat      = fitz.Matrix(150 / 72, 150 / 72)
    pageData = []
    for i in range(len(doc)):
        pix = doc[i].get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pageData.append((i, pix.tobytes("png")))
    doc.close()

    # OCR all pages in parallel — 4 threads is safe on most machines and
    # gives near-linear speedup for typical DPS documents (10–30 pages)
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_ocrPage, item): item[0] for item in pageData}
        for future in as_completed(futures):
            pageNum, text = future.result()
            results[pageNum] = text

    # Reconstruct full text in page order (futures complete out of order)
    return "\n\n".join(results[i] for i in sorted(results))


# =============================================================================
# SECTION PARSER
# =============================================================================

def _matchesAnyPattern(text: str, patterns: List[str]) -> bool:
    """Return True if any of the regex patterns match anywhere in text."""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return True
    return False


def _extractSectionContent(fullText: str, sectionPatterns: List[str],
                            nextSectionPatterns: Optional[List[str]] = None) -> str:
    """
    Extract the body text between this section's heading and the next section's heading.

    Algorithm:
        1. Find the earliest match for any of this section's heading patterns
        2. Set the end position to the start of the next section (or EOF)
        3. Return the text between them (trimmed)

    Args:
        fullText:             Full document text
        sectionPatterns:      Regex patterns that identify this section's heading
        nextSectionPatterns:  Patterns for the following section — used to find end boundary

    Returns:
        Section body text, or "" if the section heading was not found
    """
    # Find the earliest heading match among all patterns for this section
    startMatch = None
    for pattern in sectionPatterns:
        m = re.search(pattern, fullText, re.IGNORECASE | re.MULTILINE)
        if m and (startMatch is None or m.start() < startMatch.start()):
            startMatch = m

    if not startMatch:
        return ""   # heading not found — section is MISSING

    startPos = startMatch.end()
    endPos   = len(fullText)   # default: read to end of document

    # Narrow the end boundary to the start of the next section
    if nextSectionPatterns:
        for pattern in nextSectionPatterns:
            m = re.search(pattern, fullText[startPos:], re.IGNORECASE | re.MULTILINE)
            if m:
                candidate = startPos + m.start()
                if candidate < endPos:
                    endPos = candidate

    return fullText[startPos:endPos].strip()


def _isContentEmpty(content: str) -> bool:
    """
    Determine whether a section body should be treated as empty.

    A section is empty if:
        - The body is shorter than MIN_CONTENT_LENGTH characters, OR
        - The body contains only placeholder text (from EMPTY_TABLE_MARKERS)
          with fewer than MIN_CONTENT_LENGTH non-placeholder characters remaining

    Args:
        content: Section body text (already stripped)

    Returns:
        True if the section should be flagged as EMPTY
    """
    # Quick check: too short to contain meaningful content
    if not content or len(content.strip()) < MIN_CONTENT_LENGTH:
        return True

    # Check for placeholder markers — strip them and see what's left
    lower = content.lower()
    for marker in EMPTY_TABLE_MARKERS:
        if marker in lower:
            cleaned = lower
            for m in EMPTY_TABLE_MARKERS:
                cleaned = cleaned.replace(m, "")
            if len(cleaned.strip()) < MIN_CONTENT_LENGTH:
                return True

    return False


# =============================================================================
# COMPLETENESS CHECK
# =============================================================================

def checkCompleteness(fullText: str) -> Dict[str, Dict]:
    """
    Check every section and sub-section from the DPS template.

    Recursively processes top-level sections and their subsections.
    Each section is checked in order with its successor's patterns used
    as the end-boundary for content extraction.

    Args:
        fullText: Full extracted text of the DPS PDF

    Returns:
        Dict keyed by section_id, each value containing:
            label    — human-readable section name
            status   — PRESENT / EMPTY / MISSING
            guidance — what to fill in if status is not PRESENT
            required — True if this section is mandatory
    """
    from dps.template import DPS_SECTIONS

    results = {}

    def checkSection(section: Dict, parentNextPatterns: Optional[List[str]] = None):
        """Recursively check a section and all its subsections."""
        sId      = section["id"]
        patterns = section["patterns"]

        headingFound = _matchesAnyPattern(fullText, patterns)
        content      = _extractSectionContent(fullText, patterns, parentNextPatterns)

        # Determine status: heading must exist AND content must be non-empty
        if not headingFound:
            status = STATUS_MISSING
        elif _isContentEmpty(content):
            status = STATUS_EMPTY
        else:
            status = STATUS_PRESENT

        results[sId] = {
            "label":    section["label"],
            "status":   status,
            "guidance": section.get("guidance", ""),
            "required": section.get("required", True),
        }

        # Process subsections with their successors' patterns as boundaries
        subsections = section.get("subsections", [])
        for i, sub in enumerate(subsections):
            # Next subsection's patterns serve as the end boundary for this subsection
            nextPat = subsections[i + 1]["patterns"] if i + 1 < len(subsections) else parentNextPatterns
            checkSection(sub, nextPat)

    for i, section in enumerate(DPS_SECTIONS):
        # Each top-level section ends where the next one begins
        nextPatterns = DPS_SECTIONS[i + 1]["patterns"] if i + 1 < len(DPS_SECTIONS) else None
        checkSection(section, nextPatterns)

    return results


# =============================================================================
# ENGINE
# =============================================================================

class DpsEngine:
    """
    DPS evaluation engine — completeness check only (no LLM scoring).

    Usage:
        engine = DpsEngine()
        report = engine.evaluate("path/to/dps.pdf")
        engine.printReport(report)
    """

    def evaluate(self, pdfPath: str) -> Dict[str, Any]:
        """
        Run DPS evaluation: extract text → check sections → build report dict.

        The completeness score is calculated only over required sections
        (required=True in template.py) — optional sections like Appendix
        don't count against the score.

        Args:
            pdfPath: Path to the DPS PDF file

        Returns:
            Report dict with keys:
                fileName, totalSections, present, empty, missing,
                completenessScore (0–100%), sections (detailed per-section results)
        """
        fullText = extractTextFromPdf(pdfPath)
        sections = checkCompleteness(fullText)

        # Partition section IDs into the three status buckets
        present = [sid for sid, s in sections.items() if s["status"] == STATUS_PRESENT]
        empty   = [sid for sid, s in sections.items() if s["status"] == STATUS_EMPTY]
        missing = [sid for sid, s in sections.items() if s["status"] == STATUS_MISSING]

        # Score = (required sections present) / (total required sections) × 100
        requiredIds     = [sid for sid, s in sections.items() if s["required"]]
        requiredPresent = [sid for sid in present if sid in requiredIds]
        completenessScore = (len(requiredPresent) / len(requiredIds) * 100) if requiredIds else 0

        return {
            "fileName":          os.path.basename(pdfPath),
            "totalSections":     len(sections),
            "present":           present,
            "empty":             empty,
            "missing":           missing,
            "completenessScore": round(completenessScore, 1),
            "sections":          sections,
        }

    def printReport(self, report: Dict[str, Any]) -> None:
        """
        Print a concise DPS evaluation report to stdout.

        Layout:
            Header       — file name
            Summary      — completeness bar + counts
            Status table — one row per section with PRESENT/EMPTY/MISSING
            Gaps section — only shown if there are issues; includes fill guidance
            Footer       — actionable summary line
        """
        from utils.formatting import console, scoreBar, colorStatus, printHeader, printSection

        W        = 70
        sections = report["sections"]
        score    = report["completenessScore"]

        # ── Header ────────────────────────────────────────────────────────────
        printHeader(f"DPS EVALUATION — {report['fileName']}", width=W)

        # ── Summary ───────────────────────────────────────────────────────────
        bar = scoreBar(score, width=25)
        console.print(f"\n  Completeness  {bar}  [bold]{score:.0f}%[/bold]")
        console.print(f"  [green]✓ Present   :[/green] {len(report['present'])}")
        console.print(f"  [yellow]⚠ Empty     :[/yellow] {len(report['empty'])}  [dim](heading exists, no content)[/dim]")
        console.print(f"  [red]✗ Missing   :[/red] {len(report['missing'])}  [dim](section not found)[/dim]")

        # ── Status table ──────────────────────────────────────────────────────
        printSection("SECTION STATUS", width=W)

        # Map each status to a colored symbol + colored status text
        def statusLine(s: Dict) -> str:
            st = s["status"]
            if st == STATUS_PRESENT:
                sym = "[green]✓[/green]"
                colored = "[green]PRESENT[/green]"
            elif st == STATUS_EMPTY:
                sym = "[yellow]⚠[/yellow]"
                colored = "[yellow]EMPTY[/yellow]"
            else:
                sym = "[red]✗[/red]"
                colored = "[red]MISSING[/red]"
            opt = " [dim](optional)[/dim]" if not s["required"] else ""
            return f"  {sym}  {s['label']:<42} {colored}{opt}"

        for sId, s in sections.items():
            console.print(statusLine(s))

        # ── Gaps + fill guidance ──────────────────────────────────────────────
        # Only sections that need work — don't waste space on already-complete sections
        needsWork = report["empty"] + report["missing"]
        if needsWork:
            printSection("WHAT NEEDS TO BE FILLED", width=W)
            for sId in needsWork:
                s   = sections[sId]
                tag = "[yellow]EMPTY[/yellow]" if s["status"] == STATUS_EMPTY else "[red]MISSING[/red]"
                # Truncate guidance to ~160 chars (2–3 lines) to keep the report scannable
                guidance = s["guidance"]
                if len(guidance) > 160:
                    guidance = guidance[:157] + "..."
                console.print(f"\n  [{tag}] [bold]{s['label']}[/bold]")
                console.print(f"  [dim]→[/dim] {guidance}")

        # ── Footer ────────────────────────────────────────────────────────────
        console.print()
        console.print("=" * W, style="cyan dim")
        if not needsWork:
            console.print("  [green]All sections present. DPS is ready for review.[/green]")
        else:
            console.print(f"  [yellow]Fix {len(needsWork)} section(s) before submitting the DPS.[/yellow]")
        console.print("=" * W, style="cyan dim")
        console.print()
