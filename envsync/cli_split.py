"""CLI subcommand: split an .env file by key prefix."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.parser import parse_env_file
from envsync.splitter import SplitOptions, split_env


def add_split_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *split* subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "split",
        help="Split a .env file into multiple files by key prefix.",
    )
    parser.add_argument("env_file", help="Path to the source .env file.")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where split files are written (default: current directory).",
    )
    parser.add_argument(
        "--delimiter",
        default="_",
        help="Delimiter used to identify the prefix segment (default: '_').",
    )
    parser.add_argument(
        "--prefixes",
        nargs="+",
        metavar="PREFIX",
        help="Only extract these prefixes; all others go to remainder.env.",
    )
    parser.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove the prefix and delimiter from keys in the output files.",
    )
    parser.add_argument(
        "--no-remainder",
        action="store_true",
        default=False,
        help="Do not write remainder.env for unmatched keys.",
    )
    parser.set_defaults(func=cmd_split)


def cmd_split(args: argparse.Namespace) -> int:
    """Execute the split subcommand."""
    source = Path(args.env_file)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = parse_env_file(source)
    opts = SplitOptions(
        delimiter=args.delimiter,
        include_prefixes=args.prefixes,
        strip_prefix=args.strip_prefix,
    )
    result = split_env(env, opts)

    written: list[Path] = []
    for prefix, env_file in result.groups.items():
        out_path = output_dir / f"{prefix.lower()}.env"
        lines = [f"{e.key}={e.value}\n" for e in env_file.entries]
        out_path.write_text("".join(lines))
        written.append(out_path)
        print(f"  wrote {out_path}  ({len(env_file.entries)} keys)")

    if not args.no_remainder and result.remainder.entries:
        rem_path = output_dir / "remainder.env"
        lines = [f"{e.key}={e.value}\n" for e in result.remainder.entries]
        rem_path.write_text("".join(lines))
        written.append(rem_path)
        print(f"  wrote {rem_path}  ({len(result.remainder.entries)} keys)")

    print(f"\nSplit into {len(written)} file(s).")
    return 0
