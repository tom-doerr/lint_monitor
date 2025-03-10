import subprocess
import glob
import os

from lint_monitor.monitor import LintMonitor, MonitorConfig


def test_monitor_runs_without_errors() -> None:
    """Test that the monitor runs without errors."""
    # This test assumes that pylint is installed and accessible in the environment.
    # It also assumes that there are python files in the project directory.
    python_files = glob.glob("*.py") + glob.glob("**/*.py", recursive=True)
    pylint_command = ["pylint"] + python_files
    config = MonitorConfig(
        pylint_command=pylint_command, max_iterations=1
    )  # Limit to one iteration for testing
    monitor = LintMonitor(config)
    try:
        monitor.run()
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        assert False, f"LintMonitor.run() raised an exception: {e}"
