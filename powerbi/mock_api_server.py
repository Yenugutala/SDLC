"""Mock Power BI REST API Server: FastAPI app with exact PBI v1.0 endpoints.

Each endpoint returns ONLY its specific data — no single endpoint exposes
everything. Response schemas match the official Microsoft PBI REST API contract.
Internal mapping fields (gold_view, gold_column) are stripped from responses.
"""

from fastapi import FastAPI, HTTPException, Query
from powerbi.mock_data_model import (
    WORKSPACE, DATASETS, DATASET_TABLES, REPORTS,
    DASHBOARDS, DASHBOARD_TILES, DATASET_DATASOURCES,
    REFRESH_HISTORY,
)


app = FastAPI(title="Power BI REST API Mock", version="1.0")

# In-memory storage for rows pushed via POST endpoint
_pushed_rows: dict[str, dict[str, list]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INTERNAL_KEYS = {"gold_view", "gold_column", "dependent_columns"}


def _strip_internal(obj):
    """Recursively strip internal mapping keys from API response objects."""
    if isinstance(obj, dict):
        return {k: _strip_internal(v) for k, v in obj.items() if k not in INTERNAL_KEYS}
    if isinstance(obj, list):
        return [_strip_internal(item) for item in obj]
    return obj


def _validate_group(group_id: str):
    if group_id != WORKSPACE["id"]:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "ItemNotFound", "message": f"Workspace '{group_id}' not found"}},
        )


def _find_dataset(dataset_id: str):
    for ds in DATASETS:
        if ds["id"] == dataset_id:
            return ds
    raise HTTPException(
        status_code=404,
        detail={"error": {"code": "ItemNotFound", "message": f"Dataset '{dataset_id}' not found"}},
    )


def _find_dashboard(dashboard_id: str):
    for db in DASHBOARDS:
        if db["id"] == dashboard_id:
            return db
    raise HTTPException(
        status_code=404,
        detail={"error": {"code": "ItemNotFound", "message": f"Dashboard '{dashboard_id}' not found"}},
    )


# ---------------------------------------------------------------------------
# Endpoint 1: GET /v1.0/myorg/groups — List workspaces
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups")
def get_groups():
    return {"value": [WORKSPACE]}


# ---------------------------------------------------------------------------
# Endpoint 2: GET /v1.0/myorg/groups/{gid}/datasets — Datasets in workspace
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups/{group_id}/datasets")
def get_datasets_in_group(group_id: str):
    _validate_group(group_id)
    return {"value": _strip_internal(DATASETS)}


# ---------------------------------------------------------------------------
# Endpoint 3: GET /v1.0/myorg/groups/{gid}/datasets/{did}/tables
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/tables")
def get_tables_in_dataset(group_id: str, dataset_id: str):
    _validate_group(group_id)
    _find_dataset(dataset_id)
    tables = DATASET_TABLES.get(dataset_id, [])
    return {"value": _strip_internal(tables)}


# ---------------------------------------------------------------------------
# Endpoint 4: GET /v1.0/myorg/groups/{gid}/datasets/{did}/datasources
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/datasources")
def get_datasources(group_id: str, dataset_id: str):
    _validate_group(group_id)
    _find_dataset(dataset_id)
    sources = DATASET_DATASOURCES.get(dataset_id, [])
    return {"value": _strip_internal(sources)}


# ---------------------------------------------------------------------------
# Endpoint 5: GET /v1.0/myorg/groups/{gid}/reports — Reports in workspace
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups/{group_id}/reports")
def get_reports_in_group(group_id: str):
    _validate_group(group_id)
    return {"value": _strip_internal(REPORTS)}


# ---------------------------------------------------------------------------
# Endpoint 6: GET /v1.0/myorg/groups/{gid}/dashboards — Dashboards
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups/{group_id}/dashboards")
def get_dashboards_in_group(group_id: str):
    _validate_group(group_id)
    return {"value": _strip_internal(DASHBOARDS)}


# ---------------------------------------------------------------------------
# Endpoint 7: GET /v1.0/myorg/groups/{gid}/dashboards/{dbid}/tiles
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/groups/{group_id}/dashboards/{dashboard_id}/tiles")
def get_tiles_in_dashboard(group_id: str, dashboard_id: str):
    _validate_group(group_id)
    _find_dashboard(dashboard_id)
    tiles = DASHBOARD_TILES.get(dashboard_id, [])
    return {"value": _strip_internal(tiles)}


# ---------------------------------------------------------------------------
# Endpoint 8: GET /v1.0/myorg/datasets/{did}/refreshes — Refresh history
# ---------------------------------------------------------------------------

@app.get("/v1.0/myorg/datasets/{dataset_id}/refreshes")
def get_refresh_history(dataset_id: str, top: int = Query(default=10, alias="$top")):
    _find_dataset(dataset_id)
    history = REFRESH_HISTORY.get(dataset_id, [])
    return {"value": history[:top]}


# ---------------------------------------------------------------------------
# Endpoint 9: POST /v1.0/myorg/groups/{gid}/datasets/{did}/tables/{tbl}/rows
# ---------------------------------------------------------------------------

@app.post("/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/tables/{table_name}/rows")
def post_rows(group_id: str, dataset_id: str, table_name: str, body: dict):
    _validate_group(group_id)
    _find_dataset(dataset_id)

    # Validate table exists
    tables = DATASET_TABLES.get(dataset_id, [])
    table_found = any(t["name"] == table_name for t in tables)
    if not table_found:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "ItemNotFound", "message": f"Table '{table_name}' not found in dataset"}},
        )

    rows = body.get("rows", [])
    if dataset_id not in _pushed_rows:
        _pushed_rows[dataset_id] = {}
    if table_name not in _pushed_rows[dataset_id]:
        _pushed_rows[dataset_id][table_name] = []
    _pushed_rows[dataset_id][table_name].extend(rows)

    return {"status": "ok", "rows_added": len(rows)}


# ---------------------------------------------------------------------------
# Mock-only endpoints (not part of real PBI API)
# ---------------------------------------------------------------------------

@app.get("/mock/status")
def mock_status():
    """Health check showing artifact counts and pushed row counts."""
    pushed_summary = {}
    for ds_id, tables in _pushed_rows.items():
        pushed_summary[ds_id] = {tbl: len(rows) for tbl, rows in tables.items()}

    return {
        "status": "running",
        "artifacts": {
            "workspaces": 1,
            "datasets": len(DATASETS),
            "reports": len(REPORTS),
            "dashboards": len(DASHBOARDS),
            "tiles": sum(len(tiles) for tiles in DASHBOARD_TILES.values()),
        },
        "pushed_rows": pushed_summary,
    }


@app.get("/mock/pushed-rows/{dataset_id}/{table_name}")
def get_pushed_rows(dataset_id: str, table_name: str):
    """Retrieve rows pushed via POST (for verification)."""
    rows = _pushed_rows.get(dataset_id, {}).get(table_name, [])
    return {"dataset_id": dataset_id, "table_name": table_name, "row_count": len(rows), "rows": rows}


# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------

def start_mock_server(host="127.0.0.1", port=6789):
    """Start the mock PBI API server programmatically."""
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning")
