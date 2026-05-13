"""Tests for envsync.patcher."""

from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.patcher import PatchOptions, PatchResult, patch_env


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(k, v) for k, v in pairs]
    return EnvFile(path=".env", entries=entries)


@pytest.fixture()
def base_env() -> EnvFile:
    return _make_env(("APP_NAME", "myapp"), ("DEBUG", "false"), ("PORT", "8080"))


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_patch_updates_existing_key(base_env: EnvFile) -> None:
    result = patch_env(base_env, {"DEBUG": "true"})
    assert result.env_file is not None
    values = {e.key: e.value for e in result.env_file.entries}
    assert values["DEBUG"] == "true"


def test_patch_adds_missing_key(base_env: EnvFile) -> None:
    result = patch_env(base_env, {"NEW_KEY": "hello"})
    keys = [e.key for e in result.env_file.entries]
    assert "NEW_KEY" in keys
    assert result.total_patched == 1


def test_patch_reports_patched_keys(base_env: EnvFile) -> None:
    result = patch_env(base_env, {"PORT": "9090", "NEW_KEY": "x"})
    assert set(result.patched) == {"PORT", "NEW_KEY"}


def test_patch_does_not_mutate_original(base_env: EnvFile) -> None:
    original_values = {e.key: e.value for e in base_env.entries}
    patch_env(base_env, {"DEBUG": "true", "NEW_KEY": "y"})
    current_values = {e.key: e.value for e in base_env.entries}
    assert current_values == original_values


# ---------------------------------------------------------------------------
# PatchOptions: overwrite_existing=False
# ---------------------------------------------------------------------------

def test_skip_existing_when_overwrite_disabled(base_env: EnvFile) -> None:
    opts = PatchOptions(overwrite_existing=False)
    result = patch_env(base_env, {"DEBUG": "true"}, options=opts)
    assert "DEBUG" in result.skipped
    values = {e.key: e.value for e in result.env_file.entries}
    assert values["DEBUG"] == "false"  # unchanged


# ---------------------------------------------------------------------------
# PatchOptions: add_missing=False
# ---------------------------------------------------------------------------

def test_skip_new_key_when_add_missing_disabled(base_env: EnvFile) -> None:
    opts = PatchOptions(add_missing=False)
    result = patch_env(base_env, {"BRAND_NEW": "value"}, options=opts)
    assert "BRAND_NEW" in result.skipped
    keys = [e.key for e in result.env_file.entries]
    assert "BRAND_NEW" not in keys


# ---------------------------------------------------------------------------
# PatchOptions: dry_run
# ---------------------------------------------------------------------------

def test_dry_run_reports_changes_without_applying(base_env: EnvFile) -> None:
    opts = PatchOptions(dry_run=True)
    result = patch_env(base_env, {"DEBUG": "true", "EXTRA": "1"}, options=opts)
    assert set(result.patched) == {"DEBUG", "EXTRA"}
    # Values must remain unchanged
    values = {e.key: e.value for e in result.env_file.entries}
    assert values["DEBUG"] == "false"
    keys = [e.key for e in result.env_file.entries]
    assert "EXTRA" not in keys


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_patches_returns_identical_entries(base_env: EnvFile) -> None:
    result = patch_env(base_env, {})
    assert result.total_patched == 0
    assert result.total_skipped == 0
    assert len(result.env_file.entries) == len(base_env.entries)


def test_patch_preserves_comment_on_updated_entry(base_env: EnvFile) -> None:
    from envsync.parser import EnvEntry, EnvFile
    env = EnvFile(
        path=".env",
        entries=[EnvEntry("HOST", "localhost", comment="# server host")],
    )
    result = patch_env(env, {"HOST": "example.com"})
    entry = result.env_file.entries[0]
    assert entry.value == "example.com"
    assert entry.comment == "# server host"
