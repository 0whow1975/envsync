"""CLI sub-commands for tagging: ``envsync tag list`` and ``envsync tag filter``."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List

from envsync.parser import parse_env_file
from envsync.tagger import TagOptions, filter_by_tag, tag_entries


def _load_tag_map(path: str) -> Dict[str, List[str]]:
    """Load a JSON file mapping env-key -> list[tag]."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        print("error: tag-map must be a JSON object", file=sys.stderr)
        sys.exit(1)
    return {k: list(v) for k, v in data.items()}


def add_tag_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("tag", help="Tag and filter .env entries")
    sub = parser.add_subparsers(dest="tag_cmd", required=True)

    # --- list sub-command ---
    lst = sub.add_parser("list", help="Show tags assigned to each key")
    lst.add_argument("env_file", help="Path to .env file")
    lst.add_argument("tag_map", help="JSON file mapping key -> [tags]")
    lst.add_argument("--case-sensitive", action="store_true", default=False)

    # --- filter sub-command ---
    flt = sub.add_parser("filter", help="Print keys that carry a given tag")
    flt.add_argument("env_file", help="Path to .env file")
    flt.add_argument("tag_map", help="JSON file mapping key -> [tags]")
    flt.add_argument("tag", help="Tag to filter on")
    flt.add_argument("--case-sensitive", action="store_true", default=False)


def cmd_tag(args: argparse.Namespace) -> int:
    env = parse_env_file(args.env_file)
    tag_map = _load_tag_map(args.tag_map)
    opts = TagOptions(case_sensitive=args.case_sensitive)

    if args.tag_cmd == "list":
        result = tag_entries(env, tag_map, opts)
        for key, tags in sorted(result.tagged.items()):
            print(f"{key}: {', '.join(sorted(tags))}")
        if result.skipped:
            print(f"\n(skipped / untagged: {', '.join(sorted(result.skipped))})")
        return 0

    if args.tag_cmd == "filter":
        entries = filter_by_tag(env, tag_map, args.tag, opts)
        for entry in entries:
            print(entry.raw)
        return 0

    print(f"Unknown tag sub-command: {args.tag_cmd}", file=sys.stderr)
    return 1
