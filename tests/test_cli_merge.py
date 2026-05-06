"""Tests for envsync.cli_merge."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envsync.cli_merge import add_merge_subparser, cmd_merge


@pytest.fixture()
def env_pair(tmp_path: Path):
    base = tmp_path / ".env.base"
    base.write_text("APP=myapp\nDEBUG=false\nPORT=8000\n")
    override = tmp_path / ".env.override"
    override.write_text("DEBUG=true\nSECRET_KEY=abc123\n")
    return base, override


class _Args:
    def __init__(self, sources, output=None, strategy="last", no_comments=False):
        self.sources = [str(s) for s in sources]
        self.output = str(output) if output else None
        self.strategy = strategy
        self.no_comments = no_comments


def test_add_merge_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_merge_subparser(sub)
    args = parser.parse_args(["merge", "a.env", "b.env"])
    assert hasattr(args, "func")


def test_cmd_merge_writes_to_stdout(env_pair, capsys):
    base, override = env_pair
    args = _Args([base, override])
    rc = cmd_merge(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "SECRET_KEY=abc123" in captured.out


def test_cmd_merge_last_strategy_wins(env_pair, capsys):
    base, override = env_pair
    args = _Args([base, override], strategy="last")
    cmd_merge(args)
    out = capsys.readouterr().out
    assert "DEBUG=true" in out


def test_cmd_merge_first_strategy_wins(env_pair, capsys):
    base, override = env_pair
    args = _Args([base, override], strategy="first")
    cmd_merge(args)
    out = capsys.readouterr().out
    assert "DEBUG=false" in out


def test_cmd_merge_output_file(env_pair, tmp_path):
    base, override = env_pair
    out_file = tmp_path / "merged.env"
    args = _Args([base, override], output=out_file)
    rc = cmd_merge(args)
    assert rc == 0
    content = out_file.read_text()
    assert "APP=myapp" in content
    assert "SECRET_KEY=abc123" in content


def test_cmd_merge_missing_file_returns_error(tmp_path):
    args = _Args([tmp_path / "nonexistent.env"])
    rc = cmd_merge(args)
    assert rc == 1


def test_cmd_merge_error_strategy_conflict_returns_code(env_pair):
    base, override = env_pair
    args = _Args([base, override], strategy="error")
    rc = cmd_merge(args)
    assert rc == 2
