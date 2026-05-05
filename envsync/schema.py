"""Schema loader — reads a .env.schema file listing required and optional keys."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

_COMMENT_RE = re.compile(r"^\s*#")
_REQUIRED_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*$")
_OPTIONAL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\?\s*$")


@dataclass
class EnvSchema:
    required: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)

    @property
    def all_keys(self) -> List[str]:
        return self.required + self.optional


def parse_schema_file(path: str | Path) -> EnvSchema:
    """Parse a .env.schema file.

    Lines ending with ``?`` are optional keys; plain identifiers are required.
    Lines starting with ``#`` and blank lines are ignored.
    """
    schema = EnvSchema()
    text = Path(path).read_text(encoding="utf-8")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or _COMMENT_RE.match(line):
            continue

        optional_match = _OPTIONAL_RE.match(line)
        if optional_match:
            schema.optional.append(optional_match.group(1))
            continue

        required_match = _REQUIRED_RE.match(line)
        if required_match:
            schema.required.append(required_match.group(1))

    return schema


def schema_to_validator_kwargs(schema: EnvSchema) -> dict:
    """Return kwargs suitable for constructing an EnvValidator from a schema."""
    return {"required_keys": schema.required}
