#!/usr/bin/env python3
#!/usr/bin/env python3

from lint_monitor.monitor import LintMonitor


def main() -> None:
    monitor = LintMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
