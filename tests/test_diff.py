"""Tests for envsync.diff module."""

import textwrap
from pathlib import Path

import pytest

from envsync.diff import ChangeType, diff_env_files
from envsync.parser import parse_env_file


def _write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


@pytest.fixture
def source_env(tmp_path):
    return _write_env(tmp_path, ".env.source", """\
        DB_HOST=localhost
        DB_PORT=5432
        API_KEY=old_key
        LEGACY_VAR=remove_me
    """)


@pytest.fixture
def target_env(tmp_path):
    return _write_env(tmp_path, ".env.target", """\
        DB_HOST=localhost
        DB_PORT=5433
        API_KEY=new_key
        NEW_FEATURE_FLAG=true
    """)


@pytest.fixture
def diff_result(source_env, target_env):
    src = parse_env_file(source_env)
    tgt = parse_env_file(target_env)
    return diff_env_files(src, tgt)


def test_diff_detects_unchanged(diff_result):
    unchanged = diff_result.by_type(ChangeType.UNCHANGED)
    keys = [e.key for e in unchanged]
    assert "DB_HOST" in keys


def test_diff_detects_changed(diff_result):
    changed = diff_result.by_type(ChangeType.CHANGED)
    keys = [e.key for e in changed]
    assert "DB_PORT" in keys
    assert "API_KEY" in keys


def test_diff_detects_removed(diff_result):
    removed = diff_result.by_type(ChangeType.REMOVED)
    keys = [e.key for e in removed]
    assert "LEGACY_VAR" in keys


def test_diff_detects_added(diff_result):
    added = diff_result.by_type(ChangeType.ADDED)
    keys = [e.key for e in added]
    assert "NEW_FEATURE_FLAG" in keys


def test_diff_has_changes(diff_result):
    assert diff_result.has_changes is True


def test_diff_no_changes(tmp_path):
    env_path = _write_env(tmp_path, ".env", "KEY=value\n")
    src = parse_env_file(env_path)
    tgt = parse_env_file(env_path)
    result = diff_env_files(src, tgt)
    assert result.has_changes is False


def test_diff_summary_keys(diff_result):
    summary = diff_result.summary()
    assert set(summary.keys()) == {"added", "removed", "changed", "unchanged"}


def test_diff_changed_entry_values(diff_result):
    changed = {e.key: e for e in diff_result.by_type(ChangeType.CHANGED)}
    assert changed["DB_PORT"].source_value == "5432"
    assert changed["DB_PORT"].target_value == "5433"
