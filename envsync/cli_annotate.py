"""CLI sub-command: annotate — attach inline comments to .env keys."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envsync.annotator import AnnotateOptions, annotate
from envsync.parser import parse_env_file


def add_annotate_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "annotate",
        help="Attach inline comments to .env keys from a JSON annotation map.",
    )
    p.add_argument("env_file", help="Path to the .env file to annotate.")
    p.add_argument(
        "--map",
        required=True,
        metavar="JSON_FILE",
        help="JSON file mapping key names to comment strings.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing inline comments.",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Write changes back to the source file.",
    )
    p.set_defaults(func=cmd_annotate)


def cmd_annotate(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"error: annotation map not found: {map_path}", file=sys.stderr)
        return 1

    with map_path.open() as fh:
        annotations: dict = json.load(fh)

    env = parse_env_file(str(env_path))
    options = AnnotateOptions(annotations=annotations, overwrite=args.overwrite)
    result = annotate(env, options)

    lines = [
        f"{e.comment}\n{e.key}={e.value}" if e.comment else f"{e.key}={e.value}"
        for e in result.entries
        if e.key
    ]
    output = "\n".join(lines) + "\n"

    if args.in_place:
        env_path.write_text(output)
    else:
        print(output, end="")

    print(
        f"annotated {result.total_annotated} key(s), "
        f"skipped {result.total_skipped}",
        file=sys.stderr,
    )
    return 0
