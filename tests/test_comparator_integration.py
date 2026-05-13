"""Integration tests: parse real files then compare."""
from __future__ import annotations

from pathlib import Path

import pytest

from envsync.parser import parse_env_file
from envsync.diff import ChangeType
from envsync.comparator import CompareOptions, compare_envs


@pytest.fixture()
def env_dir(tmp_path):
    (tmp_path / "prod.env").write_text(
        "APP_ENV=production\nDB_HOST=prod-db\nAPI_KEY=secret123\nFEATURE_X=off\n"
    )
    (tmp_path / "staging.env").write_text(
        "APP_ENV=staging\nDB_HOST=staging-db\nAPI_KEY=secret123\nFEATURE_X=on\n"
    )
    (tmp_path / "dev.env").write_text(
        "APP_ENV=development\nDB_HOST=localhost\nDEBUG=true\nFEATURE_X=on\n"
    )
    return tmp_path


def _load(env_dir: Path) -> dict:
    return {
        p.stem: parse_env_file(p)
        for p in sorted(env_dir.glob("*.env"))
    }


def test_integration_three_way_compare_pair_count(env_dir):
    envs = _load(env_dir)
    result = compare_envs(envs)
    assert len(result.pairs) == 3


def test_integration_all_keys_present(env_dir):
    envs = _load(env_dir)
    result = compare_envs(envs)
    assert "APP_ENV" in result.all_keys
    assert "DEBUG" in result.all_keys
    assert "API_KEY" in result.all_keys


def test_integration_debug_missing_from_prod_and_staging(env_dir):
    envs = _load(env_dir)
    result = compare_envs(envs)
    assert "DEBUG" in result.keys_missing_from("prod")
    assert "DEBUG" in result.keys_missing_from("staging")
    assert "DEBUG" not in result.keys_missing_from("dev")


def test_integration_api_key_unchanged_between_prod_and_staging(env_dir):
    envs = _load(env_dir)
    opts = CompareOptions(baseline="prod")
    result = compare_envs(envs, opts)
    prod_staging = next(p for p in result.pairs if p.label_b == "staging")
    unchanged_keys = [
        e.key for e in prod_staging.diff.entries if e.change == ChangeType.UNCHANGED
    ]
    assert "API_KEY" in unchanged_keys


def test_integration_feature_x_changed_prod_vs_staging(env_dir):
    envs = _load(env_dir)
    opts = CompareOptions(baseline="prod")
    result = compare_envs(envs, opts)
    prod_staging = next(p for p in result.pairs if p.label_b == "staging")
    changed_keys = [
        e.key for e in prod_staging.diff.entries if e.change == ChangeType.CHANGED
    ]
    assert "FEATURE_X" in changed_keys
