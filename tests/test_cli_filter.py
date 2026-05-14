"""Tests for envsync.cli_filter."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envsync.cli_filter import add_filter_subparser, cmd_filter


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent(content))
    return p


@pytest.fixture
def env_file(tmp_path):
    return _write(
        tmp_path,
        """
        DB_HOST=localhost
        DB_PASSWORD=secret
        APP_PORT=8080
        LOG_LEVEL=info
        """,
    )


class _Args:
    def __init__(self, env_file, prefixes=None, patterns=None, invert=False, case_sensitive=False):
        self.env_file = str(env_file)
        self.prefixes = prefixes or []
        self.patterns = patterns or []
        self.invert = invert
        self.case_sensitive = case_sensitive


def test_add_filter_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_filter_subparser(sub)
    args = parser.parse_args(["filter", "/dev/null"])
    assert hasattr(args, "func")


def test_cmd_filter_returns_zero(env_file):
    assert cmd_filter(_Args(env_file)) == 0


def test_cmd_filter_missing_file_returns_one(tmp_path):
    assert cmd_filter(_Args(tmp_path / "missing.env")) == 1


def test_cmd_filter_prefix_prints_only_matching(env_file, capsys):
    cmd_filter(_Args(env_file, prefixes=["DB_"]))
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "DB_PASSWORD" in out
    assert "APP_PORT" not in out


def test_cmd_filter_invert_excludes_prefix(env_file, capsys):
    cmd_filter(_Args(env_file, prefixes=["DB_"], invert=True))
    out = capsys.readouterr().out
    assert "DB_HOST" not in out
    assert "APP_PORT" in out


def test_cmd_filter_pattern(env_file, capsys):
    cmd_filter(_Args(env_file, patterns=[r".*_PORT$"]))
    out = capsys.readouterr().out
    assert "APP_PORT" in out
    assert "DB_HOST" not in out
