"""Module for formatting lint quality data into a rich table."""

from typing import Optional

from rich.table import Table
from rich.text import Text


def add_table_columns(table: Table) -> None:
    """Adds columns to the table."""
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")


def add_score_row(table: Table, score: float) -> None:
    """Adds a row for the current score."""
    score_style = "green" if score >= 9.0 else "yellow" if score >= 7.0 else "red"
    table.add_row("Current Score", Text(f"{score:.2f}/10", style=score_style))


def add_improvement_rows(
    table: Table, improvements: dict[str, Optional[float]]
) -> None:
    """Adds rows for the improvement values."""
    for window, improvement in improvements.items():
        if improvement is not None:
            imp_style = "green" if improvement > 0 else "red"
            table.add_row(
                f"Improvement ({window})",
                Text(f"{improvement:+.2f}", style=imp_style),
            )


def create_lint_table(score: float, improvements: dict[str, Optional[float]]) -> Table:
    """Create a rich table for displaying lint quality."""
    table = Table(
        title="Lint Quality Monitor",
        show_header=True,
        header_style="bold magenta",
    )
    add_table_columns(table)
    add_score_row(table, score)
    add_improvement_rows(table, improvements)
    return table
