"""Normalize .env file values to a canonical form."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envsync.parser import EnvEntry, EnvFile


@dataclass
class NormalizeOptions:
    """Options controlling normalization behaviour."""
    strip_whitespace: bool = True
    lowercase_keys: bool = False
    remove_empty: bool = False
    quote_values: bool = False  # wrap every value in double quotes


@dataclass
class NormalizeResult:
    entries: List[EnvEntry]
    total_changed: int = 0
    total_removed: int = 0

    @property
    def was_modified(self) -> bool:
        return self.total_changed > 0 or self.total_removed > 0

    def to_env_file(self, path: str = "") -> EnvFile:
        from envsync.parser import EnvFile
        ef = EnvFile(path=path, entries=self.entries)
        return ef


def _normalize_entry(
    entry: EnvEntry,
    opts: NormalizeOptions,
) -> tuple[EnvEntry | None, bool]:
    """Return (normalized_entry, changed).  None means the entry should be dropped."""
    key = entry.key
    value = entry.value
    changed = False

    if opts.strip_whitespace:
        new_key = key.strip()
        new_value = value.strip() if value is not None else value
        if new_key != key or new_value != value:
            changed = True
        key, value = new_key, new_value

    if opts.lowercase_keys:
        new_key = key.lower()
        if new_key != key:
            changed = True
        key = new_key

    if opts.remove_empty and (value is None or value == ""):
        return None, True

    if opts.quote_values and value is not None:
        if not (value.startswith('"') and value.endswith('"')):
            value = f'"{value}"'
            changed = True

    if not changed:
        return entry, False

    return EnvEntry(
        key=key,
        value=value,
        comment=entry.comment,
        raw_line=entry.raw_line,
    ), True


def normalize_env(
    env: EnvFile,
    opts: NormalizeOptions | None = None,
) -> NormalizeResult:
    """Apply normalization rules to all entries in *env*."""
    if opts is None:
        opts = NormalizeOptions()

    normalized: List[EnvEntry] = []
    total_changed = 0
    total_removed = 0

    for entry in env.entries:
        result, changed = _normalize_entry(entry, opts)
        if result is None:
            total_removed += 1
        else:
            normalized.append(result)
            if changed:
                total_changed += 1

    return NormalizeResult(
        entries=normalized,
        total_changed=total_changed,
        total_removed=total_removed,
    )
