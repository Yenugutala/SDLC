"""Data Dictionary: Auto-generate column descriptions using LLM — no hardcoded patterns."""

import json
import os
import re
import anthropic
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def generate_descriptions_llm(table_name, layer, columns_info, row_count):
    """Use LLM to generate descriptions for all columns in a table (one API call per table)."""
    client = anthropic.Anthropic()

    columns_context = []
    for col_name, info in columns_info:
        ctx = f"- {col_name}"
        original = info.get("original_name", col_name)
        if original != col_name:
            ctx += f" (original name: {original})"
        ctx += f" | type: {info['data_type']}"
        if info.get("sample_values"):
            samples = [str(s) for s in info["sample_values"][:3]]
            ctx += f" | samples: {', '.join(samples)}"
        ctx += f" | null: {info.get('null_pct', 0)}%"
        ctx += f" | unique: {info.get('unique_count', 0)}/{row_count}"
        columns_context.append(ctx)

    prompt = (
        f"Generate a brief description (1 sentence) for each column in this database table.\n"
        f"Use the column name, data type, sample values, and statistics to infer meaning.\n\n"
        f"Table: {table_name} (Layer: {layer}, {row_count} rows)\n"
        f"Columns:\n"
        f"{chr(10).join(columns_context)}\n\n"
        f'Return ONLY a valid JSON object: {{"column_name": "description", ...}}\n'
        f"No markdown, no explanation, just the JSON object."
    )

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # Strip markdown code blocks if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        # Try to extract JSON from response
        try:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        print(f"[Dictionary] Warning: LLM call failed for {table_name}: {e}")
        return {}


def fallback_description(col_name, data_type, stats, row_count):
    """Simple fallback if LLM fails: humanize column name + stats."""
    parts = [col_name.replace("_", " ").title()]
    if "int" in data_type or "float" in data_type:
        if stats.get("min") is not None:
            parts.append(f"Range: {stats['min']}-{stats['max']}")
    unique = stats.get("unique_count", 0)
    if row_count > 0 and unique == row_count:
        parts.append("Unique per row")
    elif unique > 0:
        parts.append(f"{unique} distinct values")
    if stats.get("null_pct", 0) > 0:
        parts.append(f"{stats['null_pct']}% null")
    return ". ".join(parts)


def generate_data_dictionary():
    """Generate a data dictionary using LLM for column descriptions."""

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

            row_count = table_profile["row_count"]

            # Prepare column info for LLM
            columns_for_llm = []
            for col_name, col_stats in table_profile.get("columns", {}).items():
                original_col = col_to_original.get(col_name, col_name)
                columns_for_llm.append((col_name, {
                    "original_name": original_col,
                    "data_type": col_stats.get("data_type", "unknown"),
                    "sample_values": col_stats.get("sample_values", []),
                    "null_pct": col_stats.get("null_pct", 0),
                    "unique_count": col_stats.get("unique_count", 0),
                }))

            # Generate descriptions via LLM (one call per table)
            print(f"[Dictionary] Generating descriptions for {table_name} via LLM...")
            llm_descriptions = generate_descriptions_llm(
                table_name, layer, columns_for_llm, row_count
            )

            table_dict = {
                "table_name": table_name,
                "row_count": row_count,
                "columns": [],
            }
            for col_name, col_stats in table_profile.get("columns", {}).items():
                original_col = col_to_original.get(col_name, col_name)

                # Use LLM description, fallback if not available
                description = llm_descriptions.get(col_name)
                if not description:
                    description = fallback_description(
                        original_col,
                        col_stats.get("data_type", "unknown"),
                        col_stats,
                        row_count,
                    )

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
