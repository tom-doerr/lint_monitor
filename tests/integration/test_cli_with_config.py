"""Integration tests for the lint-monitor CLI with a configuration file."""

import subprocess
import pytest
import os
import tempfile
import shutil


def test_cli_runs_with_config() -> None:
    """Test that the CLI runs without errors when a config file is specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.ini")
        with open(config_file, "w") as f:
            f.write("[settings]\npylint_command = pylint --version")

        result = subprocess.run(
            ["lint-monitor", "--config", config_file, "--max-iterations", "1"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"CLI exited with an error: {result.stderr}"


def test_cli_config_file_not_found() -> None:
    """Test that the CLI handles the case where the config file is not found."""
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.run(
            ["lint-monitor", "--config", "nonexistent_config.ini", "--max-iterations", "1"],
            check=True,
            capture_output=True,
            text=True,
        )
    assert "FileNotFoundError" in str(excinfo.value.stderr)


def test_cli_invalid_config_file() -> None:
    """Test that the CLI handles the case where the config file is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.ini")
        with open(config_file, "w") as f:
            f.write("invalid config")

        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            subprocess.run(
                ["lint-monitor", "--config", config_file, "--max-iterations", "1"],
                check=True,
                capture_output=True,
                text=True,
            )
        assert "Error parsing" in str(excinfo.value.stderr)
        assert "config.ini" in str(excinfo.value.stderr)
