"""Tests for envsync.profiler."""
from __future__ import annotations

import pytest

from envsync.parser import EnvFile, EnvEntry
from envsync.masker import MaskConfig
from envsync.profiler import profile_env, ProfileResult


def _make_env(raw: str, path: str = ".env") -> EnvFile:
    """Build an EnvFile from a multiline string of KEY=VALUE pairs."""
    entries: list[EnvEntry] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            entries.append(EnvEntry(key="", value="", is_blank=True, is_comment=False, raw=line))
        elif stripped.startswith("#"):
            entries.append(EnvEntry(key="", value="", is_blank=False, is_comment=True, raw=line))
        else:
            key, _, value = stripped.partition("=")
            entries.append(EnvEntry(key=key.strip(), value=value.strip(), is_blank=False, is_comment=False, raw=line))
    return EnvFile(path=path, entries=entries)


@pytest.fixture()
def env() -> EnvFile:
    return _make_env(
        "# app config\n"
        "APP_NAME=myapp\n"
        "\n"
        "SECRET_KEY=supersecret\n"
        "DATABASE_URL=postgres://localhost/db\n"
        "DEBUG=true\n"
        "EMPTY_VAR=\n"
    )


def test_profile_returns_profile_result(env: EnvFile) -> None:
    result = profile_env(env)
    assert isinstance(result, ProfileResult)


def test_profile_total_keys(env: EnvFile) -> None:
    result = profile_env(env)
    assert result.total_keys == 5


def test_profile_counts_comment_lines(env: EnvFile) -> None:
    result = profile_env(env)
    assert result.comment_lines == 1


def test_profile_counts_blank_lines(env: EnvFile) -> None:
    result = profile_env(env)
    assert result.blank_lines == 1


def test_profile_detects_secret_keys(env: EnvFile) -> None:
    result = profile_env(env)
    assert "SECRET_KEY" in result.secret_keys
    assert "DATABASE_URL" in result.secret_keys


def test_profile_detects_plain_keys(env: EnvFile) -> None:
    result = profile_env(env)
    assert "APP_NAME" in result.plain_keys
    assert "DEBUG" in result.plain_keys


def test_profile_detects_empty_keys(env: EnvFile) -> None:
    result = profile_env(env)
    assert "EMPTY_VAR" in result.empty_keys


def test_profile_secret_count_matches_list(env: EnvFile) -> None:
    result = profile_env(env)
    assert result.secret_count == len(result.secret_keys)


def test_profile_plain_count_matches_list(env: EnvFile) -> None:
    result = profile_env(env)
    assert result.plain_count == len(result.plain_keys)


def test_profile_as_dict_has_expected_keys(env: EnvFile) -> None:
    d = profile_env(env).as_dict()
    for key in ("path", "total_keys", "secret_count", "plain_count", "empty_count",
                "comment_lines", "blank_lines", "secret_keys", "plain_keys", "empty_keys"):
        assert key in d


def test_profile_str_contains_path(env: EnvFile) -> None:
    result = profile_env(env)
    assert ".env" in str(result)


def test_profile_case_sensitive_mask_config(env: EnvFile) -> None:
    config = MaskConfig(case_sensitive=True)
    result = profile_env(env, mask_config=config)
    # With case-sensitive matching, SECRET_KEY should still be detected (uppercase pattern)
    assert "SECRET_KEY" in result.secret_keys
