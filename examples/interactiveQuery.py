"""
Interactive Natural Language Query Interface for Data Platform Knowledge Graph.
Supports natural language queries and slash commands for feature search.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.kg import KnowledgeGraph
from src.core.vectorStore import VectorStore
from src.data.mockData import (
    pipelines, tables, columns, confluencePages,
    jiraTickets, alerts, dataQualityRules, environments
)
from src.data.dataIngestion import ingestAllData
from src.utils.formatting import printHeader
from src.queries.naturalLanguageQuery import NaturalLanguageQueryEngine
from src.queries.queryEngine import (
    findFeature, showFeatureStatus, showAllFeatures,
    isFeatureInProject, queryGraphStatistics
)


# =============================================================================
# Constants
# =============================================================================

EXIT_COMMANDS = {'exit', 'quit', 'q'}

FEATURE_QUESTION_KEYWORDS = {'is ', 'does ', 'has ', 'have '}
FEATURE_CONTEXT_KEYWORDS = {'part of', 'in this project', 'in the project', 'exist', 'have'}
WORDS_TO_STRIP = {
    'is', 'does', 'has', 'have', 'this', 'project', 'the', 'a', 'an',
    'part', 'of', 'exist', 'in', '?', 'feature', 'component', 'pipeline', 'table'
}

EXAMPLE_QUESTIONS = [
    "Is customer data part of this project?",
    "Is payment pluggable framework part of this project?",
    "What pipelines are related to fraud detection?",
    "Show me all Jira tickets for the order pipeline",
    "Which tables contain PII data?",
    "What is the status of the inventory sync pipeline?",
    "What Confluence pages document the payment framework?",
    "What data quality rules are configured?",
]

HELP_TEXT = """
================================================================================
AVAILABLE COMMANDS
================================================================================

  Natural Language Queries:
    Just type your question in plain English

  Feature Search Commands:
    /find <feature>     - Check if a feature exists in the project
    /status <feature>   - Get full status of a feature (pipeline, tables, tickets)
    /list               - List all components in the project
    /stats              - Show knowledge graph statistics

  Other Commands:
    /help               - Show this help message
    exit, quit, q       - Exit the program

================================================================================
"""


# =============================================================================
# Helper Functions
# =============================================================================

def printHelp():
    """Display available commands."""
    print(HELP_TEXT)


def printExamples():
    """Display example questions."""
    print("Example questions you can ask:")
    for question in EXAMPLE_QUESTIONS:
        print(f"  - {question}")
    print("\n" + "=" * 80 + "\n")


def loadKnowledgeGraph():
    """Initialize and populate the knowledge graph."""
    kg = KnowledgeGraph()
    vectorDb = VectorStore()

    data = {
        'pipelines': pipelines,
        'tables': tables,
        'columns': columns,
        'confluencePages': confluencePages,
        'jiraTickets': jiraTickets,
        'alerts': alerts,
        'dataQualityRules': dataQualityRules,
        'environments': environments
    }

    ingestAllData(kg, vectorDb, data)
    return kg, vectorDb


def extractFeatureName(userInput: str) -> str:
    """Extract feature name from a natural language question."""
    words = userInput.replace('?', '').split()
    featureWords = [w for w in words if w.lower() not in WORDS_TO_STRIP]
    return ' '.join(featureWords)


def isFeatureQuestion(userInput: str) -> bool:
    """Check if the input is asking about a feature's existence."""
    lowerInput = userInput.lower()
    hasKeyword = any(kw in lowerInput for kw in FEATURE_QUESTION_KEYWORDS)
    hasContext = any(ctx in lowerInput for ctx in FEATURE_CONTEXT_KEYWORDS)
    return hasKeyword and hasContext


def handleFeatureQuestion(kg, vectorDb, userInput: str):
    """Handle 'Is X part of this project?' style questions."""
    featureName = extractFeatureName(userInput)

    if not featureName:
        return

    result = isFeatureInProject(kg, vectorDb, featureName)

    if result['found']:
        print(f"\n  YES - '{featureName}' is part of this project!")
        print(f"\n  Found {result['matchCount']} related items:")
        for match in result['matches'][:3]:
            print(f"    - [{match['type']}] {match['name']}")
        print(f"\n  Use '/status {featureName}' for full status.")
    else:
        print(f"\n  NO - '{featureName}' was not found in this project.")
        print("\n  Try different keywords or use '/list' to see all components.")


# =============================================================================
# Command Handlers
# =============================================================================

class CommandHandler:
    """Handles slash commands and user input routing."""

    def __init__(self, kg, vectorDb, queryEngine):
        self.kg = kg
        self.vectorDb = vectorDb
        self.queryEngine = queryEngine

    def handle(self, userInput: str) -> bool:
        """
        Process user input and execute appropriate action.
        Returns False if user wants to exit, True otherwise.
        """
        if not userInput:
            return True

        if userInput.lower() in EXIT_COMMANDS:
            print("\nGoodbye!")
            return False

        # Route to appropriate handler
        if userInput.startswith('/'):
            self._handleSlashCommand(userInput)
        elif isFeatureQuestion(userInput):
            handleFeatureQuestion(self.kg, self.vectorDb, userInput)
        else:
            self._handleNaturalLanguageQuery(userInput)

        return True

    def _handleSlashCommand(self, userInput: str):
        """Handle slash commands."""
        command = userInput.lower()

        if command == '/help':
            printHelp()

        elif command == '/list':
            showAllFeatures(self.kg)

        elif command == '/stats':
            queryGraphStatistics(self.kg)

        elif command.startswith('/find '):
            featureName = userInput[6:].strip()
            if featureName:
                findFeature(self.kg, self.vectorDb, featureName)
            else:
                print("\n  Usage: /find <feature name>")
                print("  Example: /find customer data")

        elif command.startswith('/status '):
            featureName = userInput[8:].strip()
            if featureName:
                showFeatureStatus(self.kg, self.vectorDb, featureName)
            else:
                print("\n  Usage: /status <feature name>")
                print("  Example: /status fraud detection")

        else:
            print(f"\n  Unknown command: {userInput}")
            print("  Type /help for available commands.")

    def _handleNaturalLanguageQuery(self, userInput: str):
        """Handle natural language queries using the AI engine."""
        printHeader("Searching knowledge graph...\n")
        answer = self.queryEngine.query(self.kg, self.vectorDb, userInput)
        printHeader("ANSWER:")
        print(answer)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the interactive query interface."""
    printHeader("DATA PLATFORM KNOWLEDGE GRAPH - INTERACTIVE QUERY INTERFACE")
    print("\nInitializing knowledge graph...\n")

    # Load data
    kg, vectorDb = loadKnowledgeGraph()
    printHeader("Knowledge graph loaded successfully!")

    # Show help and examples
    printHelp()
    printExamples()

    # Initialize components
    queryEngine = NaturalLanguageQueryEngine()
    handler = CommandHandler(kg, vectorDb, queryEngine)

    # Interactive loop
    while True:
        try:
            userInput = input("Your question: ").strip()
            if not handler.handle(userInput):
                break

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
