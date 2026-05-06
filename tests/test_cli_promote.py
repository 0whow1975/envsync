"""Tests for envsync.cli_promote."""
import argparse
from pathlib import Path

import pytest

from envsync.cli_promote import add_promote_subparser, cmd_promote


@pytest.fixture
def env_pair(tmp_path):
    src = tmp_path / ".env.staging"
    tgt = tmp_path / ".env.production"
    src.write_text("APP_NAME=myapp\nSECRET_KEY=new-secret\nNEW_KEY=hello\n")
    tgt.write_text("APP_NAME=myapp\nSECRET_KEY=old-secret\n")
    return src, tgt


class _Args:
    def __init__(self, source, target, dry_run=False, allow_removals=False,
                 only_keys=None, no_mask=False):
        self.source = str(source)
        self.target = str(target)
        self.dry_run = dry_run
        self.allow_removals = allow_removals
        self.only_keys = only_keys
        self.no_mask = no_mask


def test_add_promote_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_promote_subparser(sub)
    args = parser.parse_args(["promote", "src.env", "tgt.env"])
    assert args.source == "src.env"
    assert args.target == "tgt.env"


def test_cmd_promote_returns_zero(env_pair, capsys):
    src, tgt = env_pair
    rc = cmd_promote(_Args(src, tgt))
    assert rc == 0


def test_cmd_promote_reports_new_key(env_pair, capsys):
    src, tgt = env_pair
    cmd_promote(_Args(src, tgt, no_mask=True))
    out = capsys.readouterr().out
    assert "NEW_KEY" in out


def test_cmd_promote_dry_run_prefix(env_pair, capsys):
    src, tgt = env_pair
    cmd_promote(_Args(src, tgt, dry_run=True))
    out = capsys.readouterr().out
    assert "[dry-run]" in out


def test_cmd_promote_only_keys_restricts(env_pair, capsys):
    src, tgt = env_pair
    cmd_promote(_Args(src, tgt, only_keys=["NEW_KEY"], no_mask=True))
    out = capsys.readouterr().out
    assert "NEW_KEY" in out
    assert "SECRET_KEY" not in out


def test_cmd_promote_skipped_keys_in_stderr(env_pair, capsys):
    src, tgt = env_pair
    cmd_promote(_Args(src, tgt, only_keys=["NEW_KEY"]))
    err = capsys.readouterr().err
    assert "SECRET_KEY" in err


def test_cmd_promote_masks_secret_by_default(env_pair, capsys):
    src, tgt = env_pair
    cmd_promote(_Args(src, tgt))
    out = capsys.readouterr().out
    # SECRET_KEY value should be masked, not shown in plain text
    assert "new-secret" not in out
