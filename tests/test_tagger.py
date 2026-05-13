"""Tests for envsync.tagger."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.tagger import TagOptions, tag_entries, filter_by_tag


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_env(*keys: str) -> EnvFile:
    entries = [EnvEntry(key=k, value="val", raw=f"{k}=val") for k in keys]
    return EnvFile(entries=entries, path=".env")


@pytest.fixture()
def env() -> EnvFile:
    return _make_env("DB_HOST", "DB_PASSWORD", "APP_ENV", "SECRET_KEY")


@pytest.fixture()
def tag_map():
    return {
        "DB_HOST": ["database", "infra"],
        "DB_PASSWORD": ["database", "secret"],
        "APP_ENV": ["app"],
        "SECRET_KEY": ["secret"],
    }


# ---------------------------------------------------------------------------
# tag_entries
# ---------------------------------------------------------------------------

def test_tag_entries_all_mapped(env, tag_map):
    result = tag_entries(env, tag_map)
    assert result.total_tagged == 4
    assert result.total_skipped == 0


def test_tag_entries_skips_unmapped_keys(env):
    result = tag_entries(env, {"DB_HOST": ["infra"]})
    assert "DB_HOST" in result.tagged
    assert result.total_skipped == 3


def test_tag_entries_normalises_to_lowercase_by_default(env, tag_map):
    result = tag_entries(env, {"DB_HOST": ["Database", "INFRA"]})
    assert "database" in result.tagged["DB_HOST"]
    assert "infra" in result.tagged["DB_HOST"]


def test_tag_entries_case_sensitive_option(env):
    opts = TagOptions(case_sensitive=True)
    result = tag_entries(env, {"DB_HOST": ["Database"]}, opts)
    assert "Database" in result.tagged["DB_HOST"]
    assert "database" not in result.tagged["DB_HOST"]


def test_tag_entries_allow_multiple_false_keeps_only_first(env):
    opts = TagOptions(allow_multiple=False)
    result = tag_entries(env, {"DB_HOST": ["database", "infra"]}, opts)
    assert len(result.tagged["DB_HOST"]) == 1


def test_tag_entries_multiple_allowed_by_default(env, tag_map):
    result = tag_entries(env, tag_map)
    assert len(result.tagged["DB_HOST"]) == 2


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

def test_filter_by_tag_returns_matching_entries(env, tag_map):
    entries = filter_by_tag(env, tag_map, "secret")
    keys = [e.key for e in entries]
    assert "DB_PASSWORD" in keys
    assert "SECRET_KEY" in keys
    assert "APP_ENV" not in keys


def test_filter_by_tag_returns_empty_for_unknown_tag(env, tag_map):
    entries = filter_by_tag(env, tag_map, "nonexistent")
    assert entries == []


def test_filter_by_tag_case_insensitive_by_default(env, tag_map):
    entries = filter_by_tag(env, tag_map, "DATABASE")
    keys = [e.key for e in entries]
    assert "DB_HOST" in keys


def test_filter_by_tag_ignores_comments():
    comment = EnvEntry(key=None, value=None, raw="# comment", is_comment=True)
    entry = EnvEntry(key="FOO", value="bar", raw="FOO=bar")
    env = EnvFile(entries=[comment, entry], path=".env")
    entries = filter_by_tag(env, {"FOO": ["misc"]}, "misc")
    assert all(not e.is_comment for e in entries)
