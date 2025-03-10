#!/usr/bin/env python3
"""Real-time lint quality monitoring with improvement tracking."""

import subprocess
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

LOG_FILE = "pylint_monitor.log"
INTERVAL = 60
TIME_WINDOWS: list[tuple[str, timedelta]] = [
    ("5m", timedelta(minutes=5)),
    ("15m", timedelta(minutes=15)),
    ("1h", timedelta(hours=1)),
    ("4h", timedelta(hours=4)),
    ("16h", timedelta(hours=16)),
]


@dataclass
class MonitorConfig:
    """Configuration parameters for the LintMonitor."""

    pylint_command: Optional[list[str]] = None
    max_iterations: float = float("inf")


class LintMonitor:
    """Monitor and track lint quality improvements over time."""

    DEFAULT_PYLINT_COMMAND: list[str] = ["pylint", "evoprompt/**py"]
    TIME_WINDOWS = TIME_WINDOWS

    def __init__(self, config: Optional[MonitorConfig] = None) -> None:
        self.history: deque[tuple[datetime, float]] = deque()
        self.last_score: Optional[float] = None
        self._console = Console()
        self.running: bool = True
        self.config = config or MonitorConfig()
        if self.config.pylint_command is None:
            self.config.pylint_command = self.DEFAULT_PYLINT_COMMAND

    def get_pylint_score(self) -> Optional[float]:
        """Run pylint and extract the score."""
        output = self._run_pylint()
        if output is None:
            return None
        return self._extract_score(output)

    def __run_pylint(self) -> Optional[str]:
        """Helper function to run pylint and return the last line of output."""
        try:
            result = subprocess.run(
                self.config.pylint_command, capture_output=True, text=True, check=True
            )
            output = result.stdout.strip()
            self._console.log(f"Pylint Output: {output}")
            return output
        except subprocess.CalledProcessError as e:
            self._console.log(f"Pylint Error: {e}")
            return None

    def _extract_score(self, output: str) -> Optional[float]:
        """Helper function to extract the score from the pylint output."""
        if not output:
            self._console.log("No pylint output to extract score from.")
            return None

        if "Your code has been rated at" not in output:
            self._console.log("No score found in pylint output.")
            return None

        score = self._extract_score_value(output)
        if score is None:
            return None

        self._console.log(f"Extracted Score: {score}")
        return score

    def _extract_score_value(self, output: str) -> Optional[float]:
        """Extracts the score value from the pylint output."""
        try:
            score_str = output.split("Your code has been rated at ")[1].split("/")[0]
            return float(score_str)
        except (IndexError, ValueError) as e:
            self._console.log(f"Error extracting score: {e}")
            return None

    def calculate_improvements(self) -> dict[str, Optional[float]]:
        """Calculate improvements for each time window."""
        current_time = datetime.now()
        improvements = {
            window_name: self._calculate_improvement_for_window(
                current_time, window_delta
            )
            for window_name, window_delta in self.TIME_WINDOWS
        }
        return improvements

    def _calculate_improvement_for_window(
        self, current_time: datetime, window_delta: timedelta
    ) -> Optional[float]:
        """Calculates the improvement for a specific time window."""
        window_scores = self._get_window_scores(current_time, window_delta)
        if not window_scores or len(window_scores) < 2:
            return None
        return self._calculate_score_difference(window_scores)

    def _calculate_score_difference(self, window_scores: list[float]) -> float:
        """Calculates the difference between the last and first scores."""
        return window_scores[-1] - window_scores[0]

    def _get_window_scores(
        self, current_time: datetime, window_delta: timedelta
    ) -> list[float]:
        """Helper function to get the scores within a time window."""
        window_start = current_time - window_delta
        return [score for timestamp, score in self.history if timestamp >= window_start]

    def _create_lint_table(self, improvements: dict[str, Optional[float]]) -> Table:
        """Create a rich table for displaying lint quality."""
        table = self.create_lint_table(self.last_score, improvements)
        return table

    def _log_and_display(self, timestamp: datetime, table: Table) -> None:
        self._log_score(self.last_score, timestamp)
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
            while self.running and iteration < self.config.max_iterations:
                self._process_iteration()
                iteration += 1
                time.sleep(INTERVAL)

        except KeyboardInterrupt:
            self._console.print("\n[bold red]Monitoring stopped.[/]")
            self.running = False

    def _process_iteration(self) -> None:
        score = self.get_pylint_score()
        if score is not None:
            timestamp = datetime.now()
            self.last_score = score
            self.history.append((timestamp, score))
            self._trim_history()
            improvements = self.calculate_improvements()
            table = self._create_lint_table(improvements)
            self._log_and_display(timestamp, table)

    def _trim_history(self) -> None:
        cutoff = datetime.now() - self.TIME_WINDOWS[-1][1]
        while self.history and self.history[0][0] < cutoff:
            self.history.popleft()

    # def __run_pylint(self) -> Optional[str]:
    #     """Helper function to run pylint and return the last line of output."""
    #     try:
    #         result = subprocess.run(
    #             self.config.pylint_command, capture_output=True, text=True, check=True
    #         )
    #         output = result.stdout.strip()
    #         self._console.log(f"Pylint Output: {output}")
    #         return output
    #     except subprocess.CalledProcessError as e:
    #         self._console.log(f"Pylint Error: {e}")
    #         return None
