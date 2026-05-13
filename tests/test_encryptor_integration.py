"""Integration tests: encrypt -> write -> read -> decrypt."""
from __future__ import annotations

from pathlib import Path

import pytest

from envsync.parser import parse_env_file
from envsync.encryptor import EncryptOptions, encrypt_env, decrypt_env, generate_key


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    (tmp_path / ".env").write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=topsecret\n"
        "DATABASE_URL=postgres://user:pass@localhost/db\n"
        "DEBUG=false\n"
    )
    return tmp_path


def _save_env_file(env, path: str) -> None:
    lines = []
    for entry in env.entries:
        if entry.comment:
            lines.append(f"# {entry.comment}")
        lines.append(f"{entry.key}={entry.value}")
    Path(path).write_text("\n".join(lines) + "\n")


def test_integration_secrets_are_unreadable_after_encrypt(env_dir):
    env_path = str(env_dir / ".env")
    env = parse_env_file(env_path)
    key = generate_key()
    result = encrypt_env(env, EncryptOptions(key=key, secrets_only=True))
    _save_env_file(result.to_env_file(env_path), env_path)

    raw = Path(env_path).read_text()
    assert "topsecret" not in raw
    assert "postgres://user:pass" not in raw


def test_integration_plain_values_survive_encrypt(env_dir):
    env_path = str(env_dir / ".env")
    env = parse_env_file(env_path)
    key = generate_key()
    result = encrypt_env(env, EncryptOptions(key=key, secrets_only=True))
    _save_env_file(result.to_env_file(env_path), env_path)

    raw = Path(env_path).read_text()
    assert "APP_NAME=myapp" in raw
    assert "DEBUG=false" in raw


def test_integration_full_roundtrip_restores_all_values(env_dir):
    env_path = str(env_dir / ".env")
    original = {e.key: e.value for e in parse_env_file(env_path).entries}

    key = generate_key()
    env = parse_env_file(env_path)
    encrypted = encrypt_env(env, EncryptOptions(key=key, secrets_only=False))
    _save_env_file(encrypted.to_env_file(env_path), env_path)

    env_enc = parse_env_file(env_path)
    decrypted = decrypt_env(env_enc, key)
    restored = {e.key: e.value for e in decrypted.entries}

    assert restored == original


def test_integration_partial_encrypt_then_decrypt(env_dir):
    env_path = str(env_dir / ".env")
    key = generate_key()

    env = parse_env_file(env_path)
    encrypted = encrypt_env(env, EncryptOptions(key=key, secrets_only=True))
    _save_env_file(encrypted.to_env_file(env_path), env_path)

    env_enc = parse_env_file(env_path)
    decrypted = decrypt_env(env_enc, key)

    secret = next(e for e in decrypted.entries if e.key == "SECRET_KEY")
    assert secret.value == "topsecret"

    db = next(e for e in decrypted.entries if e.key == "DATABASE_URL")
    assert db.value == "postgres://user:pass@localhost/db"
