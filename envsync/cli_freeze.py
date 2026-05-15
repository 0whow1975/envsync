"""CLI subcommands for freeze / drift-check."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.freezer import (
    FreezeOptions,
    check_drift,
    freeze_env,
    load_freeze,
    save_freeze,
)
from envsync.parser import parse_env_file


def add_freeze_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("freeze", help="Freeze env values and check for drift")
    sub = p.add_subparsers(dest="freeze_cmd", required=True)

    take = sub.add_parser("take", help="Capture a freeze of an env file")
    take.add_argument("env_file", help="Path to .env file")
    take.add_argument("--output", "-o", required=True, help="Destination .freeze.json file")

    check = sub.add_parser("check", help="Check an env file against a freeze")
    check.add_argument("freeze_file", help="Path to .freeze.json")
    check.add_argument("env_file", help="Path to current .env file")

    p.set_defaults(func=cmd_freeze)


def cmd_freeze(args: argparse.Namespace) -> int:
    if args.freeze_cmd == "take":
        return _cmd_take(args)
    if args.freeze_cmd == "check":
        return _cmd_check(args)
    return 1


def _cmd_take(args: argparse.Namespace) -> int:
    env = parse_env_file(Path(args.env_file))
    result = freeze_env(env, FreezeOptions())
    dest = Path(args.output)
    save_freeze(result, dest)
    print(f"Frozen {result.key_count} keys → {dest}  (checksum: {result.checksum[:12]}…)")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    frozen = load_freeze(Path(args.freeze_file))
    current = parse_env_file(Path(args.env_file))
    report = check_drift(frozen, current)

    if report.is_clean:
        print("✓ No drift detected.")
        return 0

    if report.drifted:
        print(f"⚠  {len(report.drifted)} key(s) changed value:")
        for d in report.drifted:
            print(f"   {d.key}")
    if report.missing:
        print(f"✗  {len(report.missing)} key(s) removed: {', '.join(report.missing)}")
    if report.added:
        print(f"+  {len(report.added)} key(s) added: {', '.join(report.added)}")
    return 1
