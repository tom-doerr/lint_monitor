"""Unit tests for the lint monitor package."""

from collections import deque
from datetime import datetime, timedelta
import subprocess
from typing import Optional

import pytest

from lint_monitor.monitor import LintMonitor, MonitorConfig


@pytest.fixture()
def lm() -> LintMonitor:
    """Fixture to create a LintMonitor instance with a default configuration."""
    config = MonitorConfig(pylint_command=["pylint", "evoprompt/**py"])
    return LintMonitor(config)


NOW = datetime.now()  # Store current datetime


def test_get_pylint_score(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the pylint score extraction functionality."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = "Your code has been rated at 9.50/10"
    assert lm.get_pylint_score() == 9.5

    mock_run.side_effect = subprocess.CalledProcessError(1, "pylint")
    assert lm.get_pylint_score() is None


def test_run_pylint(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the _run_pylint method."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = "Your code has been rated at 9.50/10"
    lm.__run_pylint()
    mock_run.assert_called_once()

    mock_run.side_effect = subprocess.CalledProcessError(1, "pylint")
    assert lm.__run_pylint() is None


def test_extract_score(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the _extract_score method."""
    assert lm.__extract_score("Your code has been rated at 9.50/10") == 9.5
    assert lm.__extract_score("Invalid score format") is None
    assert lm.__extract_score(None) is None

    mock_run.side_effect = None
    mock_run.return_value.stdout = "Invalid score format"
    assert lm.get_pylint_score() is None


def test_calculate_improvements(lm: LintMonitor) -> None:
    """Test the improvement calculation over time windows."""

    def _assert_improvements(improvements: dict[str, Optional[float]], expected_values: list[float | None]) -> None:
        assert len(improvements) == len(lm.TIME_WINDOWS)
        for i, window in enumerate(lm.TIME_WINDOWS):
            expected = expected_values[i]
            actual = improvements[window[0]]
            if expected is None:
                assert actual is None
            else:
                assert actual == pytest.approx(expected)

    def _run_test(history: list[tuple[datetime, float]], expected_values: list[float | None]) -> None:
        lm.history = deque(history)
        improvements = lm.calculate_improvements()
        _assert_improvements(improvements, expected_values)

    test_cases = [
        (
            [(NOW - timedelta(hours=1), 6.0), (NOW - timedelta(minutes=15), 7.0), (NOW - timedelta(minutes=5), 8.0),
             (NOW, 9.0)],
            [3.0, 2.0, 3.0, None, None],
        ),
        (
            [],
            [None] * len(lm.TIME_WINDOWS),
        ),
        (
            [(NOW, 7.0)],
            [None] * len(lm.TIME_WINDOWS),
        ),
        (
            [(NOW - timedelta(minutes=4), 7.0), (NOW, 8.0)],
            [1.0, None, None, None, None],
        ),
    ]
    for history, expected_values in test_cases:
        _run_test(history, expected_values)


def test_get_pylint_score_no_score(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the pylint score extraction when no score is returned."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = "Some other output"
    mock_run.return_value.returncode = 1  # Simulate an error
    lm.get_pylint_score()
    assert lm.get_pylint_score() is None


def test_run(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the main monitoring loop functionality."""
    lm.get_pylint_score = mocker.MagicMock(return_value=9.0)
    lm.running = False  # Stop the loop after one iteration
    mocker.patch("lint_monitor.monitor.Console")

    lm.run()


def test_run_score_below_7(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the main monitoring loop functionality with score below 7."""
    lm.get_pylint_score = mocker.MagicMock(return_value=6.0)
    lm.running = False  # Stop the loop after one iteration
    mocker.patch("lint_monitor.monitor.Console")

    lm.run()


def test_run_score_between_7_and_9(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the main monitoring loop functionality with score between 7 and 9."""
    lm.get_pylint_score = mocker.MagicMock(return_value=8.0)
    lm.running = False  # Stop the loop after one iteration
    mocker.patch("lint_monitor.monitor.Console")

    lm.run()
