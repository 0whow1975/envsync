"""CLI sub-command: normalize"""
from __future__ import annotations

import argparse
import sys

from envsync.normalizer import NormalizeOptions, normalize_env
from envsync.parser import parse_env_file


def add_normalize_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "normalize",
        help="Normalize keys and values in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to normalize.")
    p.add_argument(
        "--inplace", "-i",
        action="store_true",
        default=False,
        help="Write normalized output back to the original file.",
    )
    p.add_argument(
        "--lowercase-keys",
        action="store_true",
        default=False,
        help="Convert all keys to lower-case.",
    )
    p.add_argument(
        "--remove-empty",
        action="store_true",
        default=False,
        help="Drop entries whose value is empty.",
    )
    p.add_argument(
        "--quote-values",
        action="store_true",
        default=False,
        help="Wrap every value in double quotes.",
    )
    p.set_defaults(func=cmd_normalize)


def _build_output(result) -> str:
    """Serialize normalized env entries to a .env-formatted string."""
    lines = [
        f"{e.key}={e.value}" if e.value is not None else f"{e.key}="
        for e in result.entries
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def cmd_normalize(args: argparse.Namespace) -> int:
    """Entry point for the ``normalize`` sub-command."""
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    opts = NormalizeOptions(
        strip_whitespace=True,
        lowercase_keys=args.lowercase_keys,
        remove_empty=args.remove_empty,
        quote_values=args.quote_values,
    )

    result = normalize_env(env, opts)
    output = _build_output(result)

    if args.inplace:
        try:
            with open(args.file, "w", encoding="utf-8") as fh:
                fh.write(output)
        except OSError as exc:
            print(f"error: could not write to {args.file}: {exc}", file=sys.stderr)
            return 1
        print(
            f"normalized {args.file}: "
            f"{result.total_changed} changed, {result.total_removed} removed."
        )
    else:
        sys.stdout.write(output)

    return 0
