"""Tests for envsync.cli_freeze."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsync.cli_freeze import add_freeze_subparser, cmd_freeze


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return _write(
        tmp_path / ".env",
        "DB_HOST=localhost\nSECRET_KEY=abc123\nPORT=5432\n",
    )


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_add_freeze_subparser_registers_command() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_freeze_subparser(sub)
    choices = list(sub.choices.keys())
    assert "freeze" in choices


def test_cmd_take_creates_freeze_file(env_file: Path, tmp_path: Path) -> None:
    freeze_path = tmp_path / "out.freeze.json"
    args = _Args(freeze_cmd="take", env_file=str(env_file), output=str(freeze_path))
    rc = cmd_freeze(args)
    assert rc == 0
    assert freeze_path.exists()


def test_cmd_take_freeze_file_is_valid_json(env_file: Path, tmp_path: Path) -> None:
    freeze_path = tmp_path / "out.freeze.json"
    args = _Args(freeze_cmd="take", env_file=str(env_file), output=str(freeze_path))
    cmd_freeze(args)
    data = json.loads(freeze_path.read_text())
    assert "checksum" in data
    assert "keys" in data


def test_cmd_check_returns_zero_when_no_drift(env_file: Path, tmp_path: Path) -> None:
    freeze_path = tmp_path / "out.freeze.json"
    take_args = _Args(freeze_cmd="take", env_file=str(env_file), output=str(freeze_path))
    cmd_freeze(take_args)
    check_args = _Args(freeze_cmd="check", freeze_file=str(freeze_path), env_file=str(env_file))
    rc = cmd_freeze(check_args)
    assert rc == 0


def test_cmd_check_returns_nonzero_on_drift(env_file: Path, tmp_path: Path) -> None:
    freeze_path = tmp_path / "out.freeze.json"
    take_args = _Args(freeze_cmd="take", env_file=str(env_file), output=str(freeze_path))
    cmd_freeze(take_args)

    modified = tmp_path / ".env.modified"
    _write(modified, "DB_HOST=changed\nSECRET_KEY=abc123\nPORT=5432\n")
    check_args = _Args(freeze_cmd="check", freeze_file=str(freeze_path), env_file=str(modified))
    rc = cmd_freeze(check_args)
    assert rc == 1
