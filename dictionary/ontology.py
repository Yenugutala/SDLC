"""Ontology: Define entity relationships across all layers."""

import json
import os


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiling_output")


def generate_ontology():
    """Generate ontology describing entity relationships across layers."""

    ontology = {
        "entities": {
            "Patient": {
                "description": "A person receiving healthcare services",
                "source_file": "patients.csv",
                "primary_key": "patient_id",
                "attributes": [
                    "first_name", "last_name", "dob", "gender",
                    "blood_type", "phone", "address", "insurance_provider",
                ],
                "layers": {
                    "bronze": {"table": "bronze_patients", "key_column": "patient_id"},
                    "silver": {"table": "silver_tbl_a1", "key_column": "col_x1a"},
                    "gold": {"view": "gold_vw_p99", "key_column": "attr_m1"},
                },
            },
            "Visit": {
                "description": "A healthcare encounter or appointment for a patient",
                "source_file": "visits.csv",
                "primary_key": "visit_id",
                "attributes": [
                    "visit_date", "department", "diagnosis",
                    "doctor_name", "treatment", "bill_amount", "status",
                ],
                "layers": {
                    "bronze": {"table": "bronze_visits", "key_column": "visit_id"},
                    "silver": {"table": "silver_tbl_b2", "key_column": "col_y2b"},
                    "gold": {"view": "gold_vw_q88", "key_column": "dim_n1"},
                },
            },
        },
        "relationships": [
            {
                "name": "Patient has Visits",
                "type": "one_to_many",
                "from_entity": "Patient",
                "to_entity": "Visit",
                "join_description": "A patient can have multiple visits. Linked by patient_id.",
                "join_keys": {
                    "bronze": {
                        "from_table": "bronze_patients",
                        "from_column": "patient_id",
                        "to_table": "bronze_visits",
                        "to_column": "patient_id",
                    },
                    "silver": {
                        "from_table": "silver_tbl_a1",
                        "from_column": "col_x1a",
                        "to_table": "silver_tbl_b2",
                        "to_column": "col_x1a",
                    },
                    "gold": {
                        "from_table": "gold_vw_p99",
                        "from_column": "attr_m1",
                        "to_table": "gold_vw_q88",
                        "to_column": "dim_n2",
                    },
                },
            }
        ],
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "ontology.json")
    with open(output_path, "w") as f:
        json.dump(ontology, f, indent=2)

    print(f"[Ontology] Generated ontology with {len(ontology['entities'])} entities and {len(ontology['relationships'])} relationships")
    print(f"[Ontology] Saved to {output_path}")
    return ontology


if __name__ == "__main__":
    generate_ontology()
