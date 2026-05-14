"""CLI sub-command: envsync rotate — bulk key rotation across env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envsync.parser import parse_env_file
from envsync.rotator import RotateOptions, rotate_key
from envsync.syncer import _write_env_file  # reuse existing write helper


def add_rotate_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("rotate", help="Rename keys across one or more .env files")
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to update")
    p.add_argument(
        "--rename",
        action="append",
        metavar="OLD=NEW",
        required=True,
        help="Key rename mapping, e.g. --rename OLD_KEY=NEW_KEY (repeatable)",
    )
    p.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Error if a key is missing from any file (default: skip silently)",
    )
    p.set_defaults(func=cmd_rotate)


def _parse_rename_map(rename_args: List[str]) -> dict:
    mapping: dict = {}
    for item in rename_args:
        if "=" not in item:
            print(f"[error] invalid --rename value '{item}', expected OLD=NEW", file=sys.stderr)
            sys.exit(1)
        old, new = item.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def cmd_rotate(args: argparse.Namespace) -> int:
    rename_map = _parse_rename_map(args.rename)
    opts = RotateOptions(dry_run=args.dry_run, ignore_missing=not args.strict)

    env_files = [parse_env_file(p) for p in args.files]
    updated, result = rotate_key(env_files, rename_map, opts)

    if result.has_violations:
        for v in result.violations:
            print(f"[error] {v}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] would rotate {result.total_rotated} key(s) across {len(args.files)} file(s)")
        for old_key, paths in result.rotated.items():
            new_key = rename_map[old_key]
            for path in paths:
                print(f"  {path}: {old_key} -> {new_key}")
        return 0

    for env_file in updated:
        _write_env_file(Path(env_file.path), env_file)

    print(f"Rotated {result.total_rotated} key(s), skipped {result.total_skipped} key(s)")
    return 0
