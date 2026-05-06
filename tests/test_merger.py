"""Tests for envsync.merger."""

from __future__ import annotations

import pytest

from envsync.merger import ConflictStrategy, MergeError, merge
from envsync.parser import EnvEntry, EnvFile


def _make_env(path: str, pairs: dict) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", comment=False, source=path)
        for k, v in pairs.items()
    ]
    return EnvFile(path=path, entries=entries)


@pytest.fixture()
def base_env() -> EnvFile:
    return _make_env(".env.base", {"APP_NAME": "myapp", "DEBUG": "false", "PORT": "8000"})


@pytest.fixture()
def override_env() -> EnvFile:
    return _make_env(".env.override", {"DEBUG": "true", "SECRET_KEY": "abc123"})


def test_merge_combines_unique_keys(base_env, override_env):
    result = merge([base_env, override_env])
    keys = {e.key for e in result.merged.entries}
    assert {"APP_NAME", "DEBUG", "PORT", "SECRET_KEY"} == keys


def test_merge_last_strategy_prefers_later_file(base_env, override_env):
    result = merge([base_env, override_env], strategy=ConflictStrategy.LAST)
    entry = next(e for e in result.merged.entries if e.key == "DEBUG")
    assert entry.value == "true"


def test_merge_first_strategy_prefers_earlier_file(base_env, override_env):
    result = merge([base_env, override_env], strategy=ConflictStrategy.FIRST)
    entry = next(e for e in result.merged.entries if e.key == "DEBUG")
    assert entry.value == "false"


def test_merge_error_strategy_raises_on_conflict(base_env, override_env):
    with pytest.raises(MergeError, match="DEBUG"):
        merge([base_env, override_env], strategy=ConflictStrategy.ERROR)


def test_merge_error_strategy_ok_when_no_conflict(base_env):
    extra = _make_env(".env.extra", {"NEW_KEY": "val"})
    result = merge([base_env, extra], strategy=ConflictStrategy.ERROR)
    assert not result.has_conflicts


def test_merge_records_conflicts(base_env, override_env):
    result = merge([base_env, override_env])
    assert result.has_conflicts
    assert any(c.key == "DEBUG" for c in result.conflicts)


def test_merge_no_conflict_when_values_identical():
    a = _make_env("a", {"KEY": "same"})
    b = _make_env("b", {"KEY": "same"})
    result = merge([a, b])
    assert not result.has_conflicts


def test_merge_empty_list_returns_empty_env_file():
    result = merge([])
    assert result.merged.entries == []
    assert not result.has_conflicts


def test_merge_single_file_returns_same_keys():
    env = _make_env(".env", {"A": "1", "B": "2"})
    result = merge([env])
    keys = {e.key for e in result.merged.entries}
    assert keys == {"A", "B"}


def test_merge_sources_recorded(base_env, override_env):
    result = merge([base_env, override_env])
    assert ".env.base" in result.sources
    assert ".env.override" in result.sources
