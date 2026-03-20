"""Data profiling using Great Expectations 1.8.x + pandas for each layer."""

import json
import os
import sqlite3
import pandas as pd
import great_expectations as gx
from great_expectations import expectations as gxe

from pipeline.schema_utils import get_tables_by_prefix


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def profile_dataframe(df, table_name):
    """Profile a dataframe using pandas for basic stats."""
    profile = {"table_name": table_name, "row_count": len(df), "columns": {}}

    for col in df.columns:
        col_stats = {
            "data_type": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(float(df[col].isnull().mean() * 100), 2),
            "unique_count": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(3).tolist(),
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            col_stats["min"] = float(df[col].min()) if not df[col].isnull().all() else None
            col_stats["max"] = float(df[col].max()) if not df[col].isnull().all() else None
            col_stats["mean"] = round(float(df[col].mean()), 2) if not df[col].isnull().all() else None
        else:
            col_stats["min_length"] = int(df[col].astype(str).str.len().min())
            col_stats["max_length"] = int(df[col].astype(str).str.len().max())

        profile["columns"][col] = col_stats

    return profile


def build_expectations(df, table_name, profile):
    """Auto-generate and run GE expectations based on data characteristics."""
    context = gx.get_context()

    ds = context.data_sources.add_pandas(f"ds_{table_name}")
    asset = ds.add_dataframe_asset(f"asset_{table_name}")
    batch_def = asset.add_batch_definition_whole_dataframe(f"batch_{table_name}")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(gx.ExpectationSuite(name=f"suite_{table_name}"))

    # Row count expectation
    row_count = profile["row_count"]
    suite.add_expectation(
        gxe.ExpectTableRowCountToBeBetween(min_value=row_count, max_value=row_count)
    )

    for col_name, col_stats in profile["columns"].items():
        # Not-null expectation for columns with 0% nulls
        if col_stats["null_pct"] == 0:
            suite.add_expectation(
                gxe.ExpectColumnValuesToNotBeNull(column=col_name)
            )

        # Uniqueness expectation for identifier columns
        if col_stats["unique_count"] == row_count:
            suite.add_expectation(
                gxe.ExpectColumnValuesToBeUnique(column=col_name)
            )

        # Range expectation for numeric columns
        if "min" in col_stats and col_stats["min"] is not None:
            suite.add_expectation(
                gxe.ExpectColumnValuesToBeBetween(
                    column=col_name,
                    min_value=col_stats["min"],
                    max_value=col_stats["max"],
                )
            )

        # Set expectation for low-cardinality columns
        if col_stats["unique_count"] <= 10 and col_stats["unique_count"] > 0:
            distinct_values = df[col_name].dropna().unique().tolist()
            suite.add_expectation(
                gxe.ExpectColumnDistinctValuesToBeInSet(
                    column=col_name, value_set=distinct_values
                )
            )

    # Run validation
    result = batch.validate(suite)

    # Extract expectation results
    expectations_output = {
        "success": result.success,
        "expectations_count": len(result.results),
        "successful": sum(1 for r in result.results if r.success),
        "failed": sum(1 for r in result.results if not r.success),
        "results": [],
    }

    for r in result.results:
        exp_result = {
            "expectation_type": r.expectation_config.type,
            "success": r.success,
            "kwargs": {
                k: v for k, v in r.expectation_config.kwargs.items()
                if k not in ("batch_id",)
            },
        }
        if r.result:
            exp_result["observed_value"] = r.result.get("observed_value")
        expectations_output["results"].append(exp_result)

    # Cleanup context resources for this table
    context.suites.delete(f"suite_{table_name}")

    return expectations_output


def run_profiling(db_path=None):
    """Profile all layers: bronze, silver, gold with pandas stats + GE expectations."""
    db_path = db_path or DB_PATH
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = sqlite3.connect(db_path)

    tables = {
        "bronze": get_tables_by_prefix(db_path, "bronze_"),
        "silver": get_tables_by_prefix(db_path, "silver_"),
        "gold": get_tables_by_prefix(db_path, "gold_"),
    }

    all_profiles = {}

    for layer, table_list in tables.items():
        layer_profiles = {}
        for table_name in table_list:
            try:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

                # Pandas-based profiling (stats)
                profile = profile_dataframe(df, table_name)

                # Great Expectations validation
                ge_results = build_expectations(df, table_name, profile)
                profile["expectations"] = ge_results

                layer_profiles[table_name] = profile
                print(
                    f"[Profiling] {layer}/{table_name}: {len(df)} rows, "
                    f"{len(df.columns)} cols, "
                    f"{ge_results['expectations_count']} expectations "
                    f"({ge_results['successful']} passed, {ge_results['failed']} failed)"
                )
            except Exception as e:
                print(f"[Profiling] Error profiling {table_name}: {e}")
                layer_profiles[table_name] = {"error": str(e)}

        all_profiles[layer] = layer_profiles

        output_path = os.path.join(OUTPUT_DIR, f"{layer}_profile.json")
        with open(output_path, "w") as f:
            json.dump(layer_profiles, f, indent=2, default=str)

    conn.close()

    print(f"[Profiling] Results saved to {OUTPUT_DIR}")
    return all_profiles


if __name__ == "__main__":
    run_profiling()
