"""Tests for envsync.pinner."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.pinner import PinOptions, PinResult, PinViolation, pin_check


def _make_env(pairs: dict) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", comment=False)
        for k, v in pairs.items()
    ]
    return EnvFile(entries=entries, path="test.env")


@pytest.fixture()
def pinned_env():
    return _make_env({"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"})


@pytest.fixture()
def matching_env():
    return _make_env({"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"})


def test_pin_check_no_drift(pinned_env, matching_env):
    result = pin_check(pinned_env, matching_env)
    assert result.is_pinned
    assert result.violation_count == 0


def test_pin_check_detects_changed_value(pinned_env):
    current = _make_env({"DB_HOST": "prod-db", "API_KEY": "secret", "PORT": "5432"})
    result = pin_check(pinned_env, current)
    assert not result.is_pinned
    assert result.violation_count == 1
    assert result.violations[0].key == "DB_HOST"
    assert result.violations[0].pinned_value == "localhost"
    assert result.violations[0].current_value == "prod-db"


def test_pin_check_detects_missing_key(pinned_env):
    current = _make_env({"DB_HOST": "localhost", "PORT": "5432"})
    result = pin_check(pinned_env, current)
    assert not result.is_pinned
    keys = [v.key for v in result.violations]
    assert "API_KEY" in keys
    missing = next(v for v in result.violations if v.key == "API_KEY")
    assert missing.current_value is None


def test_pin_check_counts_checked_keys(pinned_env, matching_env):
    result = pin_check(pinned_env, matching_env)
    assert result.checked_keys == 3


def test_pin_check_ignores_extra_keys_in_current(pinned_env):
    current = _make_env(
        {"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432", "NEW_KEY": "x"}
    )
    result = pin_check(pinned_env, current)
    assert result.is_pinned


def test_pin_check_respects_ignore_keys(pinned_env):
    current = _make_env({"DB_HOST": "changed", "API_KEY": "secret", "PORT": "5432"})
    options = PinOptions(ignore_keys=["DB_HOST"])
    result = pin_check(pinned_env, current, options=options)
    assert result.is_pinned
    assert result.checked_keys == 2


def test_pin_check_ignore_keys_case_insensitive():
    pinned = _make_env({"DB_HOST": "localhost"})
    current = _make_env({"DB_HOST": "changed"})
    options = PinOptions(ignore_keys=["db_host"], case_sensitive=False)
    result = pin_check(pinned, current, options=options)
    assert result.is_pinned


def test_pin_violation_str_changed():
    v = PinViolation(key="FOO", pinned_value="bar", current_value="baz")
    assert "pinned=" in str(v)
    assert "current=" in str(v)


def test_pin_violation_str_missing():
    v = PinViolation(key="FOO", pinned_value="bar", current_value=None)
    assert "missing" in str(v)


def test_pin_result_as_dict(pinned_env):
    current = _make_env({"DB_HOST": "other", "API_KEY": "secret", "PORT": "5432"})
    result = pin_check(pinned_env, current)
    d = result.as_dict()
    assert d["is_pinned"] is False
    assert d["checked_keys"] == 3
    assert len(d["violations"]) == 1
    assert d["violations"][0]["key"] == "DB_HOST"
