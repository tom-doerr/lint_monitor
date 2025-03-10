"""Integration tests for the lint-monitor CLI."""

import subprocess
import pytest


def test_cli_runs_without_errors() -> None:
    """Test that the CLI runs without errors."""
    result = subprocess.run(
        ["lint-monitor", "--max-iterations", "1"], check=True, capture_output=True, text=True
    )
    assert result.returncode == 0, f"CLI exited with an error: {result.stderr}"
