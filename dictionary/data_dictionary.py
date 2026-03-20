"""Data Dictionary: Auto-generate column descriptions for all layers."""

import json
import os
import re


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")

# Regex patterns to infer column descriptions from column names
COLUMN_PATTERNS = [
    (r"_id$", "Unique identifier for {entity}"),
    (r"^id$", "Primary identifier"),
    (r"first_name|fname", "First/given name"),
    (r"last_name|lname|surname", "Last/family name"),
    (r"^name$|_name$", "Name field for {entity}"),
    (r"dob|date_of_birth|birth_date", "Date of birth (date format)"),
    (r"_date$|^date_|^dt_", "Date field"),
    (r"gender|sex", "Gender/sex classification"),
    (r"blood_type", "Blood type classification (e.g., A+, B-, O+)"),
    (r"phone|tel|mobile", "Phone/telephone contact number"),
    (r"address|addr|street", "Physical/mailing address"),
    (r"email", "Email address"),
    (r"insurance|insurer", "Insurance provider or plan"),
    (r"department|dept", "Department or organizational unit"),
    (r"diagnosis|dx", "Medical diagnosis"),
    (r"doctor|physician|provider", "Healthcare provider/physician name"),
    (r"treatment|therapy|procedure", "Treatment or medical procedure"),
    (r"bill|amount|cost|price|charge", "Monetary amount (numeric)"),
    (r"status|state", "Current status indicator"),
    (r"visit", "Visit/encounter information"),
    (r"zip|postal", "ZIP/postal code"),
    (r"city", "City name"),
    (r"country", "Country name"),
    (r"age", "Age (numeric)"),
    (r"weight|height", "Physical measurement"),
]


def infer_description(col_name, data_type, stats):
    """Generate a column description from its name, type, and profiling stats."""
    parts = []

    # Pattern match on column name
    matched = False
    for pattern, desc_template in COLUMN_PATTERNS:
        if re.search(pattern, col_name, re.IGNORECASE):
            entity = col_name.replace("_id", "").replace("_", " ").strip()
            parts.append(desc_template.format(entity=entity or "record"))
            matched = True
            break

    if not matched:
        humanized = col_name.replace("_", " ").title()
        parts.append(humanized)

    # Enrich with data type info
    if "float" in data_type or "int" in data_type:
        if "min" in stats and "max" in stats and stats["min"] is not None:
            parts.append(f"Range: {stats['min']}-{stats['max']}")
            if "mean" in stats and stats["mean"] is not None:
                parts.append(f"Avg: {stats['mean']}")

    # Enrich with cardinality info
    unique_count = stats.get("unique_count", 0)
    row_count = stats.get("_row_count", 0)
    if row_count > 0 and unique_count > 0:
        if unique_count == row_count:
            parts.append("Unique per row (likely identifier)")
        elif unique_count <= 10:
            samples = stats.get("sample_values", [])
            parts.append(f"{unique_count} distinct values")
            if samples:
                parts.append(f"e.g., {', '.join(str(s) for s in samples[:3])}")
        else:
            parts.append(f"{unique_count} distinct values")

    # Null info
    null_pct = stats.get("null_pct", 0)
    if null_pct > 0:
        parts.append(f"{null_pct}% null")

    return ". ".join(parts)


def generate_data_dictionary():
    """Generate a data dictionary combining profiling stats and auto-inferred descriptions."""

    # Load profiling data
    profiles = {}
    for layer in ["bronze", "silver", "gold"]:
        profile_path = os.path.join(OUTPUT_DIR, f"{layer}_profile.json")
        if os.path.exists(profile_path):
            with open(profile_path) as f:
                profiles[layer] = json.load(f)

    # Load lineage
    lineage_path = os.path.join(OUTPUT_DIR, "lineage.json")
    lineage_data = {}
    if os.path.exists(lineage_path):
        with open(lineage_path) as f:
            lineage_data = json.load(f)

    # Build reverse lookup: obfuscated_col -> original_col
    col_to_original = {}
    for lineage_list in lineage_data.values():
        for entry in lineage_list:
            col_to_original[entry["silver_column"]] = entry["source_column"]
            col_to_original[entry["gold_column"]] = entry["source_column"]
            col_to_original[entry["bronze_column"]] = entry["source_column"]

    data_dictionary = {}

    for layer, tables in profiles.items():
        data_dictionary[layer] = {}
        for table_name, table_profile in tables.items():
            if "error" in table_profile:
                continue
            table_dict = {
                "table_name": table_name,
                "row_count": table_profile["row_count"],
                "columns": [],
            }
            for col_name, col_stats in table_profile.get("columns", {}).items():
                original_col = col_to_original.get(col_name, col_name)

                # Auto-infer description from column name + stats
                enriched_stats = {**col_stats, "_row_count": table_profile["row_count"]}
                description = infer_description(original_col, col_stats.get("data_type", "unknown"), enriched_stats)

                col_entry = {
                    "column_name": col_name,
                    "original_name": original_col,
                    "data_type": col_stats.get("data_type", "unknown"),
                    "description": description,
                    "null_pct": col_stats.get("null_pct", 0),
                    "unique_count": col_stats.get("unique_count", 0),
                    "sample_values": col_stats.get("sample_values", []),
                }
                table_dict["columns"].append(col_entry)

            data_dictionary[layer][table_name] = table_dict

    output_path = os.path.join(OUTPUT_DIR, "data_dictionary.json")
    with open(output_path, "w") as f:
        json.dump(data_dictionary, f, indent=2, default=str)

    print(f"[Dictionary] Generated data dictionary for {sum(len(t) for t in data_dictionary.values())} tables")
    print(f"[Dictionary] Saved to {output_path}")
    return data_dictionary


if __name__ == "__main__":
    generate_data_dictionary()
