"""
Formatting utilities for consistent, color-coded CLI output.

Uses the `rich` library for ANSI colors, bold text, and progress bars.
A single module-level `console` instance is shared across all callers —
import it directly when you need to print colored output:

    from utils.formatting import console, colorScore, colorStatus

Color scheme:
    Green  — active / done / present / high score
    Yellow — paused / in-progress / empty / medium score
    Red    — failed / missing / critical / low score
    Orange — Bronze layer
    White  — Silver layer
    Gold   — Gold layer
    Cyan   — entity type labels and headers
    Dim    — IDs and secondary info
"""

from typing import Optional
from rich.console import Console
from rich.text import Text

# Single shared console — all print calls go through this so colors are consistent
console = Console(highlight=False)

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────
SEPARATOR_CHAR    = "="
SUBSEPARATOR_CHAR = "-"
DEFAULT_WIDTH     = 80

# ─────────────────────────────────────────────────────────────────────────────
# Color helpers — return rich markup strings
# ─────────────────────────────────────────────────────────────────────────────

def colorScore(score: float) -> str:
    """
    Return a rich-markup colored score string.
        ≥ 75%  → green
        50–74% → yellow
        < 50%  → red
    """
    s = f"{score:.0f}%"
    if score >= 75:
        return f"[green]{s}[/green]"
    elif score >= 50:
        return f"[yellow]{s}[/yellow]"
    else:
        return f"[red]{s}[/red]"


def colorStatus(status: str) -> str:
    """
    Return a colored status label.
    Handles pipeline statuses, Jira statuses, and DPS section statuses.
    """
    s = status.lower()
    if s in ('active', 'done', 'present', 'healthy', 'running'):
        return f"[green]{status}[/green]"
    elif s in ('paused', 'in progress', 'empty', 'degraded', 'warning'):
        return f"[yellow]{status}[/yellow]"
    elif s in ('failed', 'missing', 'error', 'critical', 'to do'):
        return f"[red]{status}[/red]"
    return status


def colorStatusIcon(status: str) -> str:
    """
    Return a colored ASCII status icon.
        active / done / present → green  [+]
        paused / in progress   → yellow [~]
        failed / missing       → red    [✗]
    """
    s = status.lower()
    if s in ('active', 'done', 'present', 'healthy'):
        return "[green]+[/green]"
    elif s in ('paused', 'in progress', 'empty'):
        return "[yellow]~[/yellow]"
    else:
        return "[red]✗[/red]"


def colorSeverity(severity: str) -> str:
    """Return a colored severity label (critical → red, high → red, medium → yellow, low → green)."""
    s = severity.lower()
    if s == 'critical':
        return f"[bold red]{severity}[/bold red]"
    elif s == 'high':
        return f"[red]{severity}[/red]"
    elif s in ('medium', 'warning'):
        return f"[yellow]{severity}[/yellow]"
    elif s == 'low':
        return f"[green]{severity}[/green]"
    return severity


def colorLayer(layer: str) -> str:
    """Return a colored [LAYER] label for Bronze / Silver / Gold."""
    l = layer.lower()
    if l == 'bronze':
        return f"[dark_orange][BRONZE][/dark_orange]"
    elif l == 'silver':
        return f"[bright_white][SILVER][/bright_white]"
    elif l == 'gold':
        return f"[gold1][GOLD][/gold1]"
    return f"[{layer.upper()}]"


def colorEntityType(entityType: str) -> str:
    """Return a cyan-colored entity type label like [Pipeline]."""
    return f"[cyan][{entityType}][/cyan]"


def colorPriority(priority: str) -> str:
    """Color Jira priority labels."""
    p = priority.lower()
    if p == 'critical':
        return f"[bold red]{priority}[/bold red]"
    elif p == 'high':
        return f"[red]{priority}[/red]"
    elif p == 'medium':
        return f"[yellow]{priority}[/yellow]"
    elif p == 'low':
        return f"[green]{priority}[/green]"
    return priority


def colorPii(flag: bool) -> str:
    """Return a colored [PII] badge if flag is True, else empty string."""
    return " [bold red][PII][/bold red]" if flag else ""


def scoreBar(score: float, width: int = 25) -> str:
    """
    Build a colored ASCII progress bar for a 0–100 score.

        100% → [█████████████████████████]  green
         57% → [██████████████░░░░░░░░░░░]  yellow
         20% → [█████░░░░░░░░░░░░░░░░░░░░]  red
    """
    filled = int(score / 100 * width)
    bar    = "█" * filled + "░" * (width - filled)
    if score >= 75:
        color = "green"
    elif score >= 50:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}][{bar}][/{color}]"


# ─────────────────────────────────────────────────────────────────────────────
# Section dividers
# ─────────────────────────────────────────────────────────────────────────────

def printSeparator(width: int = DEFAULT_WIDTH, char: str = SEPARATOR_CHAR,
                   newline_before: bool = True) -> None:
    """Print a plain separator line (no color — used as visual dividers)."""
    if newline_before:
        console.print()
    console.print(char * width, style="dim")


def printHeader(text: str, width: int = DEFAULT_WIDTH) -> None:
    """
    Print a major section header in bold cyan with "=" separators.

    Example:
        ================================================================================
        QUERY: Pipeline Status
        ================================================================================
    """
    console.print()
    console.print(SEPARATOR_CHAR * width, style="cyan dim")
    console.print(text, style="bold cyan")
    console.print(SEPARATOR_CHAR * width, style="cyan dim")


def printSubHeader(text: str, width: int = DEFAULT_WIDTH) -> None:
    """
    Print a sub-section header in bold white with "-" separators.

    Example:
        --------------------------------------------------------------------------------
        Example 1: Find Jira tickets about data quality
        --------------------------------------------------------------------------------
    """
    console.print()
    console.print(SUBSEPARATOR_CHAR * width, style="dim")
    console.print(text, style="bold white")
    console.print(SUBSEPARATOR_CHAR * width, style="dim")


def printSection(title: str, content: Optional[str] = None,
                 width: int = DEFAULT_WIDTH) -> None:
    """Print a section with a "-" separator title and optional body text."""
    console.print()
    console.print(SUBSEPARATOR_CHAR * width, style="dim")
    console.print(title, style="bold white")
    console.print(SUBSEPARATOR_CHAR * width, style="dim")
    if content:
        console.print(content)


def formatNodeInfo(nodeType: str, nodeName: str, nodeId: str,
                   distance: Optional[float] = None) -> str:
    """Format a node for single-line display with colored entity type."""
    base = f"[cyan][{nodeType}][/cyan] {nodeName} [dim](ID: {nodeId})[/dim]"
    if distance is not None:
        sim = round((1 - distance / 2) * 100, 1)
        return base + f" {colorScore(sim)}"
    return base


def formatRelationship(relation: str, targetType: str, targetName: str,
                        targetId: Optional[str] = None, direction: str = "-->") -> str:
    """Format a relationship edge for single-line display."""
    target = f"[cyan][{targetType}][/cyan] {targetName}"
    if targetId:
        target += f" [dim](ID: {targetId})[/dim]"
    return f"[blue]--[[/blue][bold]{relation}[/bold][blue]]{direction}[/blue] {target}"


# ─────────────────────────────────────────────────────────────────────────────
# Shorthand aliases
# ─────────────────────────────────────────────────────────────────────────────

def header(text: str) -> None:
    """Shorthand for printHeader."""
    printHeader(text)


def subheader(text: str) -> None:
    """Shorthand for printSubHeader."""
    printSubHeader(text)


def separator(newline: bool = True) -> None:
    """Shorthand for printSeparator."""
    printSeparator(newline_before=newline)
