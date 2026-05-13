"""Tests for envsync.deduplicator."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.deduplicator import (
    DeduplicateOptions,
    DeduplicateResult,
    deduplicate,
)


def _make_env(*pairs: tuple[str | None, str | None]) -> EnvFile:
    """Build an EnvFile from (key, value) pairs; key=None means a comment/blank."""
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}" if k else (v or ""))
        for k, v in pairs
    ]
    return EnvFile(path="test.env", entries=entries)


@pytest.fixture()
def dup_env() -> EnvFile:
    return _make_env(
        ("FOO", "first"),
        ("BAR", "bar"),
        ("FOO", "second"),
        ("BAZ", "baz"),
        ("FOO", "third"),
    )


def test_no_duplicates_returns_all_entries():
    env = _make_env(("A", "1"), ("B", "2"), ("C", "3"))
    result = deduplicate(env)
    assert len(result.entries) == 3
    assert not result.has_duplicates


def test_detects_duplicate_keys(dup_env):
    result = deduplicate(dup_env)
    assert "FOO" in result.duplicates
    assert len(result.duplicates["FOO"]) == 3


def test_keep_last_is_default(dup_env):
    result = deduplicate(dup_env)
    foo_entries = [e for e in result.entries if e.key == "FOO"]
    assert len(foo_entries) == 1
    assert foo_entries[0].value == "third"


def test_keep_first(dup_env):
    opts = DeduplicateOptions(keep="first")
    result = deduplicate(dup_env, opts)
    foo_entries = [e for e in result.entries if e.key == "FOO"]
    assert len(foo_entries) == 1
    assert foo_entries[0].value == "first"


def test_total_removed(dup_env):
    result = deduplicate(dup_env)
    # FOO appears 3 times → 2 removed
    assert result.total_removed == 2


def test_non_duplicate_keys_preserved(dup_env):
    result = deduplicate(dup_env)
    keys = [e.key for e in result.entries if e.key]
    assert "BAR" in keys
    assert "BAZ" in keys


def test_report_only_does_not_remove_entries(dup_env):
    opts = DeduplicateOptions(report_only=True)
    result = deduplicate(dup_env, opts)
    assert len(result.entries) == len(dup_env.entries)
    assert result.has_duplicates


def test_to_env_file_preserves_path(dup_env):
    result = deduplicate(dup_env)
    new_env = result.to_env_file(dup_env)
    assert new_env.path == dup_env.path


def test_comments_and_blanks_ignored():
    env = _make_env(
        (None, "# comment"),
        ("KEY", "val"),
        (None, ""),
        ("KEY", "val2"),
    )
    result = deduplicate(env)
    # blank + comment entries kept; only one KEY entry remains
    assert sum(1 for e in result.entries if e.key == "KEY") == 1
    assert sum(1 for e in result.entries if e.key is None) == 2
