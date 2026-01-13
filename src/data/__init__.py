"""
Data management components for Data Platform Knowledge Graph.
"""

from src.data.dataIngestion import (
    ingestAllData,
    ingestPipelines,
    ingestTables,
    ingestColumns,
    ingestConfluencePages,
    ingestJiraTickets,
    ingestAlerts,
    ingestDataQualityRules,
    ingestEnvironments
)
from src.data.mockData import (
    pipelines,
    tables,
    columns,
    confluencePages,
    jiraTickets,
    alerts,
    dataQualityRules,
    environments
)

__all__ = [
    'ingestAllData',
    'ingestPipelines',
    'ingestTables',
    'ingestColumns',
    'ingestConfluencePages',
    'ingestJiraTickets',
    'ingestAlerts',
    'ingestDataQualityRules',
    'ingestEnvironments',
    'pipelines',
    'tables',
    'columns',
    'confluencePages',
    'jiraTickets',
    'alerts',
    'dataQualityRules',
    'environments'
]
