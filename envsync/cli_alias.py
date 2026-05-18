"""CLI sub-command: alias — resolve key aliases in an env file."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envsync.aliaser import AliasOptions, resolve_aliases
from envsync.parser import parse_env_file


def _load_alias_map(path: str) -> dict:
    """Load alias map from a JSON file ({alias: canonical, ...})."""
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        print(f"error: alias map must be a JSON object, got {type(data).__name__}", file=sys.stderr)
        sys.exit(1)
    return {str(k): str(v) for k, v in data.items()}


def add_alias_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "alias",
        help="Resolve key aliases to canonical names in an env file",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("alias_map", help="JSON file mapping alias -> canonical key")
    p.add_argument(
        "--no-remove",
        dest="remove_alias",
        action="store_false",
        default=True,
        help="Keep alias keys instead of removing them after resolution",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite canonical key if it already exists",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Write result back to the source file",
    )
    p.set_defaults(func=cmd_alias)


def cmd_alias(args: Namespace) -> int:
    alias_map = _load_alias_map(args.alias_map)
    env = parse_env_file(args.env_file)
    options = AliasOptions(
        alias_map=alias_map,
        overwrite=args.overwrite,
        remove_alias=args.remove_alias,
    )
    result = resolve_aliases(env, options)

    if result.total_skipped:
        for v in result.skipped:
            print(f"skip: {v}", file=sys.stderr)

    lines = []
    for entry in result.entries:
        lines.append(entry.raw if entry.raw else f"{entry.key}={entry.value}")
    output = "\n".join(lines) + "\n"

    if args.in_place:
        Path(args.env_file).write_text(output)
    else:
        sys.stdout.write(output)

    print(
        f"resolved {result.total_resolved} alias(es), skipped {result.total_skipped}",
        file=sys.stderr,
    )
    return 0
