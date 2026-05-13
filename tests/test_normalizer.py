"""Tests for envsync.normalizer."""
from __future__ import annotations

import pytest

from envsync.normalizer import NormalizeOptions, normalize_env
from envsync.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, comment="", raw_line=f"{k}={v}") for k, v in pairs]
    return EnvFile(path=".env", entries=entries)


@pytest.fixture
default_env() -> EnvFile:
    return _make_env(
        ("  APP_NAME  ", "  myapp  "),
        ("DEBUG", "true"),
        ("EMPTY_KEY", ""),
    )


def test_strip_whitespace_from_keys_and_values():
    env = _make_env(("  KEY  ", "  value  "))
    result = normalize_env(env, NormalizeOptions(strip_whitespace=True))
    assert result.entries[0].key == "KEY"
    assert result.entries[0].value == "value"
    assert result.total_changed == 1


def test_no_change_when_already_clean():
    env = _make_env(("KEY", "value"))
    result = normalize_env(env, NormalizeOptions(strip_whitespace=True))
    assert result.total_changed == 0
    assert result.was_modified is False


def test_lowercase_keys():
    env = _make_env(("APP_NAME", "test"), ("DEBUG", "1"))
    result = normalize_env(env, NormalizeOptions(lowercase_keys=True))
    keys = [e.key for e in result.entries]
    assert keys == ["app_name", "debug"]
    assert result.total_changed == 2


def test_remove_empty_values():
    env = _make_env(("KEY", "value"), ("EMPTY", ""), ("ALSO_EMPTY", ""))
    result = normalize_env(env, NormalizeOptions(remove_empty=True))
    assert len(result.entries) == 1
    assert result.total_removed == 2
    assert result.was_modified is True


def test_remove_empty_keeps_non_empty():
    env = _make_env(("A", "1"), ("B", "2"))
    result = normalize_env(env, NormalizeOptions(remove_empty=True))
    assert result.total_removed == 0
    assert len(result.entries) == 2


def test_quote_values_wraps_bare_values():
    env = _make_env(("KEY", "hello"))
    result = normalize_env(env, NormalizeOptions(quote_values=True))
    assert result.entries[0].value == '"hello"'
    assert result.total_changed == 1


def test_quote_values_does_not_double_quote():
    env = _make_env(("KEY", '"already"'))
    result = normalize_env(env, NormalizeOptions(quote_values=True))
    assert result.entries[0].value == '"already"'
    assert result.total_changed == 0


def test_to_env_file_returns_env_file():
    env = _make_env(("A", "1"))
    result = normalize_env(env)
    ef = result.to_env_file(path="out.env")
    assert ef.path == "out.env"
    assert len(ef.entries) == 1


def test_combined_options():
    env = _make_env(("  DB_HOST  ", "  localhost  "), ("EMPTY", ""))
    opts = NormalizeOptions(
        strip_whitespace=True,
        lowercase_keys=True,
        remove_empty=True,
    )
    result = normalize_env(env, opts)
    assert len(result.entries) == 1
    assert result.entries[0].key == "db_host"
    assert result.entries[0].value == "localhost"
    assert result.total_removed == 1
