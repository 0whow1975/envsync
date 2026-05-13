"""CLI sub-command: envsync profile <file>"""
from __future__ import annotations

import argparse
import json
import sys

from envsync.parser import parse_env_file
from envsync.masker import MaskConfig
from envsync.profiler import profile_env


def add_profile_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "profile",
        help="Show statistics about an .env file.",
    )
    p.add_argument("file", help="Path to the .env file to profile.")
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Output result as JSON.",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive secret-key matching.",
    )
    p.set_defaults(func=cmd_profile)


def cmd_profile(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    mask_config = MaskConfig(case_sensitive=getattr(args, "case_sensitive", False))
    result = profile_env(env, mask_config=mask_config)

    if args.as_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result)

    return 0
