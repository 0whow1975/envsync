"""CLI sub-command: envsync score — report hygiene score for an .env file."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from envsync.parser import parse_env_file
from envsync.masker import SecretMasker, MaskConfig
from envsync.scorer import score_env


def add_score_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "score",
        help="Score an .env file for quality and hygiene.",
    )
    p.add_argument("env_file", help="Path to the .env file to score.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-below",
        type=int,
        default=None,
        metavar="N",
        help="Exit with code 1 if score is below N.",
    )
    p.set_defaults(func=cmd_score)


def cmd_score(args: Namespace) -> int:
    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 2

    masker = SecretMasker(MaskConfig())
    result = score_env(env, masker)

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(f"File  : {args.env_file}")
        print(f"Score : {result.score}/{result.max_score}  (Grade: {result.grade})")
        if result.issues:
            print("Issues:")
            for issue in result.issues:
                print(f"  - {issue}")
        else:
            print("Issues: none")

    if args.fail_below is not None and result.score < args.fail_below:
        return 1
    return 0
