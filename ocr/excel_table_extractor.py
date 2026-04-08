"""
excel_table_extractor.py
------------------------
Extracts multiple independent tables from Excel files (.xlsx / .xls),
then chunks and stores them in a persistent ChromaDB vector store.

Handles sheets where several disconnected data blocks coexist — standard
pd.read_excel() would merge them into one broken DataFrame. This module
detects each table individually using a visited-cell matrix and a
2-consecutive-empty-row/column heuristic.

Advanced RAG techniques used:
    1. Table-aware chunking    — each table is a natural semantic unit and
                                 stored as its own parent document. Large
                                 tables (>15 data rows) are further split
                                 into row-group chunks.
    2. Contextual retrieval    — each chunk is prefixed with a sheet/table
                                 context header before embedding so the model
                                 understands what the data represents.
    3. Parent-child chunking   — full table markdown stored as parent;
                                 row-group chunks stored as children with
                                 a parentId pointer for context recovery.
    4. Persistent ChromaDB     — data survives sessions (same db as llm_ocr).
    5. Metadata filtering      — source, filename, sheet, table index, row
                                 range stored for fine-grained filtering.

Usage:
    python excel_table_extractor.py <path_to_excel_file>
"""

import sys
import subprocess
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook

import chromadb
from chromadb.utils import embedding_functions

# Allow importing rag.chunker from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Rows per row-group chunk for large tables (header always prepended)
ROW_CHUNK_SIZE = 15

# Shared persistent ChromaDB path (same store as llm_ocr.py)
CHROMA_PATH = Path(__file__).parent / "chroma_db"


# ---------------------------------------------------------------------------
# Vector store (persistent, shared with llm_ocr)
# ---------------------------------------------------------------------------

def get_vector_store():
    """
    Return a persistent ChromaDB collection for OCR Excel documents.

    Uses all-MiniLM-L6-v2 (384-dim) — same embedding model as the main KG
    store so similarity scores are comparable across collections.
    Persistent client writes to ocr/chroma_db/ on disk.
    """
    db_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return db_client.get_or_create_collection(
        name="ocr_excel_documents",
        embedding_function=embed_fn,
    )


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def convert_xls_to_xlsx(input_file: str, output_dir: str) -> None:
    """
    Convert a legacy .xls file to .xlsx using LibreOffice headless mode.

    Args:
        input_file: Path to the source .xls file.
        output_dir: Directory where the converted .xlsx will be written.
                    Must be a directory path, not a file path.
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
    """
    Return True if a cell value is None or contains only whitespace.

    Note: 0 (integer zero) is treated as non-empty — it is valid data.
    Using `if not value` would incorrectly treat 0 as empty.
    """
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
        Empty list if the sheet is completely blank.
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
        A cell already processed (visited) is treated as empty so it does not
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
    df.dropna(how="all", inplace=True)         # drop rows that are entirely NaN
    df.dropna(axis=1, how="all", inplace=True)  # drop columns that are entirely NaN
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
    downstream LLM prompts or RAG pipelines.

    Returns:
        List of strings, one per sheet. Each string contains all tables
        found on that sheet, labelled ## Table 1, ## Table 2, etc.
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
            # Promote first row to header if it looks like one (all strings)
            if df.iloc[0].apply(lambda v: isinstance(v, str)).all():
                df.columns = df.iloc[0].tolist()
                df = df[1:].reset_index(drop=True)

            # Render as markdown — far more readable than to_dict() in LLM context
            markdown = df.to_markdown(index=False)
            sheet_blocks.append(f"\n## Table {idx}\n\n{markdown}\n")

        file_tables.append("\n".join(sheet_blocks))

    return file_tables


# ---------------------------------------------------------------------------
# Table chunking (row-group splitting for large tables)
# ---------------------------------------------------------------------------

def chunk_table(df: pd.DataFrame, sheet: str, table_idx: int) -> list[tuple[str, dict]]:
    """
    Split a DataFrame into row-group chunks, each prefixed with context.

    Contextual retrieval technique:
        Each chunk is prefixed with a header like:
            "Sheet: Sales Report | Table 2 | Rows 15-29"
        This anchors the chunk's meaning before embedding so queries about
        specific tables retrieve the right row groups.

    For small tables (≤ ROW_CHUNK_SIZE rows), returns a single chunk.
    For large tables, splits into ROW_CHUNK_SIZE-row groups with the
    column headers repeated in each chunk.

    Args:
        df:         Cleaned DataFrame with headers as column names.
        sheet:      Sheet name (for context prefix).
        table_idx:  1-based table index within the sheet.

    Returns:
        List of (text_to_embed, metadata_dict) tuples.
    """
    # Ensure first row is used as header
    if df.columns.tolist() == list(range(len(df.columns))):
        df.columns = df.iloc[0].tolist()
        df = df[1:].reset_index(drop=True)

    full_markdown = df.to_markdown(index=False)
    context_prefix = f"Sheet: {sheet} | Table {table_idx}"

    # Small table — single chunk, no splitting needed
    if len(df) <= ROW_CHUNK_SIZE:
        text = f"{context_prefix}\n\n{full_markdown}"
        meta = {
            "chunk_type":  "parent",
            "sheet":       sheet,
            "table_index": str(table_idx),
            "row_start":   "0",
            "row_end":     str(len(df)),
        }
        return [(text, meta)]

    # Large table — split into row groups; repeat headers in each chunk
    chunks = []
    for start in range(0, len(df), ROW_CHUNK_SIZE):
        end = min(start + ROW_CHUNK_SIZE, len(df))
        group = df.iloc[start:end]
        group_markdown = group.to_markdown(index=False)
        # Context prefix includes row range so LLM knows where in the table this is
        text = f"{context_prefix} | Rows {start}-{end - 1}\n\n{group_markdown}"
        meta = {
            "chunk_type":  "child",
            "sheet":       sheet,
            "table_index": str(table_idx),
            "row_start":   str(start),
            "row_end":     str(end),
        }
        chunks.append((text, meta))

    return chunks


# ---------------------------------------------------------------------------
# Vector store ingestion
# ---------------------------------------------------------------------------

def store_tables_in_vectordb(filepath: str) -> None:
    """
    Extract all tables from an Excel file and store them in ChromaDB.

    Strategy:
        Parent-child chunking:
            - Full table markdown → stored as parent (chunk_type="parent" for small,
              or as an additional parent entry for large tables)
            - Row-group chunks → stored as children (chunk_type="child") with
              parentId pointing back to the full-table document.

        Contextual retrieval:
            - Every chunk (parent and child) is prefixed with a context header
              containing the sheet name, table index, and row range before embedding.

    Args:
        filepath: Path to the .xlsx file.
    """
    collection = get_vector_store()
    wb = load_workbook(filepath, data_only=True)
    stem = Path(filepath).stem.replace(" ", "_")
    filename = Path(filepath).name

    print(f"\nStoring tables from '{filename}' in ChromaDB...")

    for sheetname in wb.sheetnames:
        sheet = wb[sheetname]
        tables = extract_tables_from_sheet(sheet)

        if not tables:
            continue

        for table_idx, df in enumerate(tables, 1):
            # Promote first row to header if it looks like one
            if df.iloc[0].apply(lambda v: isinstance(v, str)).all():
                df.columns = df.iloc[0].tolist()
                df = df[1:].reset_index(drop=True)

            parent_id = f"excel_{stem}_{sheetname.replace(' ', '_')}_table_{table_idx}"
            full_markdown = df.to_markdown(index=False)
            context_prefix = f"Sheet: {sheetname} | Table {table_idx}"

            # --- Parent: full table markdown ---
            # Always stored so retriever can return the complete table when a
            # child row-group chunk matches a query.
            collection.upsert(
                ids=[parent_id],
                documents=[f"{context_prefix}\n\n{full_markdown}"],
                metadatas=[{
                    "source":      "excel",
                    "filename":    filename,
                    "sheet":       sheetname,
                    "table_index": str(table_idx),
                    "chunk_type":  "parent",
                    "row_count":   str(len(df)),
                }]
            )

            # --- Children: row-group chunks (only for large tables) ---
            chunks = chunk_table(df, sheetname, table_idx)

            # Single chunk returned means table was small — parent IS the chunk
            if len(chunks) == 1:
                print(f"  [{sheetname}] Table {table_idx}: 1 chunk (small table, parent only)")
                continue

            print(f"  [{sheetname}] Table {table_idx}: {len(chunks)} row-group chunks")

            for i, (text, chunk_meta) in enumerate(chunks):
                collection.upsert(
                    ids=[f"{parent_id}_chunk_{i}"],
                    documents=[text],
                    metadatas={
                        **chunk_meta,
                        "source":    "excel",
                        "filename":  filename,
                        "parent_id": parent_id,
                    }
                )

    total = collection.count()
    print(f"\nDone. Total documents in ocr_excel_documents collection: {total}")


# ---------------------------------------------------------------------------
# Search helper
# ---------------------------------------------------------------------------

def search_excel(query: str, k: int = 5, sheet: str = None) -> None:
    """
    Semantic search over stored Excel table chunks.

    Args:
        query:  Natural language query (e.g. "pipelines with failed status").
        k:      Number of results to return.
        sheet:  Optional — filter results to a specific sheet name.
    """
    collection = get_vector_store()
    where = {"sheet": sheet} if sheet else None

    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where,
    )

    print(f"\nSearch: '{query}'\n{'=' * 60}")
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
        print(f"\n[{i}] Sheet: {meta.get('sheet')} | Table {meta.get('table_index')} "
              f"| {meta.get('chunk_type')} | {meta.get('filename')}")
        print(f"    {doc[:300]}...")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python excel_table_extractor.py <path_to_excel_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"\nExtracting tables from: {filepath}\n{'=' * 60}\n")

    # Print extracted tables to console
    results = extract_tables_from_file(filepath)
    if not results:
        print("No tables found.")
    else:
        for sheet_output in results:
            print(sheet_output)
            print("\n" + "=" * 60 + "\n")

    # Store in ChromaDB
    store_tables_in_vectordb(filepath)

    # Demo search
    print("\n--- Demo search ---")
    search_excel("failed pipelines", k=3)
    search_excel("PII columns", k=3)
