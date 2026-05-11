"""Tests for the rename CLI command."""

import argparse
import pytest
from pathlib import Path

from envsync.renamer import RenameOptions, RenameResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


@pytest.fixture()
def env_pair(tmp_path):
    """Two env files that share a key to be renamed."""
    src = _write(tmp_path, ".env.source", "OLD_KEY=hello\nKEEP=world\n")
    tgt = _write(tmp_path, ".env.target", "OLD_KEY=there\nOTHER=value\n")
    return src, tgt


class _Args:
    """Minimal namespace that mimics argparse output for cmd_rename."""

    def __init__(
        self,
        files,
        old_key,
        new_key,
        dry_run=False,
        overwrite=False,
    ):
        self.files = [str(f) for f in files]
        self.old_key = old_key
        self.new_key = new_key
        self.dry_run = dry_run
        self.overwrite = overwrite


# ---------------------------------------------------------------------------
# Import the CLI module under test
# ---------------------------------------------------------------------------

from envsync.cli_rename import add_rename_subparser, cmd_rename  # noqa: E402


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def test_add_rename_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_rename_subparser(sub)
    args = parser.parse_args(["rename", "--old", "A", "--new", "B", "f.env"])
    assert args.command == "rename"


def test_subparser_exposes_old_and_new_keys():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_rename_subparser(sub)
    args = parser.parse_args(["rename", "--old", "FOO", "--new", "BAR", "a.env"])
    assert args.old_key == "FOO"
    assert args.new_key == "BAR"


def test_subparser_dry_run_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_rename_subparser(sub)
    args = parser.parse_args(
        ["rename", "--old", "X", "--new", "Y", "--dry-run", "f.env"]
    )
    assert args.dry_run is True


# ---------------------------------------------------------------------------
# cmd_rename behaviour
# ---------------------------------------------------------------------------

def test_cmd_rename_returns_zero_on_success(env_pair):
    src, tgt = env_pair
    args = _Args(files=[src, tgt], old_key="OLD_KEY", new_key="NEW_KEY")
    rc = cmd_rename(args)
    assert rc == 0


def test_cmd_rename_renames_key_in_file(env_pair):
    src, _ = env_pair
    args = _Args(files=[src], old_key="OLD_KEY", new_key="NEW_KEY")
    cmd_rename(args)
    content = src.read_text()
    assert "NEW_KEY=hello" in content
    assert "OLD_KEY" not in content


def test_cmd_rename_dry_run_does_not_modify_file(env_pair):
    src, _ = env_pair
    original = src.read_text()
    args = _Args(files=[src], old_key="OLD_KEY", new_key="NEW_KEY", dry_run=True)
    cmd_rename(args)
    assert src.read_text() == original


def test_cmd_rename_returns_nonzero_when_key_missing(env_pair, capsys):
    src, _ = env_pair
    args = _Args(files=[src], old_key="NONEXISTENT", new_key="NEW_KEY")
    rc = cmd_rename(args)
    # When no file contained the key the command should signal a problem
    assert rc != 0


def test_cmd_rename_prints_summary(env_pair, capsys):
    src, tgt = env_pair
    args = _Args(files=[src, tgt], old_key="OLD_KEY", new_key="NEW_KEY")
    cmd_rename(args)
    captured = capsys.readouterr()
    assert "OLD_KEY" in captured.out or "NEW_KEY" in captured.out
