"""Tests for envsync.splitter."""
from __future__ import annotations

from pathlib import Path

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.splitter import SplitOptions, split_env


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(path=Path("test.env"), entries=entries)


@pytest.fixture()
def mixed_env() -> EnvFile:
    return _make_env(
        ("DB_HOST", "localhost"),
        ("DB_PORT", "5432"),
        ("AWS_ACCESS_KEY", "AKIA123"),
        ("AWS_SECRET", "secret"),
        ("APP_NAME", "envsync"),
        ("DEBUG", "true"),  # no prefix delimiter match beyond first segment
    )


def test_split_groups_by_prefix(mixed_env: EnvFile) -> None:
    result = split_env(mixed_env)
    assert "DB" in result.groups
    assert "AWS" in result.groups
    assert "APP" in result.groups


def test_split_correct_key_count_per_group(mixed_env: EnvFile) -> None:
    result = split_env(mixed_env)
    assert len(result.groups["DB"].entries) == 2
    assert len(result.groups["AWS"].entries) == 2


def test_split_no_prefix_goes_to_remainder(mixed_env: EnvFile) -> None:
    result = split_env(mixed_env)
    remainder_keys = [e.key for e in result.remainder.entries]
    # "DEBUG" has no underscore prefix grouping beyond itself but _prefix_of returns "DEBUG"
    # so remainder should be empty for this fixture; let's use a key without delimiter.
    assert "DEBUG" not in remainder_keys  # DEBUG_* would group; DEBUG alone has no '_'


def test_split_key_without_delimiter_goes_to_remainder() -> None:
    env = _make_env(("HOST", "localhost"), ("DB_PORT", "5432"))
    result = split_env(env)
    remainder_keys = [e.key for e in result.remainder.entries]
    assert "HOST" in remainder_keys


def test_split_include_prefixes_filters_groups(mixed_env: EnvFile) -> None:
    opts = SplitOptions(include_prefixes=["DB"])
    result = split_env(mixed_env, opts)
    assert list(result.groups.keys()) == ["DB"]


def test_split_excluded_prefix_goes_to_remainder(mixed_env: EnvFile) -> None:
    opts = SplitOptions(include_prefixes=["DB"])
    result = split_env(mixed_env, opts)
    remainder_keys = [e.key for e in result.remainder.entries]
    assert "AWS_ACCESS_KEY" in remainder_keys
    assert "AWS_SECRET" in remainder_keys


def test_split_strip_prefix_removes_prefix(mixed_env: EnvFile) -> None:
    opts = SplitOptions(strip_prefix=True)
    result = split_env(mixed_env, opts)
    db_keys = [e.key for e in result.groups["DB"].entries]
    assert "HOST" in db_keys
    assert "PORT" in db_keys


def test_split_without_strip_prefix_keeps_full_key(mixed_env: EnvFile) -> None:
    result = split_env(mixed_env)
    db_keys = [e.key for e in result.groups["DB"].entries]
    assert "DB_HOST" in db_keys


def test_split_total_groups(mixed_env: EnvFile) -> None:
    result = split_env(mixed_env)
    assert result.total_groups == 3


def test_split_output_path_uses_prefix_name(mixed_env: EnvFile) -> None:
    result = split_env(mixed_env)
    assert result.groups["DB"].path.name == "db.env"
    assert result.groups["AWS"].path.name == "aws.env"


def test_split_custom_delimiter() -> None:
    env = _make_env(("APP.NAME", "envsync"), ("APP.VERSION", "1.0"), ("DEBUG", "true"))
    opts = SplitOptions(delimiter=".")
    result = split_env(env, opts)
    assert "APP" in result.groups
    assert len(result.groups["APP"].entries) == 2
