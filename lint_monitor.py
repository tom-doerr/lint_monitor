#!/usr/bin/env python3
"""Entry point for the lint-monitor CLI."""

from lint_monitor.monitor import LintMonitor


def main() -> None:
    """Main function."""
    config = LintMonitor.MonitorConfig(pylint_command=["pylint", "evoprompt/**py"])
    monitor = LintMonitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
