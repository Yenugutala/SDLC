"""
Formatting utilities for graceful output display.
"""

from typing import Optional

# Constants for consistent formatting
SEPARATOR_CHAR = "="
SUBSEPARATOR_CHAR = "-"
DEFAULT_WIDTH = 80


def printSeparator(width: int = DEFAULT_WIDTH, char: str = SEPARATOR_CHAR, newline_before: bool = True) -> None:
    """
    Print a separator line.

    Args:
        width: Width of the separator line
        char: Character to use for the separator
        newline_before: Whether to print a newline before the separator

    Example:
        printSeparator()
        # Output:
        # ================================================================================
    """
    if newline_before:
        print()
    print(char * width)


def printHeader(text: str, width: int = DEFAULT_WIDTH) -> None:
    """
    Print a header with separators above and below.

    Args:
        text: Header text to display
        width: Width of the separator lines

    Example:
        printHeader("MAIN TITLE")
        # Output:
        # ================================================================================
        # MAIN TITLE
        # ================================================================================
    """
    printSeparator(width, newline_before=True)
    print(text)
    printSeparator(width, newline_before=False)


def printSubHeader(text: str, width: int = DEFAULT_WIDTH) -> None:
    """
    Print a subheader with separator above.

    Args:
        text: Subheader text to display
        width: Width of the separator line

    Example:
        printSubHeader("Section Title")
        # Output:
        #
        # --------------------------------------------------------------------------------
        # Section Title
        # --------------------------------------------------------------------------------
    """
    printSeparator(width, SUBSEPARATOR_CHAR, newline_before=True)
    print(text)
    printSeparator(width, SUBSEPARATOR_CHAR, newline_before=False)


def printSection(title: str, content: Optional[str] = None, width: int = DEFAULT_WIDTH) -> None:
    """
    Print a section with title and optional content.

    Args:
        title: Section title
        content: Optional content to display
        width: Width of the separator linethe 

    Example:
        printSection("Results", "Found 10 items")
    """
    printSeparator(width, SUBSEPARATOR_CHAR, newline_before=True)
    print(title)
    printSeparator(width, SUBSEPARATOR_CHAR, newline_before=False)
    if content:
        print(content)


def formatNodeInfo(nodeType: str, nodeName: str, nodeId: str, distance: Optional[float] = None) -> str:
    """
    Format node information for display.

    Args:
        nodeType: Type of the node (e.g., 'Pipeline', 'Dataset')
        nodeName: Name of the node
        nodeId: ID of the node
        distance: Optional distance/similarity score

    Returns:
        Formatted string

    Example:
        formatNodeInfo("Pipeline", "Data Pipeline", "pipeline_1", 0.23)
        # Output: "[Pipeline] Data Pipeline (ID: pipeline_1) (distance: 0.230)"
    """
    base = f"[{nodeType}] {nodeName} (ID: {nodeId})"
    if distance is not None:
        return f"{base} (distance: {distance:.3f})"
    return base


def formatRelationship(relation: str, targetType: str, targetName: str,
                       targetId: Optional[str] = None, direction: str = "-->") -> str:
    """
    Format relationship information for display.

    Args:
        relation: Relationship type (e.g., 'PRODUCES', 'CONTAINS')
        targetType: Type of the target node
        targetName: Name of the target node
        targetId: Optional ID of the target node
        direction: Direction arrow (default: "-->")

    Returns:
        Formatted string

    Example:
        formatRelationship("PRODUCES", "Dataset", "Sales Data", "ds_1")
        # Output: "--[PRODUCES]--> [Dataset] Sales Data (ID: ds_1)"
    """
    target = f"[{targetType}] {targetName}"
    if targetId:
        target += f" (ID: {targetId})"
    return f"--[{relation}]{direction} {target}"


# Convenience functions for common use cases
def header(text: str) -> None:
    """Shorthand for printHeader."""
    printHeader(text)


def subheader(text: str) -> None:
    """Shorthand for printSubHeader."""
    printSubHeader(text)


def separator(newline: bool = True) -> None:
    """Shorthand for printSeparator."""
    printSeparator(newline_before=newline)
