"""Tests driving the roll CLI through a subprocess."""

import json
import subprocess
import sys


def run_cli(*args):
    """Run tools/roll.py with args and return the completed process."""
    return subprocess.run(
        [sys.executable, "tools/roll.py", *args],
        capture_output=True,
        text=True,
    )


def test_json_keys_without_detail():
    proc = run_cli("1d20", "--seed", "42", "--json")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert set(payload) == {"result", "description", "seed"}


def test_json_keys_with_detail():
    proc = run_cli("1d20", "--seed", "42", "--json", "--detail")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert set(payload) == {"result", "description", "seed", "breakdown"}


def test_format_minimal_prints_only_total():
    proc = run_cli("4d6kh3", "--seed", "42", "--format", "minimal")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "8"


def test_check_valid_expression_text():
    proc = run_cli("4d6kh3 + 2", "--check")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "valid"
    assert proc.stderr == ""


def test_check_invalid_expression_text():
    proc = run_cli("1d20+{{ x }}", "--check")
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "Invalid character" in proc.stderr


def test_check_valid_expression_json():
    proc = run_cli("4d6kh3 + 2", "--check", "--json")
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {"valid": True}


def test_check_invalid_expression_json():
    proc = run_cli("1d6r<=6", "--check", "--json")
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["valid"] is False
    assert "Infinite reroll condition" in payload["error"]
