"""CLI sub-command: envsync watch — live-poll two .env files for drift."""
from __future__ import annotations

import argparse
from pathlib import Path

from envsync.watcher import EnvWatcher, WatchEvent, WatchOptions
from envsync.formatter import format_diff
from envsync.masker import SecretMasker, MaskConfig


def add_watch_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "watch",
        help="Poll source and target .env files and print diffs as they appear.",
    )
    p.add_argument("source", type=Path, help="Source .env file")
    p.add_argument("target", type=Path, help="Target .env file")
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 2.0)",
    )
    p.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Disable secret masking in output",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour output",
    )
    p.set_defaults(func=cmd_watch)


def cmd_watch(args: argparse.Namespace) -> None:
    masker = None if args.no_mask else SecretMasker(MaskConfig())

    def on_change(event: WatchEvent) -> None:
        print(
            f"\n[envsync watch] change detected "
            f"(source={event.source_path.name}, "
            f"target={event.target_path.name})"
        )
        output = format_diff(event.diff, masker=masker, color=args.color)
        print(output if output.strip() else "  (no diff — files are in sync)")

    opts = WatchOptions(poll_interval=args.interval)
    watcher = EnvWatcher(
        source=args.source,
        target=args.target,
        on_change=on_change,
        options=opts,
    )
    print(
        f"[envsync watch] watching {args.source} vs {args.target} "
        f"(interval={args.interval}s) — Ctrl-C to stop"
    )
    try:
        watcher.run()
    except KeyboardInterrupt:
        print("\n[envsync watch] stopped.")
