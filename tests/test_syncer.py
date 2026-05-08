"""Tests for envsync.syncer module."""

import pytest
from pathlib import Path

from envsync.diff import diff_env_files
from envsync.syncer import SyncOptions, SyncResult, sync_env_files


@pytest.fixture
def source_env(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text("APP_NAME=myapp\nDB_HOST=localhost\nNEW_KEY=newval\n")
    return p


@pytest.fixture
def target_env(tmp_path: Path) -> Path:
    p = tmp_path / "target.env"
    p.write_text("APP_NAME=myapp\nDB_HOST=oldhost\nEXTRA_KEY=extra\n")
    return p


@pytest.fixture
def diff_result(source_env, target_env):
    return diff_env_files(source_env, target_env)


def test_sync_adds_missing_keys(diff_result, target_env):
    result = sync_env_files(diff_result, target_env, SyncOptions(add_missing=True))
    assert "NEW_KEY" in result.added
    content = target_env.read_text()
    assert "NEW_KEY=newval" in content


def test_sync_updates_changed_keys(diff_result, target_env):
    result = sync_env_files(diff_result, target_env, SyncOptions(update_changed=True))
    assert "DB_HOST" in result.updated
    content = target_env.read_text()
    assert "DB_HOST=localhost" in content


def test_sync_removes_extra_keys(diff_result, target_env):
    result = sync_env_files(diff_result, target_env, SyncOptions(remove_extra=True))
    assert "EXTRA_KEY" in result.removed
    content = target_env.read_text()
    assert "EXTRA_KEY" not in content


def test_sync_skips_missing_when_disabled(diff_result, target_env):
    result = sync_env_files(diff_result, target_env, SyncOptions(add_missing=False))
    assert "NEW_KEY" in result.skipped
    content = target_env.read_text()
    assert "NEW_KEY" not in content


def test_sync_dry_run_does_not_write(diff_result, target_env):
    original = target_env.read_text()
    result = sync_env_files(
        diff_result,
        target_env,
        SyncOptions(add_missing=True, update_changed=True, dry_run=True),
    )
    assert target_env.read_text() == original
    assert result.total_changes > 0


def test_sync_no_options_makes_no_changes(diff_result, target_env):
    """With all options disabled, no keys should be added, updated, or removed."""
    original = target_env.read_text()
    result = sync_env_files(
        diff_result,
        target_env,
        SyncOptions(add_missing=False, update_changed=False, remove_extra=False),
    )
    assert target_env.read_text() == original
    assert result.total_changes == 0


def test_sync_result_total_changes():
    result = SyncResult()
    result.added = ["A", "B"]
    result.updated = ["C"]
    result.removed = []
    assert result.total_changes == 3


def test_sync_result_repr():
    result = SyncResult()
    result.added = ["X"]
    assert "added=1" in repr(result)
