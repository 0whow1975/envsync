"""CLI subcommand: filter — select .env entries by prefix or pattern."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envsync.parser import parse_env_file
from envsync.pinecone_filter import FilterOptions, filter_env


def add_filter_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "filter",
        help="Print only the .env entries that match the given criteria.",
    )
    p.add_argument("env_file", help="Path to the .env file to filter.")
    p.add_argument(
        "--prefix",
        dest="prefixes",
        metavar="PREFIX",
        action="append",
        default=[],
        help="Keep entries whose key starts with PREFIX (repeatable).",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Keep entries whose key matches REGEX (repeatable).",
    )
    p.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert the filter — print entries that do NOT match.",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Apply prefix/pattern matching case-sensitively.",
    )
    p.set_defaults(func=cmd_filter)


def cmd_filter(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    opts = FilterOptions(
        prefixes=args.prefixes,
        patterns=args.patterns,
        invert=args.invert,
        case_sensitive=args.case_sensitive,
    )

    result = filter_env(env, opts)

    for entry in result.matched:
        print(entry.raw)

    return 0
