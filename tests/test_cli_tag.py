"""Tests for envsync.cli_tag."""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import pytest

from envsync.cli_tag import add_tag_subparser, cmd_tag


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


@pytest.fixture()
def env_file(tmp_path):
    return _write(tmp_path, ".env", """
        DB_HOST=localhost
        DB_PASSWORD=s3cr3t
        APP_ENV=production
    """)


@pytest.fixture()
def tag_file(tmp_path):
    data = {
        "DB_HOST": ["database", "infra"],
        "DB_PASSWORD": ["database", "secret"],
        "APP_ENV": ["app"],
    }
    p = tmp_path / "tags.json"
    p.write_text(json.dumps(data))
    return p


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# ---------------------------------------------------------------------------
# subparser registration
# ---------------------------------------------------------------------------

def test_add_tag_subparser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_tag_subparser(sub)
    ns = root.parse_args(["tag", "list", ".env", "tags.json"])
    assert ns.cmd == "tag"


# ---------------------------------------------------------------------------
# cmd_tag list
# ---------------------------------------------------------------------------

def test_cmd_tag_list_returns_zero(env_file, tag_file, capsys):
    args = _Args(
        tag_cmd="list",
        env_file=str(env_file),
        tag_map=str(tag_file),
        case_sensitive=False,
    )
    rc = cmd_tag(args)
    assert rc == 0


def test_cmd_tag_list_outputs_tags(env_file, tag_file, capsys):
    args = _Args(
        tag_cmd="list",
        env_file=str(env_file),
        tag_map=str(tag_file),
        case_sensitive=False,
    )
    cmd_tag(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "database" in out


# ---------------------------------------------------------------------------
# cmd_tag filter
# ---------------------------------------------------------------------------

def test_cmd_tag_filter_returns_zero(env_file, tag_file, capsys):
    args = _Args(
        tag_cmd="filter",
        env_file=str(env_file),
        tag_map=str(tag_file),
        tag="secret",
        case_sensitive=False,
    )
    assert cmd_tag(args) == 0


def test_cmd_tag_filter_prints_matching_entries(env_file, tag_file, capsys):
    args = _Args(
        tag_cmd="filter",
        env_file=str(env_file),
        tag_map=str(tag_file),
        tag="database",
        case_sensitive=False,
    )
    cmd_tag(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "DB_PASSWORD" in out
    assert "APP_ENV" not in out


def test_cmd_tag_unknown_subcommand_returns_one(env_file, tag_file, capsys):
    args = _Args(
        tag_cmd="unknown",
        env_file=str(env_file),
        tag_map=str(tag_file),
        case_sensitive=False,
    )
    assert cmd_tag(args) == 1
