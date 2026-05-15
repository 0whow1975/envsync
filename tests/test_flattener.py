"""Tests for envsync.flattener."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.flattener import FlattenOptions, flatten_env


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path=None)


@pytest.fixture()
def mixed_env() -> EnvFile:
    return _make_env(
        ("DB__HOST", "localhost"),
        ("DB__PORT", "5432"),
        ("DB__NAME", "mydb"),
        ("REDIS__HOST", "127.0.0.1"),
        ("REDIS__PORT", "6379"),
        ("APP_NAME", "envsync"),
        ("DEBUG", "true"),
    )


def test_flatten_creates_correct_groups(mixed_env):
    result = flatten_env(mixed_env)
    assert "DB" in result.groups
    assert "REDIS" in result.groups


def test_flatten_group_key_count(mixed_env):
    result = flatten_env(mixed_env)
    assert result.groups["DB"].size == 3
    assert result.groups["REDIS"].size == 2


def test_flatten_ungrouped_contains_plain_keys(mixed_env):
    result = flatten_env(mixed_env)
    ungrouped_keys = [e.key for e in result.ungrouped]
    assert "APP_NAME" in ungrouped_keys
    assert "DEBUG" in ungrouped_keys


def test_flatten_total_keys_matches_input(mixed_env):
    result = flatten_env(mixed_env)
    assert result.total_keys == len(mixed_env.entries)


def test_flatten_total_groups(mixed_env):
    result = flatten_env(mixed_env)
    assert result.total_groups == 2


def test_flatten_no_separator_all_ungrouped():
    env = _make_env(("FOO", "1"), ("BAR", "2"))
    result = flatten_env(env)
    assert result.total_groups == 0
    assert len(result.ungrouped) == 2


def test_flatten_custom_separator():
    env = _make_env(("DB.HOST", "localhost"), ("DB.PORT", "5432"), ("PLAIN", "x"))
    opts = FlattenOptions(separator=".")
    result = flatten_env(env, opts)
    assert "DB" in result.groups
    assert result.groups["DB"].size == 2


def test_flatten_prefix_filter_excludes_non_matching(mixed_env):
    opts = FlattenOptions(prefix_filter="DB")
    result = flatten_env(mixed_env, opts)
    assert "REDIS" not in result.groups
    assert "DB" in result.groups


def test_flatten_prefix_filter_moves_excluded_to_ungrouped(mixed_env):
    opts = FlattenOptions(prefix_filter="DB")
    result = flatten_env(mixed_env, opts)
    ungrouped_keys = [e.key for e in result.ungrouped]
    assert "REDIS__HOST" in ungrouped_keys
    assert "REDIS__PORT" in ungrouped_keys


def test_to_env_file_contains_all_entries(mixed_env):
    result = flatten_env(mixed_env)
    flat = result.to_env_file()
    assert len(flat.entries) == len(mixed_env.entries)


def test_to_env_file_groups_appear_before_ungrouped(mixed_env):
    result = flatten_env(mixed_env)
    flat = result.to_env_file()
    keys = [e.key for e in flat.entries]
    last_grouped = max(i for i, k in enumerate(keys) if k and "__" in k)
    first_ungrouped = min(i for i, k in enumerate(keys) if k and "__" not in k)
    assert last_grouped < first_ungrouped
