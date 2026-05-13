"""CLI subcommands: encrypt / decrypt."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.parser import parse_env_file
from envsync.encryptor import EncryptOptions, encrypt_env, decrypt_env, generate_key


def add_encrypt_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    enc = subparsers.add_parser("encrypt", help="Encrypt secret values in a .env file")
    enc.add_argument("file", help="Path to the .env file")
    enc.add_argument("--key-file", default=".envsync.key", help="File to write/read the Fernet key")
    enc.add_argument("--all", dest="all_keys", action="store_true", help="Encrypt all values, not just secrets")
    enc.add_argument("--output", "-o", default=None, help="Output file (default: overwrite input)")
    enc.set_defaults(func=cmd_encrypt)

    dec = subparsers.add_parser("decrypt", help="Decrypt enc:-prefixed values in a .env file")
    dec.add_argument("file", help="Path to the .env file")
    dec.add_argument("--key-file", default=".envsync.key", help="File containing the Fernet key")
    dec.add_argument("--output", "-o", default=None, help="Output file (default: overwrite input)")
    dec.set_defaults(func=cmd_decrypt)


def cmd_encrypt(args: argparse.Namespace) -> int:
    env = parse_env_file(args.file)
    options = EncryptOptions(secrets_only=not args.all_keys)

    key_path = Path(args.key_file)
    if key_path.exists():
        key = key_path.read_bytes().strip()
        options.key = key
    else:
        options.key = generate_key()
        key_path.write_bytes(options.key)
        print(f"[envsync] Key written to {key_path}", file=sys.stderr)

    result = encrypt_env(env, options)
    output = args.output or args.file
    _write_env(result.to_env_file(output), output)
    print(f"[envsync] Encrypted {result.total_encrypted} value(s), skipped {result.total_skipped}.", file=sys.stderr)
    return 0


def cmd_decrypt(args: argparse.Namespace) -> int:
    key_path = Path(args.key_file)
    if not key_path.exists():
        print(f"[envsync] Key file not found: {key_path}", file=sys.stderr)
        return 1
    key = key_path.read_bytes().strip()
    env = parse_env_file(args.file)
    decrypted = decrypt_env(env, key)
    output = args.output or args.file
    _write_env(decrypted, output)
    print(f"[envsync] Decrypted {args.file} -> {output}", file=sys.stderr)
    return 0


def _write_env(env, path: str) -> None:
    lines = []
    for entry in env.entries:
        if entry.comment:
            lines.append(f"# {entry.comment}")
        lines.append(f"{entry.key}={entry.value}")
    Path(path).write_text("\n".join(lines) + "\n")
