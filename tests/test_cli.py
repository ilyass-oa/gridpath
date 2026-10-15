"""Run the installed-style module in fresh subprocesses without a display."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments, stdin=None):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment.pop("DISPLAY", None)
    environment.pop("WAYLAND_DISPLAY", None)
    return subprocess.run(
        [sys.executable, "-m", "gridpath", *map(str, arguments)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=15,
    )


@pytest.mark.parametrize("algorithm", ["dfs", "bfs", "astar"])
def test_cooperative_example_without_display(algorithm):
    result = run(
        "--map", "examples/cooperative.txt", "--problem", "gems", "--algorithm", algorithm, "--json"
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["status"] == "solved"
    assert data["algorithm"] == algorithm
    assert data["steps"] == len(data["actions"])
    assert all(len(actions) == 2 for actions in data["actions"])


def test_stdin_and_plain_output():
    result = run("--map", "-", stdin="S0 . X")
    assert result.returncode == 0, result.stderr
    assert "Solved in 2 steps" in result.stdout
    assert "EAST" in result.stdout


def test_unreachable_and_budget_are_distinct():
    unreachable = run("--map", "-", "--json", stdin="S0 @ X")
    assert unreachable.returncode == 1
    assert json.loads(unreachable.stdout)["status"] == "unreachable"
    limited = run("--map", "-", "--max-expanded", "1", "--json", stdin="S0 . X")
    assert limited.returncode == 3
    assert json.loads(limited.stdout)["status"] == "limit_reached"


@pytest.mark.parametrize(
    "arguments",
    [
        ("--level", "7"),
        ("--algorithm", "greedy"),
        ("--max-expanded", "0"),
        ("--max-expanded", "no"),
        ("--map", "missing.txt"),
        ("--map", "examples"),
        ("--level", "1", "--map", "examples/gems.txt"),
    ],
)
def test_invalid_arguments(arguments):
    result = run(*arguments)
    assert result.returncode == 2
    assert "error" in result.stderr.lower()
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("content", ["", "S0 X\n. . .", "S0 ? X"])
def test_invalid_map_is_reported_cleanly(content):
    result = run("--map", "-", stdin=content)
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert "Traceback" not in result.stderr


def test_oversized_map_and_nonregular_file(tmp_path):
    result = run("--map", "-", stdin="." * (1024 * 1024 + 1))
    assert result.returncode == 2
    assert "exceeds" in result.stderr
    fifo = tmp_path / "map.pipe"
    os.mkfifo(fifo)
    result = run("--map", fifo)
    assert result.returncode == 2
    invalid_utf8 = tmp_path / "bad.map"
    invalid_utf8.write_bytes(b"\xff\xff")
    assert run("--map", invalid_utf8).returncode == 2


def test_help_and_import_have_no_interactive_side_effects():
    assert run("--help").returncode == 0
    result = subprocess.run(
        [sys.executable, "-c", "import gridpath; import gridpath.cli"],
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
