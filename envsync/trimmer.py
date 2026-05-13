"""Trim whitespace and normalize values in .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envsync.parser import EnvEntry, EnvFile


@dataclass
class TrimOptions:
    """Options controlling trim behaviour."""
    strip_keys: bool = True
    strip_values: bool = True
    normalize_empty: bool = True  # collapse whitespace-only values to ""
    skip_comments: bool = True


@dataclass
class TrimResult:
    """Result of a trim operation."""
    entries: List[EnvEntry] = field(default_factory=list)
    total_trimmed: int = 0

    @property
    def was_modified(self) -> bool:
        return self.total_trimmed > 0

    def to_env_file(self, path: str = "") -> EnvFile:
        env = EnvFile(path=path)
        for entry in self.entries:
            env._entries.append(entry)
        return env


def _trim_entry(entry: EnvEntry, opts: TrimOptions) -> tuple[EnvEntry, bool]:
    """Return a (possibly new) entry and whether it changed."""
    if entry.is_comment or entry.is_blank:
        return entry, False

    key = entry.key.strip() if opts.strip_keys else entry.key
    value = entry.value

    if opts.strip_values:
        value = value.strip()

    if opts.normalize_empty and value.strip() == "":
        value = ""

    changed = key != entry.key or value != entry.value
    if changed:
        new_entry = EnvEntry(
            key=key,
            value=value,
            raw=f"{key}={value}",
            is_comment=entry.is_comment,
            is_blank=entry.is_blank,
        )
        return new_entry, True
    return entry, False


def trim_env(env: EnvFile, opts: TrimOptions | None = None) -> TrimResult:
    """Trim and normalise all entries in *env*.

    Returns a :class:`TrimResult` with cleaned entries and a count of
    how many entries were modified.
    """
    if opts is None:
        opts = TrimOptions()

    result = TrimResult()
    for entry in env:
        cleaned, changed = _trim_entry(entry, opts)
        result.entries.append(cleaned)
        if changed:
            result.total_trimmed += 1

    return result
