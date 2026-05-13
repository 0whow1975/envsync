"""Tests for envsync.encryptor."""
from __future__ import annotations

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.encryptor import (
    EncryptOptions,
    encrypt_env,
    decrypt_env,
    generate_key,
)
from envsync.masker import SecretMasker, MaskConfig


@pytest.fixture()
def env() -> EnvFile:
    return EnvFile(
        path=".env",
        entries=[
            EnvEntry(key="APP_NAME", value="myapp"),
            EnvEntry(key="SECRET_KEY", value="supersecret"),
            EnvEntry(key="DATABASE_URL", value="postgres://localhost/db"),
            EnvEntry(key="DEBUG", value="true"),
        ],
    )


def test_generate_key_returns_bytes():
    key = generate_key()
    assert isinstance(key, bytes)
    assert len(key) > 0


def test_encrypt_secrets_only_by_default(env):
    result = encrypt_env(env)
    keys_encrypted = [e for e in result.entries if e.value.startswith("enc:")]
    plain_keys = [e for e in result.entries if not e.value.startswith("enc:")]
    assert any(e.key == "SECRET_KEY" for e in keys_encrypted)
    assert any(e.key == "DATABASE_URL" for e in keys_encrypted)
    assert any(e.key == "APP_NAME" for e in plain_keys)
    assert any(e.key == "DEBUG" for e in plain_keys)


def test_encrypt_all_keys_when_requested(env):
    options = EncryptOptions(secrets_only=False)
    result = encrypt_env(env, options)
    assert all(e.value.startswith("enc:") for e in result.entries)
    assert result.total_encrypted == 4
    assert result.total_skipped == 0


def test_encrypt_result_counts(env):
    result = encrypt_env(env)
    assert result.total_encrypted + result.total_skipped == len(env.entries)


def test_encrypt_uses_provided_key(env):
    key = generate_key()
    options = EncryptOptions(key=key)
    result = encrypt_env(env, options)
    assert result.key == key


def test_decrypt_restores_original_values(env):
    key = generate_key()
    options = EncryptOptions(key=key, secrets_only=False)
    encrypted = encrypt_env(env, options)
    decrypted = decrypt_env(encrypted.to_env_file(".env"), key)
    original = {e.key: e.value for e in env.entries}
    restored = {e.key: e.value for e in decrypted.entries}
    assert original == restored


def test_decrypt_leaves_plain_values_untouched(env):
    key = generate_key()
    options = EncryptOptions(key=key, secrets_only=True)
    encrypted = encrypt_env(env, options)
    decrypted = decrypt_env(encrypted.to_env_file(".env"), key)
    app_name = next(e for e in decrypted.entries if e.key == "APP_NAME")
    assert app_name.value == "myapp"


def test_decrypt_with_wrong_key_leaves_enc_prefix(env):
    key = generate_key()
    wrong_key = generate_key()
    options = EncryptOptions(key=key, secrets_only=False)
    encrypted = encrypt_env(env, options)
    decrypted = decrypt_env(encrypted.to_env_file(".env"), wrong_key)
    # Values should remain as enc:... because decryption fails
    assert all(e.value.startswith("enc:") for e in decrypted.entries)


def test_to_env_file_returns_correct_path(env):
    result = encrypt_env(env)
    env_file = result.to_env_file("/tmp/out.env")
    assert env_file.path == "/tmp/out.env"
    assert len(env_file.entries) == len(env.entries)
