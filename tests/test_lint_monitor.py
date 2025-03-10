"""Unit tests for the lint monitor package."""

from unittest.mock import patch
from datetime import datetime, timedelta
from collections import deque
import subprocess
import pytest

from unittest.mock import patch
from datetime import datetime, timedelta
from collections import deque
import subprocess
import pytest

from lint_monitor.monitor import LintMonitor


INTERVAL = 0.1  # Shorten interval for testing
MAX_ITERATIONS = 5  # Limit iterations
NOW = datetime.now()  # Store current datetime


@pytest.fixture
def monitor():
    """Fixture for creating a LintMonitor instance."""
    monitor = LintMonitor(pylint_command=["pylint", "evoprompt/**py"])
    monitor.interval = INTERVAL
    monitor.max_iterations = MAX_ITERATIONS
    return monitor


@patch("subprocess.run")
def test_get_pylint_score(mock_run, monitor):
    """Test the pylint score extraction functionality."""
    mock_run.return_value.stdout = "Your code has been rated at 9.50/10"
    score = monitor.get_pylint_score()
    assert score == 9.5

    mock_run.side_effect = subprocess.CalledProcessError(1, "pylint")
    score = monitor.get_pylint_score()
    assert score is None

    mock_run.return_value.stdout = "Invalid score format"
    score = monitor.get_pylint_score()
    assert score is None


def test_calculate_improvements(monitor):
    """Test the improvement calculation over time windows."""
    monitor.history = deque(
        [
            (NOW - timedelta(minutes=10), 7.0),
            (NOW - timedelta(minutes=5), 8.0),
            (NOW, 9.0),
        ]
    )

    improvements = monitor.calculate_improvements()
    assert len(improvements) == len(LintMonitor.TIME_WINDOWS)
    assert improvements["5m"] == 0.0
    assert improvements["15m"] == 2.0
    assert improvements["1h"] == 2.0
    assert improvements["4h"] == 2.0
    assert improvements["16h"] == 2.0

    monitor.history = deque()
    improvements = monitor.calculate_improvements()
    assert len(improvements) == len(LintMonitor.TIME_WINDOWS)
    assert all(value is None for value in improvements.values())

    monitor.history = deque([(NOW, 7.0)])
    improvements = monitor.calculate_improvements()
    assert len(improvements) == len(LintMonitor.TIME_WINDOWS)
    assert all(value is None for value in improvements.values())


@patch("subprocess.run")
def test_get_pylint_score_no_score(mock_run, monitor):
    """Test the pylint score extraction when no score is returned."""
    mock_run.return_value.stdout = "Some other output"
    mock_run.return_value.returncode = 1  # Simulate an error
    score = monitor.get_pylint_score()
    assert score is None


@patch("lint_monitor.monitor.Console")
def test_run(mock_console, monitor):
    """Test the main monitoring loop functionality."""
    monitor.get_pylint_score = MagicMock(return_value=9.0)
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()

    assert mock_console.return_value.print.call_args[0][0] == "\n[bold red]Monitoring stopped.[/]"
    assert monitor.running is False


@patch("lint_monitor.monitor.Console")
def test_run_score_below_7(mock_console, monitor):
    """Test the main monitoring loop functionality with score below 7."""
    monitor.get_pylint_score = MagicMock(return_value=6.0)
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()

    assert mock_console.return_value.print.call_args[0][0] == "\n[bold red]Monitoring stopped.[/]"
    assert monitor.running is False


@patch("lint_monitor.monitor.Console")
def test_run_score_between_7_and_9(mock_console, monitor):
    """Test the main monitoring loop functionality with score between 7 and 9."""
    monitor.get_pylint_score = MagicMock(return_value=8.0)
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()

    assert mock_console.return_value.print.call_args[0][0] == "\n[bold red]Monitoring stopped.[/]"
    assert monitor.running is False
