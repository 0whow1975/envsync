"""Tests for envsync.cli_alias."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsync.cli_alias import add_alias_subparser, cmd_alias


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


@pytest.fixture()
def env_file(tmp_path):
    return _write(tmp_path, ".env", "OLD_API_KEY=secret\nDB_HOST=localhost\n")


@pytest.fixture()
def alias_file(tmp_path):
    mapping = {"OLD_API_KEY": "API_KEY"}
    p = tmp_path / "aliases.json"
    p.write_text(json.dumps(mapping))
    return p


class _Args:
    def __init__(self, env_file, alias_map, remove_alias=True, overwrite=False, in_place=False):
        self.env_file = str(env_file)
        self.alias_map = str(alias_map)
        self.remove_alias = remove_alias
        self.overwrite = overwrite
        self.in_place = in_place


def test_add_alias_subparser_registers_command():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_alias_subparser(sub)
    args = parser.parse_args(["alias", "env", "map.json"])
    assert hasattr(args, "func")


def test_cmd_alias_returns_zero(env_file, alias_file):
    args = _Args(env_file, alias_file)
    assert cmd_alias(args) == 0


def test_cmd_alias_outputs_canonical_key(env_file, alias_file, capsys):
    args = _Args(env_file, alias_file)
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "API_KEY=secret" in out


def test_cmd_alias_removes_old_key_by_default(env_file, alias_file, capsys):
    args = _Args(env_file, alias_file)
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "OLD_API_KEY" not in out


def test_cmd_alias_keeps_old_key_when_no_remove(env_file, alias_file, capsys):
    args = _Args(env_file, alias_file, remove_alias=False)
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "OLD_API_KEY" in out
    assert "API_KEY=secret" in out


def test_cmd_alias_writes_in_place(env_file, alias_file):
    args = _Args(env_file, alias_file, in_place=True)
    cmd_alias(args)
    content = Path(str(env_file)).read_text()
    assert "API_KEY=secret" in content
    assert "OLD_API_KEY" not in content
