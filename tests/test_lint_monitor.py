"""Unit tests for the lint monitor package."""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from collections import deque
import subprocess
from lint_monitor import LintMonitor


class TestLintMonitor(unittest.TestCase):
    """Test cases for the LintMonitor class."""

    def setUp(self):
        self.monitor = LintMonitor()

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

    def test_calculate_improvements(self):
        """Test the improvement calculation over time windows."""
        # Setup test data
        now = datetime.now()
        self.monitor.history = deque(
            [
                (now - timedelta(minutes=10), 7.0),
                (now - timedelta(minutes=5), 8.0),
                (now, 9.0),
            ]
        )

        improvements = self.monitor.calculate_improvements()

        # Check that we get improvements for all windows
        self.assertEqual(len(improvements), 5)
        self.assertAlmostEqual(improvements["5m"], 1.0)
        self.assertAlmostEqual(improvements["15m"], 2.0)
        self.assertAlmostEqual(improvements["1h"], 2.0)
        self.assertAlmostEqual(improvements["4h"], 2.0)
        self.assertAlmostEqual(improvements["16h"], 2.0)

        # Test with empty history
        self.monitor.history = deque()
        improvements = self.monitor.calculate_improvements()
        self.assertEqual(len(improvements), 5)
        for window in improvements:
            self.assertIsNone(improvements[window])

    @patch("lint_monitor.monitor.LintMonitor.get_pylint_score")
    @patch("lint_monitor.monitor.Console")
    def test_run(self, mock_console, mock_score):
        """Test the main monitoring loop functionality."""
        # Setup mock score
        mock_score.return_value = 9.0

        # Test keyboard interrupt handling
        mock_console.return_value.print.side_effect = KeyboardInterrupt()

        # Run and verify it handles interrupt
        self.monitor.run()
        mock_console.return_value.print.assert_called_with(
            "\n[bold red]Monitoring stopped.[/]"
        )

    @patch("lint_monitor.monitor.LintMonitor.get_pylint_score")
    @patch("lint_monitor.monitor.Console")
    def test_run_score_below_7(self, mock_console, mock_score):
        """Test the main monitoring loop functionality with score below 7."""
        mock_score.return_value = 6.0
        mock_console.return_value.print.side_effect = KeyboardInterrupt()
        self.monitor.run()
        mock_console.return_value.print.assert_called_with(
            "\n[bold red]Monitoring stopped.[/]"
        )

    @patch("lint_monitor.monitor.LintMonitor.get_pylint_score")
    @patch("lint_monitor.monitor.Console")
    def test_run_score_between_7_and_9(self, mock_console, mock_score):
        """Test the main monitoring loop functionality with score between 7 and 9."""
        mock_score.return_value = 8.0
        mock_console.return_value.print.side_effect = KeyboardInterrupt()
        self.monitor.run()
        mock_console.return_value.print.assert_called_with(
            "\n[bold red]Monitoring stopped.[/]"
        )


if __name__ == "__main__":
    unittest.main()
