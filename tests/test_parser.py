"""Tests for envsync.parser module."""

import textwrap
from pathlib import Path

import pytest

from envsync.parser import EnvFile, parse_env_file, _strip_quotes, _split_inline_comment


@pytest.fixture
def sample_env_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        # Database config
        DB_HOST=localhost
        DB_PORT=5432
        DB_NAME="myapp_db"
        DB_PASSWORD='s3cr3t'
        API_KEY=abc123  # production key
        EMPTY_VAR=
    """)
    env_path = tmp_path / ".env"
    env_path.write_text(content)
    return env_path


def test_parse_returns_env_file(sample_env_file):
    result = parse_env_file(sample_env_file)
    assert isinstance(result, EnvFile)


def test_parse_extracts_keys(sample_env_file):
    result = parse_env_file(sample_env_file)
    assert "DB_HOST" in result.entries
    assert "DB_PORT" in result.entries
    assert "API_KEY" in result.entries


def test_parse_strips_double_quotes(sample_env_file):
    result = parse_env_file(sample_env_file)
    assert result.get("DB_NAME") == "myapp_db"


def test_parse_strips_single_quotes(sample_env_file):
    result = parse_env_file(sample_env_file)
    assert result.get("DB_PASSWORD") == "s3cr3t"


def test_parse_handles_empty_value(sample_env_file):
    result = parse_env_file(sample_env_file)
    assert result.get("EMPTY_VAR") == ""


def test_parse_preserves_order(sample_env_file):
    result = parse_env_file(sample_env_file)
    assert result.order == ["DB_HOST", "DB_PORT", "DB_NAME", "DB_PASSWORD", "API_KEY", "EMPTY_VAR"]


def test_parse_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/.env")


def test_strip_quotes_no_quotes():
    assert _strip_quotes("hello") == "hello"


def test_strip_quotes_double():
    assert _strip_quotes('"hello world"') == "hello world"


def test_split_inline_comment_present():
    value, comment = _split_inline_comment("abc123  # production key")
    assert value == "abc123"
    assert comment is not None and comment.startswith("#")


def test_split_inline_comment_absent():
    value, comment = _split_inline_comment("abc123")
    assert value == "abc123"
    assert comment is None


def test_split_inline_comment_inside_quotes():
    value, comment = _split_inline_comment('"url#fragment"')
    assert value == '"url#fragment"'
    assert comment is None
