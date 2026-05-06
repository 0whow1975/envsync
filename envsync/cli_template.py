"""CLI sub-command: envsync template — generate .env template files."""
from __future__ import annotations

import argparse
from pathlib import Path

from envsync.parser import parse_env_file
from envsync.schema import parse_schema_file
from envsync.masker import MaskConfig
from envsync.templater import TemplateOptions, generate_template, generate_template_from_schema, save_template


def add_template_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "template",
        help="Generate a .env template with secrets masked or blanked out.",
    )
    source_group = p.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--env", metavar="FILE", help="Source .env file.")
    source_group.add_argument("--schema", metavar="FILE", help="Schema TOML/JSON file.")
    p.add_argument("--output", "-o", metavar="FILE", default=None, help="Destination file (default: stdout).")
    p.add_argument("--placeholder", default="", help="Value to use for masked/blank entries.")
    p.add_argument("--no-mask", action="store_true", help="Do not mask secret values.")
    p.add_argument("--no-comments", action="store_true", help="Omit comments from output.")
    p.set_defaults(func=cmd_template)


def cmd_template(args: argparse.Namespace) -> int:
    opts = TemplateOptions(
        mask_secrets=not args.no_mask,
        include_comments=not args.no_comments,
        placeholder=args.placeholder,
        mask_config=MaskConfig(),
    )

    if args.env:
        env_file = parse_env_file(Path(args.env))
        content = generate_template(env_file, opts)
    else:
        schema = parse_schema_file(Path(args.schema))
        content = generate_template_from_schema(schema, opts)

    if args.output:
        dest = Path(args.output)
        save_template(content, dest)
        print(f"Template written to {dest}")
    else:
        print(content, end="")

    return 0
