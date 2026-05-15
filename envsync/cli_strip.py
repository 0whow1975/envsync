"""CLI sub-command: strip comments and blank lines from a .env file."""
from __future__ import annotations

import argparse
import sys

from envsync.parser import parse_env_file
from envsync.stripper import StripOptions, strip_env


def add_strip_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "strip",
        help="Remove comments and blank lines from a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to strip.")
    p.add_argument(
        "--keep-comments",
        action="store_true",
        default=False,
        help="Preserve comment lines.",
    )
    p.add_argument(
        "--keep-blanks",
        action="store_true",
        default=False,
        help="Preserve blank lines.",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the source file instead of printing to stdout.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be removed without writing anything.",
    )
    p.set_defaults(func=cmd_strip)


def cmd_strip(args: argparse.Namespace) -> int:
    env = parse_env_file(args.file)
    options = StripOptions(
        remove_comments=not args.keep_comments,
        remove_blank_lines=not args.keep_blanks,
        dry_run=args.dry_run,
    )
    result = strip_env(env, options)

    if args.dry_run:
        print(result.summary())
        return 0

    output_lines = [
        (e.raw if e.raw.endswith("\n") else e.raw + "\n")
        for e in result.stripped.entries
    ]
    content = "".join(output_lines)

    if args.in_place:
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(result.summary())
    else:
        sys.stdout.write(content)

    return 0
