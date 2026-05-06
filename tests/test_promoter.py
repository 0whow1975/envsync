"""Tests for envsync.promoter."""
import pytest

from envsync.diff import ChangeType, diff_env_files
from envsync.parser import EnvFile, EnvEntry
from envsync.promoter import PromoteOptions, promote


def _make_env(pairs: dict, path: str = ".env") -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs.items()]
    return EnvFile(path=path, entries=entries)


@pytest.fixture
def source_env():
    return _make_env(
        {"APP_NAME": "myapp", "SECRET_KEY": "new-secret", "NEW_KEY": "hello"},
        path=".env.staging",
    )


@pytest.fixture
def target_env():
    return _make_env(
        {"APP_NAME": "myapp", "SECRET_KEY": "old-secret"},
        path=".env.production",
    )


def test_promote_adds_new_keys(source_env, target_env):
    result = promote(source_env, target_env)
    assert result.promoted_count >= 1
    keys_in_result = {e.key for e in result.sync_result.applied}
    assert "NEW_KEY" in keys_in_result


def test_promote_updates_changed_keys(source_env, target_env):
    result = promote(source_env, target_env)
    keys_in_result = {e.key for e in result.sync_result.applied}
    assert "SECRET_KEY" in keys_in_result


def test_promote_skips_unchanged_keys(source_env, target_env):
    result = promote(source_env, target_env)
    keys_in_result = {e.key for e in result.sync_result.applied}
    assert "APP_NAME" not in keys_in_result


def test_promote_key_filter_restricts_keys(source_env, target_env):
    opts = PromoteOptions(key_filter=lambda k: not k.startswith("SECRET"))
    result = promote(source_env, target_env, opts)
    keys_in_result = {e.key for e in result.sync_result.applied}
    assert "SECRET_KEY" not in keys_in_result
    assert "NEW_KEY" in keys_in_result


def test_promote_skipped_keys_recorded(source_env, target_env):
    opts = PromoteOptions(key_filter=lambda k: k == "NEW_KEY")
    result = promote(source_env, target_env, opts)
    assert "SECRET_KEY" in result.skipped_keys


def test_promote_dry_run_makes_no_changes(source_env, target_env, tmp_path):
    opts = PromoteOptions(dry_run=True)
    result = promote(source_env, target_env, opts)
    # dry_run means no file is written; but promoted_count still reflects intent
    assert result.skipped_count == 0


def test_promote_allow_removals_includes_removed_keys(tmp_path):
    src = _make_env({"A": "1"}, path=str(tmp_path / "src.env"))
    tgt = _make_env({"A": "1", "B": "2"}, path=str(tmp_path / "tgt.env"))
    opts = PromoteOptions(
        include_change_types=[ChangeType.ADDED, ChangeType.CHANGED],
        allow_removals=True,
    )
    result = promote(src, tgt, opts)
    keys_in_result = {e.key for e in result.sync_result.applied}
    assert "B" in keys_in_result
