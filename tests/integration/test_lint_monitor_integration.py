import unittest
import subprocess
from lint_monitor.monitor import LintMonitor


class TestLintMonitorIntegration(unittest.TestCase):
    def test_monitor_runs_without_errors(self):
        # This test assumes that pylint is installed and accessible in the environment.
        # It also assumes that there are python files in the evoprompt directory.
        try:
            monitor = LintMonitor()
            monitor.max_iterations = 1  # Limit to one iteration for testing
            monitor.run()
        except Exception as e:
            self.fail(f"LintMonitor.run() raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
