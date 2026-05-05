"""CLI helpers for the 'export' sub-command."""

from __future__ import annotations

import argparse
from pathlib import Path

from envsync.diff import diff_env_files
from envsync.exporter import ExportOptions, export_diff
from envsync.masker import MaskConfig, SecretMasker


def add_export_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "export",
        help="Export diff between two .env files to a structured format.",
    )
    parser.add_argument("source", type=Path, help="Source .env file")
    parser.add_argument("target", type=Path, help="Target .env file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output file path")
    parser.add_argument(
        "--format",
        choices=["json", "csv", "dotenv"],
        default="json",
        help="Export format (default: json)",
    )
    parser.add_argument(
        "--include-unchanged",
        action="store_true",
        default=False,
        help="Include unchanged keys in the export",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Disable secret masking in the export",
    )
    parser.set_defaults(func=cmd_export)


def cmd_export(args: argparse.Namespace) -> int:
    """Execute the export sub-command. Returns an exit code."""
    diff = diff_env_files(args.source, args.target)

    masker = None if args.no_mask else SecretMasker(MaskConfig())
    options = ExportOptions(
        format=args.format,
        mask_secrets=not args.no_mask,
        include_unchanged=args.include_unchanged,
    )

    export_diff(diff, args.output, options=options, masker=masker)
    print(f"Exported diff to {args.output} ({args.format})")
    return 0
