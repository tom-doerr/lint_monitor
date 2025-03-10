import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from collections import deque
from lint_monitor import LintMonitor

class TestLintMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = LintMonitor()
        
    @patch('subprocess.run')
    def test_get_pylint_score(self, mock_run):
        # Test successful score extraction
        mock_run.return_value.stdout = "Your code has been rated at 9.50/10"
        score = self.monitor.get_pylint_score()
        self.assertEqual(score, 9.5)
        
        # Test failed run
        mock_run.side_effect = subprocess.CalledProcessError(1, 'pylint')
        score = self.monitor.get_pylint_score()
        self.assertIsNone(score)
        
    def test_calculate_improvements(self):
        # Setup test data
        now = datetime.now()
        self.monitor.history = deque([
            (now - timedelta(minutes=10), 7.0),
            (now - timedelta(minutes=5), 8.0),
            (now, 9.0)
        ])
        
        improvements = self.monitor.calculate_improvements()
        
        # Check that we get improvements for all windows
        self.assertEqual(len(improvements), 5)
        self.assertAlmostEqual(improvements['5m'], 1.0)
        
    @patch('lint_monitor.monitor.LintMonitor.get_pylint_score')
    @patch('lint_monitor.monitor.Console')
    def test_run(self, mock_console, mock_score):
        # Setup mock score
        mock_score.return_value = 9.0
        
        # Test keyboard interrupt handling
        mock_console.return_value.print.side_effect = KeyboardInterrupt()
        
        # Run and verify it handles interrupt
        self.monitor.run()
        mock_console.return_value.print.assert_called_with("\n[bold red]Monitoring stopped.[/]")

if __name__ == '__main__':
    unittest.main()
