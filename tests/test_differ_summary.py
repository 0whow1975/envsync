"""Tests for envsync.differ_summary."""
from __future__ import annotations

import pytest

from envsync.diff import ChangeType, DiffEntry, DiffResult
from envsync.parser import EnvEntry, EnvFile
from envsync.differ_summary import DiffSummary, summarize


def _make_entry(key: str, change_type: ChangeType) -> DiffEntry:
    entry = EnvEntry(key=key, value="val", raw=f"{key}=val")
    return DiffEntry(
        key=key,
        change_type=change_type,
        source_value="val" if change_type != ChangeType.ADDED else None,
        target_value="val" if change_type != ChangeType.REMOVED else None,
    )


@pytest.fixture()
def mixed_diff() -> DiffResult:
    source = EnvFile(entries=[], path=None)
    target = EnvFile(entries=[], path=None)
    entries = [
        _make_entry("ADDED_KEY", ChangeType.ADDED),
        _make_entry("REMOVED_KEY", ChangeType.REMOVED),
        _make_entry("CHANGED_KEY", ChangeType.CHANGED),
        _make_entry("SAME_KEY", ChangeType.UNCHANGED),
        _make_entry("SAME_KEY2", ChangeType.UNCHANGED),
    ]
    return DiffResult(entries=entries, source=source, target=target)


def test_summarize_counts_added(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.added == 1


def test_summarize_counts_removed(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.removed == 1


def test_summarize_counts_changed(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.changed == 1


def test_summarize_counts_unchanged(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.unchanged == 2


def test_summarize_total(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.total == 5


def test_total_changes_excludes_unchanged(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.total_changes == 3


def test_is_clean_false_when_differences_exist(mixed_diff):
    summary = summarize(mixed_diff)
    assert summary.is_clean is False


def test_is_clean_true_for_identical_files():
    source = EnvFile(entries=[], path=None)
    target = EnvFile(entries=[], path=None)
    entries = [
        _make_entry("KEY1", ChangeType.UNCHANGED),
        _make_entry("KEY2", ChangeType.UNCHANGED),
    ]
    result = DiffResult(entries=entries, source=source, target=target)
    summary = summarize(result)
    assert summary.is_clean is True


def test_as_dict_contains_all_fields(mixed_diff):
    summary = summarize(mixed_diff)
    d = summary.as_dict()
    for field in ("added", "removed", "changed", "unchanged", "total", "total_changes", "is_clean"):
        assert field in d


def test_str_contains_counts(mixed_diff):
    summary = summarize(mixed_diff)
    text = str(summary)
    assert "added=1" in text
    assert "removed=1" in text
    assert "changed=1" in text


def test_str_reports_not_in_sync(mixed_diff):
    summary = summarize(mixed_diff)
    assert "differ" in str(summary)


def test_str_reports_in_sync():
    source = EnvFile(entries=[], path=None)
    target = EnvFile(entries=[], path=None)
    result = DiffResult(entries=[], source=source, target=target)
    summary = summarize(result)
    assert "in sync" in str(summary)
