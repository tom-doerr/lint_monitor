"""Unit tests for the lint monitor package."""

from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from collections import deque
import subprocess

from lint_monitor.monitor import LintMonitor


INTERVAL = 0.1  # Shorten interval for testing
MAX_ITERATIONS = 5  # Limit iterations
NOW = datetime.now()  # Store current datetime


@patch("subprocess.run")
def test_get_pylint_score(mock_run: MagicMock) -> None:
    """Test the pylint score extraction functionality."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])

    mock_run.return_value.stdout = "Your code has been rated at 9.50/10"
    assert monitor.get_pylint_score() == 9.5

    mock_run.side_effect = subprocess.CalledProcessError(1, "pylint")
    assert monitor.get_pylint_score() is None

    mock_run.side_effect = None
    mock_run.return_value.stdout = "Invalid score format"
    assert monitor.get_pylint_score() is None


def test_calculate_improvements() -> None:
    """Test the improvement calculation over time windows."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])
    
    def run_test(history: list[tuple[datetime, float]], expected_values: list[float | None]):
        monitor.history = deque(history)
        improvements = monitor.calculate_improvements()
        assert len(improvements) == len(LintMonitor.TIME_WINDOWS)
        for i, window in enumerate(LintMonitor.TIME_WINDOWS):
            assert improvements[window[0]] == expected_values[i]

    run_test(
        [(NOW - timedelta(minutes=10), 7.0),
         (NOW - timedelta(minutes=5), 8.0),
         (NOW, 9.0)],
        [1.0, 2.0, 2.0, 2.0, 2.0]
    )

    run_test([], [None] * len(LintMonitor.TIME_WINDOWS))
    run_test([(NOW, 7.0)], [None] * len(LintMonitor.TIME_WINDOWS))


@patch("subprocess.run")
def test_get_pylint_score_no_score(mock_run: MagicMock) -> None:
    """Test the pylint score extraction when no score is returned."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])
    mock_run.return_value.stdout = "Some other output"
    mock_run.return_value.returncode = 1  # Simulate an error
    score = monitor.get_pylint_score()
    assert score is None


@patch("lint_monitor.monitor.Console")
def test_run(mock_console: MagicMock) -> None:
    """Test the main monitoring loop functionality."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])
    monitor.get_pylint_score = MagicMock(return_value=9.0)
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()

    assert (
        mock_console.return_value.print.call_args[0][0]
        == "\n[bold red]Monitoring stopped.[/]"
    )
    assert monitor.running is False


@patch("lint_monitor.monitor.Console")
def test_run_score_below_7(mock_console: MagicMock) -> None:
    """Test the main monitoring loop functionality with score below 7."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])
    monitor.get_pylint_score = MagicMock(return_value=6.0)
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()

    assert (
        mock_console.return_value.print.call_args[0][0]
        == "\n[bold red]Monitoring stopped.[/]"
    )
    assert monitor.running is False


@patch("lint_monitor.monitor.Console")
def test_run_score_between_7_and_9(mock_console: MagicMock) -> None:
    """Test the main monitoring loop functionality with score between 7 and 9."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])
    monitor.get_pylint_score = MagicMock(return_value=8.0)
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()

    assert (
        mock_console.return_value.print.call_args[0][0]
        == "\n[bold red]Monitoring stopped.[/]"
    )
    assert monitor.running is False
