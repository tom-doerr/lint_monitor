"""Unit tests for the lint monitor package."""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from collections import deque
import subprocess
from lint_monitor import LintMonitor


class TestLintMonitor(unittest.TestCase):
    """Test cases for the LintMonitor class."""

    INTERVAL = 0.1  # Shorten interval for testing
    MAX_ITERATIONS = 5  # Limit iterations

    def setUp(self):
        """Set up for test methods."""
        self.monitor = LintMonitor()
        self.monitor.interval = self.INTERVAL
        self.monitor.max_iterations = self.MAX_ITERATIONS

    @patch("subprocess.run")
    def test_get_pylint_score(self, mock_run):
        """Test the pylint score extraction functionality."""
        # Test successful score extraction
        mock_run.return_value.stdout = "Your code has been rated at 9.50/10"
        score = self.monitor.get_pylint_score()
        self.assertEqual(score, 9.5)

        # Test failed run
        mock_run.side_effect = subprocess.CalledProcessError(1, "pylint")
        score = self.monitor.get_pylint_score()
        self.assertIsNone(score)

        # Test invalid score format
        mock_run.return_value.stdout = "Invalid score format"
        score = self.monitor.get_pylint_score()
        self.assertIsNone(score)

    def test_calculate_improvements(self):
        """Test the improvement calculation over time windows."""
        # Set up test data
        now = datetime.now()
        self.monitor.history = deque(
            [
                (now - timedelta(minutes=10), 7.0),
                (now - timedelta(minutes=5), 8.0),
                (now, 9.0),
            ]
        )

        improvements = self.monitor.calculate_improvements()

        self.assertEqual(len(improvements), len(LintMonitor.TIME_WINDOWS))
        # The 5m improvement should be 0.0 because there are not 2 data points within the 5m window
        self.assertAlmostEqual(improvements["5m"], 0.0)
        self.assertAlmostEqual(improvements["15m"], 2.0)
        self.assertAlmostEqual(improvements["1h"], 2.0)
        self.assertAlmostEqual(improvements["4h"], 2.0)
        self.assertAlmostEqual(improvements["16h"], 2.0)

        # Test with empty history
        self.monitor.history = deque()
        improvements = self.monitor.calculate_improvements()
        self.assertEqual(len(improvements), len(LintMonitor.TIME_WINDOWS))
        for _, value in improvements.items():
            self.assertIsNone(value)

        # Test with only one data point
        self.monitor.history = deque([(now, 7.0)])
        improvements = self.monitor.calculate_improvements()
        self.assertEqual(len(improvements), len(LintMonitor.TIME_WINDOWS))
        for _, value in improvements.items():
            self.assertIsNone(value)

    @patch("subprocess.run")
    def test_get_pylint_score_no_score(self, mock_run):
        """Test the pylint score extraction when no score is returned."""
        mock_run.return_value.stdout = "Some other output"
        mock_run.return_value.returncode = 1  # Simulate an error
        score = self.monitor.get_pylint_score()
        self.assertIsNone(score)

    def _run_monitor_test(
        self, mock_console, mock_score, expected_score: float
    ) -> None:
        """Helper function to run monitor tests."""
        mock_score.return_value = expected_score
        mock_console.return_value.print.side_effect = KeyboardInterrupt()

        try:
            self.monitor.run()
        except KeyboardInterrupt:
            self.monitor.running = False
        mock_console.return_value.print.assert_called_with(
            "\n[bold red]Monitoring stopped.[/]"
        )

    @patch("lint_monitor.monitor.LintMonitor.get_pylint_score")
    @patch("lint_monitor.monitor.Console")
    def test_run(self, mock_console, mock_score) -> None:
        """Test the main monitoring loop functionality."""
        self._run_monitor_test(mock_console, mock_score, 9.0)

    @patch("lint_monitor.monitor.LintMonitor.get_pylint_score")
    @patch("lint_monitor.monitor.Console")
    def test_run_score_below_7(self, mock_console, mock_score) -> None:
        """Test the main monitoring loop functionality with score below 7."""
        self._run_monitor_test(mock_console, mock_score, 6.0)

    @patch("lint_monitor.monitor.LintMonitor.get_pylint_score")
    @patch("lint_monitor.monitor.Console")
    def test_run_score_between_7_and_9(self, mock_console, mock_score) -> None:
        """Test the main monitoring loop functionality with score between 7 and 9."""
        self._run_monitor_test(mock_console, mock_score, 8.0)


if __name__ == "__main__":
    unittest.main()
