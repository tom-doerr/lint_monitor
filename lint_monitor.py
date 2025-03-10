#!/usr/bin/env python3

import argparse
import subprocess
from lint_monitor.monitor import LintMonitor, MonitorConfig


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor lint quality and track improvements over time."
    )
    parser.add_argument(
        "--pylint-command",
        nargs="+",
        default=["pylint"],
        help="The pylint command to run.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=float("inf"),
        help="Maximum number of iterations to run the monitor for.",
    )
    args = parser.parse_args()

    if args.pylint_command == ["pylint"]:
        # If the user didn't specify a command, use the default which is pylint + all python files
        pylint_command = ["pylint"] + subprocess.check_output(
            ["git", "ls-files", "*.py"]
        ).decode("utf-8").split()
    else:
        pylint_command = args.pylint_command

    config = MonitorConfig(pylint_command=pylint_command, max_iterations=args.max_iterations)
    monitor = LintMonitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
