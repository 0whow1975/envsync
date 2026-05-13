"""Tests for envsync.comparator."""
from __future__ import annotations

import pytest

from envsync.parser import EnvFile, EnvEntry
from envsync.diff import ChangeType
from envsync.comparator import CompareOptions, compare_envs


def _make_env(pairs: dict) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs.items()]
    return EnvFile(entries=entries)


@pytest.fixture()
def prod_env():
    return _make_env({"APP_ENV": "production", "DB_HOST": "prod-db", "SECRET": "abc"})


@pytest.fixture()
def staging_env():
    return _make_env({"APP_ENV": "staging", "DB_HOST": "staging-db", "DEBUG": "true"})


@pytest.fixture()
def dev_env():
    return _make_env({"APP_ENV": "development", "DEBUG": "true", "LOCAL": "yes"})


def test_compare_returns_one_pair_for_two_envs(prod_env, staging_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env})
    assert len(result.pairs) == 1
    assert result.pairs[0].label_a == "prod"
    assert result.pairs[0].label_b == "staging"


def test_compare_three_envs_produces_three_pairs(prod_env, staging_env, dev_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env, "dev": dev_env})
    assert len(result.pairs) == 3


def test_baseline_option_limits_pairs_to_baseline_vs_others(prod_env, staging_env, dev_env):
    opts = CompareOptions(baseline="prod")
    result = compare_envs({"prod": prod_env, "staging": staging_env, "dev": dev_env}, opts)
    assert all(p.label_a == "prod" for p in result.pairs)
    assert len(result.pairs) == 2


def test_all_keys_combines_all_envs(prod_env, staging_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env})
    assert "SECRET" in result.all_keys
    assert "DEBUG" in result.all_keys


def test_keys_missing_from_identifies_absent_keys(prod_env, staging_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env})
    missing_from_prod = result.keys_missing_from("prod")
    assert "DEBUG" in missing_from_prod
    assert "SECRET" not in missing_from_prod


def test_keys_unique_to_returns_exclusive_keys(prod_env, staging_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env})
    unique_prod = result.keys_unique_to("prod")
    assert "SECRET" in unique_prod
    assert "APP_ENV" not in unique_prod


def test_diff_detects_changed_values(prod_env, staging_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env})
    pair = result.pairs[0]
    changed_keys = [
        e.key for e in pair.diff.entries if e.change == ChangeType.CHANGED
    ]
    assert "APP_ENV" in changed_keys
    assert "DB_HOST" in changed_keys


def test_presence_map_populated(prod_env, staging_env):
    result = compare_envs({"prod": prod_env, "staging": staging_env})
    assert "prod" in result.presence
    assert "staging" in result.presence
    assert "SECRET" in result.presence["prod"]
    assert "DEBUG" in result.presence["staging"]
