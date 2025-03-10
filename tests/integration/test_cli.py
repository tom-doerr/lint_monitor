"""Integration tests for the lint-monitor CLI."""

import subprocess
import pytest


def test_cli_runs_without_errors() -> None:
    """Test that the CLI runs without errors."""
    try:
        subprocess.run(
            ["lint-monitor", "--max-iterations", "1"], check=True, capture_output=True
        )
    except subprocess.CalledProcessError as e:
        pytest.fail(f"CLI exited with an error: {e.stderr.decode()}")
