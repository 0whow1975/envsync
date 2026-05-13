"""CLI sub-command: envsync compare <env1> <env2> [<env3> ...]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.parser import parse_env_file
from envsync.comparator import CompareOptions, compare_envs
from envsync.formatter import format_diff, format_summary


def add_compare_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "compare",
        help="Compare two or more .env files side-by-side",
    )
    p.add_argument(
        "envfiles",
        nargs="+",
        metavar="FILE",
        help=".env files to compare (at least two required)",
    )
    p.add_argument(
        "--baseline",
        metavar="LABEL",
        default=None,
        help="Treat this file label (stem) as the reference environment",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print only the summary line for each pair",
    )
    p.add_argument(
        "--no-color",
        dest="color",
        action="store_false",
        default=True,
        help="Disable ANSI colour output",
    )
    p.set_defaults(func=cmd_compare)


def cmd_compare(args: argparse.Namespace) -> int:
    if len(args.envfiles) < 2:
        print("error: at least two env files are required", file=sys.stderr)
        return 1

    envs = {}
    for path_str in args.envfiles:
        path = Path(path_str)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        label = path.stem
        envs[label] = parse_env_file(path)

    options = CompareOptions(baseline=getattr(args, "baseline", None))
    result = compare_envs(envs, options)

    for pair in result.pairs:
        header = f"--- {pair.label_a}  +++  {pair.label_b}"
        print(header)
        print("-" * len(header))
        if args.summary:
            print(format_summary(pair.diff))
        else:
            print(format_diff(pair.diff, color=args.color))
            print(format_summary(pair.diff))
        print()

    # Report keys missing from any env
    for label in envs:
        missing = result.keys_missing_from(label)
        if missing:
            print(f"Keys absent from [{label}]: {', '.join(missing)}")

    return 0
