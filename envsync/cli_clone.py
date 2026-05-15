"""CLI sub-command: envsync clone."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.cloner import CloneOptions, clone_env
from envsync.parser import parse_env_file


def add_clone_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "clone",
        help="Clone a .env file, optionally filtering or transforming keys.",
    )
    p.add_argument("source", help="Path to the source .env file.")
    p.add_argument("dest", help="Destination path for the cloned file.")
    p.add_argument(
        "--include",
        metavar="KEY",
        nargs="+",
        help="Only copy these keys.",
    )
    p.add_argument(
        "--exclude",
        metavar="KEY",
        nargs="+",
        default=[],
        help="Skip these keys.",
    )
    p.add_argument(
        "--uppercase-keys",
        action="store_true",
        help="Transform all keys to UPPER_CASE.",
    )
    p.add_argument(
        "--strip-comments",
        action="store_true",
        help="Omit comment and blank lines from the output.",
    )
    p.set_defaults(func=cmd_clone)


def cmd_clone(args: argparse.Namespace) -> int:
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"error: source file not found: {source_path}", file=sys.stderr)
        return 1

    source = parse_env_file(source_path)

    key_transform = (lambda k: k.upper()) if args.uppercase_keys else None

    options = CloneOptions(
        include_keys=args.include,
        exclude_keys=args.exclude or [],
        key_transform=key_transform,
        strip_comments=args.strip_comments,
    )

    result = clone_env(source, options)

    dest_path = Path(args.dest)
    lines = [
        (e.raw if e.raw is not None else f"{e.key}={e.value}")
        for e in result.env.entries
    ]
    dest_path.write_text("\n".join(lines) + ("\n" if lines else ""))

    print(
        f"Cloned {result.total_copied} key(s) to {dest_path}"
        + (f" ({result.total_skipped} skipped)" if result.was_filtered else ".")
    )
    return 0
