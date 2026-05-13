"""Integration tests for tagger: real files on disk, full round-trip."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envsync.parser import parse_env_file
from envsync.tagger import TagOptions, filter_by_tag, tag_entries


@pytest.fixture()
def env_dir(tmp_path):
    env = tmp_path / ".env"
    env.write_text(textwrap.dedent("""\
        DB_HOST=db.internal
        DB_PORT=5432
        DB_PASSWORD=hunter2
        REDIS_URL=redis://localhost
        APP_DEBUG=true
        SECRET_KEY=abc123
    """))

    tags = {
        "DB_HOST": ["database", "infra"],
        "DB_PORT": ["database", "infra"],
        "DB_PASSWORD": ["database", "secret"],
        "REDIS_URL": ["cache", "infra"],
        "APP_DEBUG": ["app"],
        "SECRET_KEY": ["secret"],
    }
    tag_file = tmp_path / "tags.json"
    tag_file.write_text(json.dumps(tags))
    return tmp_path


def test_integration_all_keys_tagged(env_dir):
    env = parse_env_file(str(env_dir / ".env"))
    tags = json.loads((env_dir / "tags.json").read_text())
    result = tag_entries(env, tags)
    assert result.total_tagged == 6
    assert result.total_skipped == 0


def test_integration_infra_filter(env_dir):
    env = parse_env_file(str(env_dir / ".env"))
    tags = json.loads((env_dir / "tags.json").read_text())
    entries = filter_by_tag(env, tags, "infra")
    keys = {e.key for e in entries}
    assert keys == {"DB_HOST", "DB_PORT", "REDIS_URL"}


def test_integration_secret_filter(env_dir):
    env = parse_env_file(str(env_dir / ".env"))
    tags = json.loads((env_dir / "tags.json").read_text())
    entries = filter_by_tag(env, tags, "secret")
    keys = {e.key for e in entries}
    assert keys == {"DB_PASSWORD", "SECRET_KEY"}


def test_integration_unknown_tag_returns_empty(env_dir):
    env = parse_env_file(str(env_dir / ".env"))
    tags = json.loads((env_dir / "tags.json").read_text())
    entries = filter_by_tag(env, tags, "nonexistent")
    assert entries == []


def test_integration_no_multiple_tags_respects_option(env_dir):
    env = parse_env_file(str(env_dir / ".env"))
    tags = json.loads((env_dir / "tags.json").read_text())
    opts = TagOptions(allow_multiple=False)
    result = tag_entries(env, tags, opts)
    for assigned in result.tagged.values():
        assert len(assigned) == 1
