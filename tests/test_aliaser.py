"""Tests for envsync.aliaser."""
from __future__ import annotations

import pytest

from envsync.aliaser import AliasOptions, AliasViolation, resolve_aliases
from envsync.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(path=".env", entries=entries)


@pytest.fixture()
def base_env() -> EnvFile:
    return _make_env(
        ("OLD_API_KEY", "secret123"),
        ("DB_HOST", "localhost"),
        ("OLD_DB_PORT", "5432"),
    )


def test_resolve_renames_alias_to_canonical(base_env):
    opts = AliasOptions(alias_map={"OLD_API_KEY": "API_KEY"})
    result = resolve_aliases(base_env, opts)
    keys = [e.key for e in result.entries]
    assert "API_KEY" in keys
    assert "OLD_API_KEY" not in keys


def test_resolved_entry_preserves_value(base_env):
    opts = AliasOptions(alias_map={"OLD_API_KEY": "API_KEY"})
    result = resolve_aliases(base_env, opts)
    entry = next(e for e in result.entries if e.key == "API_KEY")
    assert entry.value == "secret123"


def test_total_resolved_count(base_env):
    opts = AliasOptions(alias_map={"OLD_API_KEY": "API_KEY", "OLD_DB_PORT": "DB_PORT"})
    result = resolve_aliases(base_env, opts)
    assert result.total_resolved == 2


def test_missing_alias_is_skipped(base_env):
    opts = AliasOptions(alias_map={"NONEXISTENT": "NEW_KEY"})
    result = resolve_aliases(base_env, opts)
    assert result.total_skipped == 1
    assert result.skipped[0].alias == "NONEXISTENT"


def test_no_overwrite_skips_when_canonical_exists():
    env = _make_env(("OLD_KEY", "old_val"), ("NEW_KEY", "existing"))
    opts = AliasOptions(alias_map={"OLD_KEY": "NEW_KEY"}, overwrite=False)
    result = resolve_aliases(env, opts)
    assert result.total_skipped == 1
    canonical = next(e for e in result.entries if e.key == "NEW_KEY")
    assert canonical.value == "existing"


def test_overwrite_replaces_existing_canonical():
    env = _make_env(("OLD_KEY", "new_val"), ("NEW_KEY", "existing"))
    opts = AliasOptions(alias_map={"OLD_KEY": "NEW_KEY"}, overwrite=True)
    result = resolve_aliases(env, opts)
    assert result.total_resolved == 1
    canonical = next(e for e in result.entries if e.key == "NEW_KEY")
    assert canonical.value == "new_val"


def test_no_remove_keeps_alias_key(base_env):
    opts = AliasOptions(alias_map={"OLD_API_KEY": "API_KEY"}, remove_alias=False)
    result = resolve_aliases(base_env, opts)
    keys = [e.key for e in result.entries]
    assert "OLD_API_KEY" in keys
    assert "API_KEY" in keys


def test_unrelated_keys_unchanged(base_env):
    opts = AliasOptions(alias_map={"OLD_API_KEY": "API_KEY"})
    result = resolve_aliases(base_env, opts)
    db_entry = next(e for e in result.entries if e.key == "DB_HOST")
    assert db_entry.value == "localhost"


def test_to_env_file_returns_env_file(base_env):
    opts = AliasOptions(alias_map={"OLD_API_KEY": "API_KEY"})
    result = resolve_aliases(base_env, opts)
    ef = result.to_env_file(".env.out")
    assert ef.path == ".env.out"
    assert any(e.key == "API_KEY" for e in ef.entries)


def test_alias_violation_str():
    v = AliasViolation(alias="OLD", canonical="NEW", reason="alias key not found")
    assert "OLD" in str(v)
    assert "NEW" in str(v)
