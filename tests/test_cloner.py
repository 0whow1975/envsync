"""Tests for envsync.cloner."""
from __future__ import annotations

import pytest

from envsync.cloner import CloneOptions, clone_env
from envsync.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple[str, str], path: str = ".env") -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(path=path, entries=entries)


@pytest.fixture()
def base_env() -> EnvFile:
    return _make_env(
        ("DB_HOST", "localhost"),
        ("DB_PORT", "5432"),
        ("SECRET_KEY", "s3cr3t"),
        ("APP_ENV", "production"),
    )


def test_clone_copies_all_keys_by_default(base_env: EnvFile) -> None:
    result = clone_env(base_env)
    assert result.total_copied == 4
    assert result.total_skipped == 0


def test_clone_include_filter(base_env: EnvFile) -> None:
    opts = CloneOptions(include_keys=["DB_HOST", "DB_PORT"])
    result = clone_env(base_env, opts)
    keys = [e.key for e in result.env.entries if e.key]
    assert keys == ["DB_HOST", "DB_PORT"]
    assert result.total_copied == 2
    assert result.total_skipped == 2


def test_clone_exclude_filter(base_env: EnvFile) -> None:
    opts = CloneOptions(exclude_keys=["SECRET_KEY"])
    result = clone_env(base_env, opts)
    keys = [e.key for e in result.env.entries if e.key]
    assert "SECRET_KEY" not in keys
    assert result.total_copied == 3
    assert result.total_skipped == 1


def test_clone_key_transform(base_env: EnvFile) -> None:
    opts = CloneOptions(key_transform=str.lower)
    result = clone_env(base_env, opts)
    keys = [e.key for e in result.env.entries if e.key]
    assert all(k == k.lower() for k in keys)


def test_clone_value_transform(base_env: EnvFile) -> None:
    opts = CloneOptions(value_transform=lambda _k, v: v.upper())
    result = clone_env(base_env, opts)
    values = [e.value for e in result.env.entries if e.key]
    assert all(v == v.upper() for v in values)


def test_clone_strip_comments_removes_structural_lines() -> None:
    comment_entry = EnvEntry(key=None, value="", comment="# a comment", raw="# a comment")
    env = EnvFile(
        path=".env",
        entries=[comment_entry, EnvEntry(key="FOO", value="bar", comment=None, raw="FOO=bar")],
    )
    opts = CloneOptions(strip_comments=True)
    result = clone_env(env, opts)
    assert all(e.key is not None for e in result.env.entries)


def test_clone_preserves_comment_lines_by_default() -> None:
    comment_entry = EnvEntry(key=None, value="", comment="# header", raw="# header")
    env = EnvFile(
        path=".env",
        entries=[comment_entry, EnvEntry(key="X", value="1", comment=None, raw="X=1")],
    )
    result = clone_env(env)
    assert any(e.key is None for e in result.env.entries)


def test_was_filtered_false_when_nothing_skipped(base_env: EnvFile) -> None:
    result = clone_env(base_env)
    assert result.was_filtered is False


def test_was_filtered_true_when_keys_excluded(base_env: EnvFile) -> None:
    opts = CloneOptions(exclude_keys=["APP_ENV"])
    result = clone_env(base_env, opts)
    assert result.was_filtered is True


def test_clone_preserves_source_path(base_env: EnvFile) -> None:
    result = clone_env(base_env)
    assert result.env.path == base_env.path
