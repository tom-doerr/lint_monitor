import subprocess
import pytest
from lint_monitor.monitor import LintMonitor


def test_monitor_runs_without_errors():
    # This test assumes that pylint is installed and accessible in the environment.
    # It also assumes that there are python files in the evoprompt directory.
    try:
        monitor = LintMonitor()
        monitor.max_iterations = 1  # Limit to one iteration for testing
        monitor.run()
    except subprocess.CalledProcessError as e:
        assert False, f"LintMonitor.run() raised an exception: {e}"
