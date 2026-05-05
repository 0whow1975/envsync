"""Tests for envsync.schema module."""

import pytest
from pathlib import Path
from envsync.schema import parse_schema_file, schema_to_validator_kwargs, EnvSchema
from envsync.validator import EnvValidator


@pytest.fixture
def schema_file(tmp_path: Path) -> Path:
    content = """
# Required keys
APP_ENV
DATABASE_URL
SECRET_KEY

# Optional keys
DEBUG?
LOG_LEVEL?
REDIS_URL?
"""
    p = tmp_path / ".env.schema"
    p.write_text(content)
    return p


def test_parse_required_keys(schema_file):
    schema = parse_schema_file(schema_file)
    assert "APP_ENV" in schema.required
    assert "DATABASE_URL" in schema.required
    assert "SECRET_KEY" in schema.required


def test_parse_optional_keys(schema_file):
    schema = parse_schema_file(schema_file)
    assert "DEBUG" in schema.optional
    assert "LOG_LEVEL" in schema.optional
    assert "REDIS_URL" in schema.optional


def test_optional_keys_not_in_required(schema_file):
    schema = parse_schema_file(schema_file)
    for key in schema.optional:
        assert key not in schema.required


def test_all_keys_combines_both(schema_file):
    schema = parse_schema_file(schema_file)
    assert set(schema.all_keys) == set(schema.required) | set(schema.optional)


def test_comments_and_blank_lines_ignored(schema_file):
    schema = parse_schema_file(schema_file)
    for key in schema.all_keys:
        assert not key.startswith("#")
        assert key.strip() != ""


def test_schema_to_validator_kwargs(schema_file):
    schema = parse_schema_file(schema_file)
    kwargs = schema_to_validator_kwargs(schema)
    assert "required_keys" in kwargs
    assert set(kwargs["required_keys"]) == set(schema.required)


def test_validator_built_from_schema(schema_file):
    schema = parse_schema_file(schema_file)
    validator = EnvValidator(**schema_to_validator_kwargs(schema))
    assert set(validator.required_keys) == set(schema.required)


def test_empty_schema_file(tmp_path):
    p = tmp_path / ".env.schema"
    p.write_text("# just a comment\n\n")
    schema = parse_schema_file(p)
    assert schema.required == []
    assert schema.optional == []
