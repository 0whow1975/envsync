"""Tests for envsync.grouper."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.grouper import GroupOptions, GroupResult, group_env


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path=".env")


@pytest.fixture()
def mixed_env() -> EnvFile:
    return _make_env(
        ("DB_HOST", "localhost"),
        ("DB_PORT", "5432"),
        ("AWS_ACCESS_KEY", "AKIA..."),
        ("AWS_SECRET", "secret"),
        ("PORT", "8080"),
        ("DEBUG", "true"),
    )


def test_group_by_prefix_creates_correct_groups(mixed_env):
    result = group_env(mixed_env)
    assert "DB" in result.group_names()
    assert "AWS" in result.group_names()


def test_keys_without_prefix_go_to_fallback(mixed_env):
    result = group_env(mixed_env)
    assert "MISC" in result.group_names()
    assert "PORT" in result.keys_in_group("MISC")
    assert "DEBUG" in result.keys_in_group("MISC")


def test_total_keys_matches_input(mixed_env):
    result = group_env(mixed_env)
    assert result.total_keys == len(mixed_env.entries)


def test_total_groups_count(mixed_env):
    result = group_env(mixed_env)
    # DB, AWS, MISC
    assert result.total_groups == 3


def test_custom_fallback_group_name(mixed_env):
    opts = GroupOptions(fallback_group="other")
    result = group_env(mixed_env, opts)
    assert "OTHER" in result.group_names()
    assert "MISC" not in result.group_names()


def test_custom_mapper_overrides_prefix(mixed_env):
    def mapper(entry):
        return "secrets" if "SECRET" in entry.key or "KEY" in entry.key else "general"

    opts = GroupOptions(custom_mapper=mapper)
    result = group_env(mixed_env, opts)
    assert "SECRETS" in result.group_names()
    assert "GENERAL" in result.group_names()


def test_comment_entries_are_skipped():
    comment = EnvEntry(key=None, value=None, raw="# a comment", is_comment=True)
    normal = EnvEntry(key="APP_NAME", value="envsync", raw="APP_NAME=envsync")
    env = EnvFile(entries=[comment, normal], path=".env")
    result = group_env(env)
    assert result.total_keys == 1


def test_group_result_keys_in_group(mixed_env):
    result = group_env(mixed_env)
    db_keys = result.keys_in_group("DB")
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys


def test_empty_env_returns_empty_result():
    env = EnvFile(entries=[], path=".env")
    result = group_env(env)
    assert result.total_groups == 0
    assert result.total_keys == 0
