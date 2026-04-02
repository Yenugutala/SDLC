"""PBI Lineage Builder: Discover PBI artifacts via REST API and build lineage.

Two outputs:
  1. pbi_lineage.json — PBI-internal: Tile -> Report -> Dataset -> Column/Measure
  2. pbi_end_to_end_lineage.json — Joined: PBI -> Gold -> Silver -> Bronze -> CSV
"""

import json
import os
import httpx

from powerbi.mock_data_model import (
    WORKSPACE, DATASET_TABLES, PBI_MOCK_HOST, PBI_MOCK_PORT,
    get_pbi_to_gold_column_map,
)


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "profiling_output")


def _get(client, path):
    """GET a path from the PBI API and return the 'value' list."""
    resp = client.get(path)
    resp.raise_for_status()
    return resp.json().get("value", [])


def discover_pbi_artifacts(api_base_url=None):
    """Call each PBI API endpoint to discover all artifacts.

    Returns a dict with all discovered artifacts keyed by type.
    """
    api_base_url = api_base_url or f"http://{PBI_MOCK_HOST}:{PBI_MOCK_PORT}"
    client = httpx.Client(base_url=api_base_url, timeout=10.0)

    # Step 1: Discover workspace
    groups = _get(client, "/v1.0/myorg/groups")
    if not groups:
        raise RuntimeError("No workspaces found")
    group_id = groups[0]["id"]
    base = f"/v1.0/myorg/groups/{group_id}"

    # Step 2: Discover datasets
    datasets = _get(client, f"{base}/datasets")

    # Step 3: For each dataset, discover tables and datasources
    dataset_tables = {}
    dataset_datasources = {}
    for ds in datasets:
        ds_id = ds["id"]
        dataset_tables[ds_id] = _get(client, f"{base}/datasets/{ds_id}/tables")
        dataset_datasources[ds_id] = _get(client, f"{base}/datasets/{ds_id}/datasources")

    # Step 4: Discover reports
    reports = _get(client, f"{base}/reports")

    # Step 5: Discover dashboards and tiles
    dashboards = _get(client, f"{base}/dashboards")
    dashboard_tiles = {}
    for db in dashboards:
        db_id = db["id"]
        dashboard_tiles[db_id] = _get(client, f"{base}/dashboards/{db_id}/tiles")

    # Step 6: Discover refresh history
    refresh_history = {}
    for ds in datasets:
        ds_id = ds["id"]
        resp = client.get(f"/v1.0/myorg/datasets/{ds_id}/refreshes")
        resp.raise_for_status()
        refresh_history[ds_id] = resp.json().get("value", [])

    client.close()

    return {
        "workspace": groups[0],
        "datasets": datasets,
        "dataset_tables": dataset_tables,
        "dataset_datasources": dataset_datasources,
        "reports": reports,
        "dashboards": dashboards,
        "dashboard_tiles": dashboard_tiles,
        "refresh_history": refresh_history,
    }


def build_pbi_lineage(api_base_url=None):
    """Discover PBI artifacts via REST API and build PBI lineage.

    Returns the PBI lineage dict and saves both JSON files.
    """
    api_base_url = api_base_url or f"http://{PBI_MOCK_HOST}:{PBI_MOCK_PORT}"

    print("[PBI Lineage] Discovering PBI artifacts via REST API...")
    artifacts = discover_pbi_artifacts(api_base_url)

    # Build report lookup: report_id -> report
    report_lookup = {r["id"]: r for r in artifacts["reports"]}

    # Build dataset lookup: dataset_id -> dataset
    dataset_lookup = {d["id"]: d for d in artifacts["datasets"]}

    # --- Build PBI-internal lineage ---

    # 1. Dashboard -> Tile -> Report -> Dataset lineage
    dashboard_lineage = []
    for db in artifacts["dashboards"]:
        db_id = db["id"]
        db_name = db.get("displayName", db.get("name", db_id))
        tiles_lineage = []

        for tile in artifacts["dashboard_tiles"].get(db_id, []):
            report_id = tile.get("reportId")
            dataset_id = tile.get("datasetId")
            report = report_lookup.get(report_id, {})
            dataset = dataset_lookup.get(dataset_id, {})

            # Find the table and its measures for this dataset
            # Use the internal model for measures (API response strips them)
            tables_from_model = DATASET_TABLES.get(dataset_id, [])
            table_name = tables_from_model[0]["name"] if tables_from_model else "Unknown"
            measures = tables_from_model[0].get("measures", []) if tables_from_model else []

            # Find datasource to get gold_view
            datasources = artifacts["dataset_datasources"].get(dataset_id, [])
            # Gold view comes from internal model since API strips it
            from powerbi.mock_data_model import DATASET_DATASOURCES as _DS_INTERNAL
            internal_ds = _DS_INTERNAL.get(dataset_id, [{}])
            gold_view = internal_ds[0].get("gold_view", "N/A") if internal_ds else "N/A"

            # Match tile to a measure by title heuristic
            tile_title = tile.get("title", "")
            matched_measure = None
            for m in measures:
                # Simple heuristic: check if measure name words appear in tile title
                if m["name"].lower().replace(" ", "") in tile_title.lower().replace(" ", ""):
                    matched_measure = m
                    break

            tile_entry = {
                "tile": tile_title,
                "tile_id": tile.get("id"),
                "report": report.get("name", "Unknown"),
                "report_id": report_id,
                "dataset": dataset.get("name", "Unknown"),
                "dataset_id": dataset_id,
                "table": table_name,
                "gold_view": gold_view,
            }
            if matched_measure:
                tile_entry["measure"] = matched_measure["name"]
                tile_entry["dax_expression"] = matched_measure["expression"]
                tile_entry["dependent_columns"] = matched_measure.get("dependent_columns", [])
            else:
                # All columns in the table are potentially relevant
                all_cols = [c["name"] for c in tables_from_model[0].get("columns", [])] if tables_from_model else []
                tile_entry["dependent_columns"] = all_cols

            tiles_lineage.append(tile_entry)

        dashboard_lineage.append({
            "dashboard": db_name,
            "dashboard_id": db_id,
            "tiles": tiles_lineage,
        })

    # 2. Column mappings (PBI -> Gold)
    column_mappings = []
    for ds in artifacts["datasets"]:
        ds_id = ds["id"]
        pbi_to_gold = get_pbi_to_gold_column_map(ds_id)
        tables_from_model = DATASET_TABLES.get(ds_id, [])

        for table in tables_from_model:
            for col in table["columns"]:
                # Get gold_view from datasource
                internal_ds = _DS_INTERNAL.get(ds_id, [{}])
                gold_view = internal_ds[0].get("gold_view", "N/A") if internal_ds else "N/A"

                column_mappings.append({
                    "pbi_dataset": ds["name"],
                    "pbi_table": table["name"],
                    "pbi_column": col["name"],
                    "pbi_data_type": col["dataType"],
                    "gold_view": gold_view,
                    "gold_column": col.get("gold_column", pbi_to_gold.get(col["name"], "N/A")),
                })

    # 3. Measures
    measures_lineage = []
    for ds in artifacts["datasets"]:
        ds_id = ds["id"]
        tables_from_model = DATASET_TABLES.get(ds_id, [])
        internal_ds = _DS_INTERNAL.get(ds_id, [{}])
        gold_view = internal_ds[0].get("gold_view", "N/A") if internal_ds else "N/A"

        for table in tables_from_model:
            for measure in table.get("measures", []):
                measures_lineage.append({
                    "pbi_dataset": ds["name"],
                    "pbi_table": table["name"],
                    "measure_name": measure["name"],
                    "dax_expression": measure["expression"],
                    "dependent_pbi_columns": measure.get("dependent_columns", []),
                    "gold_view": gold_view,
                })

    pbi_lineage = {
        "dashboards": dashboard_lineage,
        "column_mappings": column_mappings,
        "measures": measures_lineage,
    }

    # Save PBI lineage
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pbi_lineage_path = os.path.join(OUTPUT_DIR, "pbi_lineage.json")
    with open(pbi_lineage_path, "w") as f:
        json.dump(pbi_lineage, f, indent=2)
    print(f"[PBI Lineage] Saved PBI lineage to {pbi_lineage_path}")
    print(f"[PBI Lineage]   Dashboards: {len(dashboard_lineage)}, "
          f"Column mappings: {len(column_mappings)}, "
          f"Measures: {len(measures_lineage)}")

    # --- Build end-to-end lineage (PBI -> Gold -> Silver -> Bronze -> CSV) ---
    _build_end_to_end_lineage(column_mappings)

    return pbi_lineage


def _build_end_to_end_lineage(column_mappings):
    """Join PBI column mappings with existing lineage.json for end-to-end chains."""
    lineage_path = os.path.join(OUTPUT_DIR, "lineage.json")
    if not os.path.exists(lineage_path):
        print("[PBI Lineage] lineage.json not found, skipping end-to-end join")
        return

    with open(lineage_path) as f:
        existing_lineage = json.load(f)

    # Build lookup: (gold_view, gold_column) -> lineage entry
    gold_lookup = {}
    for lineage_key, entries in existing_lineage.items():
        for entry in entries:
            key = (entry.get("gold_view"), entry.get("gold_column"))
            if key != ("N/A", "N/A"):
                gold_lookup[key] = entry

    end_to_end = []
    for cm in column_mappings:
        gold_key = (cm["gold_view"], cm["gold_column"])
        existing = gold_lookup.get(gold_key, {})

        e2e_entry = {
            "pbi_column": cm["pbi_column"],
            "pbi_table": cm["pbi_table"],
            "pbi_dataset": cm["pbi_dataset"],
            "pbi_data_type": cm["pbi_data_type"],
            "gold_view": cm["gold_view"],
            "gold_column": cm["gold_column"],
            "silver_table": existing.get("silver_table", "N/A"),
            "silver_column": existing.get("silver_column", "N/A"),
            "bronze_table": existing.get("bronze_table", "N/A"),
            "bronze_column": existing.get("bronze_column", "N/A"),
            "source_file": existing.get("source_file", "N/A"),
            "source_column": existing.get("source_column", "N/A"),
            "transformation_type": existing.get("transformation_type", "N/A"),
            "transformation_chain": (
                f"{existing.get('source_file', '?')}"
                f" -> {existing.get('bronze_table', '?')}.{existing.get('bronze_column', '?')}"
                f" -> {existing.get('silver_table', '?')}.{existing.get('silver_column', '?')}"
                f" -> {cm['gold_view']}.{cm['gold_column']}"
                f" -> PBI.{cm['pbi_table']}.{cm['pbi_column']}"
            ),
        }
        end_to_end.append(e2e_entry)

    e2e_path = os.path.join(OUTPUT_DIR, "pbi_end_to_end_lineage.json")
    with open(e2e_path, "w") as f:
        json.dump(end_to_end, f, indent=2)
    print(f"[PBI Lineage] Saved end-to-end lineage to {e2e_path}")
    print(f"[PBI Lineage]   {len(end_to_end)} column chains (PBI -> Source)")


if __name__ == "__main__":
    build_pbi_lineage()
