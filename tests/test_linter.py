"""Tests for envsync.linter."""
from __future__ import annotations

import pytest

from envsync.linter import LintSeverity, lint_env_file
from envsync.parser import EnvEntry, EnvFile


def _make_env(*entries: tuple[str, str, int]) -> EnvFile:
    """Build an EnvFile from (key, value, line) tuples."""
    env_entries = []
    for key, value, lineno in entries:
        e = EnvEntry(key=key, value=value, raw=f"{key}={value}")
        e.line = lineno
        env_entries.append(e)
    return EnvFile(path="test.env", entries=env_entries)


@pytest.fixture
def clean_env() -> EnvFile:
    return _make_env(("APP_NAME", "myapp", 1), ("PORT", "8080", 2))


def test_clean_env_has_no_issues(clean_env):
    result = lint_env_file(clean_env)
    assert result.is_clean


def test_is_clean_false_when_issues_exist():
    env = _make_env(("app_name", "myapp", 1))
    result = lint_env_file(env)
    assert not result.is_clean


def test_duplicate_key_is_error():
    env = _make_env(("APP_NAME", "foo", 1), ("APP_NAME", "bar", 2))
    result = lint_env_file(env)
    errors = result.errors
    assert len(errors) == 1
    assert errors[0].key == "APP_NAME"
    assert errors[0].severity == LintSeverity.ERROR
    assert "duplicate" in errors[0].message


def test_empty_value_is_warning():
    env = _make_env(("SECRET_KEY", "", 1))
    result = lint_env_file(env)
    warnings = result.warnings
    assert any(w.key == "SECRET_KEY" and "empty" in w.message for w in warnings)


def test_lowercase_key_is_warning():
    env = _make_env(("app_name", "myapp", 1))
    result = lint_env_file(env)
    warnings = result.warnings
    assert any(w.key == "app_name" and "UPPER_SNAKE_CASE" in w.message for w in warnings)


def test_mixed_case_key_is_warning():
    env = _make_env(("AppName", "myapp", 1))
    result = lint_env_file(env)
    assert any("UPPER_SNAKE_CASE" in w.message for w in result.warnings)


def test_str_output_clean(clean_env):
    result = lint_env_file(clean_env)
    assert "No lint issues" in str(result)


def test_str_output_with_issues():
    env = _make_env(("bad_key", "", 3))
    result = lint_env_file(env)
    output = str(result)
    assert "WARNING" in output
    assert "bad_key" in output


def test_errors_and_warnings_are_separated():
    env = _make_env(
        ("GOOD_KEY", "value", 1),
        ("GOOD_KEY", "dupe", 2),   # error: duplicate
        ("bad_key", "x", 3),       # warning: lowercase
    )
    result = lint_env_file(env)
    assert len(result.errors) == 1
    assert any(w.severity == LintSeverity.WARNING for w in result.warnings)
