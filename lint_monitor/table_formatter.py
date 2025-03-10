"""Module for formatting lint quality data into a rich table."""

from typing import Optional
from rich.table import Table


def create_lint_table(score: float, improvements: dict[str, Optional[float]]) -> Table:
    """Create a rich table for displaying lint quality."""
    table = Table(title="Lint Quality Metrics")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Current Score", f"{score:.2f}/10")
    for window, improvement in improvements.items():
        if improvement is not None:
            table.add_row(f"Improvement ({window})", f"{improvement:.2f}")
        else:
            table.add_row(f"Improvement ({window})", "N/A")

    return table
