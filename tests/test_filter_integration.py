"""Integration tests for filter — parse real files then filter."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envsync.parser import parse_env_file
from envsync.pinecone_filter import FilterOptions, filter_env


@pytest.fixture
def env_dir(tmp_path: Path) -> Path:
    (tmp_path / "prod.env").write_text(
        textwrap.dedent("""\
            DB_HOST=db.prod.example.com
            DB_PORT=5432
            DB_PASSWORD=supersecret
            APP_DEBUG=false
            APP_PORT=443
            LOG_LEVEL=warning
            CACHE_TTL=3600
        """)
    )
    return tmp_path


def test_integration_prefix_db_returns_three_keys(env_dir):
    env = parse_env_file(env_dir / "prod.env")
    result = filter_env(env, FilterOptions(prefixes=["DB_"]))
    assert result.total_matched == 3


def test_integration_multi_prefix(env_dir):
    env = parse_env_file(env_dir / "prod.env")
    result = filter_env(env, FilterOptions(prefixes=["APP_", "LOG_"]))
    keys = {e.key for e in result.matched}
    assert keys == {"APP_DEBUG", "APP_PORT", "LOG_LEVEL"}


def test_integration_invert_gives_complement(env_dir):
    env = parse_env_file(env_dir / "prod.env")
    normal = filter_env(env, FilterOptions(prefixes=["DB_"]))
    inverted = filter_env(env, FilterOptions(prefixes=["DB_"], invert=True))
    total = len(env.entries)
    assert normal.total_matched + inverted.total_matched == total


def test_integration_pattern_port_keys(env_dir):
    env = parse_env_file(env_dir / "prod.env")
    result = filter_env(env, FilterOptions(patterns=[r"_PORT$"]))
    keys = {e.key for e in result.matched}
    assert keys == {"DB_PORT", "APP_PORT"}


def test_integration_no_criteria_returns_all(env_dir):
    env = parse_env_file(env_dir / "prod.env")
    result = filter_env(env, FilterOptions())
    assert result.total_matched == len(env.entries)
