"""Unit tests for the table_formatter module."""

from typing import Optional

from rich.table import Table

from lint_monitor.table_formatter import create_lint_table


def test_create_lint_table() -> None:
    """Test the creation of the lint table."""
    score = 8.5
    improvements: dict[str, Optional[float]] = {"5m": 1.0, "15m": None, "1h": 2.0}
    table = create_lint_table(score, improvements)

    assert isinstance(table, Table)
    assert table.title == "Lint Quality Metrics"
    assert len(table.columns) == 2
    assert len(table.rows) == 4

    # Check the contents of the table
    rows = list(table.rows)
    assert str(rows[0].cells[0].text) == "Current Score"
    assert str(rows[0].cells[1].text) == "8.50/10"
    assert str(rows[1].cells[0].text) == "Improvement (5m)"
    assert str(rows[1].cells[1].text) == "1.00"
    assert str(rows[2].cells[0].text) == "Improvement (15m)"
    assert str(rows[2].cells[1].text) == "N/A"
    assert str(rows[3].cells[0].text) == "Improvement (1h)"
    assert str(rows[3].cells[1].text) == "2.00"
