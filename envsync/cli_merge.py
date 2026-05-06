"""CLI sub-command: merge multiple .env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.merger import ConflictStrategy, MergeError, merge
from envsync.parser import parse_env_file


def add_merge_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "merge",
        help="Merge multiple .env files into one",
    )
    p.add_argument(
        "sources",
        nargs="+",
        metavar="FILE",
        help=".env files to merge (in order)",
    )
    p.add_argument(
        "-o", "--output",
        metavar="FILE",
        default=None,
        help="Write merged output to FILE (default: stdout)",
    )
    p.add_argument(
        "--strategy",
        choices=[s.value for s in ConflictStrategy],
        default=ConflictStrategy.LAST.value,
        help="Conflict resolution strategy (default: last)",
    )
    p.add_argument(
        "--no-comments",
        action="store_true",
        help="Strip comment lines from merged output",
    )
    p.set_defaults(func=cmd_merge)


def cmd_merge(args: argparse.Namespace) -> int:
    strategy = ConflictStrategy(args.strategy)
    env_files = []
    for src in args.sources:
        path = Path(src)
        if not path.exists():
            print(f"error: file not found: {src}", file=sys.stderr)
            return 1
        env_files.append(parse_env_file(str(path)))

    try:
        result = merge(env_files, strategy=strategy, ignore_comments=getattr(args, "no_comments", False))
    except MergeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if result.has_conflicts:
        for conflict in result.conflicts:
            print(f"warning: {conflict}", file=sys.stderr)

    lines = []
    for entry in result.merged.entries:
        if entry.comment:
            lines.append(entry.raw)
        else:
            lines.append(f"{entry.key}={entry.value}")
    output = "\n".join(lines) + "\n"

    if args.output:
        Path(args.output).write_text(output)
        print(f"Merged {len(args.sources)} files -> {args.output}")
    else:
        sys.stdout.write(output)

    return 0
