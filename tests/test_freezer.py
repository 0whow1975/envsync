"""Tests for envsync.freezer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsync.freezer import (
    FreezeOptions,
    FreezeResult,
    check_drift,
    freeze_env,
    load_freeze,
    save_freeze,
)
from envsync.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple[str, str], path: str = ".env") -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(path=Path(path), entries=entries)


@pytest.fixture()
def simple_env() -> EnvFile:
    return _make_env(("DB_HOST", "localhost"), ("SECRET_KEY", "abc123"), ("PORT", "5432"))


def test_freeze_captures_all_keys(simple_env: EnvFile) -> None:
    result = freeze_env(simple_env)
    keys = [fk.key for fk in result.frozen_keys]
    assert "DB_HOST" in keys
    assert "SECRET_KEY" in keys
    assert "PORT" in keys


def test_freeze_key_count_matches(simple_env: EnvFile) -> None:
    result = freeze_env(simple_env)
    assert result.key_count == 3


def test_freeze_checksum_is_stable(simple_env: EnvFile) -> None:
    r1 = freeze_env(simple_env)
    r2 = freeze_env(simple_env)
    assert r1.checksum == r2.checksum


def test_freeze_checksum_changes_on_value_change() -> None:
    env1 = _make_env(("KEY", "value1"))
    env2 = _make_env(("KEY", "value2"))
    assert freeze_env(env1).checksum != freeze_env(env2).checksum


def test_freeze_to_dict_has_expected_structure(simple_env: EnvFile) -> None:
    result = freeze_env(simple_env)
    d = result.to_dict()
    assert "checksum" in d
    assert "keys" in d
    assert isinstance(d["keys"], list)
    assert all("key" in k and "value_hash" in k for k in d["keys"])


def test_save_and_load_freeze_roundtrip(simple_env: EnvFile, tmp_path: Path) -> None:
    result = freeze_env(simple_env)
    dest = tmp_path / "test.freeze.json"
    save_freeze(result, dest)
    loaded = load_freeze(dest)
    assert loaded.checksum == result.checksum
    assert {fk.key for fk in loaded.frozen_keys} == {fk.key for fk in result.frozen_keys}


def test_check_drift_clean_when_identical(simple_env: EnvFile) -> None:
    frozen = freeze_env(simple_env)
    report = check_drift(frozen, simple_env)
    assert report.is_clean


def test_check_drift_detects_changed_value(simple_env: EnvFile) -> None:
    frozen = freeze_env(simple_env)
    modified = _make_env(("DB_HOST", "remotehost"), ("SECRET_KEY", "abc123"), ("PORT", "5432"))
    report = check_drift(frozen, modified)
    assert not report.is_clean
    assert any(d.key == "DB_HOST" for d in report.drifted)


def test_check_drift_detects_removed_key(simple_env: EnvFile) -> None:
    frozen = freeze_env(simple_env)
    reduced = _make_env(("DB_HOST", "localhost"), ("PORT", "5432"))
    report = check_drift(frozen, reduced)
    assert "SECRET_KEY" in report.missing


def test_check_drift_detects_added_key(simple_env: EnvFile) -> None:
    frozen = freeze_env(simple_env)
    expanded = _make_env(
        ("DB_HOST", "localhost"), ("SECRET_KEY", "abc123"), ("PORT", "5432"), ("NEW_KEY", "new")
    )
    report = check_drift(frozen, expanded)
    assert "NEW_KEY" in report.added
