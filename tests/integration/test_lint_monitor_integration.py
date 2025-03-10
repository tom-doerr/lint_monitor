import subprocess
import glob

from lint_monitor import LintMonitor, MonitorConfig


def test_monitor_runs_without_errors() -> None:
    """Test that the monitor runs without errors."""
    # This test assumes that pylint is installed and accessible in the environment.
    # It also assumes that there are python files in the project directory.
    python_files = glob.glob("*.py") + glob.glob("**/*.py", recursive=True)
    pylint_command = ["pylint"] + python_files
    config = MonitorConfig(pylint_command=pylint_command, max_iterations=1)
    monitor = LintMonitor(config)
    monitor.run()
