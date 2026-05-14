"""Tests for envsync.rotator."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.rotator import RotateOptions, rotate_key


def _make_env(path: str, **kwargs: str) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in kwargs.items()]
    return EnvFile(path=path, entries=entries)


@pytest.fixture
def env_a() -> EnvFile:
    return _make_env(".env.a", DB_HOST="localhost", DB_PORT="5432", SECRET_KEY="abc")


@pytest.fixture
env_b() -> EnvFile:
    return _make_env(".env.b", DB_HOST="prod-db", DB_PORT="5432")


def test_rotate_renames_key_in_single_file(env_a):
    updated, result = rotate_key([env_a], {"DB_HOST": "DATABASE_HOST"})
    keys = [e.key for e in updated[0].entries]
    assert "DATABASE_HOST" in keys
    assert "DB_HOST" not in keys


def test_rotate_preserves_value(env_a):
    updated, result = rotate_key([env_a], {"DB_HOST": "DATABASE_HOST"})
    entry = next(e for e in updated[0].entries if e.key == "DATABASE_HOST")
    assert entry.value == "localhost"


def test_rotate_reports_rotated_paths(env_a):
    _, result = rotate_key([env_a], {"DB_HOST": "DATABASE_HOST"})
    assert ".env.a" in result.rotated["DB_HOST"]


def test_rotate_across_multiple_files(env_a, env_b):
    _, result = rotate_key([env_a, env_b], {"DB_HOST": "DATABASE_HOST"})
    assert len(result.rotated["DB_HOST"]) == 2


def test_rotate_skips_missing_key_by_default(env_a):
    _, result = rotate_key([env_a], {"NONEXISTENT": "NEW_KEY"})
    assert result.total_violations == 0 if hasattr(result, 'total_violations') else not result.has_violations
    assert ".env.a" in result.skipped.get("NONEXISTENT", [])


def test_rotate_strict_missing_key_is_violation(env_a):
    opts = RotateOptions(ignore_missing=False)
    _, result = rotate_key([env_a], {"NONEXISTENT": "NEW_KEY"}, opts)
    assert result.has_violations
    assert any("NONEXISTENT" in str(v) for v in result.violations)


def test_rotate_conflict_when_target_key_exists(env_a):
    # DB_PORT already exists; renaming DB_HOST -> DB_PORT should be a violation
    _, result = rotate_key([env_a], {"DB_HOST": "DB_PORT"})
    assert result.has_violations
    assert any("DB_PORT" in str(v) for v in result.violations)


def test_dry_run_does_not_modify_entries(env_a):
    opts = RotateOptions(dry_run=True)
    updated, result = rotate_key([env_a], {"DB_HOST": "DATABASE_HOST"}, opts)
    keys = [e.key for e in updated[0].entries]
    # dry_run returns original file unchanged
    assert "DB_HOST" in keys
    assert result.total_rotated == 1  # still counted


def test_rotate_multiple_keys_at_once(env_a):
    rename_map = {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"}
    updated, result = rotate_key([env_a], rename_map)
    keys = [e.key for e in updated[0].entries]
    assert "DATABASE_HOST" in keys
    assert "DATABASE_PORT" in keys
    assert result.total_rotated == 2
