"""Encrypt and decrypt .env file values using Fernet symmetric encryption."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import List, Optional

from cryptography.fernet import Fernet, InvalidToken

from envsync.parser import EnvEntry, EnvFile
from envsync.masker import SecretMasker, MaskConfig


@dataclass
class EncryptOptions:
    secrets_only: bool = True
    key: Optional[bytes] = None  # raw Fernet key; generated if None


@dataclass
class EncryptResult:
    entries: List[EnvEntry]
    key: bytes  # the Fernet key used (caller must persist this)
    total_encrypted: int = 0
    total_skipped: int = 0

    def to_env_file(self, path: str) -> EnvFile:
        return EnvFile(path=path, entries=self.entries)


def generate_key() -> bytes:
    """Generate a new Fernet key."""
    return Fernet.generate_key()


def encrypt_env(
    env: EnvFile,
    options: Optional[EncryptOptions] = None,
    masker: Optional[SecretMasker] = None,
) -> EncryptResult:
    """Return a new EnvFile with secret values encrypted."""
    options = options or EncryptOptions()
    masker = masker or SecretMasker(MaskConfig())
    key = options.key or generate_key()
    fernet = Fernet(key)

    new_entries: List[EnvEntry] = []
    total_encrypted = 0
    total_skipped = 0

    for entry in env.entries:
        if options.secrets_only and not masker.is_secret(entry.key):
            new_entries.append(entry)
            total_skipped += 1
        else:
            encrypted = fernet.encrypt(entry.value.encode()).decode()
            new_entries.append(EnvEntry(key=entry.key, value=f"enc:{encrypted}", comment=entry.comment))
            total_encrypted += 1

    return EncryptResult(
        entries=new_entries,
        key=key,
        total_encrypted=total_encrypted,
        total_skipped=total_skipped,
    )


def decrypt_env(env: EnvFile, key: bytes) -> EnvFile:
    """Return a new EnvFile with enc:-prefixed values decrypted."""
    fernet = Fernet(key)
    new_entries: List[EnvEntry] = []

    for entry in env.entries:
        if entry.value.startswith("enc:"):
            try:
                raw = fernet.decrypt(entry.value[4:].encode()).decode()
            except InvalidToken:
                raw = entry.value  # leave as-is if key is wrong
            new_entries.append(EnvEntry(key=entry.key, value=raw, comment=entry.comment))
        else:
            new_entries.append(entry)

    return EnvFile(path=env.path, entries=new_entries)
