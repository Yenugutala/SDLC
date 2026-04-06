"""Mock Power BI Data Model: Central source of truth for all PBI artifact definitions.

All UUIDs are deterministic for reproducibility. Internal mapping fields
(gold_view, gold_column) are used by the lineage builder but stripped from
API responses by the mock server.
"""

import os


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "pipeline.db")

# Mock PBI API server settings
PBI_MOCK_HOST = "127.0.0.1"
PBI_MOCK_PORT = 6789

# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------
WORKSPACE = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Healthcare Analytics",
    "isReadOnly": False,
    "isOnDedicatedCapacity": False,
}

# ---------------------------------------------------------------------------
# Datasets — keyed to Gold views
# ---------------------------------------------------------------------------
DATASETS = [
    {
        "id": "d001-clinical-analytics-dataset-id",
        "name": "Patient Clinical Analytics",
        "addRowsAPIEnabled": True,
        "configuredBy": "admin@healthcare.local",
        "isRefreshable": True,
        "isEffectiveIdentityRequired": False,
        "isEffectiveIdentityRolesRequired": False,
        "isOnPremGatewayRequired": False,
        "gold_view": "gold_vw_hqb",
    },
    {
        "id": "d002-financial-performance-dataset-id",
        "name": "Financial Performance",
        "addRowsAPIEnabled": True,
        "configuredBy": "admin@healthcare.local",
        "isRefreshable": True,
        "isEffectiveIdentityRequired": False,
        "isEffectiveIdentityRolesRequired": False,
        "isOnPremGatewayRequired": False,
        "gold_view": "gold_vw_ohg",
    },
]

# ---------------------------------------------------------------------------
# Tables within each dataset — maps Gold columns to PBI business names
# ---------------------------------------------------------------------------
DATASET_TABLES = {
    "d001-clinical-analytics-dataset-id": [
        {
            "name": "PatientClinical",
            "columns": [
                {"name": "PatientID", "dataType": "String", "gold_column": "dim_h7"},
                {"name": "FullName", "dataType": "String", "gold_column": "dim_0p"},
                {"name": "Age", "dataType": "Int64", "gold_column": "dim_7x"},
                {"name": "Gender", "dataType": "String", "gold_column": "attr_dg"},
                {"name": "BloodType", "dataType": "String", "gold_column": "fct_cp"},
                {"name": "VisitDate", "dataType": "DateTime", "gold_column": "attr_fw"},
                {"name": "Department", "dataType": "String", "gold_column": "fct_ls"},
                {"name": "Diagnosis", "dataType": "String", "gold_column": "dim_69"},
                {"name": "DoctorName", "dataType": "String", "gold_column": "dim_pt"},
                {"name": "Treatment", "dataType": "String", "gold_column": "dim_mz"},
                {"name": "VisitStatus", "dataType": "String", "gold_column": "attr_e5"},
            ],
            "measures": [
                {
                    "name": "Patient Count",
                    "expression": "COUNTROWS(PatientClinical)",
                    "dependent_columns": ["PatientID"],
                },
                {
                    "name": "Avg Patient Age",
                    "expression": "AVERAGE(PatientClinical[Age])",
                    "dependent_columns": ["Age"],
                },
                {
                    "name": "Unique Departments",
                    "expression": "DISTINCTCOUNT(PatientClinical[Department])",
                    "dependent_columns": ["Department"],
                },
                {
                    "name": "Active Visits",
                    "expression": 'CALCULATE(COUNTROWS(PatientClinical), PatientClinical[VisitStatus]="Completed")',
                    "dependent_columns": ["VisitStatus"],
                },
            ],
        }
    ],
    "d002-financial-performance-dataset-id": [
        {
            "name": "FinancialRecords",
            "columns": [
                {"name": "VisitID", "dataType": "String", "gold_column": "dim_ed"},
                {"name": "PatientID", "dataType": "String", "gold_column": "fct_tz"},
                {"name": "Department", "dataType": "String", "gold_column": "attr_7r"},
                {"name": "ProcedureCode", "dataType": "String", "gold_column": "fct_0v"},
                {"name": "BillAmount", "dataType": "Double", "gold_column": "msr_35"},
                {"name": "InsuranceCovered", "dataType": "Double", "gold_column": "dim_fx"},
                {"name": "PatientCopay", "dataType": "Double", "gold_column": "key_m8"},
                {"name": "OutOfPocket", "dataType": "Double", "gold_column": "key_yd"},
                {"name": "InsuranceProvider", "dataType": "String", "gold_column": "msr_oj"},
                {"name": "PaymentStatus", "dataType": "String", "gold_column": "attr_pn"},
                {"name": "BillingDate", "dataType": "DateTime", "gold_column": "key_cs"},
            ],
            "measures": [
                {
                    "name": "Total Revenue",
                    "expression": "SUM(FinancialRecords[BillAmount])",
                    "dependent_columns": ["BillAmount"],
                },
                {
                    "name": "Avg Copay",
                    "expression": "AVERAGE(FinancialRecords[PatientCopay])",
                    "dependent_columns": ["PatientCopay"],
                },
                {
                    "name": "Insurance Coverage Rate",
                    "expression": "DIVIDE(SUM(FinancialRecords[InsuranceCovered]), SUM(FinancialRecords[BillAmount]))",
                    "dependent_columns": ["InsuranceCovered", "BillAmount"],
                },
                {
                    "name": "Total Out Of Pocket",
                    "expression": "SUM(FinancialRecords[OutOfPocket])",
                    "dependent_columns": ["OutOfPocket"],
                },
                {
                    "name": "Paid Claims",
                    "expression": 'CALCULATE(COUNTROWS(FinancialRecords), FinancialRecords[PaymentStatus]="Paid")',
                    "dependent_columns": ["PaymentStatus"],
                },
            ],
        }
    ],
}

# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
REPORTS = [
    {
        "id": "r001-patient-demographics-report-id",
        "name": "Patient Demographics Overview",
        "datasetId": "d001-clinical-analytics-dataset-id",
        "reportType": "PowerBIReport",
        "description": "Demographics breakdown by age, gender, blood type across departments",
        "webUrl": "https://app.powerbi.com/groups/a1b2c3d4-e5f6-7890-abcd-ef1234567890/reports/r001-patient-demographics-report-id",
        "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=r001-patient-demographics-report-id&groupId=a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    },
    {
        "id": "r002-department-performance-report-id",
        "name": "Department Performance",
        "datasetId": "d001-clinical-analytics-dataset-id",
        "reportType": "PowerBIReport",
        "description": "Department-level visit volumes, diagnosis distribution, treatment patterns",
        "webUrl": "https://app.powerbi.com/groups/a1b2c3d4-e5f6-7890-abcd-ef1234567890/reports/r002-department-performance-report-id",
        "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=r002-department-performance-report-id&groupId=a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    },
    {
        "id": "r003-revenue-analysis-report-id",
        "name": "Revenue Analysis",
        "datasetId": "d002-financial-performance-dataset-id",
        "reportType": "PowerBIReport",
        "description": "Revenue trends, billing analysis, procedure-level cost breakdown",
        "webUrl": "https://app.powerbi.com/groups/a1b2c3d4-e5f6-7890-abcd-ef1234567890/reports/r003-revenue-analysis-report-id",
        "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=r003-revenue-analysis-report-id&groupId=a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    },
    {
        "id": "r004-insurance-coverage-report-id",
        "name": "Insurance Coverage Report",
        "datasetId": "d002-financial-performance-dataset-id",
        "reportType": "PowerBIReport",
        "description": "Insurance provider analysis, coverage rates, copay distribution",
        "webUrl": "https://app.powerbi.com/groups/a1b2c3d4-e5f6-7890-abcd-ef1234567890/reports/r004-insurance-coverage-report-id",
        "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=r004-insurance-coverage-report-id&groupId=a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    },
]

# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------
DASHBOARDS = [
    {
        "id": "db001-executive-summary-dashboard-id",
        "displayName": "Executive Summary",
        "isReadOnly": False,
        "embedUrl": "https://app.powerbi.com/dashboardEmbed?dashboardId=db001-executive-summary-dashboard-id&groupId=a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    },
    {
        "id": "db002-operational-metrics-dashboard-id",
        "displayName": "Operational Metrics",
        "isReadOnly": False,
        "embedUrl": "https://app.powerbi.com/dashboardEmbed?dashboardId=db002-operational-metrics-dashboard-id&groupId=a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    },
]

# ---------------------------------------------------------------------------
# Tiles within dashboards
# ---------------------------------------------------------------------------
DASHBOARD_TILES = {
    "db001-executive-summary-dashboard-id": [
        {
            "id": "t001-patient-count-tile",
            "title": "Total Patient Count",
            "reportId": "r001-patient-demographics-report-id",
            "datasetId": "d001-clinical-analytics-dataset-id",
            "rowSpan": 1,
            "colSpan": 2,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db001&tileId=t001",
        },
        {
            "id": "t002-total-revenue-tile",
            "title": "Total Revenue",
            "reportId": "r003-revenue-analysis-report-id",
            "datasetId": "d002-financial-performance-dataset-id",
            "rowSpan": 1,
            "colSpan": 2,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db001&tileId=t002",
        },
        {
            "id": "t003-department-breakdown-tile",
            "title": "Department Visit Breakdown",
            "reportId": "r002-department-performance-report-id",
            "datasetId": "d001-clinical-analytics-dataset-id",
            "rowSpan": 2,
            "colSpan": 3,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db001&tileId=t003",
        },
        {
            "id": "t004-insurance-coverage-rate-tile",
            "title": "Insurance Coverage Rate",
            "reportId": "r004-insurance-coverage-report-id",
            "datasetId": "d002-financial-performance-dataset-id",
            "rowSpan": 1,
            "colSpan": 2,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db001&tileId=t004",
        },
    ],
    "db002-operational-metrics-dashboard-id": [
        {
            "id": "t005-avg-copay-tile",
            "title": "Average Patient Copay",
            "reportId": "r003-revenue-analysis-report-id",
            "datasetId": "d002-financial-performance-dataset-id",
            "rowSpan": 1,
            "colSpan": 2,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db002&tileId=t005",
        },
        {
            "id": "t006-active-visits-tile",
            "title": "Active Visit Count",
            "reportId": "r001-patient-demographics-report-id",
            "datasetId": "d001-clinical-analytics-dataset-id",
            "rowSpan": 1,
            "colSpan": 2,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db002&tileId=t006",
        },
        {
            "id": "t007-payment-status-tile",
            "title": "Payment Status Distribution",
            "reportId": "r004-insurance-coverage-report-id",
            "datasetId": "d002-financial-performance-dataset-id",
            "rowSpan": 2,
            "colSpan": 3,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db002&tileId=t007",
        },
        {
            "id": "t008-avg-age-tile",
            "title": "Average Patient Age",
            "reportId": "r002-department-performance-report-id",
            "datasetId": "d001-clinical-analytics-dataset-id",
            "rowSpan": 1,
            "colSpan": 2,
            "embedUrl": "https://app.powerbi.com/embed?dashboardId=db002&tileId=t008",
        },
    ],
}

# ---------------------------------------------------------------------------
# Datasources — link datasets back to Gold layer
# ---------------------------------------------------------------------------
DATASET_DATASOURCES = {
    "d001-clinical-analytics-dataset-id": [
        {
            "datasourceType": "Sql",
            "connectionDetails": {
                "server": "localhost",
                "database": "pipeline.db",
                "path": DB_PATH,
            },
            "datasourceId": "ds001-clinical-datasource-id",
            "gatewayId": "gw001-local-gateway-id",
            "gold_view": "gold_vw_hqb",
        }
    ],
    "d002-financial-performance-dataset-id": [
        {
            "datasourceType": "Sql",
            "connectionDetails": {
                "server": "localhost",
                "database": "pipeline.db",
                "path": DB_PATH,
            },
            "datasourceId": "ds002-financial-datasource-id",
            "gatewayId": "gw001-local-gateway-id",
            "gold_view": "gold_vw_ohg",
        }
    ],
}

# ---------------------------------------------------------------------------
# Refresh history
# ---------------------------------------------------------------------------
REFRESH_HISTORY = {
    "d001-clinical-analytics-dataset-id": [
        {
            "refreshType": "ViaApi",
            "startTime": "2026-03-25T08:00:00.000Z",
            "endTime": "2026-03-25T08:02:15.000Z",
            "status": "Completed",
            "requestId": "ref-001-clinical",
        },
    ],
    "d002-financial-performance-dataset-id": [
        {
            "refreshType": "ViaApi",
            "startTime": "2026-03-25T08:05:00.000Z",
            "endTime": "2026-03-25T08:07:30.000Z",
            "status": "Completed",
            "requestId": "ref-001-financial",
        },
    ],
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_pbi_to_gold_column_map(dataset_id):
    """Return {pbi_column_name: gold_column_name} for a dataset."""
    tables = DATASET_TABLES.get(dataset_id, [])
    mapping = {}
    for table in tables:
        for col in table["columns"]:
            mapping[col["name"]] = col["gold_column"]
    return mapping


def get_gold_to_pbi_column_map(dataset_id):
    """Return {gold_column_name: pbi_column_name} for a dataset."""
    return {v: k for k, v in get_pbi_to_gold_column_map(dataset_id).items()}


def get_dataset_by_gold_view(gold_view):
    """Find the dataset that maps to a given Gold view."""
    for ds in DATASETS:
        if ds["gold_view"] == gold_view:
            return ds
    return None


def get_dataset_by_id(dataset_id):
    """Find a dataset by its ID."""
    for ds in DATASETS:
        if ds["id"] == dataset_id:
            return ds
    return None


def get_report_by_id(report_id):
    """Find a report by its ID."""
    for r in REPORTS:
        if r["id"] == report_id:
            return r
    return None
