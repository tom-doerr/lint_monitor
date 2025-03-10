#!/usr/bin/env python3
"""Entry point for the lint-monitor CLI."""

import argparse
from lint_monitor.monitor import LintMonitor, MonitorConfig


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Monitor lint quality and track improvements over time."
    )
    parser.add_argument(
        "--pylint-command",
        nargs="+",
        default=["pylint", "evoprompt/**py"],
        help="The pylint command to run.",
    )
    args = parser.parse_args()

    config = MonitorConfig(pylint_command=args.pylint_command)
    monitor = LintMonitor(config)


