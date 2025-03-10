#!/usr/bin/env python3
"""Real-time lint quality monitoring with improvement tracking."""

import subprocess
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

LOG_FILE = "pylint_monitor.log"
INTERVAL = 60
TIME_WINDOWS: list[tuple[str, timedelta]] = [
    ("5m", timedelta(minutes=5)),
    ("15m", timedelta(minutes=15)),
    ("1h", timedelta(hours=1)),
    ("4h", timedelta(hours=4)),
    ("16h", timedelta(hours=16)),
]


class LintMonitor:
    """Monitor and track lint quality improvements over time."""

    DEFAULT_PYLINT_COMMAND: list[str] = ["pylint", "evoprompt/**py"]
    TIME_WINDOWS = TIME_WINDOWS

    def __init__(self, pylint_command: list[str] | None = None) -> None:
        self.history: deque[tuple[datetime, float]] = deque()
        self.last_score: Optional[float] = None
        self._console = Console()
        self.running: bool = True
        self.max_iterations: float = float("inf")
        self.pylint_command: list[str] = (
            pylint_command
            if pylint_command is not None
            else self.DEFAULT_PYLINT_COMMAND
        )

    def get_pylint_score(self) -> Optional[float]:
        """Run pylint and extract the score."""
        try:
            result = self._run_pylint()
            return self._extract_score(result) if result else None
        except subprocess.CalledProcessError:
            return None
        except ValueError as e:
            raise e

    def _run_pylint(self) -> Optional[str]:
        """Helper function to run pylint and return the last line of output."""
        try:
            result = subprocess.run(
                self.pylint_command, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _extract_score(self, last_line: str) -> Optional[float]:
        """Helper function to extract the score from the pylint output."""
        if "Your code has been rated at" in last_line:
            try:
                score_str = last_line.split("Your code has been rated at ")[1].split("/")[0]
                return float(score_str)
            except (IndexError, ValueError):
                return None
        return None

    def calculate_improvements(self) -> dict[str, Optional[float]]:
        """Calculate improvements for each time window."""
        current_time = datetime.now()
        improvements = {
            window_name: self._calculate_improvement_for_window(current_time, window_delta)
            for window_name, window_delta in self.TIME_WINDOWS
        }
        return improvements

    def _calculate_improvement_for_window(
        self, current_time: datetime, window_delta: timedelta
    ) -> Optional[float]:
        """Calculates the improvement for a specific time window."""
        window_start = current_time - window_delta
        window_scores = [
            score for timestamp, score in self.history if timestamp >= window_start
        ]

        if len(window_scores) < 2:
            return None

        first, last = window_scores[0], window_scores[-1]
        return last - first

    def _create_lint_table(self, score: float, improvements: dict[str, Optional[float]]) -> Table:
        """Create a rich table for displaying lint quality."""
        table = create_lint_table(score, improvements)
        return table

    def _log_and_display(self, score: float, table: Table, timestamp: datetime) -> None:
        self._log_score(score, timestamp)
        self._display_table(table, timestamp)

    def _log_score(self, score: float, timestamp: datetime) -> None:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp.isoformat()} - Current: {score:.2f}/10\n")

    def _display_table(self, table: Table, timestamp: datetime) -> None:
        panel = Panel(
            table,
            title=f"Lint Quality at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue",
        )
        self._console.clear()
        self._console.print(panel)

    def run(self) -> None:
        """Main monitoring loop."""
        start_panel = Panel(
            f"Starting lint monitor. Logging to [bold cyan]{LOG_FILE}[/]\n"
            "Press [bold red]Ctrl+C[/] to stop...",
            title="Lint Monitor",
            border_style="green",
        )
        self._console.print(start_panel)

        iteration = 0
        try:
            while self.running and iteration < self.max_iterations:
                self._process_iteration()
                iteration += 1
                time.sleep(INTERVAL)

        except KeyboardInterrupt:
            self._console.print("\n[bold red]Monitoring stopped.[/]")

    def _process_iteration(self) -> None:
        score = self.get_pylint_score()
        if score is not None:
            timestamp = datetime.now()
            self.history.append((timestamp, score))
            self._trim_history()
            improvements = self.calculate_improvements()
            table = self._create_lint_table(score, improvements)
            self._log_and_display(score, table, timestamp)

    def _trim_history(self) -> None:
        cutoff = datetime.now() - self.TIME_WINDOWS[-1][1]
        while self.history and self.history[0][0] < cutoff:
            self.history.popleft()


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


def add_table_columns(table: Table) -> None:
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")


def add_score_row(table: Table, score: float) -> None:
    score_style = "green" if score >= 9.0 else "yellow" if score >= 7.0 else "red"
    table.add_row("Current Score", Text(f"{score:.2f}/10", style=score_style))


def add_improvement_rows(table: Table, improvements: dict[str, Optional[float]]) -> None:
    for window, improvement in improvements.items():
        if improvement is not None:
            imp_style = "green" if improvement > 0 else "red"
            table.add_row(
                f"Improvement ({window})",
                Text(f"{improvement:+.2f}", style=imp_style),
            )


def main() -> None:
    """Main entry point for the lint monitor."""
    monitor = LintMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
