"""Integration tests: merge via parse_env_file -> merger -> output lines."""

from __future__ import annotations

from pathlib import Path

import pytest

from envsync.merger import ConflictStrategy, merge
from envsync.parser import parse_env_file


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    (tmp_path / "base.env").write_text(
        "# base config\nAPP_ENV=production\nDB_HOST=localhost\nDB_PORT=5432\n"
    )
    (tmp_path / "local.env").write_text(
        "DB_HOST=127.0.0.1\nDEBUG=true\n"
    )
    (tmp_path / "secrets.env").write_text(
        "SECRET_KEY=supersecret\nDB_PASSWORD=hunter2\n"
    )
    return tmp_path


def test_integration_all_keys_present(env_dir):
    files = [parse_env_file(str(env_dir / f)) for f in ("base.env", "local.env", "secrets.env")]
    result = merge(files)
    keys = {e.key for e in result.merged.entries if e.key}
    assert {"APP_ENV", "DB_HOST", "DB_PORT", "DEBUG", "SECRET_KEY", "DB_PASSWORD"}.issubset(keys)


def test_integration_last_wins_for_db_host(env_dir):
    files = [parse_env_file(str(env_dir / f)) for f in ("base.env", "local.env")]
    result = merge(files, strategy=ConflictStrategy.LAST)
    entry = next(e for e in result.merged.entries if e.key == "DB_HOST")
    assert entry.value == "127.0.0.1"


def test_integration_first_wins_for_db_host(env_dir):
    files = [parse_env_file(str(env_dir / f)) for f in ("base.env", "local.env")]
    result = merge(files, strategy=ConflictStrategy.FIRST)
    entry = next(e for e in result.merged.entries if e.key == "DB_HOST")
    assert entry.value == "localhost"


def test_integration_conflict_recorded(env_dir):
    files = [parse_env_file(str(env_dir / f)) for f in ("base.env", "local.env")]
    result = merge(files)
    conflict_keys = {c.key for c in result.conflicts}
    assert "DB_HOST" in conflict_keys


def test_integration_no_conflict_for_unique_keys(env_dir):
    files = [parse_env_file(str(env_dir / f)) for f in ("base.env", "secrets.env")]
    result = merge(files)
    assert not result.has_conflicts
