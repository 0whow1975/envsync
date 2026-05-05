"""Tests for envsync.reporter module."""
import pytest
from envsync.diff import DiffResult, DiffEntry, ChangeType
from envsync.masker import SecretMasker, MaskConfig
from envsync.reporter import ReportOptions, Report, generate_report, _build_summary


@pytest.fixture
def simple_diff():
    entries = [
        DiffEntry(key="APP_NAME", change=ChangeType.UNCHANGED, source_value="myapp", target_value="myapp"),
        DiffEntry(key="DB_URL", change=ChangeType.ADDED, source_value="postgres://localhost", target_value=None),
        DiffEntry(key="OLD_KEY", change=ChangeType.REMOVED, source_value=None, target_value="old"),
        DiffEntry(key="API_KEY", change=ChangeType.CHANGED, source_value="new_secret", target_value="old_secret"),
    ]
    return DiffResult(entries=entries)


@pytest.fixture
def masker():
    return SecretMasker(MaskConfig())


def test_report_has_title(simple_diff, masker):
    report = generate_report(simple_diff, "source.env", "target.env", masker=masker)
    assert "source.env" in report.title
    assert "target.env" in report.title


def test_report_summary_counts(simple_diff):
    summary = _build_summary(simple_diff)
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "~1 changed" in summary


def test_summary_only_has_no_body(simple_diff, masker):
    opts = ReportOptions(summary_only=True)
    report = generate_report(simple_diff, "a.env", "b.env", masker=masker, options=opts)
    assert report.body == ""
    assert "Summary" in report.summary


def test_report_str_combines_sections(simple_diff, masker):
    report = generate_report(simple_diff, "a.env", "b.env", masker=masker)
    full = str(report)
    assert report.title in full
    assert report.summary in full


def test_no_changes_summary():
    entries = [
        DiffEntry(key="X", change=ChangeType.UNCHANGED, source_value="1", target_value="1"),
    ]
    diff = DiffResult(entries=entries)
    summary = _build_summary(diff)
    assert "No differences" in summary or "unchanged" in summary


def test_mask_secrets_in_report(simple_diff, masker):
    opts = ReportOptions(mask_secrets=True, show_unchanged=True, use_color=False)
    report = generate_report(simple_diff, "a.env", "b.env", masker=masker, options=opts)
    assert "new_secret" not in report.body
    assert "old_secret" not in report.body


def test_no_mask_when_disabled(simple_diff):
    opts = ReportOptions(mask_secrets=False, show_unchanged=True, use_color=False)
    report = generate_report(simple_diff, "a.env", "b.env", masker=None, options=opts)
    assert "new_secret" in report.body or "old_secret" in report.body
