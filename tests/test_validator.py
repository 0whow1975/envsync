"""Tests for envsync.validator module."""

import pytest
from envsync.validator import EnvValidator, ValidationResult, ValidationIssue
from envsync.parser import EnvFile, EnvEntry


def _make_env(*pairs: tuple) -> EnvFile:
    """Build an EnvFile from (key, value) pairs."""
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries, path="test.env")


@pytest.fixture
def validator() -> EnvValidator:
    return EnvValidator(required_keys=["APP_ENV", "DATABASE_URL"])


def test_valid_env_passes(validator):
    env = _make_env(("APP_ENV", "production"), ("DATABASE_URL", "postgres://localhost/db"))
    result = validator.validate(env)
    assert result.is_valid
    assert result.errors == []


def test_missing_required_key_is_error(validator):
    env = _make_env(("APP_ENV", "production"))
    result = validator.validate(env)
    assert not result.is_valid
    keys = [i.key for i in result.errors]
    assert "DATABASE_URL" in keys


def test_all_required_keys_missing(validator):
    env = _make_env(("SOME_OTHER", "value"))
    result = validator.validate(env)
    assert len(result.errors) == 2


def test_empty_value_warning_when_disallowed():
    validator = EnvValidator(allow_empty_values=False)
    env = _make_env(("API_KEY", ""), ("HOST", "localhost"))
    result = validator.validate(env)
    assert result.is_valid  # warnings don't make it invalid
    assert len(result.warnings) == 1
    assert result.warnings[0].key == "API_KEY"


def test_empty_value_allowed_by_default():
    validator = EnvValidator()
    env = _make_env(("API_KEY", ""))
    result = validator.validate(env)
    assert result.is_valid
    assert result.warnings == []


def test_key_exceeds_max_length():
    long_key = "A" * 200
    validator = EnvValidator(max_key_length=128)
    env = _make_env((long_key, "value"))
    result = validator.validate(env)
    assert not result.is_valid
    assert any(long_key in i.key for i in result.errors)


def test_key_with_whitespace_is_error():
    validator = EnvValidator()
    env = _make_env(("BAD KEY", "value"))
    result = validator.validate(env)
    assert not result.is_valid
    assert result.errors[0].key == "BAD KEY"


def test_validation_issue_str():
    issue = ValidationIssue(key="FOO", message="is missing", severity="error")
    assert str(issue) == "[ERROR] FOO: is missing"


def test_no_required_keys_always_passes():
    validator = EnvValidator()
    env = _make_env(("ANYTHING", "goes"))
    result = validator.validate(env)
    assert result.is_valid
