import subprocess

from lint_monitor.monitor import LintMonitor, MonitorConfig


def test_monitor_runs_without_errors() -> None:
    """Test that the monitor runs without errors."""
    # This test assumes that pylint is installed and accessible in the environment.
    # It also assumes that there are python files in the evoprompt directory.
    config = MonitorConfig(max_iterations=1)  # Limit to one iteration for testing
    monitor = LintMonitor(config)
    try:
        monitor.run()
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        assert False, f"LintMonitor.run() raised an exception: {e}"
