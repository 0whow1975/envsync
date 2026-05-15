"""Tests for envsync.stripper."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.stripper import StripOptions, strip_env


def _make_env(lines: list[str]) -> EnvFile:
    entries = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("#") or stripped == "":
            entries.append(EnvEntry(key=None, value=None, raw=raw))
        else:
            key, _, value = stripped.partition("=")
            entries.append(EnvEntry(key=key.strip(), value=value.strip(), raw=raw))
    return EnvFile(path=".env", entries=entries)


@pytest.fixture()
def mixed_env() -> EnvFile:
    return _make_env([
        "# This is a comment\n",
        "\n",
        "APP_ENV=production\n",
        "# Another comment\n",
        "DEBUG=false\n",
        "\n",
        "SECRET_KEY=abc123\n",
    ])


def test_strip_removes_comments_by_default(mixed_env):
    result = strip_env(mixed_env)
    keys = [e.key for e in result.stripped.entries if e.key]
    assert "APP_ENV" in keys
    assert "DEBUG" in keys
    comment_lines = [e for e in result.stripped.entries if e.raw.lstrip().startswith("#")]
    assert comment_lines == []


def test_strip_removes_blank_lines_by_default(mixed_env):
    result = strip_env(mixed_env)
    blank_lines = [e for e in result.stripped.entries if e.raw.strip() == ""]
    assert blank_lines == []


def test_strip_counts_removed_comments(mixed_env):
    result = strip_env(mixed_env)
    assert len(result.removed_comments) == 2


def test_strip_counts_removed_blanks(mixed_env):
    result = strip_env(mixed_env)
    assert result.removed_blanks == 2


def test_strip_total_removed(mixed_env):
    result = strip_env(mixed_env)
    assert result.total_removed == 4


def test_strip_was_modified_true(mixed_env):
    result = strip_env(mixed_env)
    assert result.was_modified is True


def test_strip_keep_comments_option(mixed_env):
    opts = StripOptions(remove_comments=False, remove_blank_lines=True)
    result = strip_env(mixed_env, opts)
    comment_lines = [e for e in result.stripped.entries if e.raw.lstrip().startswith("#")]
    assert len(comment_lines) == 2


def test_strip_keep_blanks_option(mixed_env):
    opts = StripOptions(remove_comments=True, remove_blank_lines=False)
    result = strip_env(mixed_env, opts)
    blank_lines = [e for e in result.stripped.entries if e.raw.strip() == ""]
    assert len(blank_lines) == 2


def test_strip_clean_env_not_modified():
    env = _make_env(["FOO=bar\n", "BAZ=qux\n"])
    result = strip_env(env)
    assert result.was_modified is False
    assert result.total_removed == 0


def test_strip_summary_no_changes():
    env = _make_env(["FOO=bar\n"])
    result = strip_env(env)
    assert result.summary() == "No changes."


def test_strip_summary_with_changes(mixed_env):
    result = strip_env(mixed_env)
    summary = result.summary()
    assert "comment" in summary
    assert "blank" in summary


def test_strip_to_env_file_returns_stripped(mixed_env):
    result = strip_env(mixed_env)
    assert result.to_env_file() is result.stripped
