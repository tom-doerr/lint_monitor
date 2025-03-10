"""Unit tests for the lint monitor package."""

from collections import deque
from datetime import datetime, timedelta
import subprocess

import pytest

from lint_monitor.monitor import LintMonitor, MonitorConfig


@pytest.fixture
def lint_monitor() -> LintMonitor:
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

    mock_run.side_effect = None
    mock_run.return_value.stdout = "Invalid score format"
    assert lm.get_pylint_score() is None


def _assert_improvements(
    improvements: dict[str, Optional[float]],
    expected_values: list[float | None],
    lm: LintMonitor,
) -> None:
    assert len(improvements) == len(lm.TIME_WINDOWS)
    for i, window in enumerate(lm.TIME_WINDOWS):
        expected = expected_values[i]
        actual = improvements[window[0]]
        if expected is None:
            assert actual is None
        else:
            assert actual == pytest.approx(expected)


def _run_test(
    lm: LintMonitor,
    history: list[tuple[datetime, float]],
    expected_values: list[float | None],
) -> None:
    lm.history = deque(history)
    improvements = lm.calculate_improvements()
    _assert_improvements(improvements, expected_values, lm)


def test_calculate_improvements(lm: LintMonitor) -> None:
    """Test the improvement calculation over time windows."""

    # Test case 1: Sufficient data for all time windows
    _run_test(
        lm,
        [
            (NOW - timedelta(hours=1), 6.0),
            (NOW - timedelta(minutes=15), 7.0),
            (NOW - timedelta(minutes=5), 8.0),
            (NOW, 9.0),
        ],
        [3.0, 2.0, 3.0, None, None],
    )

    # Test case 2: Insufficient data for any time window
    _run_test(lm, [], [None] * len(lm.TIME_WINDOWS))

    # Test case 3: Only one data point
    _run_test(lm, [(NOW, 7.0)], [None] * len(lm.TIME_WINDOWS))

    # Test case 4: Data only within the shortest time window
    _run_test(
        lm,
        [
            (NOW - timedelta(minutes=4), 7.0),
            (NOW, 8.0),
        ],
        [1.0, None, None, None, None],
    )


def test_get_pylint_score_no_score(mocker: pytest.fixture, lm: LintMonitor) -> None:
    """Test the pylint score extraction when no score is returned."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = "Some other output"
    mock_run.return_value.returncode = 1  # Simulate an error
    lm.get_pylint_score()
    assert lm.get_pylint_score() is None


def test_run(mocker: pytest.fixture) -> None:
    """Test the main monitoring loop functionality."""
    config = MonitorConfig(pylint_command=["pylint", "evoprompt/**py"])
    monitor = LintMonitor(config)
    monitor.get_pylint_score = mocker.MagicMock(return_value=9.0)
    mock_console = mocker.patch("lint_monitor.monitor.Console")
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()


def test_run_score_below_7(mocker: pytest.fixture) -> None:
    """Test the main monitoring loop functionality with score below 7."""
    config = MonitorConfig(pylint_command=["pylint", "evoprompt/**py"])
    monitor = LintMonitor(config)
    monitor.get_pylint_score = mocker.MagicMock(return_value=6.0)
    mock_console = mocker.patch("lint_monitor.monitor.Console")
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()


def test_run_score_between_7_and_9(mocker: pytest.fixture) -> None:
    """Test the main monitoring loop functionality with score between 7 and 9."""
    config = MonitorConfig(pylint_command=["pylint", "evoprompt/**py"])
    monitor = LintMonitor(config)
    monitor.get_pylint_score = mocker.MagicMock(return_value=8.0)
    mock_console = mocker.patch("lint_monitor.monitor.Console")
    mock_console.return_value.print.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        monitor.run()
