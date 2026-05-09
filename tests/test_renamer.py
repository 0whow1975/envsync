"""Tests for envsync.renamer."""
import pytest

from envsync.parser import EnvFile, EnvEntry
from envsync.renamer import RenameOptions, RenameResult, rename_key


def _make_env(path: str, **kwargs: str) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in kwargs.items()]
    return EnvFile(path=path, entries=entries)


@pytest.fixture()
def env_a() -> EnvFile:
    return _make_env("a.env", DB_HOST="localhost", DB_PORT="5432", SECRET_KEY="abc")


@pytest.fixture()
def env_b() -> EnvFile:
    return _make_env("b.env", DB_HOST="prod.host", APP_ENV="production")


def test_rename_updates_key_in_place(env_a):
    rename_key([env_a], old_key="DB_HOST", new_key="DATABASE_HOST")
    assert env_a.get("DATABASE_HOST") is not None
    assert env_a.get("DB_HOST") is None


def test_rename_preserves_value(env_a):
    rename_key([env_a], old_key="DB_HOST", new_key="DATABASE_HOST")
    assert env_a.get("DATABASE_HOST").value == "localhost"


def test_rename_across_multiple_files(env_a, env_b):
    result = rename_key([env_a, env_b], old_key="DB_HOST", new_key="DATABASE_HOST")
    assert result.total_renamed == 2
    assert env_a.get("DATABASE_HOST") is not None
    assert env_b.get("DATABASE_HOST") is not None


def test_rename_skips_file_without_key(env_a, env_b):
    # SECRET_KEY only exists in env_a
    result = rename_key([env_a, env_b], old_key="SECRET_KEY", new_key="APP_SECRET")
    assert "a.env" in result.renamed
    assert "b.env" in result.skipped


def test_rename_ignore_missing_omits_from_skipped(env_a, env_b):
    opts = RenameOptions(ignore_missing=True)
    result = rename_key([env_a, env_b], old_key="SECRET_KEY", new_key="APP_SECRET", options=opts)
    assert result.total_skipped == 0
    assert "a.env" in result.renamed


def test_dry_run_does_not_mutate(env_a):
    opts = RenameOptions(dry_run=True)
    rename_key([env_a], old_key="DB_HOST", new_key="DATABASE_HOST", options=opts)
    # Original key must still be present
    assert env_a.get("DB_HOST") is not None
    assert env_a.get("DATABASE_HOST") is None


def test_dry_run_still_reports_renamed(env_a):
    opts = RenameOptions(dry_run=True)
    result = rename_key([env_a], old_key="DB_HOST", new_key="DATABASE_HOST", options=opts)
    assert result.total_renamed == 1
    assert "a.env" in result.renamed


def test_result_counts(env_a, env_b):
    result = rename_key([env_a, env_b], old_key="DB_HOST", new_key="DATABASE_HOST")
    assert result.total_renamed == 2
    assert result.total_skipped == 0
    assert result.old_key == "DB_HOST"
    assert result.new_key == "DATABASE_HOST"
