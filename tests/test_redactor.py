"""Tests for envsync.redactor."""
import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.masker import MaskConfig
from envsync.redactor import RedactOptions, redact, redact_to_string


def _make_env(*pairs: tuple[str | None, str | None]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment="") for k, v in pairs
    ]
    return EnvFile(path="test.env", entries=entries)


@pytest.fixture()
def env() -> EnvFile:
    return _make_env(
        ("APP_NAME", "myapp"),
        ("SECRET_KEY", "supersecret"),
        ("DATABASE_URL", "postgres://localhost/db"),
        ("DEBUG", "true"),
        ("API_TOKEN", "tok_abc123"),
    )


def test_redact_replaces_secret_keys(env):
    result = redact(env)
    redacted = {e.key: e.value for e in result.redacted.entries if e.key}
    assert redacted["SECRET_KEY"] == "REDACTED"
    assert redacted["API_TOKEN"] == "REDACTED"


def test_redact_keeps_plain_values(env):
    result = redact(env)
    redacted = {e.key: e.value for e in result.redacted.entries if e.key}
    assert redacted["APP_NAME"] == "myapp"
    assert redacted["DEBUG"] == "true"


def test_redact_database_url_is_secret(env):
    result = redact(env)
    redacted = {e.key: e.value for e in result.redacted.entries if e.key}
    assert redacted["DATABASE_URL"] == "REDACTED"


def test_redact_records_redacted_keys(env):
    result = redact(env)
    assert "SECRET_KEY" in result.redacted_keys
    assert "API_TOKEN" in result.redacted_keys
    assert "APP_NAME" not in result.redacted_keys


def test_total_redacted_count(env):
    result = redact(env)
    assert result.total_redacted == 3  # SECRET_KEY, DATABASE_URL, API_TOKEN


def test_custom_placeholder(env):
    opts = RedactOptions(placeholder="***")
    result = redact(env, opts)
    redacted = {e.key: e.value for e in result.redacted.entries if e.key}
    assert redacted["SECRET_KEY"] == "***"


def test_original_env_is_unchanged(env):
    redact(env)
    original = {e.key: e.value for e in env.entries if e.key}
    assert original["SECRET_KEY"] == "supersecret"


def test_redact_to_string_contains_placeholder(env):
    text = redact_to_string(env)
    assert "SECRET_KEY=REDACTED" in text
    assert "APP_NAME=myapp" in text


def test_redact_to_string_no_raw_secrets(env):
    text = redact_to_string(env)
    assert "supersecret" not in text
    assert "tok_abc123" not in text


def test_redact_blank_lines_preserved():
    env = _make_env((None, None), ("KEY", "val"), (None, None))
    result = redact(env)
    assert len(result.redacted.entries) == 3
