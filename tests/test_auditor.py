"""Tests for envsync.auditor."""

import json
from pathlib import Path

import pytest

from envsync.diff import DiffEntry, DiffResult, ChangeType
from envsync.auditor import (
    AuditEntry,
    AuditRecord,
    build_audit_record,
    write_audit_log,
)


def _make_diff(*entries: DiffEntry) -> DiffResult:
    return DiffResult(entries=list(entries))


@pytest.fixture()
def simple_diff() -> DiffResult:
    return _make_diff(
        DiffEntry(key="DB_HOST", change_type=ChangeType.ADDED, old_value=None, new_value="localhost"),
        DiffEntry(key="DB_PASS", change_type=ChangeType.CHANGED, old_value="old", new_value="new"),
        DiffEntry(key="APP_ENV", change_type=ChangeType.UNCHANGED, old_value="prod", new_value="prod"),
        DiffEntry(key="SECRET", change_type=ChangeType.REMOVED, old_value="abc", new_value=None),
    )


def test_build_audit_record_excludes_unchanged(simple_diff):
    record = build_audit_record(simple_diff, source=".env.prod", target=".env.staging")
    keys = [e.key for e in record.entries]
    assert "APP_ENV" not in keys


def test_build_audit_record_includes_all_change_types(simple_diff):
    record = build_audit_record(simple_diff, source=".env.prod", target=".env.staging")
    change_types = {e.change_type for e in record.entries}
    assert "added" in change_types
    assert "changed" in change_types
    assert "removed" in change_types


def test_build_audit_record_masks_values_by_default(simple_diff):
    record = build_audit_record(simple_diff, source="a", target="b")
    for entry in record.entries:
        if entry.new_value is not None:
            assert entry.new_value == "***"
        if entry.old_value is not None:
            assert entry.old_value == "***"


def test_build_audit_record_preserves_values_when_unmasked(simple_diff):
    record = build_audit_record(simple_diff, source="a", target="b", mask_values=False)
    added = next(e for e in record.entries if e.key == "DB_HOST")
    assert added.new_value == "localhost"
    assert added.old_value is None


def test_build_audit_record_sets_user(simple_diff):
    record = build_audit_record(simple_diff, source="a", target="b", user="ci-bot")
    assert record.user == "ci-bot"


def test_build_audit_record_has_timestamp(simple_diff):
    record = build_audit_record(simple_diff, source="a", target="b")
    assert record.timestamp  # non-empty
    assert "T" in record.timestamp  # ISO-8601 format


def test_audit_entry_to_dict():
    entry = AuditEntry(key="FOO", change_type="added", old_value=None, new_value="bar")
    d = entry.to_dict()
    assert d == {"key": "FOO", "change_type": "added", "old_value": None, "new_value": "bar"}


def test_write_audit_log_creates_file(tmp_path, simple_diff):
    log_path = tmp_path / "logs" / "audit.log"
    record = build_audit_record(simple_diff, source="a", target="b", user="tester")
    write_audit_log(record, log_path)
    assert log_path.exists()


def test_write_audit_log_appends_json_lines(tmp_path, simple_diff):
    log_path = tmp_path / "audit.log"
    record = build_audit_record(simple_diff, source="a", target="b", user="tester")
    write_audit_log(record, log_path)
    write_audit_log(record, log_path)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        data = json.loads(line)
        assert "timestamp" in data
        assert "entries" in data
