"""Tests for envsync.masker module."""

import pytest

from envsync.masker import (
    DEFAULT_SECRET_PATTERNS,
    MASK_PLACEHOLDER,
    MaskConfig,
    SecretMasker,
    mask_keys,
)


@pytest.fixture()
def masker() -> SecretMasker:
    return SecretMasker()


# --- is_secret ---


@pytest.mark.parametrize(
    "key",
    [
        "SECRET_KEY",
        "DB_PASSWORD",
        "API_TOKEN",
        "GITHUB_API_KEY",
        "PRIVATE_KEY",
        "AUTH_HEADER",
        "USER_CREDENTIALS",
        "APP_SECRET",
    ],
)
def test_is_secret_returns_true_for_sensitive_keys(masker: SecretMasker, key: str) -> None:
    assert masker.is_secret(key) is True


@pytest.mark.parametrize(
    "key",
    ["APP_ENV", "DATABASE_URL", "PORT", "DEBUG", "LOG_LEVEL"],
)
def test_is_secret_returns_false_for_plain_keys(masker: SecretMasker, key: str) -> None:
    assert masker.is_secret(key) is False


def test_is_secret_case_insensitive_by_default(masker: SecretMasker) -> None:
    assert masker.is_secret("db_password") is True
    assert masker.is_secret("Api_Token") is True


def test_is_secret_case_sensitive_when_configured() -> None:
    config = MaskConfig(case_sensitive=True)
    masker = SecretMasker(config)
    # lowercase pattern won't match uppercase key when case-sensitive
    assert masker.is_secret("DB_PASSWORD") is False
    assert masker.is_secret("db_password") is True


# --- mask_value ---


def test_mask_value_replaces_secret(masker: SecretMasker) -> None:
    assert masker.mask_value("API_TOKEN", "super-secret-123") == MASK_PLACEHOLDER


def test_mask_value_keeps_plain_value(masker: SecretMasker) -> None:
    assert masker.mask_value("APP_ENV", "production") == "production"


def test_mask_value_uses_custom_mask() -> None:
    config = MaskConfig(mask="<REDACTED>")
    masker = SecretMasker(config)
    assert masker.mask_value("SECRET_KEY", "abc") == "<REDACTED>"


# --- mask_dict ---


def test_mask_dict_masks_only_secrets(masker: SecretMasker) -> None:
    env = {"APP_ENV": "prod", "DB_PASSWORD": "hunter2", "PORT": "8080"}
    result = masker.mask_dict(env)
    assert result["APP_ENV"] == "prod"
    assert result["DB_PASSWORD"] == MASK_PLACEHOLDER
    assert result["PORT"] == "8080"


# --- add_pattern ---


def test_add_pattern_extends_masker(masker: SecretMasker) -> None:
    masker.add_pattern(r".*custom_sensitive.*")
    assert masker.is_secret("MY_CUSTOM_SENSITIVE_VALUE") is True


# --- mask_keys convenience ---


def test_mask_keys_returns_only_secret_keys() -> None:
    keys = ["APP_ENV", "DB_PASSWORD", "API_TOKEN", "PORT"]
    result = mask_keys(keys)
    assert set(result) == {"DB_PASSWORD", "API_TOKEN"}
