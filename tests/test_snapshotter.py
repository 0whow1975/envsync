"""Tests for envsync.snapshotter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsync.parser import parse_env_file
from envsync.snapshotter import (
    Snapshot,
    list_snapshots,
    load_snapshot,
    restore_snapshot,
    save_snapshot,
    take_snapshot,
)


@pytest.fixture()
def env_file(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envsync\nSECRET_KEY=abc123\nDEBUG=false\n")
    return parse_env_file(str(p))


@pytest.fixture()
def snapshot(env_file):
    return take_snapshot(env_file)


def test_take_snapshot_captures_all_keys(snapshot):
    assert set(snapshot.entries.keys()) == {"APP_NAME", "SECRET_KEY", "DEBUG"}


def test_take_snapshot_captures_values(snapshot):
    assert snapshot.entries["APP_NAME"] == "envsync"
    assert snapshot.entries["SECRET_KEY"] == "abc123"


def test_take_snapshot_records_path(env_file, snapshot):
    assert snapshot.path == env_file.path


def test_take_snapshot_records_timestamp(snapshot):
    assert snapshot.captured_at  # non-empty ISO string
    assert "T" in snapshot.captured_at  # rough ISO-8601 check


def test_save_snapshot_creates_file(tmp_path, snapshot):
    snap_dir = str(tmp_path / "snapshots")
    dest = save_snapshot(snapshot, snap_dir)
    assert dest.exists()
    assert dest.suffix == ".json"


def test_save_snapshot_json_is_valid(tmp_path, snapshot):
    snap_dir = str(tmp_path / "snapshots")
    dest = save_snapshot(snapshot, snap_dir)
    data = json.loads(dest.read_text())
    assert data["entries"]["APP_NAME"] == "envsync"


def test_load_snapshot_roundtrip(tmp_path, snapshot):
    snap_dir = str(tmp_path / "snapshots")
    dest = save_snapshot(snapshot, snap_dir)
    loaded = load_snapshot(str(dest))
    assert loaded.entries == snapshot.entries
    assert loaded.path == snapshot.path


def test_list_snapshots_returns_saved_files(tmp_path, snapshot):
    snap_dir = str(tmp_path / "snapshots")
    save_snapshot(snapshot, snap_dir)
    save_snapshot(snapshot, snap_dir)  # save twice
    files = list_snapshots(snap_dir)
    assert len(files) == 2


def test_list_snapshots_filters_by_filename(tmp_path, snapshot):
    snap_dir = str(tmp_path / "snapshots")
    save_snapshot(snapshot, snap_dir)
    # filter by a name that won't match
    files = list_snapshots(snap_dir, env_filename="other.env")
    assert files == []


def test_list_snapshots_empty_dir_returns_empty(tmp_path):
    assert list_snapshots(str(tmp_path / "nonexistent")) == []


def test_restore_snapshot_writes_file(tmp_path, snapshot):
    out = tmp_path / "restored.env"
    restore_snapshot(snapshot, dest_path=str(out))
    content = out.read_text()
    assert "APP_NAME=envsync" in content
    assert "SECRET_KEY=abc123" in content


def test_snapshot_to_dict_and_from_dict(snapshot):
    d = snapshot.to_dict()
    restored = Snapshot.from_dict(d)
    assert restored.entries == snapshot.entries
    assert restored.path == snapshot.path
    assert restored.captured_at == snapshot.captured_at
