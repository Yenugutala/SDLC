"""Data Dictionary: Generate column descriptions for all layers."""

import json
import os


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")

# Human-readable descriptions for original columns
COLUMN_DESCRIPTIONS = {
    "patient_id": "Unique identifier for each patient in the healthcare system",
    "first_name": "Patient's first/given name",
    "last_name": "Patient's last/family name",
    "dob": "Patient's date of birth (YYYY-MM-DD format)",
    "gender": "Patient's gender (Male/Female)",
    "blood_type": "Patient's blood type (A+, B-, O+, AB+, etc.)",
    "phone": "Patient's contact phone number",
    "address": "Patient's residential address",
    "insurance_provider": "Name of the patient's health insurance provider",
    "visit_id": "Unique identifier for each patient visit/encounter",
    "visit_date": "Date of the patient visit (YYYY-MM-DD format)",
    "department": "Medical department where the visit occurred",
    "diagnosis": "Medical diagnosis recorded during the visit",
    "doctor_name": "Name of the attending physician",
    "treatment": "Treatment or procedure administered during the visit",
    "bill_amount": "Total bill amount for the visit in USD",
    "status": "Current status of the visit (Completed/In Progress)",
}


def generate_data_dictionary():
    """Generate a data dictionary combining profiling stats and descriptions."""

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
                description = COLUMN_DESCRIPTIONS.get(original_col, f"Derived column mapped from {original_col}")

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
