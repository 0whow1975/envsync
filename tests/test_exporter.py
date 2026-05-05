"""Tests for envsync.exporter."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from envsync.diff import ChangeType, DiffEntry, DiffResult
from envsync.exporter import ExportOptions, export_diff
from envsync.masker import MaskConfig, SecretMasker


@pytest.fixture()
def simple_diff() -> DiffResult:
    return DiffResult(
        entries=[
            DiffEntry(key="APP_NAME", change_type=ChangeType.UNCHANGED, old_value="app", value="app"),
            DiffEntry(key="SECRET_KEY", change_type=ChangeType.ADDED, old_value=None, value="s3cr3t"),
            DiffEntry(key="DB_HOST", change_type=ChangeType.MODIFIED, old_value="localhost", value="prod-db"),
            DiffEntry(key="OLD_VAR", change_type=ChangeType.REMOVED, old_value="gone", value=None),
        ]
    )


@pytest.fixture()
def masker() -> SecretMasker:
    return SecretMasker(MaskConfig(keywords=["secret"]))


def test_export_json_creates_file(tmp_path, simple_diff):
    dest = tmp_path / "out.json"
    export_diff(simple_diff, dest, ExportOptions(format="json", include_unchanged=True))
    assert dest.exists()


def test_export_json_excludes_unchanged_by_default(tmp_path, simple_diff):
    dest = tmp_path / "out.json"
    export_diff(simple_diff, dest, ExportOptions(format="json"))
    data = json.loads(dest.read_text())
    keys = [r["key"] for r in data]
    assert "APP_NAME" not in keys
    assert "SECRET_KEY" in keys


def test_export_json_includes_unchanged_when_requested(tmp_path, simple_diff):
    dest = tmp_path / "out.json"
    export_diff(simple_diff, dest, ExportOptions(format="json", include_unchanged=True))
    data = json.loads(dest.read_text())
    assert len(data) == 4


def test_export_json_masks_secrets(tmp_path, simple_diff, masker):
    dest = tmp_path / "out.json"
    export_diff(simple_diff, dest, ExportOptions(format="json"), masker=masker)
    data = json.loads(dest.read_text())
    secret_row = next(r for r in data if r["key"] == "SECRET_KEY")
    assert secret_row["new_value"] != "s3cr3t"


def test_export_csv_creates_valid_csv(tmp_path, simple_diff):
    dest = tmp_path / "out.csv"
    export_diff(simple_diff, dest, ExportOptions(format="csv"))
    with dest.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 3  # unchanged excluded
    assert all("key" in r for r in rows)


def test_export_dotenv_format(tmp_path, simple_diff):
    dest = tmp_path / "out.env"
    export_diff(simple_diff, dest, ExportOptions(format="dotenv"))
    content = dest.read_text()
    assert "SECRET_KEY=s3cr3t" in content
    assert "DB_HOST=prod-db" in content


def test_export_creates_parent_dirs(tmp_path, simple_diff):
    dest = tmp_path / "nested" / "deep" / "out.json"
    export_diff(simple_diff, dest)
    assert dest.exists()


def test_export_unsupported_format_raises(tmp_path, simple_diff):
    dest = tmp_path / "out.xml"
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_diff(simple_diff, dest, ExportOptions(format="xml"))  # type: ignore[arg-type]
