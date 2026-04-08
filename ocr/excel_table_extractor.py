"""
excel_table_extractor.py
------------------------
Extracts multiple independent tables from Excel files (.xlsx / .xls).

Handles sheets where several disconnected data blocks coexist — standard
pd.read_excel() would merge them into one broken DataFrame. This module
detects each table individually using a visited-cell matrix and a
2-consecutive-empty-row/column heuristic.

Usage:
    python excel_table_extractor.py <path_to_excel_file>
"""

import sys
import subprocess
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def convert_xls_to_xlsx(input_file: str, output_dir: str) -> None:
    """
    Convert a legacy .xls file to .xlsx using LibreOffice headless mode.

    Args:
        input_file: Path to the source .xls file.
        output_dir: Directory where the converted .xlsx will be written.
                    Must be a directory, not a file path.
    """
    command = [
        "libreoffice", "--headless", "--convert-to", "xlsx",
        input_file, "--outdir", output_dir   # --outdir expects a folder
    ]
    subprocess.run(command, check=True)


# ---------------------------------------------------------------------------
# Cell helpers
# ---------------------------------------------------------------------------

def is_empty_cell(value) -> bool:
    """Return True if a cell value is None or contains only whitespace."""
    return value is None or str(value).strip() == ""


# ---------------------------------------------------------------------------
# Sheet loading
# ---------------------------------------------------------------------------

def load_sheet_values(sheet) -> list[list]:
    """
    Read all cell values from an openpyxl sheet into a plain 2D list.

    Operates on raw values only (no formatting or formula evaluation).
    Merged cells: openpyxl populates only the top-left cell of a merged
    region; remaining cells are None, which may affect boundary detection
    for tables with merged headers.

    Returns:
        2D list where result[row][col] is the cell value (0-indexed).
    """
    max_row = sheet.max_row
    max_col = sheet.max_column

    # Guard: return empty list if the sheet is completely blank
    if max_row is None or max_col is None:
        return []

    values = []
    for r in range(1, max_row + 1):
        row = [sheet.cell(row=r, column=c).value for c in range(1, max_col + 1)]
        values.append(row)
    return values


# ---------------------------------------------------------------------------
# Table boundary detection
# ---------------------------------------------------------------------------

def detect_table_boundary(
    data: list[list],
    start_row: int,
    start_col: int,
    visited: list[list[bool]],
) -> tuple[int, int]:
    """
    Find the bottom-right boundary of a table starting at (start_row, start_col).

    Strategy:
        - Scan rows downward; stop after 2 consecutive fully-empty rows.
        - Scan columns rightward; stop after 2 consecutive fully-empty columns.
        A cell already processed (visited) is treated as empty so it doesn't
        pull unrelated tables into the current boundary.

    Args:
        data:       2D list of cell values (from load_sheet_values).
        start_row:  0-indexed row where the table begins.
        start_col:  0-indexed column where the table begins.
        visited:    Boolean matrix; True means the cell belongs to a prior table.

    Returns:
        (end_row, end_col) — exclusive indices (slice-style).
    """
    max_rows = len(data)
    max_cols = len(data[0]) if data else 0

    # --- Row boundary ---
    row = start_row
    empty_row_streak = 0
    while row < max_rows:
        row_is_empty = all(
            is_empty_cell(data[row][c]) or visited[row][c]
            for c in range(start_col, max_cols)
        )
        if row_is_empty:
            empty_row_streak += 1
            if empty_row_streak >= 2:
                break
        else:
            empty_row_streak = 0
        row += 1
    end_row = row if empty_row_streak >= 2 else max_rows

    # --- Column boundary ---
    col = start_col
    empty_col_streak = 0
    while col < max_cols:
        col_is_empty = all(
            is_empty_cell(data[r][col]) or visited[r][col]
            for r in range(start_row, end_row)
        )
        if col_is_empty:
            empty_col_streak += 1
            if empty_col_streak >= 2:
                break
        else:
            empty_col_streak = 0
        col += 1
    end_col = col if empty_col_streak >= 2 else max_cols

    return end_row, end_col


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------

def extract_table(
    data: list[list],
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
) -> pd.DataFrame | None:
    """
    Slice a region from the 2D data array and return it as a cleaned DataFrame.

    Fully-empty rows and columns are dropped. Returns None if nothing remains
    after cleaning (avoids storing ghost tables from edge artefacts).
    """
    rows = [data[r][start_col:end_col] for r in range(start_row, end_row)]
    df = pd.DataFrame(rows)
    df.dropna(how="all", inplace=True)        # drop rows that are all NaN
    df.dropna(axis=1, how="all", inplace=True) # drop columns that are all NaN
    df.reset_index(drop=True, inplace=True)
    return df if not df.empty else None


def extract_tables_from_sheet(sheet) -> list[pd.DataFrame]:
    """
    Detect and extract all independent tables from a single worksheet.

    Scans cells top-left → bottom-right. When an unvisited non-empty cell
    is found it marks the top-left corner of a new table. Boundary detection
    runs from that corner; all cells in the detected region are marked visited
    before the scan continues, preventing double-counting.

    Returns:
        List of DataFrames, one per detected table (may be empty list).
    """
    data = load_sheet_values(sheet)

    # Guard: nothing to process on a blank sheet
    if not data or not data[0]:
        return []

    num_rows = len(data)
    num_cols = len(data[0])
    visited = [[False] * num_cols for _ in range(num_rows)]
    tables = []

    for r in range(num_rows):
        for c in range(num_cols):
            if not is_empty_cell(data[r][c]) and not visited[r][c]:
                # Found the start of a new table — detect its full extent
                end_r, end_c = detect_table_boundary(data, r, c, visited)

                # Mark every cell in this region as visited
                for i in range(r, end_r):
                    for j in range(c, end_c):
                        visited[i][j] = True

                df = extract_table(data, r, end_r, c, end_c)
                if df is not None:
                    tables.append(df)

    return tables


# ---------------------------------------------------------------------------
# File-level extraction
# ---------------------------------------------------------------------------

def extract_tables_from_file(filepath: str) -> list[str]:
    """
    Open an Excel workbook and extract all tables from every sheet.

    Each table is rendered as a markdown table string for readability in
    downstream LLM prompts or RAG pipelines (instead of raw dict output).

    Returns:
        List of strings, one per sheet. Each string contains all tables
        found on that sheet, labelled ##Table 1, ##Table 2, etc.
    """
    wb = load_workbook(filepath, data_only=True)
    file_tables = []

    for sheetname in wb.sheetnames:
        sheet = wb[sheetname]
        tables = extract_tables_from_sheet(sheet)

        if not tables:
            continue

        sheet_blocks = [f"### Sheet: {sheetname}\n"]
        for idx, df in enumerate(tables, 1):
            # Use first row as header if it looks like one (all strings)
            if df.iloc[0].apply(lambda v: isinstance(v, str)).all():
                df.columns = df.iloc[0].tolist()
                df = df[1:].reset_index(drop=True)

            # Render as markdown — far more readable than to_dict() in LLM context
            markdown = df.to_markdown(index=False)
            sheet_blocks.append(f"\n## Table {idx}\n\n{markdown}\n")

        file_tables.append("\n".join(sheet_blocks))

    return file_tables


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python excel_table_extractor.py <path_to_excel_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"\nExtracting tables from: {filepath}\n{'=' * 60}\n")

    results = extract_tables_from_file(filepath)

    if not results:
        print("No tables found.")
    else:
        for sheet_output in results:
            print(sheet_output)
            print("\n" + "=" * 60 + "\n")
