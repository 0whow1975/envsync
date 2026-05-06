"""CLI subcommands for snapshot management: take, list, restore."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envsync.parser import parse_env_file
from envsync.snapshotter import (
    list_snapshots,
    load_snapshot,
    restore_snapshot,
    save_snapshot,
    take_snapshot,
)

DEFAULT_SNAPSHOT_DIR = ".envsync_snapshots"


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("snapshot", help="Manage .env snapshots")
    sub = parser.add_subparsers(dest="snapshot_cmd", required=True)

    # take
    take_p = sub.add_parser("take", help="Take a snapshot of an .env file")
    take_p.add_argument("env_file", help="Path to the .env file")
    take_p.add_argument(
        "--snapshot-dir",
        default=DEFAULT_SNAPSHOT_DIR,
        help="Directory to store snapshots (default: .envsync_snapshots)",
    )

    # list
    list_p = sub.add_parser("list", help="List available snapshots")
    list_p.add_argument(
        "--snapshot-dir",
        default=DEFAULT_SNAPSHOT_DIR,
    )
    list_p.add_argument(
        "--filter",
        dest="filter_name",
        default=None,
        help="Filter by original env filename (e.g. .env)",
    )

    # restore
    restore_p = sub.add_parser("restore", help="Restore a snapshot to an .env file")
    restore_p.add_argument("snapshot_file", help="Path to the snapshot JSON file")
    restore_p.add_argument(
        "--output",
        default=None,
        help="Destination path (defaults to original path stored in snapshot)",
    )


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Dispatch snapshot sub-commands."""
    if args.snapshot_cmd == "take":
        return _cmd_take(args)
    if args.snapshot_cmd == "list":
        return _cmd_list(args)
    if args.snapshot_cmd == "restore":
        return _cmd_restore(args)
    print(f"Unknown snapshot command: {args.snapshot_cmd}", file=sys.stderr)
    return 1


def _cmd_take(args: argparse.Namespace) -> int:
    env = parse_env_file(args.env_file)
    snap = take_snapshot(env)
    dest = save_snapshot(snap, args.snapshot_dir)
    print(f"Snapshot saved: {dest}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    files = list_snapshots(args.snapshot_dir, env_filename=args.filter_name)
    if not files:
        print("No snapshots found.")
        return 0
    for f in files:
        print(str(f))
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    snap = load_snapshot(args.snapshot_file)
    dest = restore_snapshot(snap, dest_path=args.output)
    print(f"Restored snapshot to: {dest}")
    return 0
