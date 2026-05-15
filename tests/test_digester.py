"""Tests for envsync.digester."""
from __future__ import annotations

import pytest

from envsync.digester import (
    DigestOptions,
    compare_digests,
    digest_env,
)
from envsync.parser import EnvEntry, EnvFile


def _make_env(pairs: dict, path: str = ".env") -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", is_comment=False, is_blank=False)
        for k, v in pairs.items()
    ]
    return EnvFile(path=path, entries=entries)


@pytest.fixture()
def simple_env() -> EnvFile:
    return _make_env({"APP_ENV": "production", "SECRET_KEY": "abc123", "PORT": "8080"})


def test_digest_returns_digest_result(simple_env):
    result = digest_env(simple_env)
    assert result is not None
    assert result.overall_digest != ""


def test_digest_key_count_matches_entries(simple_env):
    result = digest_env(simple_env)
    assert result.key_count == 3


def test_digest_algorithm_recorded(simple_env):
    for algo in ("sha256", "md5", "sha1"):
        result = digest_env(simple_env, DigestOptions(algorithm=algo))
        assert result.algorithm == algo


def test_digest_is_stable_across_calls(simple_env):
    r1 = digest_env(simple_env)
    r2 = digest_env(simple_env)
    assert r1.overall_digest == r2.overall_digest


def test_digest_changes_when_value_changes():
    env_a = _make_env({"KEY": "value_a"})
    env_b = _make_env({"KEY": "value_b"})
    assert digest_env(env_a).overall_digest != digest_env(env_b).overall_digest


def test_digest_keys_only_ignores_value_change():
    opts = DigestOptions(keys_only=True)
    env_a = _make_env({"KEY": "value_a"})
    env_b = _make_env({"KEY": "value_b"})
    assert digest_env(env_a, opts).overall_digest == digest_env(env_b, opts).overall_digest


def test_digest_keys_only_detects_key_change():
    opts = DigestOptions(keys_only=True)
    env_a = _make_env({"KEY_A": "same"})
    env_b = _make_env({"KEY_B": "same"})
    assert digest_env(env_a, opts).overall_digest != digest_env(env_b, opts).overall_digest


def test_matches_returns_true_for_identical_envs(simple_env):
    r1 = digest_env(simple_env)
    r2 = digest_env(simple_env)
    assert r1.matches(r2)


def test_matches_returns_false_for_different_envs():
    env_a = _make_env({"A": "1"})
    env_b = _make_env({"A": "2"})
    assert not digest_env(env_a).matches(digest_env(env_b))


def test_compare_digests_returns_empty_for_equal_envs(simple_env):
    r1 = digest_env(simple_env)
    r2 = digest_env(simple_env)
    assert compare_digests(r1, r2) == {}


def test_compare_digests_reports_changed_key():
    env_a = _make_env({"PORT": "8080", "HOST": "localhost"})
    env_b = _make_env({"PORT": "9090", "HOST": "localhost"})
    diffs = compare_digests(digest_env(env_a), digest_env(env_b))
    assert "PORT" in diffs
    assert "HOST" not in diffs


def test_compare_digests_reports_missing_key():
    env_a = _make_env({"A": "1", "B": "2"})
    env_b = _make_env({"A": "1"})
    diffs = compare_digests(digest_env(env_a), digest_env(env_b))
    assert "B" in diffs


def test_to_dict_contains_expected_fields(simple_env):
    result = digest_env(simple_env)
    d = result.to_dict()
    assert "overall_digest" in d
    assert "key_count" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)
