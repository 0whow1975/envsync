"""Parser for .env files — handles reading, tokenizing, and writing."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

ENV_LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
COMMENT_RE = re.compile(r"^\s*#.*$")


@dataclass
class EnvEntry:
    key: str
    value: str
    comment: Optional[str] = None  # inline comment stripped from value
    raw_line: str = ""


@dataclass
class EnvFile:
    path: Path
    entries: Dict[str, EnvEntry] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)  # preserves insertion order

    def get(self, key: str) -> Optional[str]:
        entry = self.entries.get(key)
        return entry.value if entry else None

    def keys(self) -> List[str]:
        return list(self.order)


def parse_env_file(path: str | Path) -> EnvFile:
    """Parse a .env file and return an EnvFile instance."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    env_file = EnvFile(path=path)

    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")

            if not line.strip() or COMMENT_RE.match(line):
                continue

            match = ENV_LINE_RE.match(line)
            if match:
                key, value = match.group(1), match.group(2)
                value, inline_comment = _split_inline_comment(value)
                entry = EnvEntry(
                    key=key,
                    value=_strip_quotes(value),
                    comment=inline_comment,
                    raw_line=raw_line,
                )
                env_file.entries[key] = entry
                if key not in env_file.order:
                    env_file.order.append(key)

    return env_file


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _split_inline_comment(value: str) -> tuple[str, Optional[str]]:
    """Split value from an inline comment (unquoted # portion)."""
    if '#' not in value:
        return value, None
    # Only split on # outside of quotes
    in_quote = None
    for i, ch in enumerate(value):
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
        elif ch == in_quote:
            in_quote = None
        elif ch == '#' and in_quote is None:
            return value[:i].rstrip(), value[i:]
    return value, None
