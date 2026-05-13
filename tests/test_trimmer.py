"""Tests for envsync.trimmer."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.trimmer import TrimOptions, TrimResult, trim_env


def _make_env(*raw_lines: str) -> EnvFile:
    """Build an EnvFile from raw KEY=VALUE strings."""
    env = EnvFile(path="test.env")
    for line in raw_lines:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            env._entries.append(
                EnvEntry(key="", value="", raw=line,
                         is_comment=line.startswith("#"), is_blank=not line)
            )
        else:
            k, _, v = line.partition("=")
            env._entries.append(EnvEntry(key=k, value=v, raw=line))
    return env


@pytest.fixture
def padded_env() -> EnvFile:
    return _make_env(
        "  APP_NAME  =  myapp  ",
        "DEBUG=true",
        "SECRET_KEY=  abc123  ",
        "EMPTY_VAL=   ",
    )


def test_trim_strips_key_whitespace(padded_env: EnvFile) -> None:
    result = trim_env(padded_env)
    keys = [e.key for e in result.entries if not e.is_blank and not e.is_comment]
    assert "APP_NAME" in keys
    assert "  APP_NAME  " not in keys


def test_trim_strips_value_whitespace(padded_env: EnvFile) -> None:
    result = trim_env(padded_env)
    entry = next(e for e in result.entries if e.key == "SECRET_KEY")
    assert entry.value == "abc123"


def test_trim_normalises_empty_value(padded_env: EnvFile) -> None:
    result = trim_env(padded_env)
    entry = next(e for e in result.entries if e.key == "EMPTY_VAL")
    assert entry.value == ""


def test_trim_counts_modified_entries(padded_env: EnvFile) -> None:
    result = trim_env(padded_env)
    # APP_NAME (key+value), SECRET_KEY (value), EMPTY_VAL (value) => 3
    assert result.total_trimmed == 3


def test_trim_unmodified_entry_not_counted() -> None:
    env = _make_env("DEBUG=true", "PORT=8080")
    result = trim_env(env)
    assert result.total_trimmed == 0
    assert result.was_modified is False


def test_trim_was_modified_true_when_changes(padded_env: EnvFile) -> None:
    result = trim_env(padded_env)
    assert result.was_modified is True


def test_trim_preserves_comments() -> None:
    env = _make_env("# this is a comment", "KEY=val")
    result = trim_env(env)
    comments = [e for e in result.entries if e.is_comment]
    assert len(comments) == 1
    assert comments[0].raw == "# this is a comment"


def test_trim_skip_keys_option() -> None:
    env = _make_env("  PADDED  =value")
    opts = TrimOptions(strip_keys=False, strip_values=False)
    result = trim_env(env, opts)
    assert result.total_trimmed == 0


def test_to_env_file_returns_env_file() -> None:
    env = _make_env("KEY=value")
    result = trim_env(env)
    out = result.to_env_file(path="out.env")
    assert out.path == "out.env"
    assert list(out.keys()) == ["KEY"]


def test_trim_all_entries_preserved() -> None:
    env = _make_env("A=1", "B=2", "C=3")
    result = trim_env(env)
    assert len(result.entries) == 3
