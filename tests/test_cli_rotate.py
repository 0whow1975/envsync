"""Tests for envsync.cli_rotate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsync.cli_rotate import add_rotate_subparser, cmd_rotate


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture
def env_pair(tmp_path):
    a = _write(tmp_path / ".env.a", "DB_HOST=localhost\nDB_PORT=5432\n")
    b = _write(tmp_path / ".env.b", "DB_HOST=prod-db\nDB_PORT=5432\n")
    return a, b


class _Args:
    def __init__(self, files, rename, dry_run=False, strict=False):
        self.files = [str(f) for f in files]
        self.rename = rename
        self.dry_run = dry_run
        self.strict = strict


def test_add_rotate_subparser_registers_command():
    import argparse
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_rotate_subparser(subs)
    args = parser.parse_args(["rotate", "file.env", "--rename", "OLD=NEW"])
    assert hasattr(args, "func")


def test_cmd_rotate_returns_zero(env_pair):
    a, b = env_pair
    args = _Args([a, b], rename=["DB_HOST=DATABASE_HOST"])
    assert cmd_rotate(args) == 0


def test_cmd_rotate_writes_new_key(env_pair):
    a, _ = env_pair
    args = _Args([a], rename=["DB_HOST=DATABASE_HOST"])
    cmd_rotate(args)
    content = a.read_text()
    assert "DATABASE_HOST" in content
    assert "DB_HOST" not in content


def test_cmd_rotate_dry_run_does_not_write(env_pair):
    a, _ = env_pair
    original = a.read_text()
    args = _Args([a], rename=["DB_HOST=DATABASE_HOST"], dry_run=True)
    rc = cmd_rotate(args)
    assert rc == 0
    assert a.read_text() == original


def test_cmd_rotate_invalid_rename_arg_exits(env_pair, capsys):
    a, _ = env_pair
    args = _Args([a], rename=["BADFORMAT"])
    with pytest.raises(SystemExit) as exc_info:
        cmd_rotate(args)
    assert exc_info.value.code == 1


def test_cmd_rotate_strict_missing_returns_nonzero(env_pair):
    a, _ = env_pair
    args = _Args([a], rename=["NONEXISTENT=NEW_KEY"], strict=True)
    rc = cmd_rotate(args)
    assert rc == 1
