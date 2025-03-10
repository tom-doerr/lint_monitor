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
        default=["pylint"],
        help="The pylint command to run.",
    )
    args = parser.parse_args()

    if args.pylint_command == ["pylint"]:
        # If the user didn't specify a command, use the default which is pylint + all python files
        pylint_command = ["pylint"] + subprocess.check_output(["git", "ls-files", "*.py"]).decode("utf-8").split()
    else:
        pylint_command = args.pylint_command

    config = MonitorConfig(pylint_command=pylint_command)
    monitor = LintMonitor(config)
