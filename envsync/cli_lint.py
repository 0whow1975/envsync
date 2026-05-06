"""CLI subcommand: envsync lint — lint a .env file for common issues."""
from __future__ import annotations

import argparse
import sys

from envsync.linter import LintSeverity, lint_env_file
from envsync.parser import parse_env_file


def add_lint_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "lint",
        help="Lint a .env file for common issues",
    )
    parser.add_argument("env_file", help="Path to the .env file to lint")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors (exit 1 if any warnings found)",
    )
    parser.add_argument(
        "--no-warnings",
        dest="no_warnings",
        action="store_true",
        default=False,
        help="Suppress warning-level issues from output",
    )
    parser.set_defaults(func=cmd_lint)


def cmd_lint(args: argparse.Namespace) -> int:
    env = parse_env_file(args.env_file)
    result = lint_env_file(env)

    issues = result.issues
    if args.no_warnings:
        issues = [i for i in issues if i.severity != LintSeverity.WARNING]

    if not issues:
        print(f"✔  {args.env_file}: no issues found")
        return 0

    for issue in issues:
        print(issue)

    error_count = len(result.errors)
    warning_count = len(result.warnings)
    print(f"\n{error_count} error(s), {warning_count} warning(s)")

    if error_count > 0:
        return 1
    if args.strict and warning_count > 0:
        return 1
    return 0
