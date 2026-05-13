"""Tests for envsync.cli_compare."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envsync.cli_compare import add_compare_subparser, cmd_compare


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


@pytest.fixture()
def env_pair(tmp_path):
    src = _write(tmp_path, "prod.env", "APP=prod\nDB_HOST=prod-db\nSECRET=abc\n")
    tgt = _write(tmp_path, "staging.env", "APP=staging\nDB_HOST=staging-db\nDEBUG=true\n")
    return src, tgt


class _Args:
    def __init__(self, envfiles, baseline=None, summary=False, color=True):
        self.envfiles = [str(f) for f in envfiles]
        self.baseline = baseline
        self.summary = summary
        self.color = color


def test_add_compare_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_compare_subparser(subs)
    ns = parser.parse_args(["compare", "a.env", "b.env"])
    assert ns.func is cmd_compare


def test_cmd_compare_returns_zero_for_valid_pair(env_pair):
    src, tgt = env_pair
    args = _Args([src, tgt])
    assert cmd_compare(args) == 0


def test_cmd_compare_returns_one_for_single_file(env_pair, capsys):
    src, _ = env_pair
    args = _Args([src])
    rc = cmd_compare(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "at least two" in captured.err


def test_cmd_compare_returns_one_for_missing_file(env_pair):
    src, _ = env_pair
    args = _Args([src, "/nonexistent/path.env"])
    assert cmd_compare(args) == 1


def test_cmd_compare_summary_flag_produces_output(env_pair, capsys):
    src, tgt = env_pair
    args = _Args([src, tgt], summary=True)
    cmd_compare(args)
    captured = capsys.readouterr()
    assert "prod" in captured.out
    assert "staging" in captured.out


def test_cmd_compare_reports_missing_keys(env_pair, capsys):
    src, tgt = env_pair
    args = _Args([src, tgt])
    cmd_compare(args)
    captured = capsys.readouterr()
    # SECRET is only in prod; DEBUG only in staging
    assert "SECRET" in captured.out or "DEBUG" in captured.out


def test_cmd_compare_baseline_option(env_pair, tmp_path, capsys):
    src, tgt = env_pair
    dev = _write(tmp_path, "dev.env", "APP=dev\nDEBUG=true\nLOCAL=yes\n")
    args = _Args([src, tgt, dev], baseline="prod")
    rc = cmd_compare(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "prod" in captured.out
