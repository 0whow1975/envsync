"""CLI sub-command: envsync promote <source> <target>."""
from __future__ import annotations

import argparse
import sys

from envsync.parser import parse_env_file
from envsync.promoter import PromoteOptions, promote
from envsync.masker import SecretMasker, MaskConfig


def add_promote_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "promote",
        help="Promote env values from SOURCE into TARGET.",
    )
    p.add_argument("source", help="Path to the source .env file")
    p.add_argument("target", help="Path to the target .env file")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk",
    )
    p.add_argument(
        "--allow-removals",
        action="store_true",
        default=False,
        help="Also remove keys from target that are absent in source",
    )
    p.add_argument(
        "--only-keys",
        metavar="KEY",
        nargs="+",
        default=None,
        help="Restrict promotion to these specific keys",
    )
    p.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Show secret values in plain text",
    )
    p.set_defaults(func=cmd_promote)


def cmd_promote(args: argparse.Namespace) -> int:
    source = parse_env_file(args.source)
    target = parse_env_file(args.target)

    key_filter = None
    if args.only_keys:
        allowed = set(args.only_keys)
        key_filter = lambda k: k in allowed  # noqa: E731

    opts = PromoteOptions(
        key_filter=key_filter,
        allow_removals=args.allow_removals,
        dry_run=args.dry_run,
    )

    result = promote(source, target, opts)

    masker = SecretMasker(MaskConfig()) if not args.no_mask else None

    prefix = "[dry-run] " if args.dry_run else ""
    for entry in result.sync_result.applied:
        raw_val = entry.source_value or ""
        display = masker.mask_value(entry.key, raw_val) if masker else raw_val
        print(f"{prefix}{entry.change_type.value.upper():10s}  {entry.key}={display}")

    if result.skipped_keys:
        print(f"Skipped ({result.skipped_count}): {', '.join(result.skipped_keys)}",
              file=sys.stderr)

    print(f"\nPromoted {result.promoted_count} key(s) from {args.source} → {args.target}.")
    return 0
