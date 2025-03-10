#!/usr/bin/env python3
"""Real-time lint quality monitoring with improvement tracking."""

import subprocess
import time
from datetime import datetime, timedelta
from collections import deque
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


LOG_FILE = "pylint_monitor.log"
INTERVAL = 60
TIME_WINDOWS = [
    ("5m", timedelta(minutes=5)),
    ("15m", timedelta(minutes=15)),
    ("1h", timedelta(hours=1)),
    ("4h", timedelta(hours=4)),
    ("16h", timedelta(hours=16)),
]


class LintMonitor:
    """Monitor and track lint quality improvements over time."""

    def __init__(self):
        self.history: deque[tuple[datetime, float]] = deque()
        self.last_score: float | None = None
        self.console = Console()
        self.running = True
        self.max_iterations = float("inf")  # type: ignore

    def get_pylint_score(self) -> float | None:
        """Run pylint and extract the score."""
        try:
            result = subprocess.run(
                ["pylint", "evoprompt/**py"], capture_output=True, text=True, check=True
            )
            last_line = result.stdout.strip()
            if "Your code has been rated at" in last_line:
                score_str = last_line.split("Your code has been rated at ")[1].split(
                    "/"
                )[0]
                return float(score_str)
        except subprocess.CalledProcessError:
            return None
        except ValueError as e:
            raise e
        return None

    def calculate_improvements(self) -> dict[str, float | None]:
        """Calculate improvements for each time window"""
        improvements: dict[str, float | None] = {}
        current_time = datetime.now()

        for window_name, window_delta in TIME_WINDOWS:
            window_start = current_time - window_delta
            window_scores = [
                score for timestamp, score in self.history if timestamp >= window_start
            ]

            if window_scores:
                first = window_scores[0]
                last = window_scores[-1]
                improvement = last - first
                improvements[window_name] = improvement
            else:
                improvements[window_name] = None

        return improvements

    def run(self):
        """Main monitoring loop."""
        self.console.print(
            Panel(
                f"Starting lint monitor. Logging to [bold cyan]{LOG_FILE}[/]\n"
                "Press [bold red]Ctrl+C[/] to stop...",
                title="Lint Monitor",
                border_style="green",
            )
        )

        iteration = 0
        try:
            while self.running and iteration < self.max_iterations:
                score = self.get_pylint_score()
                if score is not None:
                    timestamp = datetime.now()
                    self.history.append((timestamp, score))

                    # Keep only last 16 hours of data
                    cutoff = timestamp - TIME_WINDOWS[-1][1]
                    while self.history and self.history[0][0] < cutoff:
                        self.history.popleft()

                    # Calculate improvements
                    improvements = self.calculate_improvements()

                    # Create rich table for display
                    table = Table(
                        title="Lint Quality Monitor",
                        show_header=True,
                        header_style="bold magenta",
                    )
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", justify="right")

                    # Add current score
                    score_style = (
                        "green" if score >= 9.0 else "yellow" if score >= 7.0 else "red"
                    )
                    table.add_row(
                        "Current Score", Text(f"{score:.2f}/10", style=score_style)
                    )

                    # Add improvements
                    for window, improvement in improvements.items():
                        if improvement is not None:
                            imp_style = "green" if improvement > 0 else "red"
                            table.add_row(
                                f"Improvement ({window})",
                                Text(f"{improvement:+.2f}", style=imp_style),
                            )

                    # Create panel with timestamp
                    panel = Panel(
                        table,
                        title=f"Lint Quality at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                        border_style="blue",
                    )

                    # Log to file
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{timestamp.isoformat()} - Current: {score:.2f}/10\n")

                    # Clear console and display new output
                    self.console.clear()
                    self.console.print(panel)

                time.sleep(INTERVAL)
                iteration += 1

        except KeyboardInterrupt:
            self.console.print("\n[bold red]Monitoring stopped.[/]")
