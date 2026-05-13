"""Tests for envsync.sorter."""

from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.sorter import SortOptions, sort_env


def _make_env(*keys: str, path: str = ".env") -> EnvFile:
    entries = [EnvEntry(key=k, value="val", raw=f"{k}=val") for k in keys]
    return EnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# Basic alphabetical sorting
# ---------------------------------------------------------------------------

def test_sort_alphabetically():
    env = _make_env("ZEBRA", "ALPHA", "MANGO")
    result = sort_env(env)
    keys = [e.key for e in result.sorted_env.entries]
    assert keys == ["ALPHA", "MANGO", "ZEBRA"]


def test_sort_reverse():
    env = _make_env("ALPHA", "MANGO", "ZEBRA")
    result = sort_env(env, SortOptions(reverse=True))
    keys = [e.key for e in result.sorted_env.entries]
    assert keys == ["ZEBRA", "MANGO", "ALPHA"]


def test_sort_already_sorted_has_zero_moved():
    env = _make_env("ALPHA", "BETA", "GAMMA")
    result = sort_env(env)
    assert result.moved_count == 0


def test_sort_unsorted_reports_moved_count():
    env = _make_env("ZEBRA", "ALPHA")
    result = sort_env(env)
    assert result.moved_count > 0


# ---------------------------------------------------------------------------
# was_sorted flag
# ---------------------------------------------------------------------------

def test_was_sorted_true_when_order_changed():
    env = _make_env("Z", "A")
    result = sort_env(env)
    assert result.was_sorted is True


def test_was_sorted_false_when_already_ordered():
    env = _make_env("A", "Z")
    result = sort_env(env)
    assert result.was_sorted is False


# ---------------------------------------------------------------------------
# Priority keys
# ---------------------------------------------------------------------------

def test_priority_keys_come_first():
    env = _make_env("ZEBRA", "APP_ENV", "ALPHA", "APP_NAME")
    opts = SortOptions(priority_keys=["APP_ENV", "APP_NAME"])
    result = sort_env(env, opts)
    keys = [e.key for e in result.sorted_env.entries]
    assert keys[0] == "APP_ENV"
    assert keys[1] == "APP_NAME"


def test_non_priority_keys_sorted_after_priority():
    env = _make_env("ZEBRA", "APP_ENV", "ALPHA")
    opts = SortOptions(priority_keys=["APP_ENV"])
    result = sort_env(env, opts)
    keys = [e.key for e in result.sorted_env.entries]
    assert keys == ["APP_ENV", "ALPHA", "ZEBRA"]


# ---------------------------------------------------------------------------
# Case sensitivity
# ---------------------------------------------------------------------------

def test_sort_case_insensitive_by_default():
    env = _make_env("zebra", "Alpha", "MANGO")
    result = sort_env(env)
    keys = [e.key for e in result.sorted_env.entries]
    assert keys == ["Alpha", "MANGO", "zebra"]


# ---------------------------------------------------------------------------
# Comments and blank lines are preserved
# ---------------------------------------------------------------------------

def test_comments_travel_with_following_key():
    comment = EnvEntry(key="", value="", raw="# section", is_comment=True)
    key_b = EnvEntry(key="B", value="1", raw="B=1")
    key_a = EnvEntry(key="A", value="2", raw="A=2")
    env = EnvFile(path=".env", entries=[comment, key_b, key_a])

    result = sort_env(env)
    entries = result.sorted_env.entries
    # comment should precede B which now comes after A
    a_idx = next(i for i, e in enumerate(entries) if getattr(e, "key", "") == "A")
    comment_idx = next(i for i, e in enumerate(entries) if e.is_comment)
    b_idx = next(i for i, e in enumerate(entries) if getattr(e, "key", "") == "B")
    assert comment_idx < b_idx
    assert a_idx < comment_idx


# ---------------------------------------------------------------------------
# Default options
# ---------------------------------------------------------------------------

def test_sort_with_no_options_uses_defaults():
    env = _make_env("C", "A", "B")
    result = sort_env(env)
    keys = [e.key for e in result.sorted_env.entries]
    assert keys == ["A", "B", "C"]
