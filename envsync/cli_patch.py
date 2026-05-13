"""CLI sub-command: ``envsync patch`` — apply key=value patches to a .env file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envsync.parser import parse_env_file
from envsync.patcher import PatchOptions, patch_env


def add_patch_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "patch",
        help="Apply key=value patches directly to a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to patch.")
    parser.add_argument(
        "patches",
        nargs="+",
        metavar="KEY=VALUE",
        help="One or more KEY=VALUE pairs to apply.",
    )
    parser.add_argument(
        "--no-overwrite",
        dest="no_overwrite",
        action="store_true",
        default=False,
        help="Skip keys that already exist in the file.",
    )
    parser.add_argument(
        "--no-add",
        dest="no_add",
        action="store_true",
        default=False,
        help="Skip keys that are not already present in the file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report changes without writing to disk.",
    )
    parser.set_defaults(func=cmd_patch)


def _parse_patches(raw: List[str]) -> dict[str, str]:
    patches: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            print(f"[error] Invalid patch format (expected KEY=VALUE): {item!r}", file=sys.stderr)
            sys.exit(1)
        key, _, value = item.partition("=")
        patches[key.strip()] = value
    return patches


def cmd_patch(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[error] File not found: {env_path}", file=sys.stderr)
        return 1

    env = parse_env_file(str(env_path))
    patches = _parse_patches(args.patches)

    options = PatchOptions(
        overwrite_existing=not args.no_overwrite,
        add_missing=not args.no_add,
        dry_run=args.dry_run,
    )

    result = patch_env(env, patches, options=options)

    action = "[dry-run]" if args.dry_run else "[patched]"
    for key in result.patched:
        print(f"{action} {key}")
    for key in result.skipped:
        print(f"[skipped] {key}")

    if not args.dry_run and result.env_file is not None:
        lines = [
            f"{e.key}={e.value}\n" for e in result.env_file.entries
        ]
        env_path.write_text("".join(lines))

    print(
        f"Done — {result.total_patched} patched, {result.total_skipped} skipped."
    )
    return 0
