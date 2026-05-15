"""Tests for envsync.sanitizer."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.sanitizer import SanitizeOptions, sanitize_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=None, is_comment=False, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(path="test.env", entries=entries)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def padded_env() -> EnvFile:
    return _make_env(
        ("APP_NAME", "  myapp  "),
        ("DEBUG", "true"),
        ("SECRET", "  s3cr3t  "),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_strip_whitespace_sanitizes_padded_values(padded_env):
    result = sanitize_env(padded_env)
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["APP_NAME"] == "myapp"
    assert values["SECRET"] == "s3cr3t"


def test_unmodified_values_not_in_sanitized_keys(padded_env):
    result = sanitize_env(padded_env)
    assert "DEBUG" not in result.sanitized_keys


def test_was_modified_true_when_changes_made(padded_env):
    result = sanitize_env(padded_env)
    assert result.was_modified is True


def test_was_modified_false_when_no_changes():
    env = _make_env(("KEY", "value"), ("OTHER", "123"))
    result = sanitize_env(env)
    assert result.was_modified is False


def test_total_sanitized_counts_modified_keys(padded_env):
    result = sanitize_env(padded_env)
    assert result.total_sanitized == 2


def test_remove_null_bytes():
    env = _make_env(("KEY", "val\x00ue"))
    result = sanitize_env(env, SanitizeOptions(remove_null_bytes=True))
    assert result.entries[0].value == "value"
    assert "KEY" in result.sanitized_keys


def test_collapse_newlines():
    env = _make_env(("MULTILINE", "line1\nline2\r\nline3"))
    result = sanitize_env(env, SanitizeOptions(collapse_newlines=True))
    assert result.entries[0].value == "line1 line2 line3"


def test_max_value_length_truncates():
    env = _make_env(("LONG", "a" * 50))
    opts = SanitizeOptions(max_value_length=10)
    result = sanitize_env(env, opts)
    assert len(result.entries[0].value) == 10
    assert "LONG" in result.sanitized_keys


def test_max_value_length_none_does_not_truncate():
    env = _make_env(("LONG", "a" * 200))
    opts = SanitizeOptions(max_value_length=None)
    result = sanitize_env(env, opts)
    assert len(result.entries[0].value) == 200


def test_redact_patterns_replaces_matches():
    env = _make_env(("TOKEN", "Bearer abc123xyz"))
    opts = SanitizeOptions(redact_patterns=[r"abc\d+xyz"])
    result = sanitize_env(env, opts)
    assert "***" in result.entries[0].value
    assert "abc123xyz" not in result.entries[0].value


def test_comment_entries_are_passed_through_unchanged():
    entry = EnvEntry(key=None, value=None, comment="# a comment", is_comment=True, raw="# a comment")
    env = EnvFile(path="test.env", entries=[entry])
    result = sanitize_env(env)
    assert result.entries[0].is_comment is True
    assert result.total_sanitized == 0


def test_to_env_file_returns_env_file_with_cleaned_entries(padded_env):
    result = sanitize_env(padded_env)
    env_file = result.to_env_file()
    assert isinstance(env_file, EnvFile)
    values = {e.key: e.value for e in env_file.entries if e.key}
    assert values["APP_NAME"] == "myapp"
