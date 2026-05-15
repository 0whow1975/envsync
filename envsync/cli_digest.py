"""CLI sub-command: digest — compute and compare .env file digests."""
from __future__ import annotations

import argparse
import json
import sys

from envsync.digester import DigestOptions, compare_digests, digest_env
from envsync.parser import parse_env_file


def add_digest_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "digest",
        help="Compute a content digest for one or two .env files.",
    )
    p.add_argument("source", help="Primary .env file")
    p.add_argument("target", nargs="?", default=None, help="Optional second file to compare")
    p.add_argument(
        "--algorithm",
        default="sha256",
        choices=["sha256", "md5", "sha1"],
        help="Hashing algorithm (default: sha256)",
    )
    p.add_argument("--keys-only", action="store_true", help="Hash keys only, ignoring values")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_digest)


def cmd_digest(args: argparse.Namespace) -> int:
    opts = DigestOptions(
        algorithm=args.algorithm,
        keys_only=getattr(args, "keys_only", False),
    )

    source_env = parse_env_file(args.source)
    source_result = digest_env(source_env, opts)

    if args.target is None:
        if args.as_json:
            print(json.dumps(source_result.to_dict(), indent=2))
        else:
            print(f"File   : {source_result.path}")
            print(f"Keys   : {source_result.key_count}")
            print(f"Algo   : {source_result.algorithm}")
            print(f"Digest : {source_result.overall_digest}")
        return 0

    target_env = parse_env_file(args.target)
    target_result = digest_env(target_env, opts)
    diffs = compare_digests(source_result, target_result)

    if args.as_json:
        payload = {
            "source": source_result.to_dict(),
            "target": target_result.to_dict(),
            "match": not diffs,
            "differing_keys": diffs,
        }
        print(json.dumps(payload, indent=2))
    else:
        match_label = "MATCH" if not diffs else "MISMATCH"
        print(f"Source : {source_result.overall_digest}  ({args.source})")
        print(f"Target : {target_result.overall_digest}  ({args.target})")
        print(f"Result : {match_label}")
        if diffs:
            print("\nDiffering keys:")
            for key, change in diffs.items():
                print(f"  {key}: {change}")

    return 1 if diffs else 0
