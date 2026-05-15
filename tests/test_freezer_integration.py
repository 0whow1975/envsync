"""Integration tests for the freeze → drift pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from envsync.freezer import check_drift, freeze_env, load_freeze, save_freeze
from envsync.parser import parse_env_file


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    (tmp_path / "prod.env").write_text(
        "DB_HOST=prod-db\nDB_PORT=5432\nSECRET_KEY=supersecret\nDEBUG=false\n"
    )
    (tmp_path / "staging.env").write_text(
        "DB_HOST=staging-db\nDB_PORT=5432\nSECRET_KEY=supersecret\nDEBUG=true\n"
    )
    return tmp_path


def test_integration_freeze_and_reload_preserves_key_set(env_dir: Path) -> None:
    env = parse_env_file(env_dir / "prod.env")
    result = freeze_env(env)
    dest = env_dir / "prod.freeze.json"
    save_freeze(result, dest)
    loaded = load_freeze(dest)
    original_keys = {fk.key for fk in result.frozen_keys}
    loaded_keys = {fk.key for fk in loaded.frozen_keys}
    assert original_keys == loaded_keys


def test_integration_no_drift_same_file(env_dir: Path) -> None:
    env = parse_env_file(env_dir / "prod.env")
    frozen = freeze_env(env)
    report = check_drift(frozen, env)
    assert report.is_clean


def test_integration_drift_detected_between_prod_and_staging(env_dir: Path) -> None:
    prod = parse_env_file(env_dir / "prod.env")
    staging = parse_env_file(env_dir / "staging.env")
    frozen = freeze_env(prod)
    report = check_drift(frozen, staging)
    # DB_HOST and DEBUG differ between prod and staging
    drifted_keys = {d.key for d in report.drifted}
    assert "DB_HOST" in drifted_keys
    assert "DEBUG" in drifted_keys


def test_integration_added_keys_reported(env_dir: Path) -> None:
    prod = parse_env_file(env_dir / "prod.env")
    frozen = freeze_env(prod)
    extra = env_dir / "extra.env"
    extra.write_text(
        "DB_HOST=prod-db\nDB_PORT=5432\nSECRET_KEY=supersecret\nDEBUG=false\nNEW_FEATURE=1\n"
    )
    current = parse_env_file(extra)
    report = check_drift(frozen, current)
    assert "NEW_FEATURE" in report.added
    assert report.is_clean is False
