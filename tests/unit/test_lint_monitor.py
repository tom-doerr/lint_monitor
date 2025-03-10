"""Unit tests for the LintMonitor class."""

from collections import deque
from datetime import datetime, timedelta
import subprocess
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from lint_monitor import LintMonitor, MonitorConfig


@pytest.fixture
def lint_monitor() -> LintMonitor:
    """Fixture to create a LintMonitor instance with a default configuration."""
    config = MonitorConfig(pylint_command=["pylint", "evoprompt/**py"])
    return LintMonitor(config)


NOW = datetime.now()


def test_get_pylint_score_success(lint_monitor: LintMonitor) -> None:
    """Test successful pylint score extraction."""
    with patch.object(lint_monitor, "_run_pylint") as mock_run_pylint, patch.object(
        lint_monitor, "_extract_score"
    ) as mock_extract_score:
        mock_run_pylint.return_value = "Your code has been rated at 9.50/10"
        mock_extract_score.return_value = 9.5
        assert lint_monitor.get_pylint_score() == 9.5
        mock_run_pylint.assert_called_once()
        mock_extract_score.assert_called_once_with("Your code has been rated at 9.50/10")


def test_get_pylint_score_no_output(lint_monitor: LintMonitor) -> None:
    """Test pylint score extraction when there is no output."""
    with patch.object(lint_monitor, "_run_pylint") as mock_run_pylint, patch.object(
        lint_monitor, "_extract_score"
    ) as mock_extract_score:
        mock_run_pylint.return_value = None
        assert lint_monitor.get_pylint_score() is None
        mock_run_pylint.assert_called_once()
        mock_extract_score.assert_not_called()


def test_run_pylint_success(lint_monitor: LintMonitor) -> None:
    """Test successful execution of pylint."""
    mock_run = MagicMock()
    mock_run.stdout = "Your code has been rated at 9.50/10"
    with patch("subprocess.run", return_value=mock_run) as subprocess_run:
        result = lint_monitor._run_pylint()
        assert result == "Your code has been rated at 9.50/10"
        subprocess_run.assert_called_once_with(
            lint_monitor.config.pylint_command, capture_output=True, text=True, check=True
        )


def test_run_pylint_called_process_error(lint_monitor: LintMonitor) -> None:
    """Test handling of CalledProcessError during pylint execution."""
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "pylint")):
        result = lint_monitor._run_pylint()
        assert result is None


def test_extract_score_success(lint_monitor: LintMonitor) -> None:
    """Test successful score extraction from pylint output."""
    output = "Your code has been rated at 9.50/10"
    assert lint_monitor._extract_score(output) == 9.5


def test_extract_score_invalid_format(lint_monitor: LintMonitor) -> None:
    """Test score extraction with invalid pylint output format."""
    output = "Invalid score format"
    assert lint_monitor._extract_score(output) is None


def test_extract_score_none_output(lint_monitor: LintMonitor) -> None:
    """Test score extraction with None as pylint output."""
    assert lint_monitor._extract_score(None) is None


def test_extract_score_no_score_found(lint_monitor: LintMonitor) -> None:
    """Test score extraction when no score is found in the output."""
    output = "Some other output"
    assert lint_monitor._extract_score(output) is None


def test_calculate_improvements(lint_monitor: LintMonitor) -> None:
    """Test the improvement calculation over time windows."""
    test_cases = [
        (
            [
                (NOW - timedelta(hours=1), 6.0),
                (NOW - timedelta(minutes=15), 7.0),
                (NOW - timedelta(minutes=5), 8.0),
                (NOW, 9.0),
            ],
            {"5m": 3.0, "15m": 2.0, "1h": 3.0, "4h": None, "16h": None},
        ),
        ([], {window[0]: None for window in lint_monitor.TIME_WINDOWS}),
        ([(NOW, 7.0)], {window[0]: None for window in lint_monitor.TIME_WINDOWS}),
        (
            [(NOW - timedelta(minutes=4), 7.0), (NOW, 8.0)],
            {"5m": 1.0, "15m": None, "1h": None, "4h": None, "16h": None},
        ),
    ]

    for history, expected_improvements in test_cases:
        lint_monitor.history = deque(history)
        improvements = lint_monitor.calculate_improvements()
        assert improvements == expected_improvements


def test_calculate_improvement_for_window(lint_monitor: LintMonitor) -> None:
    """Test the calculation of improvement for a specific time window."""
    test_cases = [
        (
            [
                (NOW - timedelta(minutes=6), 6.0),
                (NOW - timedelta(minutes=15), 7.0),
                (NOW - timedelta(minutes=5), 8.0),
                (NOW, 9.0),
            ],
            timedelta(minutes=5),
            3.0,
        ),
        (
            [
                (NOW - timedelta(minutes=16), 6.0),
                (NOW - timedelta(minutes=15), 7.0),
                (NOW - timedelta(minutes=5), 8.0),
                (NOW, 9.0),
            ],
            timedelta(minutes=15),
            2.0,
        ),
        (
            [
                (NOW - timedelta(hours=2), 6.0),
                (NOW - timedelta(minutes=15), 7.0),
                (NOW - timedelta(minutes=5), 8.0),
                (NOW, 9.0),
            ],
            timedelta(hours=1),
            3.0,
        ),
        ([], timedelta(minutes=5), None),
        ([(NOW, 7.0)], timedelta(minutes=5), None),
        (
            [(NOW - timedelta(minutes=4), 7.0), (NOW, 8.0)],
            timedelta(minutes=5),
            1.0,
        ),
    ]

    for history, window_delta, expected_improvement in test_cases:
        lint_monitor.history = deque(history)
        improvement = lint_monitor._calculate_improvement_for_window(NOW, window_delta)
        if expected_improvement is None:
            assert improvement is None
        else:
            assert improvement == pytest.approx(expected_improvement)


def test_calculate_score_difference(lint_monitor: LintMonitor) -> None:
    """Test the calculation of score difference."""
    window_scores = [6.0, 7.0, 8.0, 9.0]
    assert lint_monitor._calculate_score_difference(window_scores) == 3.0


def test_get_window_scores(lint_monitor: LintMonitor) -> None:
    """Test the retrieval of scores within a time window."""
    history = [
        (NOW - timedelta(hours=1), 6.0),
        (NOW - timedelta(minutes=15), 7.0),
        (NOW - timedelta(minutes=5), 8.0),
        (NOW, 9.0),
    ]
    lint_monitor.history = deque(history)
    window_scores = lint_monitor._get_window_scores(NOW, timedelta(minutes=15))
    assert window_scores == [7.0, 8.0, 9.0]


def test_create_lint_table(lint_monitor: LintMonitor) -> None:
    """Test the creation of the lint table."""
    improvements = {"5m": 1.0, "15m": None, "1h": 2.0, "4h": None, "16h": 3.0}
    with patch.object(lint_monitor, "create_lint_table") as mock_create_lint_table:
        lint_monitor._create_lint_table(improvements)
        mock_create_lint_table.assert_called_once_with(lint_monitor.last_score, improvements)


def test_log_and_display(lint_monitor: LintMonitor) -> None:
    """Test the logging and display of lint quality."""
    timestamp = datetime.now()
    table = MagicMock()
    with patch.object(lint_monitor, "_log_score") as mock_log_score, patch.object(
        lint_monitor, "_display_table"
    ) as mock_display_table:
        lint_monitor._log_and_display(timestamp, table)
        mock_log_score.assert_called_once_with(lint_monitor.last_score, timestamp)
        mock_display_table.assert_called_once_with(table, timestamp)


def test_log_score(lint_monitor: LintMonitor, tmp_path: pytest.fixture) -> None:
    """Test the logging of the lint score to a file."""
    timestamp = datetime.now()
    log_file = tmp_path / "test_log.txt"
    lint_monitor.LOG_FILE = str(log_file)
    lint_monitor._log_score(9.0, timestamp)
    with open(log_file, "r") as f:
        content = f.read()
        assert f"{timestamp.isoformat()} - Current: 9.00/10\n" in content


def test_display_table(lint_monitor: LintMonitor) -> None:
    """Test the display of the lint table."""
    table = MagicMock()
    timestamp = datetime.now()
    with patch("rich.panel.Panel") as mock_panel, patch.object(lint_monitor._console, "clear") as mock_clear, patch.object(lint_monitor._console, "print") as mock_print:
        lint_monitor._display_table(table, timestamp)
        mock_panel.assert_called_once()
        mock_clear.assert_called_once()
        mock_print.assert_called_once()


def test_process_iteration(lint_monitor: LintMonitor) -> None:
    """Test the processing of a single iteration."""
    lint_monitor.get_pylint_score = MagicMock(return_value=9.0)
    lint_monitor._trim_history = MagicMock()
    lint_monitor.calculate_improvements = MagicMock(return_value={"5m": 1.0})
    lint_monitor._create_lint_table = MagicMock()
    lint_monitor._log_and_display = MagicMock()

    lint_monitor._process_iteration()

    lint_monitor.get_pylint_score.assert_called_once()
    lint_monitor._trim_history.assert_called_once()
    lint_monitor.calculate_improvements.assert_called_once()
    lint_monitor._create_lint_table.assert_called_once()
    lint_monitor._log_and_display.assert_called_once()


def test_trim_history(lint_monitor: LintMonitor) -> None:
    """Test the trimming of the history."""
    now = datetime.now()
    history = [
        (now - timedelta(hours=2), 6.0),
        (now - timedelta(minutes=15), 7.0),
        (now - timedelta(minutes=5), 8.0),
        (now, 9.0),
    ]
    lint_monitor.history = deque(history)
    lint_monitor._trim_history()
    assert len(lint_monitor.history) == 3
    assert lint_monitor.history[0][1] == 7.0
