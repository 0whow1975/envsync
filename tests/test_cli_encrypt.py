"""Tests for envsync.cli_encrypt."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envsync.cli_encrypt import add_encrypt_subparser, cmd_encrypt, cmd_decrypt
from envsync.encryptor import generate_key


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=topsecret\nDEBUG=true\n")
    return p


@pytest.fixture()
def key_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envsync.key"
    p.write_bytes(generate_key())
    return p


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_add_encrypt_subparser_registers_encrypt(tmp_path):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_encrypt_subparser(sub)
    args = parser.parse_args(["encrypt", str(tmp_path / ".env"), "--key-file", str(tmp_path / ".key")])
    assert hasattr(args, "func")


def test_add_encrypt_subparser_registers_decrypt(tmp_path):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_encrypt_subparser(sub)
    args = parser.parse_args(["decrypt", str(tmp_path / ".env"), "--key-file", str(tmp_path / ".key")])
    assert hasattr(args, "func")


def test_cmd_encrypt_creates_key_file(env_file, tmp_path):
    key_path = tmp_path / "new.key"
    args = _Args(file=str(env_file), key_file=str(key_path), all_keys=False, output=None)
    rc = cmd_encrypt(args)
    assert rc == 0
    assert key_path.exists()


def test_cmd_encrypt_modifies_file_in_place(env_file, tmp_path):
    key_path = tmp_path / ".envsync.key"
    args = _Args(file=str(env_file), key_file=str(key_path), all_keys=False, output=None)
    cmd_encrypt(args)
    content = env_file.read_text()
    assert "enc:" in content


def test_cmd_encrypt_writes_to_output_file(env_file, tmp_path):
    key_path = tmp_path / ".envsync.key"
    out = tmp_path / "out.env"
    args = _Args(file=str(env_file), key_file=str(key_path), all_keys=False, output=str(out))
    cmd_encrypt(args)
    assert out.exists()
    assert "enc:" in out.read_text()


def test_cmd_decrypt_returns_one_when_key_missing(env_file, tmp_path):
    args = _Args(file=str(env_file), key_file=str(tmp_path / "missing.key"), output=None)
    rc = cmd_decrypt(args)
    assert rc == 1


def test_cmd_encrypt_then_decrypt_roundtrip(env_file, tmp_path):
    key_path = tmp_path / ".envsync.key"
    enc_args = _Args(file=str(env_file), key_file=str(key_path), all_keys=True, output=None)
    cmd_encrypt(enc_args)
    dec_args = _Args(file=str(env_file), key_file=str(key_path), output=None)
    rc = cmd_decrypt(dec_args)
    assert rc == 0
    content = env_file.read_text()
    assert "topsecret" in content
    assert "enc:" not in content
