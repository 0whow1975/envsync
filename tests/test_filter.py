"""Tests for envsync.pinecone_filter."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.pinecone_filter import FilterOptions, FilterResult, filter_env


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(path=".env", entries=entries)


@pytest.fixture
def mixed_env() -> EnvFile:
    return _make_env(
        ("DB_HOST", "localhost"),
        ("DB_PASSWORD", "secret"),
        ("APP_DEBUG", "true"),
        ("APP_PORT", "8080"),
        ("LOG_LEVEL", "info"),
    )


def test_no_criteria_matches_all(mixed_env):
    result = filter_env(mixed_env, FilterOptions())
    assert result.total_matched == 5
    assert result.total_excluded == 0


def test_prefix_filter_returns_matching_keys(mixed_env):
    result = filter_env(mixed_env, FilterOptions(prefixes=["DB_"]))
    keys = [e.key for e in result.matched]
    assert "DB_HOST" in keys
    assert "DB_PASSWORD" in keys
    assert "APP_DEBUG" not in keys


def test_prefix_filter_is_case_insensitive_by_default(mixed_env):
    result = filter_env(mixed_env, FilterOptions(prefixes=["db_"]))
    assert result.total_matched == 2


def test_prefix_filter_case_sensitive(mixed_env):
    result = filter_env(mixed_env, FilterOptions(prefixes=["db_"], case_sensitive=True))
    assert result.total_matched == 0


def test_pattern_filter_regex(mixed_env):
    result = filter_env(mixed_env, FilterOptions(patterns=[r".*_PORT$"]))
    keys = [e.key for e in result.matched]
    assert keys == ["APP_PORT"]


def test_multiple_prefixes(mixed_env):
    result = filter_env(mixed_env, FilterOptions(prefixes=["DB_", "LOG_"]))
    keys = {e.key for e in result.matched}
    assert keys == {"DB_HOST", "DB_PASSWORD", "LOG_LEVEL"}


def test_invert_excludes_matched(mixed_env):
    result = filter_env(mixed_env, FilterOptions(prefixes=["DB_"], invert=True))
    keys = [e.key for e in result.matched]
    assert "DB_HOST" not in keys
    assert "APP_DEBUG" in keys


def test_total_matched_and_excluded_sum_to_entry_count(mixed_env):
    result = filter_env(mixed_env, FilterOptions(prefixes=["APP_"]))
    assert result.total_matched + result.total_excluded == len(mixed_env.entries)


def test_comment_entries_are_excluded():
    comment = EnvEntry(key="", value="", raw="# this is a comment", is_comment=True)
    env = EnvFile(path=".env", entries=[comment])
    result = filter_env(env, FilterOptions())
    assert result.total_matched == 0
    assert result.total_excluded == 1


def test_filter_result_type():
    env = _make_env(("KEY", "val"))
    result = filter_env(env)
    assert isinstance(result, FilterResult)
