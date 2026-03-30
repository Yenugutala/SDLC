"""
DPS (Design/Project Specification) Evaluator.

Scans a DPS PDF and reports which sections are present, empty, or missing,
along with concise fill guidance for any gaps.

Usage:
    python dps/evaluator.py path/to/dps.pdf
    python dps/evaluator.py          # interactive — prompts for path
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dps.engine import DpsEngine


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        pdfPath = args[0]
    else:
        print("\n  Enter path to DPS PDF file: ", end="")
        pdfPath = input().strip().strip('"').strip("'")

    if not pdfPath:
        print("  No file path provided.")
        sys.exit(1)

    if not os.path.exists(pdfPath):
        cwd_path = os.path.join(os.getcwd(), pdfPath)
        if os.path.exists(cwd_path):
            pdfPath = cwd_path
        else:
            print(f"  File not found: {pdfPath}")
            sys.exit(1)

    engine = DpsEngine()
    report = engine.evaluate(pdfPath)
    engine.printReport(report)


if __name__ == "__main__":
    main()
