"""Flatten nested key structures into a single-level .env file.

Supports keys using dot or double-underscore notation as a separator,
e.g. ``DB__HOST`` or ``DB.HOST`` → group ``DB``, key ``HOST``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class FlattenOptions:
    separator: str = "__"          # separator that marks nesting levels
    max_depth: int = 1             # how many levels to peel off
    prefix_filter: Optional[str] = None  # only flatten keys that start with this prefix


@dataclass
class FlattenGroup:
    prefix: str
    entries: List[EnvEntry] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)


@dataclass
class FlattenResult:
    groups: Dict[str, FlattenGroup] = field(default_factory=dict)
    ungrouped: List[EnvEntry] = field(default_factory=list)
    options: FlattenOptions = field(default_factory=FlattenOptions)

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_keys(self) -> int:
        grouped = sum(g.size for g in self.groups.values())
        return grouped + len(self.ungrouped)

    def to_env_file(self) -> EnvFile:
        """Return a flat EnvFile with all entries in group-then-ungrouped order."""
        entries: List[EnvEntry] = []
        for group in sorted(self.groups.values(), key=lambda g: g.prefix):
            entries.extend(group.entries)
        entries.extend(self.ungrouped)
        return EnvFile(entries=entries, path=None)


def flatten_env(env: EnvFile, options: Optional[FlattenOptions] = None) -> FlattenResult:
    """Group entries by the leading segment(s) of their key.

    Keys that contain *separator* are split and placed into the matching
    :class:`FlattenGroup`.  All other keys land in ``result.ungrouped``.
    """
    if options is None:
        options = FlattenOptions()

    result = FlattenResult(options=options)

    for entry in env.entries:
        # Pass through comments and blank lines as ungrouped
        if entry.key is None:
            result.ungrouped.append(entry)
            continue

        key = entry.key

        if options.prefix_filter and not key.upper().startswith(options.prefix_filter.upper()):
            result.ungrouped.append(entry)
            continue

        sep = options.separator
        if sep in key:
            parts = key.split(sep, options.max_depth)
            prefix = parts[0]
            if prefix not in result.groups:
                result.groups[prefix] = FlattenGroup(prefix=prefix)
            result.groups[prefix].entries.append(entry)
        else:
            result.ungrouped.append(entry)

    return result
