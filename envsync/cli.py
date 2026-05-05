"""Command-line interface for envsync.

Provides commands to diff and sync .env files across environments,
with optional secret masking for safe output.
"""

import argparse
import sys
from pathlib import Path

from envsync.diff import diff_env_files
from envsync.formatter import format_diff
from envsync.masker import MaskConfig, SecretMasker
from envsync.parser import parse_env_file
from envsync.syncer import Syncer, SyncOptions


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="envsync",
        description="Diff and sync .env files across environments.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # --- diff sub-command ---
    diff_cmd = subparsers.add_parser(
        "diff",
        help="Show differences between two .env files.",
    )
    diff_cmd.add_argument("source", metavar="SOURCE", help="Source .env file (reference).")
    diff_cmd.add_argument("target", metavar="TARGET", help="Target .env file to compare.")
    diff_cmd.add_argument(
        "--no-mask",
        dest="no_mask",
        action="store_true",
        default=False,
        help="Disable secret masking in output (shows plain values).",
    )
    diff_cmd.add_argument(
        "--case-sensitive",
        dest="case_sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive matching for secret key detection.",
    )

    # --- sync sub-command ---
    sync_cmd = subparsers.add_parser(
        "sync",
        help="Sync missing or changed keys from source into target.",
    )
    sync_cmd.add_argument("source", metavar="SOURCE", help="Source .env file (reference).")
    sync_cmd.add_argument("target", metavar="TARGET", help="Target .env file to update.")
    sync_cmd.add_argument(
        "--add-missing",
        dest="add_missing",
        action="store_true",
        default=True,
        help="Add keys present in source but missing from target (default: true).",
    )
    sync_cmd.add_argument(
        "--update-changed",
        dest="update_changed",
        action="store_true",
        default=False,
        help="Overwrite keys whose values differ between source and target.",
    )
    sync_cmd.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk.",
    )

    return parser


def cmd_diff(args: argparse.Namespace) -> int:
    """Execute the diff sub-command."""
    source_path = Path(args.source)
    target_path = Path(args.target)

    for path in (source_path, target_path):
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1

    source_env = parse_env_file(source_path)
    target_env = parse_env_file(target_path)
    result = diff_env_files(source_env, target_env)

    masker: SecretMasker | None = None
    if not args.no_mask:
        masker = SecretMasker(MaskConfig(case_sensitive=args.case_sensitive))

    output = format_diff(result, masker=masker)
    print(output, end="")
    return 0 if not result.has_changes() else 0  # non-zero could be a future --strict flag


def cmd_sync(args: argparse.Namespace) -> int:
    """Execute the sync sub-command."""
    source_path = Path(args.source)
    target_path = Path(args.target)

    for path in (source_path, target_path):
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1

    source_env = parse_env_file(source_path)
    target_env = parse_env_file(target_path)

    options = SyncOptions(
        add_missing=args.add_missing,
        update_changed=args.update_changed,
        dry_run=args.dry_run,
    )
    syncer = Syncer(source_env, target_env, options)
    sync_result = syncer.sync()

    label = "[dry-run] " if args.dry_run else ""
    print(f"{label}Sync complete: {sync_result.total_changes()} change(s) applied.")
    for key in sync_result.added:
        print(f"  + {key}")
    for key in sync_result.updated:
        print(f"  ~ {key}")

    if not args.dry_run and sync_result.total_changes() > 0:
        target_path.write_text(sync_result.content)

    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the envsync CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        return cmd_diff(args)
    if args.command == "sync":
        return cmd_sync(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
